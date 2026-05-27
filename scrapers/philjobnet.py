# =============================================================================
# scrapers/philjobnet.py — PhilJobNetScraper
#
# WHAT IS PHILJOBNET?
# -------------------
# PhilJobNet (philjobnet.gov.ph) is a DOLE government job portal.
# Friendly to scrape: public data, no login required for listings.
#
# THINGS WE DISCOVERED FROM INSPECTING THE REAL PAGE:
# ---------------------------------------------------
# 1. Working URL: https://philjobnet.gov.ph  (no "www" — www. is broken/404)
# 2. Job listings are at: /job-vacancies/
# 3. Each job card is a <div class="jobcard"> wrapped in <a class="nolink">
# 4. Pagination uses ASP.NET's __doPostBack — NOT simple URL parameters.
#    This means we can't do ?page=2, ?page=3. Instead, we tell Playwright
#    to call the JavaScript function that submits the next page form.
#
# HOW TO RUN:
#   make up  (start Postgres)
#   make scrape-philjobnet
# =============================================================================

import logging
import os

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL  = "https://philjobnet.gov.ph"      # no "www." — that subdomain is broken
JOBS_URL  = f"{BASE_URL}/job-vacancies/"
MAX_PAGES = 50

# ASP.NET GridView control ID — used to trigger page navigation via JavaScript.
# This is the internal name ASP.NET assigned to the job listings grid.
# If pagination ever breaks, inspect the page HTML and look for __doPostBack calls.
GRID_ID = "ctl00$BodyContentPlaceHolder$GridView1"


