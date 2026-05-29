# =============================================================================
# scrapers/jobstreet.py — JobStreetScraper
#
# WHAT IS JOBSTREET?
# ------------------
# JobStreet (jobstreet.com.ph) is one of the biggest job boards in Southeast
# Asia. It runs on the SEEK platform (an Australian company). Like Kalibrr,
# it's a modern JavaScript-heavy site.
#
# HOW WE SCRAPE IT (Redux state extraction):
# ------------------------------------------
# SEEK/JobStreet embeds ALL job listing data inside a JavaScript variable
# called window.__SEEK_REDUX_DATA__. "Redux" is a state management library
# for React apps — it holds all the data the page needs to render.
#
# Before the page renders any HTML, the server packs all the job data into
# this variable and puts it in the page source. This means we can extract
# a clean, structured dict without any HTML scraping at all.
#
# We use Playwright's page.evaluate() to read this JavaScript variable:
#
#   redux_data = page.evaluate("() => window.__SEEK_REDUX_DATA__ || null")
#
# This returns the entire application state as a Python dict. We then navigate
# the nested dict to find the jobs array.
#
# FALLBACK: If window.__SEEK_REDUX_DATA__ doesn't exist (e.g., after a site
# redesign), we fall back to parsing HTML using BeautifulSoup.
#
# HOW TO RUN:
#   make up
#   make scrape-jobstreet
# =============================================================================

import json
import logging
import os

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# www.jobstreet.com.ph/jobs redirects to the homepage; the correct URL is ph.jobstreet.com
JOBSTREET_BASE = "https://ph.jobstreet.com"
JOBS_URL = f"{JOBSTREET_BASE}/jobs"
MAX_PAGES = 30

# JS snippet: scan all window globals whose names contain these substrings
_JS_FIND_GLOBALS = """() => {
    const keys = Object.keys(window).filter(k =>
        /seek|redux|apollo|initial|next/i.test(k)
    );
    return keys.slice(0, 20);
}"""

# JS snippet: extract Next.js server-side props from __NEXT_DATA__
_JS_NEXT_DATA = """() => {
    const el = document.getElementById('__NEXT_DATA__');
    try { return el ? JSON.parse(el.textContent) : null; }
    catch(e) { return null; }
}"""


