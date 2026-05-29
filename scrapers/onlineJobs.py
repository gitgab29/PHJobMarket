# =============================================================================
# scrapers/onlineJobs.py — OnlineJobsScraper
#
# WHAT IS ONLINEJOBS.PH?
# ----------------------
# OnlineJobs.ph is a Philippine freelance job board focused on remote work.
# Every listing is remote and salaries are quoted in USD (not PHP).
# This makes it a useful outlier in the dataset — a reliable signal for
# USD-denominated remote roles in the PH market.
#
# HOW WE SCRAPE IT:
# -----------------
# Straightforward Playwright + BeautifulSoup scraping. The site has no
# significant bot detection and exposes listings without requiring login
# (as of the time this was written).
#
# Pagination uses a simple ?page=N query param. Each page contains a list
# of job cards classed `.card.job-post`. We stop at 20 pages or when a
# page returns no cards (whichever comes first).
#
# HOW TO RUN:
#   make up
#   make scrape-onlinejobs
# =============================================================================

import hashlib
import logging
import os
import re

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

ONLINEJOBS_BASE = "https://www.onlinejobs.ph"
SEARCH_URL = f"{ONLINEJOBS_BASE}/jobseekers/jobsearch"
RESULTS_PER_PAGE = 30
MAX_PAGES = 10  # site exposes ~10 pages (300 records) without login

# OnlineJobs blocks non-browser requests; Playwright's UA from get_browser_context
# is sufficient — no extra headers needed.


class OnlineJobsScraper(BaseScraper):
    """
    Scraper for onlinejobs.ph — remote-only, USD-denominated listings.

    All records are tagged is_remote=True and salary_currency="USD".
    """

    SOURCE = "onlinejobs"

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
            offset = (page_num - 1) * RESULTS_PER_PAGE
            # Page 1 has no offset in the URL path; pages 2+ use /jobseekers/jobsearch/{offset}
            url = SEARCH_URL if offset == 0 else f"{SEARCH_URL}/{offset}"
            logger.info("[onlinejobs] Loading page %d (offset=%d): %s", page_num, offset, url)

            for attempt in range(2):
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=90_000)
                    try:
                        page.wait_for_selector("div.jobpost-cat-box", timeout=15_000)
                    except Exception:
                        pass
                    break
                except Exception:
                    if attempt == 0:
                        logger.warning(
                            "[onlinejobs] Page %d timed out — rate limited; "
                            "waiting 20s then retrying once",
                            page_num,
                        )
                        self._random_delay(18, 22)
                    else:
                        logger.warning(
                            "[onlinejobs] Page %d failed on retry — stopping early "
                            "with %d records",
                            page_num, len(records),
                        )
                        return records
            self._random_delay(4, 8)

            # Check for login wall — the site may redirect to /login for some pages
            if "/login" in page.url or "sign in" in page.title().lower():
                raise RuntimeError(
                    "[onlinejobs] Redirected to login page — the site now requires "
                    "authentication to view listings. Update the scraper to use cookies."
                )

            soup = BeautifulSoup(page.content(), "lxml")
            cards = soup.select("div.jobpost-cat-box")

            if not cards:
                logger.info("[onlinejobs] No job cards on page %d (offset=%d) — stopping", page_num, offset)
                break

            page_records = [r for card in cards for r in [self._parse_card(card)] if r]

            # Deduplicate: stop if this page only returned IDs we've already seen
            page_ids = {r["source_id"] for r in page_records}
            new_ids = page_ids - seen_ids
            if page_num > 1 and not new_ids:
                logger.warning(
                    "[onlinejobs] Page %d has only duplicate IDs — pagination looping; stopping",
                    page_num,
                )
                break

            seen_ids.update(new_ids)
            records.extend(page_records)
            logger.info(
                "[onlinejobs] Page %d: %d cards, %d new (total %d)",
                page_num, len(cards), len(new_ids), len(records),
            )

        return records

    def _parse_card(self, card) -> dict | None:
        try:
            # URL from the first job link inside the card
            link = card.select_one("a[href*='/jobseekers/job/']")
            if not link:
                return None
            href = link.get("href", "")
            url = href if href.startswith("http") else f"{ONLINEJOBS_BASE}{href}"
            source_id = self._extract_id(href)

            # Title: h4.fw-700; strip the employment-type badge before reading text
            title_el = card.select_one("h4.fw-700")
            if not title_el:
                return None
            badge_el = title_el.select_one("span.badge")
            employment_type = badge_el.get_text(strip=True) if badge_el else None
            if badge_el:
                badge_el.extract()
            title = title_el.get_text(strip=True)

            # Salary: <dd class="col"> inside the no-gutters dl (the dollar-icon row)
            salary_el = card.select_one("dl.no-gutters dd.col")
            salary_raw = salary_el.get_text(strip=True) if salary_el else None
            if salary_raw in ("N/A", "n/a", ""):
                salary_raw = None

            # Posted date: use data-temp ISO datetime attribute (avoids text parsing)
            date_el = card.select_one("p[data-temp]")
            posted_date = date_el.get("data-temp") if date_el else None

            # OnlineJobs.ph hides employer names on the listing cards by design
            return {
                "source_id":       source_id,
                "title":           title,
                "company":         None,
                "salary_raw":      salary_raw,
                "salary_currency": "USD",
                "employment_type": employment_type,
                "is_remote":       True,
                "url":             url,
                "posted_date":     posted_date,
            }
        except Exception:
            logger.warning("[onlinejobs] Failed to parse card", exc_info=True)
            return None

    def _extract_id(self, href: str) -> str:
        """
        Extract the numeric job ID from the URL slug.
        URL format: /jobseekers/job/Title-Words-Here-1657818
        The ID is the trailing number after the last hyphen.
        Falls back to a hash of the href if no trailing number is found.
        """
        match = re.search(r"-(\d+)$", href.rstrip("/"))
        if match:
            return f"onlinejobs_{match.group(1)}"
        digest = hashlib.md5(href.encode()).hexdigest()[:12]
        return f"onlinejobs_{digest}"


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

    scraper = OnlineJobsScraper(db_conn_string=db_url)
    count = scraper.run()
    print(f"Done! Saved {count} records from OnlineJobs.ph.")
    print("Verify: make psql  then:  SELECT count(*) FROM raw.job_postings WHERE source='onlinejobs';")
