# =============================================================================
# scrapers/kalibrr.py — KalibrrScraper
#
# WHAT IS KALIBRR?
# ----------------
# Kalibrr (kalibrr.com) is a modern job platform popular with PH tech companies.
# It's a Single Page Application (SPA) — unlike PhilJobNet, it doesn't put job
# data directly in the HTML. Instead, the page's JavaScript code fetches jobs
# from Kalibrr's private API in the background after you load the page.
#
# HOW WE SCRAPE IT (API fetch from inside the browser):
# -------------------------------------------------------
# Instead of parsing HTML, we use Playwright to:
# 1. Load the Kalibrr jobs page (so we're on the kalibrr.com domain)
# 2. Call fetch() from INSIDE the browser's JavaScript context using
#    page.evaluate() — this lets us hit the API as if we were the site itself,
#    bypassing CORS (Cross-Origin Resource Sharing) restrictions.
# 3. Parse the clean JSON response — no HTML scraping needed.
#
# WHY FETCH FROM INSIDE THE BROWSER?
# -----------------------------------
# If you tried to call the Kalibrr API directly from Python's requests library,
# the API server would reject you with a CORS error because you're not on the
# kalibrr.com domain. But since we load the page first, the browser IS on
# kalibrr.com — so the fetch() call is allowed.
#
# HOW TO RUN:
#   make up  (start Postgres)
#   make scrape-kalibrr
# =============================================================================

import logging
import os

from playwright.sync_api import sync_playwright

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# The internal API endpoint Kalibrr's own frontend uses to fetch job listings.
# Discovered by opening browser DevTools → Network tab → watching XHR requests
# while browsing https://www.kalibrr.com/home/te/it-software/co/Philippines
KALIBRR_API = "https://www.kalibrr.com/kjs/job_board/search"

# How many jobs to request per API call (matches Kalibrr's default page size)
BATCH_SIZE = 15

# Stop after this many jobs to avoid hammering the server
MAX_RECORDS = 500


class KalibrrScraper(BaseScraper):
    """
    Scraper for kalibrr.com — fetches jobs via Kalibrr's internal JSON API.

    Key technique: page.evaluate() runs JavaScript inside the browser,
    allowing us to use fetch() on the kalibrr.com domain without CORS issues.
    """

    SOURCE = "kalibrr"

    def scrape(self) -> list[dict]:
        """Opens browser, pages through Kalibrr's API, returns all job dicts."""
        records = []

        with sync_playwright() as p:
            browser, context = self.get_browser_context(p)
            page = context.new_page()

            try:
                records = self._scrape_via_api(page)
            finally:
                browser.close()

        return records

    def _scrape_via_api(self, page) -> list[dict]:
        """
        Paginates through Kalibrr's job search API using offset-based pagination.

        offset=0  → jobs 1-15
        offset=15 → jobs 16-30
        offset=30 → jobs 31-45
        ... and so on until the API returns an empty list.
        """
        records = []
        offset = 0

        # Load the Kalibrr jobs page first so the browser is on the kalibrr.com
        # domain — required for fetch() to work without CORS errors.
        logger.info("[kalibrr] Loading Kalibrr jobs page to establish domain context")
        page.goto(
            "https://www.kalibrr.com/home/te/it-software/co/Philippines",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        self._random_delay(3, 6)

        while len(records) < MAX_RECORDS:
            api_url = (
                f"{KALIBRR_API}"
                f"?limit={BATCH_SIZE}"
                f"&offset={offset}"
                f"&country=Philippines"
            )

            logger.info("[kalibrr] Fetching API offset=%d", offset)

            # page.evaluate() runs JavaScript inside the browser.
            # We use an async JS function + Python passes the URL as an argument.
            # The "async" IIFE (Immediately Invoked Function Expression) lets us
            # use "await" for the fetch call.
            response = page.evaluate(
                """async (url) => {
                    const resp = await fetch(url, {
                        headers: { 'Accept': 'application/json' }
                    });
                    if (!resp.ok) return null;
                    return await resp.json();
                }""",
                api_url,
            )

            if not response:
                logger.warning("[kalibrr] API returned null at offset=%d — stopping", offset)
                break

            jobs = response.get("jobs", [])
            if not jobs:
                logger.info("[kalibrr] No more jobs at offset=%d — stopping", offset)
                break

            for job in jobs:
                record = self._parse_job(job)
                if record:
                    records.append(record)

            logger.info("[kalibrr] offset=%d: got %d jobs (%d total)", offset, len(jobs), len(records))
            offset += BATCH_SIZE

            # Be polite — wait between API calls
            self._random_delay(3, 7)

        return records

    def _parse_job(self, job: dict) -> dict | None:
        """
        Maps one Kalibrr API job object to our standard raw record format.

        The Kalibrr API returns deeply nested objects — we flatten what we need.
        Everything else stays in the JSONB blob for future use.
        """
        try:
            job_id = job.get("id")
            if not job_id:
                return None

            company_info = job.get("company_info", {}) or {}
            company_code = company_info.get("code", "")

            # Kalibrr stores location as a nested Google Maps structure
            google_location = job.get("google_location", {}) or {}
            address_components = google_location.get("address_components", {}) or {}
            city = address_components.get("city") or address_components.get("locality")

            # Skills are stored as a list of function objects with a "name" field,
            # but the API sometimes returns plain strings in this list — skip those.
            skills = [
                f.get("name") for f in (job.get("function") or [])
                if isinstance(f, dict) and f.get("name")
            ]

            return {
                "source_id":        f"kalibrr_{job_id}",
                "title":            job.get("name"),
                "company":          company_info.get("name"),
                "location":         city,
                "salary_raw":       self._extract_salary(job),
                "description":      job.get("description"),
                "employment_type":  job.get("tenure"),
                "experience_level": job.get("work_experience_value"),
                "skills":           skills,
                "posted_date":      job.get("activation_date"),
                "url": (
                    f"https://www.kalibrr.com/c/{company_code}/jobs/{job_id}"
                    if company_code else
                    f"https://www.kalibrr.com/jobs/{job_id}"
                ),
            }

        except Exception:
            logger.warning("[kalibrr] Failed to parse a job — skipping", exc_info=True)
            return None

    def _extract_salary(self, job: dict) -> str | None:
        """
        Builds a salary string from Kalibrr's min/max salary fields.

        Kalibrr stores salary as two separate numbers (salary_from, salary_to)
        rather than a single string, so we reconstruct the string here.
        The salary_parser.py utility will parse it again later in dbt.
        """
        sal_min = job.get("salary_from")
        sal_max = job.get("salary_to")
        currency = job.get("salary_currency") or "PHP"
        if sal_min or sal_max:
            return f"{currency} {sal_min or '?'}-{sal_max or '?'}"
        return None


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    db_url = os.environ.get("DB_URL")
    if not db_url:
        print("ERROR: DB_URL environment variable is not set.")
        print("Set it: $env:DB_URL = 'postgresql://phjobmarket:phjobmarket@127.0.0.1:15432/phjobmarket'")
        sys.exit(1)

    scraper = KalibrrScraper(db_conn_string=db_url)
    count = scraper.run()
    print(f"Done! Saved {count} records from Kalibrr.")
    print("Verify: make psql  then:  SELECT count(*) FROM raw.job_postings WHERE source='kalibrr';")
