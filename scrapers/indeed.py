# =============================================================================
# scrapers/indeed.py — IndeedScraper
#
# WHAT IS INDEED?
# ---------------
# Indeed is the world's largest job board. ph.indeed.com lists jobs for the
# Philippine market in PHP salaries alongside international remote postings.
#
# HOW WE SCRAPE IT:
# -----------------
# Playwright-based scraping using CSS selectors on HTML cards. Indeed uses
# server-side rendering so the job data is present in the initial HTML — we
# don't need to intercept JS variables or API calls.
#
# CAPTCHA HANDLING (critical):
# ----------------------------
# Indeed aggressively bot-detects scrapers. When it triggers, it either:
#   a) Redirects to a URL containing "captcha" or "challenge"
#   b) Serves a page with a #captcha-container element
#
# We check for both after every page.goto(). If detected, we stop and return
# whatever we already collected — a partial run is better than an error.
# The scrape_log will show status="captcha_stop" so Airflow can alert on it.
#
# RATE LIMITING:
# --------------
# 4–10s random delay between pages (vs 2–6s for other scrapers).
# Indeed's bot detection is time-sensitive — faster rates get CAPTCHA'd fast.
#
# HOW TO RUN:
#   make up
#   make scrape-indeed
# =============================================================================

import logging
import os
import urllib.parse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

INDEED_BASE = "https://ph.indeed.com"
SEARCH_URL = f"{INDEED_BASE}/jobs"
RESULTS_PER_PAGE = 10
MAX_PAGES_PER_QUERY = 3  # 3 pages × ~15 results = ~45 per keyword before bot risk rises

# Broad keywords covering major PH job categories.
# Each keyword is a separate search — results are deduped by source_id.
SEARCH_KEYWORDS = [
    "software developer",
    "data analyst",
    "web developer",
    "network engineer",
    "nurse",
    "customer service",
    "accountant",
    "marketing",
    "sales representative",
    "administrative assistant",
    "graphic designer",
    "teacher",
    "project manager",
    "hr",
    "finance",
]


