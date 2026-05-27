# =============================================================================
# scrapers/base.py — BaseScraper: the template every scraper inherits from
#
# WHAT IS THIS FILE?
# ------------------
# All 7 scrapers in this project (PhilJobNet, Kalibrr, JobStreet, etc.) need
# the same boring plumbing: open a browser, wait between pages, connect to
# Postgres, log results.
#
# Instead of copy-pasting that code 7 times, we write it once here.
# Each specific scraper only implements ONE method: scrape(), which contains
# the logic for that particular website.
#
# HOW INHERITANCE WORKS (quick reminder):
# ----------------------------------------
#   class Animal:            ← shared by all animals
#       def breathe(): ...
#       def speak(): ...     ← every animal must implement this
#
#   class Dog(Animal):
#       def speak(): "Woof"  ← Dog's own version
#
# BaseScraper = Animal.  PhilJobNetScraper = Dog.
#
# INTERFACE (what each subclass must do):
# ----------------------------------------
# 1. Set SOURCE = "source_name"  (e.g. "philjobnet")
# 2. Implement scrape() -> list[dict]
#    - Opens pages, parses HTML, returns a list of raw job dicts
#    - Each dict must include a "source_id" key (unique ID on that site)
# 3. Call self.run() to execute. BaseScraper handles saving and logging.
# =============================================================================

import abc           # abc = Abstract Base Classes — lets us define "must implement" methods
import json          # for JSON serialization (converting dicts to JSON strings)
import logging       # Python's built-in logging — like print() but with levels + timestamps
import random        # for random delays
import time          # for time.sleep()
from contextlib import contextmanager   # for the "with self._get_conn() as conn:" pattern
from datetime import datetime, timezone # for timestamps

import psycopg2              # Python → Postgres driver
import psycopg2.extras       # gives us Json() to insert Python dicts as JSONB
from playwright.sync_api import sync_playwright  # browser automation

from scrapers.utils.user_agents import get_random_ua  # UA rotation utility

logger = logging.getLogger(__name__)