class JobStreetScraper(BaseScraper):
    """
    Scraper for jobstreet.com.ph (SEEK platform).

    Extraction order on each page:
      1. window.__SEEK_REDUX_DATA__  (original SEEK Redux state)
      2. window.SEEK_APOLLO_DATA     (SEEK GraphQL cache, newer)
      3. #__NEXT_DATA__ script tag  (Next.js SSR props)
      4. HTML cards                  (last resort, selector-fragile)

    If all four fail, the scraper logs the page title and available JS
    globals so you can identify the current data source without headless=False.
    """

    SOURCE = "jobstreet"

    def scrape(self) -> list[dict]:
        records = []
        with sync_playwright() as p:
            browser, context = self.get_browser_context(p)
            page = context.new_page()
            try:
                records = self._scrape_all_pages(page)
            finally:
                browser.close()
        return records

    def _scrape_all_pages(self, page) -> list[dict]:
        records = []
        seen_ids: set[str] = set()

        for page_num in range(1, MAX_PAGES + 1):
            # SEEK/JobStreet paginates with ?page=N — ?pg= is silently ignored
            # and causes every "page" to return page 1 again.
            url = f"{JOBS_URL}?page={page_num}"
            logger.info("[jobstreet] Loading page %d: %s", page_num, url)

            page.goto(url, wait_until="load", timeout=45_000)
            try:
                page.wait_for_load_state("networkidle", timeout=10_000)
            except Exception:
                pass  # networkidle can time out on pages with background polling

            self._random_delay(3, 8)

            title = page.title()
            content_len = len(page.content())
            logger.info(
                "[jobstreet] Page %d ready — title=%r  html_len=%d",
                page_num, title, content_len,
            )

            jobs = self._try_extract_jobs(page, page_num)
            if not jobs:
                logger.info("[jobstreet] No jobs on page %d — stopping", page_num)
                break

            # Detect broken pagination: stop if every job on this page has
            # already been seen (i.e. the site served the same page again).
            page_ids = {j["source_id"] for j in jobs if j.get("source_id")}
            new_ids = page_ids - seen_ids
            if not new_ids:
                logger.warning(
                    "[jobstreet] Page %d returned only duplicate source_ids — "
                    "pagination appears broken; stopping early",
                    page_num,
                )
                break

            seen_ids.update(new_ids)
            records.extend(jobs)
            logger.info(
                "[jobstreet] Page %d: %d jobs (%d new, %d total)",
                page_num, len(jobs), len(new_ids), len(records),
            )

        return records

    def _try_extract_jobs(self, page, page_num: int) -> list[dict]:
        """Try each extraction strategy in priority order; return first success."""

        # ── Strategy 1: original Redux state ──────────────────────────────────
        redux_data = page.evaluate("() => window.__SEEK_REDUX_DATA__ || null")
        if redux_data:
            jobs = self._parse_redux(redux_data)
            if jobs:
                logger.info("[jobstreet] Page %d: used __SEEK_REDUX_DATA__", page_num)
                return jobs

        # ── Strategy 2: Apollo GraphQL cache (newer SEEK builds) ──────────────
        apollo_data = page.evaluate("() => window.SEEK_APOLLO_DATA || null")
        if apollo_data:
            jobs = self._parse_apollo(apollo_data)
            if jobs:
                logger.info("[jobstreet] Page %d: used SEEK_APOLLO_DATA", page_num)
                return jobs

        # ── Strategy 3: Next.js __NEXT_DATA__ SSR props ───────────────────────
        next_data = page.evaluate(_JS_NEXT_DATA)
        if next_data:
            jobs = self._parse_next_data(next_data)
            if jobs:
                logger.info("[jobstreet] Page %d: used __NEXT_DATA__", page_num)
                return jobs

        # ── Strategy 4: HTML cards (selector-fragile, last resort) ────────────
        soup = BeautifulSoup(page.content(), "lxml")
        jobs = self._parse_html(soup)
        if jobs:
            logger.info("[jobstreet] Page %d: used HTML fallback", page_num)
            return jobs

        # ── All strategies failed — log diagnostics so we know what to fix ────
        globals_found = page.evaluate(_JS_FIND_GLOBALS)
        logger.warning(
            "[jobstreet] Page %d: all strategies failed. "
            "Relevant window globals: %s",
            page_num, globals_found,
        )
        return []

    # ── Parser: original Redux state ──────────────────────────────────────────

    def _parse_redux(self, data: dict) -> list[dict]:
        """
        Navigates the nested Redux state to find the jobs array.
        Path: data → results → results → jobs  (or jobsPage → jobs).

        If this path breaks after a SEEK update, run headless=False and:
            page.evaluate("() => JSON.stringify(Object.keys(window.__SEEK_REDUX_DATA__))")
        to find the new top-level keys.
        """
        results_outer = data.get("results") or {}
        results_inner = results_outer.get("results") or {}
        jobs = results_inner.get("jobs") or []

        if not jobs:
            jobs = data.get("jobsPage", {}).get("jobs") or []

        return [r for job in jobs for r in [self._parse_redux_job(job)] if r]

    def _parse_redux_job(self, job: dict) -> dict | None:
        try:
            job_id = job.get("id")
            if not job_id:
                return None
            advertiser = job.get("advertiser") or {}
            return {
                "source_id":       f"jobstreet_{job_id}",
                "title":           job.get("title"),
                "company":         advertiser.get("description"),
                "location":        job.get("location"),
                "salary_raw":      job.get("salary"),
                "description":     job.get("teaser"),
                "posted_date":     job.get("listingDate"),
                "employment_type": job.get("workType"),
                "url":             f"{JOBSTREET_BASE}/job/{job_id}",
            }
        except Exception:
            logger.warning("[jobstreet] Failed to parse Redux job", exc_info=True)
            return None

    # ── Parser: Apollo GraphQL cache ──────────────────────────────────────────

    def _parse_apollo(self, data: dict) -> list[dict]:
        """
        SEEK_APOLLO_DATA is a flat cache keyed by GraphQL entity IDs.
        Job objects live under keys like "JobSearchResult:<id>".
        """
        records = []
        for key, value in data.items():
            if not isinstance(value, dict):
                continue
            if not key.startswith(("Job:", "JobSearchResult:", "JobListing:")):
                continue
            job_id = value.get("id") or value.get("jobId")
            if not job_id:
                continue
            records.append({
                "source_id":       f"jobstreet_{job_id}",
                "title":           value.get("title"),
                "company":         (value.get("advertiser") or {}).get("name"),
                "location":        (value.get("location") or {}).get("label"),
                "salary_raw":      value.get("salary"),
                "description":     value.get("teaser"),
                "posted_date":     value.get("listingDate"),
                "employment_type": value.get("workTypes", [None])[0],
                "url":             f"{JOBSTREET_BASE}/job/{job_id}",
            })
        return records

    # ── Parser: Next.js __NEXT_DATA__ ─────────────────────────────────────────

    def _parse_next_data(self, data: dict) -> list[dict]:
        """
        Next.js embeds server-side props in <script id="__NEXT_DATA__">.
        The jobs array is typically at props → pageProps → jobResults → jobs
        (or variations of that path — SEEK changes it between deploys).
        """
        try:
            page_props = data.get("props", {}).get("pageProps", {})
        except AttributeError:
            return []

        # Try several known paths within pageProps
        candidates = [
            page_props.get("jobResults", {}).get("jobs"),
            page_props.get("results", {}).get("jobs"),
            page_props.get("jobs"),
            page_props.get("initialData", {}).get("jobs"),
        ]

        jobs_list = next((c for c in candidates if c), None)
        if not jobs_list:
            return []

        records = []
        for job in jobs_list:
            job_id = job.get("id") or job.get("jobId")
            if not job_id:
                continue
            advertiser = job.get("advertiser") or {}
            records.append({
                "source_id":       f"jobstreet_{job_id}",
                "title":           job.get("title"),
                "company":         advertiser.get("name") or advertiser.get("description"),
                "location":        job.get("locationLabel") or job.get("location"),
                "salary_raw":      job.get("salary"),
                "description":     job.get("teaser"),
                "posted_date":     job.get("listingDate"),
                "employment_type": job.get("workType"),
                "url":             f"{JOBSTREET_BASE}/job/{job_id}",
            })
        return records

    # ── Parser: HTML cards ────────────────────────────────────────────────────

    def _parse_html(self, soup: BeautifulSoup) -> list[dict]:
        """
        HTML parser using SEEK's data-automation attributes.

        Primary card selector as of 2026: article[data-testid='job-card'].
        Fallbacks handle older SEEK layouts in case of a rollback/A-B test.
        """
        containers = (
            soup.select("article[data-testid='job-card']")
            or soup.select("article[data-automation='normalJob']")
            or soup.select("article[data-automation='jobCard']")
            or soup.select("[data-card-type='JobCard']")
        )
        return [r for art in containers for r in [self._parse_html_card(art)] if r]

    def _parse_html_card(self, article) -> dict | None:
        try:
            # Job ID lives directly on the article as data-job-id (more reliable
            # than parsing it out of the href which carries tracking params).
            job_id = article.get("data-job-id")
            if not job_id:
                # Older layout: extract from title link href
                title_href = article.select_one("a[data-automation='jobTitle']")
                href = title_href.get("href", "") if title_href else ""
                job_id = href.split("/job/")[-1].split("?")[0] if "/job/" in href else None
            if not job_id:
                return None

            def _txt(sel):
                el = article.select_one(sel)
                return el.get_text(strip=True) if el else None

            title_el = article.select_one("a[data-automation='jobTitle']")

            return {
                "source_id":        f"jobstreet_{job_id}",
                "title":            _txt("a[data-automation='jobTitle']"),
                "company":          _txt("a[data-automation='jobCompany']"),
                "location":         _txt("[data-automation='jobLocation']"),
                "salary_raw":       _txt("[data-automation='jobSalary']"),
                "description":      _txt("[data-automation='jobShortDescription']"),
                "classification":   _txt("[data-automation='jobClassification']"),
                "sub_classification": _txt("[data-automation='jobSubClassification']"),
                "posted_date":      _txt("[data-automation='jobListingDate']"),
                "url": (
                    f"{JOBSTREET_BASE}/job/{job_id}"
                    if job_id else
                    (f"{JOBSTREET_BASE}{title_el.get('href', '').split('?')[0]}" if title_el else None)
                ),
            }
        except Exception:
            logger.warning("[jobstreet] Failed to parse HTML card", exc_info=True)
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

    scraper = JobStreetScraper(db_conn_string=db_url)
    count = scraper.run()
    print(f"Done! Saved {count} records from JobStreet.")
    print("Verify: make psql  then:  SELECT count(*) FROM raw.job_postings WHERE source='jobstreet';")