class IndeedScraper(BaseScraper):
    """
    Scraper for ph.indeed.com.

    Loops over SEARCH_KEYWORDS, scraping up to MAX_PAGES_PER_QUERY pages per keyword.
    Stops the entire run on CAPTCHA detection and returns partial results.
    Deduplicates by source_id across all keywords.
    """

    SOURCE = "indeed"

    def scrape(self) -> list[dict]:
        records = []
        with sync_playwright() as p:
            browser, context = self.get_browser_context(p)
            page = context.new_page()
            try:
                records = self._scrape_all_keywords(page)
            finally:
                browser.close()
        return records

    def _scrape_all_keywords(self, page) -> list[dict]:
        all_records = []
        seen_ids: set[str] = set()

        for keyword in SEARCH_KEYWORDS:
            logger.info("[indeed] Starting keyword: %r", keyword)
            new_records, captcha_hit = self._scrape_keyword(page, keyword, seen_ids)
            all_records.extend(new_records)
            for r in new_records:
                seen_ids.add(r["source_id"])
            logger.info(
                "[indeed] Keyword %r done: %d new records (total %d)",
                keyword, len(new_records), len(all_records),
            )
            if captcha_hit:
                logger.warning("[indeed] CAPTCHA hit — stopping all keywords early")
                break
            # Pause between keywords to reduce bot-detection risk
            self._random_delay(6, 12)

        return all_records

    def _scrape_keyword(self, page, keyword: str, seen_ids: set) -> tuple[list[dict], bool]:
        """Scrape up to MAX_PAGES_PER_QUERY pages for one keyword.
        Returns (new_records, captcha_hit). Does not mutate seen_ids."""
        records = []
        q = urllib.parse.quote_plus(keyword)

        for page_num in range(1, MAX_PAGES_PER_QUERY + 1):
            start = (page_num - 1) * RESULTS_PER_PAGE
            url = f"{SEARCH_URL}?q={q}&l=Philippines&start={start}"
            logger.info("[indeed] [%s] page %d (start=%d)", keyword, page_num, start)

            page.goto(url, wait_until="domcontentloaded", timeout=45_000)
            self._random_delay(4, 10)

            if self._is_captcha_page(page):
                logger.warning("[indeed] CAPTCHA on [%s] page %d — stopping run", keyword, page_num)
                return records, True

            soup = BeautifulSoup(page.content(), "lxml")
            cards = self._find_cards(soup)

            if not cards:
                html_len = len(page.content())
                title = page.title()
                logger.info(
                    "[indeed] [%s] no cards on page %d (html_len=%d, title=%r) "
                    "— likely bot-throttled or empty results",
                    keyword, page_num, html_len, title,
                )
                break

            page_records = [r for card in cards for r in [self._parse_card(card)] if r]
            # Filter out IDs already collected across all keywords + this keyword's prior pages
            local_seen = seen_ids | {r["source_id"] for r in records}
            new_records = [r for r in page_records if r["source_id"] not in local_seen]

            if not new_records and page_num > 1:
                logger.info("[indeed] [%s] page %d all duplicates — next keyword", keyword, page_num)
                break

            records.extend(new_records)
            logger.info(
                "[indeed] [%s] page %d: %d cards, %d new",
                keyword, page_num, len(cards), len(new_records),
            )

        return records, False

    def _is_captcha_page(self, page) -> bool:
        """Return True if Indeed served a CAPTCHA or bot-check page."""
        current_url = page.url.lower()
        if "captcha" in current_url or "challenge" in current_url:
            return True
        # DOM check: Indeed's CAPTCHA page has a specific container
        try:
            return page.locator("#captcha-container").count() > 0
        except Exception:
            return False

    def _find_cards(self, soup: BeautifulSoup) -> list:
        """
        Return job card elements. Indeed has changed its selectors several times;
        we try primary then fallback selectors.
        """
        cards = soup.select("div.job_seen_beacon")
        if cards:
            return cards
        # Fallback: newer Indeed layout uses list items with data-testid
        cards = soup.select("li[data-testid='slider_item']")
        if cards:
            return cards
        # Second fallback: mosaic provider pattern
        cards = soup.select("[class*='jobsearch-ResultsList'] > li")
        return cards

    def _parse_card(self, card) -> dict | None:
        try:
            # source_id comes from the data-jk attribute (job key — Indeed's internal ID)
            job_key = card.get("data-jk")
            if not job_key:
                # Try nested element
                jk_el = card.select_one("[data-jk]")
                job_key = jk_el.get("data-jk") if jk_el else None
            if not job_key:
                return None

            source_id = f"indeed_{job_key}"

            def _txt(sel):
                el = card.select_one(sel)
                return el.get_text(strip=True) if el else None

            # Title — prefer span[title] which has the clean text without extra markup
            title_el = card.select_one("h2.jobTitle a")
            if title_el:
                title = (
                    title_el.select_one("span[title]") or title_el
                ).get_text(strip=True)
                href = title_el.get("href", "")
            else:
                # Fallback: any <a> inside an h2 or h3
                title_el = card.select_one("h2 a, h3 a")
                title = title_el.get_text(strip=True) if title_el else None
                href = title_el.get("href", "") if title_el else ""

            url = (
                href if href.startswith("http")
                else f"{INDEED_BASE}{href}" if href
                else f"{INDEED_BASE}/viewjob?jk={job_key}"
            )

            # Company name
            company = (
                _txt("[data-testid='company-name']")
                or _txt(".companyName")
                or _txt("[class*='companyName']")
            )

            # Location
            location = (
                _txt("[data-testid='text-location']")
                or _txt(".companyLocation")
                or _txt("[class*='companyLocation']")
            )

            # Salary
            salary_raw = (
                _txt(".salary-snippet-container")
                or _txt("[data-testid='attribute_snippet_testid']")
                or _txt("[class*='salary']")
            )

            # Employment type (often in metadata badges)
            employment_type = _txt("[data-testid='attribute_snippet_testid']")
            # If employment_type captured the salary, clear it
            if employment_type and salary_raw and employment_type == salary_raw:
                employment_type = None

            # Posted date — Indeed uses relative strings like "3 days ago"
            posted_date = (
                _txt("[data-testid='myJobsStateDate']")
                or _txt("span.date")
                or _txt("[class*='date']")
            )

            return {
                "source_id":       source_id,
                "title":           title,
                "company":         company,
                "location":        location,
                "salary_raw":      salary_raw,
                "employment_type": employment_type,
                "posted_date":     posted_date,
                "url":             url,
            }
        except Exception:
            logger.warning("[indeed] Failed to parse card", exc_info=True)
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

    scraper = IndeedScraper(db_conn_string=db_url)
    count = scraper.run()
    print(f"Done! Saved {count} records from Indeed PH.")
    print("Verify: make psql  then:  SELECT count(*) FROM raw.job_postings WHERE source='indeed';")