class PhilJobNetScraper(BaseScraper):
    """
    Scraper for philjobnet.gov.ph — Philippine DOLE government job portal.

    Key quirk: the site uses ASP.NET WebForms pagination. Page navigation
    is triggered by JavaScript (__doPostBack), not by changing the URL.
    We use Playwright's page.evaluate() to call that function directly.
    """

    SOURCE = "philjobnet"

    def scrape(self) -> list[dict]:
        """Opens browser, loops through all pages, returns all scraped jobs."""
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
        """
        Paginates through PhilJobNet's job listings.

        PhilJobNet uses ASP.NET WebForms — clicking "page 2" doesn't change
        the URL. Instead it calls a JavaScript function: __doPostBack().
        We call that function directly via Playwright's page.evaluate().

        For page 1: just navigate to the URL.
        For pages 2+: call __doPostBack with the page number argument.
        """
        records = []

        # Page 1: regular navigation
        logger.info("[philjobnet] Loading %s", JOBS_URL)
        page.goto(JOBS_URL, wait_until="domcontentloaded", timeout=30_000)
        self._random_delay(2, 4)

        for page_num in range(1, MAX_PAGES + 1):
            logger.info("[philjobnet] Scraping page %d", page_num)

            soup  = BeautifulSoup(page.content(), "lxml")
            cards = soup.select("a.nolink")   # each job card is wrapped in <a class="nolink">

            if not cards:
                logger.info("[philjobnet] No cards on page %d — stopping at %d total", page_num, len(records))
                break

            for card in cards:
                record = self._parse_card(card)
                if record:
                    records.append(record)

            logger.info("[philjobnet] Page %d: %d cards (%d total)", page_num, len(cards), len(records))

            # Check if there's a next page available
            if not self._go_to_next_page(page, page_num + 1):
                logger.info("[philjobnet] No more pages after page %d", page_num)
                break

            # Wait between pages — polite and avoids detection
            self._random_delay(2, 5)

        return records

    def _go_to_next_page(self, page, next_page_num: int) -> bool:
        """
        Navigates to the next page using ASP.NET's __doPostBack mechanism.

        Returns True if navigation succeeded, False if there's no next page.

        HOW __doPostBack WORKS:
        ASP.NET pages communicate page changes by submitting a hidden form.
        When you click "page 2", JavaScript sets two hidden fields:
          __EVENTTARGET   = the grid control's ID
          __EVENTARGUMENT = "Page$2"
        Then submits the form. We call __doPostBack() directly to do the same.

        WHY page.expect_navigation()?
        __doPostBack() starts a navigation (form POST) asynchronously.
        Without expect_navigation(), page.evaluate() returns immediately
        before the new page loads — and the next page.content() call
        crashes with "page is navigating and changing the content".

        expect_navigation() works like a listener: it registers BEFORE we
        trigger the navigation, then waits for it to complete. This avoids
        the race condition.
        """
        try:
            # Register the navigation listener BEFORE triggering the navigation.
            # If we registered it AFTER, we might miss the navigation event.
            with page.expect_navigation(wait_until="domcontentloaded", timeout=20_000):
                page.evaluate(f"__doPostBack('{GRID_ID}', 'Page${next_page_num}')")
            # By the time we exit the `with` block, the new page is fully loaded.
            return True

        except Exception as e:
            # TimeoutError here usually means we've gone past the last page
            # (no navigation happened because there's no "page N" link).
            logger.debug("[philjobnet] Could not navigate to page %d: %s", next_page_num, e)
            return False

    def _parse_card(self, card_link) -> dict | None:
        """
        Extracts job data from one <a class="nolink"> element.

        The structure inside each card:
            <a class="nolink" href="/job-vacancies/job/some-job-title-1389145">
              <div class="jobcard">
                <h1 class="jobtitle">JOB TITLE</h1>
                <h3 class="salary">₱25,000/month</h3>
                <span class="companytitle">COMPANY NAME</span>
                <div>  ← location is next to the bi-geo-alt icon
                <div>  ← education level is next to bi-mortarboard icon
                <div>  ← employment type is next to bi-file-text icon
                <span class="jobinfo">Posted on 5/27/2026</span>
              </div>
            </a>

        We save the salary string exactly as it appears — no parsing here.
        salary_parser.py handles that later in dbt.
        """
        try:
            href = card_link.get("href", "")

            # source_id comes from the number at the end of the URL
            # e.g. "/job-vacancies/job/motorcycle-driver-rider-1389145" → "1389145"
            source_id = href.rstrip("/").split("-")[-1] if href else None

            if not source_id or not source_id.isdigit():
                # Some cards may not have a numeric ID — skip them
                return None

            job_url = f"{BASE_URL}{href}"

            # --- Extract fields from inside the card ---
            title_el   = card_link.select_one(".jobtitle")
            salary_el  = card_link.select_one(".salary")
            company_el = card_link.select_one(".companytitle")

            # Location, education, and employment type are in unlabelled divs
            # next to Bootstrap Icons (bi-geo-alt, bi-mortarboard, bi-file-text).
            # We find the parent div of each icon and take its full text.
            location_el  = card_link.select_one(".bi-geo-alt")
            education_el = card_link.select_one(".bi-mortarboard")
            emptype_el   = card_link.select_one(".bi-file-text")
            date_el      = card_link.select_one(".jobinfo")

            def icon_text(icon_el) -> str | None:
                """Get the text from the parent div of a Bootstrap icon."""
                if not icon_el:
                    return None
                parent = icon_el.parent
                # get_text() returns the whole div's text including the icon label;
                # strip() removes leading/trailing whitespace
                return parent.get_text(separator=" ", strip=True) if parent else None

            return {
                # source_id is required — used as the unique key in the DB
                "source_id":        f"philjobnet_{source_id}",

                "title":            title_el.get_text(strip=True) if title_el else None,
                "company":          company_el.get_text(strip=True) if company_el else None,

                # Raw salary string — stored as-is, parsed later by dbt
                "salary_raw":       salary_el.get_text(strip=True) if salary_el else None,

                "location":         icon_text(location_el),
                "education_level":  icon_text(education_el),
                "employment_type":  icon_text(emptype_el),
                "posted_date":      date_el.get_text(strip=True) if date_el else None,

                # "url" is used by BaseScraper.save_raw() for the url column
                "url":              job_url,
            }

        except Exception:
            logger.warning("[philjobnet] Failed to parse a card — skipping", exc_info=True)
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
        print("Set it: $env:DB_URL = 'postgresql://phjobmarket:phjobmarket@127.0.0.1:5432/phjobmarket'")
        sys.exit(1)

    scraper = PhilJobNetScraper(db_conn_string=db_url)
    count = scraper.run()
    print(f"Done! Saved {count} records from PhilJobNet.")
    print("Verify: make psql  then:  SELECT count(*) FROM raw.job_postings;")