class BaseScraper(abc.ABC):
    """
    Abstract base class for all job scrapers.

    To create a new scraper:
        1. Subclass this: class MyScaper(BaseScraper)
        2. Set the SOURCE class attribute: SOURCE = "mysource"
        3. Implement scrape() -> list[dict]
        4. Call self.run() to execute the full pipeline
    """

    # Each subclass sets this to identify the source in the database.
    # e.g. SOURCE = "philjobnet"
    SOURCE: str = ""

    def __init__(self, db_conn_string: str, headless: bool = True):
        """
        db_conn_string : Postgres DSN, e.g.:
            "postgresql://phjobmarket:phjobmarket@localhost:5432/phjobmarket"
        headless       : if False, opens a visible browser window — useful
                         for debugging when a scraper isn't working as expected
        """
        if not self.SOURCE:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define SOURCE = 'source_name'"
            )
        self.db_conn_string = db_conn_string
        self.headless = headless
        # Pick a random User-Agent for this session and reuse it throughout.
        # Changing UA on every request is suspicious; sticking to one per
        # session looks like a real browser session.
        self.session_ua = get_random_ua()

    # =========================================================================
    # Database helpers
    # =========================================================================

    @contextmanager
    def _get_conn(self):
        """
        Opens a Postgres connection and automatically closes it when done.

        We use @contextmanager so this works with Python's "with" statement:

            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")

        The "with" block guarantees the connection is closed even if an
        exception is raised inside the block — no resource leaks.
        """
        conn = psycopg2.connect(self.db_conn_string)
        try:
            yield conn     # hand the connection to the "with" block
            conn.commit()  # save all changes to disk if no errors occurred
        except Exception:
            conn.rollback()  # undo all changes if something went wrong
            raise
        finally:
            conn.close()     # always close, even on error

    def save_raw(self, records: list[dict]) -> None:
        """
        Saves a list of job dicts to raw.job_postings as JSONB blobs.

        Each dict in records must have a "source_id" key — the unique
        identifier for that job on its source website (usually from the URL).

        "ON CONFLICT DO UPDATE" means: if this (source, source_id) pair
        already exists in the table, overwrite it with the new data.
        This makes it safe to re-run the scraper — no duplicates, no crashes.
        """
        if not records:
            return

        # Note: the url is stored inside raw_data (JSONB) — there is no
        # separate url column in the schema. All fields live in the JSON blob.
        sql = """
            INSERT INTO raw.job_postings (source, source_id, raw_data, scraped_at)
            VALUES (%(source)s, %(source_id)s, %(raw_data)s, %(scraped_at)s)
            ON CONFLICT (source, source_id)
            DO UPDATE SET
                raw_data   = EXCLUDED.raw_data,
                scraped_at = EXCLUDED.scraped_at
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                for record in records:
                    cur.execute(sql, {
                        "source":     self.SOURCE,
                        "source_id":  str(record["source_id"]),
                        # psycopg2.extras.Json() tells the driver to send
                        # this Python dict as a Postgres JSONB value
                        "raw_data":   psycopg2.extras.Json(record),
                        "scraped_at": datetime.now(timezone.utc),
                    })

        logger.info("[%s] Saved %d records to raw.job_postings", self.SOURCE, len(records))

    def _log_run(
        self,
        started_at: datetime,
        records_saved: int,
        status: str,
        error: str = None,
    ) -> None:
        """
        Writes one row to raw.scrape_log after every run.

        This is how we track pipeline health over time. Later, Airflow will
        query this table to alert us if a scraper stops producing data.

        status: "success" or "error"
        error:  the error message string if status == "error"
        """
        sql = """
            INSERT INTO raw.scrape_log
                (source, started_at, finished_at, records_scraped, status, error_message)
            VALUES
                (%(source)s, %(started_at)s, %(finished_at)s,
                 %(records)s, %(status)s, %(error)s)
        """
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, {
                        "source":     self.SOURCE,
                        "started_at": started_at,
                        "finished_at": datetime.now(timezone.utc),
                        "records":    records_saved,
                        "status":     status,
                        "error":      error,
                    })
        except Exception as log_err:
            # Never let a logging failure hide the original error
            logger.warning("[%s] Could not write to scrape_log: %s", self.SOURCE, log_err)

    # =========================================================================
    # Browser helpers
    # =========================================================================

    def _random_delay(self, min_sec: float = 2.0, max_sec: float = 6.0) -> None:
        """
        Sleeps for a random number of seconds between min_sec and max_sec.

        Why random? A fixed delay (always 3s) is easy for bot-detection to
        spot. Randomness mimics a human reading the page before clicking next.

        Call this between every page request.
        """
        delay = random.uniform(min_sec, max_sec)
        logger.debug("[%s] Waiting %.1fs before next request...", self.SOURCE, delay)
        time.sleep(delay)

    def get_browser_context(self, playwright):
        """
        Creates and returns a Playwright browser + context pair.

        The browser launches headless (invisible) by default. Pass
        headless=False to __init__ to see the browser window during debugging.

        Returns (browser, context) — the caller is responsible for calling
        browser.close() when done. We do this inside scrape() using
        a try/finally block.

        The context is configured to look like a real Filipino user:
        - PH locale and Manila timezone
        - A realistic desktop viewport (1366x768)
        - A real browser User-Agent string (rotated per session)
        """
        browser = playwright.chromium.launch(
            headless=self.headless,
            # --no-sandbox: required when running inside Docker
            # --disable-dev-shm-usage: prevents Chrome from crashing in
            # Docker due to limited /dev/shm (shared memory) size
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            user_agent=self.session_ua,
            viewport={"width": 1366, "height": 768},
            locale="en-PH",
            timezone_id="Asia/Manila",
            # Some PH government sites (e.g. philjobnet.gov.ph) have SSL
            # certificates whose domain name doesn't match the URL — a common
            # misconfiguration on .gov.ph domains. This tells Playwright to
            # proceed anyway instead of raising ERR_CERT_COMMON_NAME_INVALID.
            ignore_https_errors=True,
        )
        # If any single operation (page.goto, page.click, etc.) takes
        # longer than 30 seconds, raise a TimeoutError instead of hanging.
        context.set_default_timeout(30_000)
        return browser, context

    # =========================================================================
    # Abstract method — subclasses MUST implement this
    # =========================================================================

    @abc.abstractmethod
    def scrape(self) -> list[dict]:
        """
        Scrape all job listings from this source and return them as a list.

        This is the only method you need to implement in a subclass.

        Guidelines:
        - Open a browser with self.get_browser_context(playwright)
        - Loop through pages using self._random_delay() between requests
        - Parse job listings from each page
        - Return a flat list of dicts — one dict per job posting
        - Each dict MUST have a "source_id" key
        - Stop at 50 pages maximum (or fewer — check the plan per source)
        - Close the browser in a finally block

        Example return value:
            [
                {
                    "source_id": "philjobnet_12345",
                    "title": "Software Engineer",
                    "company": "Acme Corp",
                    "location": "Makati City",
                    "salary_raw": "₱50,000 - ₱80,000/month",
                    "posted_date": "2024-05-01",
                    "url": "https://www.philjobnet.gov.ph/...",
                },
                ...
            ]
        """

    # =========================================================================
    # Main entry point — call this to run the scraper
    # =========================================================================

    def run(self) -> int:
        """
        Execute the full scraping pipeline:
            1. Call scrape() to get all job dicts
            2. Save them to Postgres via save_raw()
            3. Write a row to raw.scrape_log (success or error)
            4. Return the number of records saved

        This is the method you call from the command line or from Airflow.
        You never need to override this.
        """
        started_at = datetime.now(timezone.utc)
        logger.info("[%s] Starting scrape run", self.SOURCE)

        try:
            records = self.scrape()        # ← your subclass runs here
            self.save_raw(records)         # ← saves to Postgres
            self._log_run(started_at, len(records), "success")
            logger.info("[%s] Run complete. Saved %d records.", self.SOURCE, len(records))
            return len(records)

        except Exception as e:
            logger.exception("[%s] Run failed: %s", self.SOURCE, e)
            self._log_run(started_at, 0, "error", str(e))
            raise
