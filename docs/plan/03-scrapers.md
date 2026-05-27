# 3. Scraper Architecture

## 3.1 Base Scraper Class

```python
# scrapers/base.py
import abc
import json
import logging
import random
import time
from datetime import datetime, timezone

import psycopg2
from playwright.sync_api import sync_playwright

from scrapers.utils.user_agents import get_random_ua

logger = logging.getLogger(__name__)


class BaseScraper(abc.ABC):
    def __init__(self, db_conn_string: str, headless: bool = True):
        self.db_conn_string = db_conn_string
        self.headless = headless
        self.session_ua = get_random_ua()

    @property
    @abc.abstractmethod
    def source_name(self) -> str:
        ...

    @abc.abstractmethod
    def scrape(self) -> list[dict]:
        ...

    def random_delay(self, min_sec: float = 2.0, max_sec: float = 6.0):
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def get_browser_context(self, playwright):
        browser = playwright.chromium.launch(headless=self.headless)
        context = browser.new_context(
            user_agent=self.session_ua,
            viewport={"width": 1366, "height": 768},
            locale="en-PH",
            timezone_id="Asia/Manila",
        )
        context.set_default_timeout(30_000)
        return browser, context

    def save_raw(self, records: list[dict]):
        conn = psycopg2.connect(self.db_conn_string)
        try:
            with conn.cursor() as cur:
                for record in records:
                    cur.execute(
                        """
                        INSERT INTO raw.job_postings
                            (source, source_id, scraped_at, raw_data)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (source, source_id)
                        DO UPDATE SET
                            raw_data = EXCLUDED.raw_data,
                            scraped_at = EXCLUDED.scraped_at
                        """,
                        (
                            self.source_name,
                            record["source_id"],
                            datetime.now(timezone.utc),
                            json.dumps(record, ensure_ascii=False),
                        ),
                    )
            conn.commit()
            logger.info("Saved %d records from %s", len(records), self.source_name)
        finally:
            conn.close()

    def run(self) -> int:
        logger.info("Starting scrape: %s", self.source_name)
        try:
            records = self.scrape()
            self.save_raw(records)
            return len(records)
        except Exception:
            logger.exception("Scrape failed: %s", self.source_name)
            raise
```

## 3.2 PhilJobNet Scraper (Primary — Government Portal)

```python
# scrapers/philjobnet.py
import logging
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)
BASE_URL = "https://www.philjobnet.gov.ph"
SEARCH_URL = f"{BASE_URL}/search-jobs"


class PhilJobNetScraper(BaseScraper):
    source_name = "philjobnet"

    def scrape(self) -> list[dict]:
        records = []
        with sync_playwright() as p:
            browser, context = self.get_browser_context(p)
            page = context.new_page()
            try:
                records = self._scrape_listings(page)
            finally:
                browser.close()
        return records

    def _scrape_listings(self, page) -> list[dict]:
        records = []
        page_num = 1
        max_pages = 50

        while page_num <= max_pages:
            url = f"{SEARCH_URL}?page={page_num}"
            page.goto(url, wait_until="domcontentloaded")
            self.random_delay(2, 5)

            soup = BeautifulSoup(page.content(), "html.parser")
            job_cards = soup.select(".job-listing-card")

            if not job_cards:
                logger.info("No more listings at page %d", page_num)
                break

            for card in job_cards:
                record = self._parse_card(card)
                if record:
                    records.append(record)
            page_num += 1

        logger.info("Scraped %d listings from PhilJobNet", len(records))
        return records

    def _parse_card(self, card) -> dict | None:
        try:
            title_el = card.select_one(".job-title a")
            company_el = card.select_one(".company-name")
            location_el = card.select_one(".location")
            salary_el = card.select_one(".salary")

            source_id = title_el["href"].split("/")[-1] if title_el else None
            if not source_id:
                return None

            return {
                "source_id": f"philjobnet_{source_id}",
                "title": title_el.get_text(strip=True) if title_el else None,
                "company": company_el.get_text(strip=True) if company_el else None,
                "location": location_el.get_text(strip=True) if location_el else None,
                "salary_raw": salary_el.get_text(strip=True) if salary_el else None,
                "url": f"{BASE_URL}{title_el['href']}" if title_el else None,
            }
        except Exception:
            logger.warning("Failed to parse card", exc_info=True)
            return None
```

## 3.3 Kalibrr Scraper (API Intercept)

Kalibrr is a modern SPA. Intercept its internal API calls instead of parsing rendered HTML.

```python
# scrapers/kalibrr.py
import json
import logging
from playwright.sync_api import sync_playwright
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)
KALIBRR_API = "https://www.kalibrr.com/kjs/job_board/search"


class KalibrrScraper(BaseScraper):
    source_name = "kalibrr"

    def scrape(self) -> list[dict]:
        records = []
        with sync_playwright() as p:
            browser, context = self.get_browser_context(p)
            page = context.new_page()
            try:
                records = self._scrape_via_api_intercept(page)
            finally:
                browser.close()
        return records

    def _scrape_via_api_intercept(self, page) -> list[dict]:
        records = []
        offset = 0
        limit = 15

        while True:
            url = (
                f"{KALIBRR_API}?limit={limit}&offset={offset}"
                f"&country=Philippines"
            )
            page.goto(
                f"https://www.kalibrr.com/home/te/it-software/co/Philippines?offset={offset}",
                wait_until="networkidle",
            )
            self.random_delay(3, 7)

            response = page.evaluate(
                """async (url) => {
                    const resp = await fetch(url);
                    return await resp.json();
                }""",
                url,
            )

            jobs = response.get("jobs", [])
            if not jobs:
                break

            for job in jobs:
                records.append(
                    {
                        "source_id": f"kalibrr_{job['id']}",
                        "title": job.get("name"),
                        "company": job.get("company_info", {}).get("name"),
                        "location": job.get("google_location", {}).get(
                            "address_components", {}
                        ).get("city"),
                        "salary_raw": self._extract_salary(job),
                        "description": job.get("description"),
                        "employment_type": job.get("tenure"),
                        "experience_level": job.get("work_experience_value"),
                        "skills": [func.get("name") for func in job.get("function", [])],
                        "url": f"https://www.kalibrr.com/c/{job.get('company_info', {}).get('code')}/jobs/{job['id']}",
                        "posted_date": job.get("activation_date"),
                    }
                )

            offset += limit
            if offset > 500:
                break

        logger.info("Scraped %d jobs from Kalibrr", len(records))
        return records

    def _extract_salary(self, job: dict) -> str | None:
        sal_min = job.get("salary_from")
        sal_max = job.get("salary_to")
        currency = job.get("salary_currency", "PHP")
        if sal_min or sal_max:
            return f"{currency} {sal_min or '?'}-{sal_max or '?'}"
        return None
```

## 3.4 JobStreet Scraper (Redux Data Extraction)

JobStreet PH (SEEK platform) embeds job data in `window.__SEEK_REDUX_DATA__`.

```python
# scrapers/jobstreet.py
import json
import logging
import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)
JOBSTREET_SEARCH = "https://www.jobstreet.com.ph/jobs"


class JobStreetScraper(BaseScraper):
    source_name = "jobstreet"

    def scrape(self) -> list[dict]:
        records = []
        with sync_playwright() as p:
            browser, context = self.get_browser_context(p)
            page = context.new_page()
            try:
                for page_num in range(1, 31):
                    url = f"{JOBSTREET_SEARCH}?pg={page_num}"
                    page.goto(url, wait_until="domcontentloaded")
                    self.random_delay(3, 8)

                    redux_data = page.evaluate(
                        "() => window.__SEEK_REDUX_DATA__ || null"
                    )
                    if redux_data:
                        jobs = self._parse_redux(redux_data)
                        if not jobs:
                            break
                        records.extend(jobs)
                    else:
                        soup = BeautifulSoup(page.content(), "html.parser")
                        jobs = self._parse_html(soup)
                        if not jobs:
                            break
                        records.extend(jobs)
            finally:
                browser.close()
        logger.info("Scraped %d jobs from JobStreet", len(records))
        return records

    def _parse_redux(self, data: dict) -> list[dict]:
        records = []
        results = data.get("results", {}).get("results", {}).get("jobs", [])
        for job in results:
            records.append(
                {
                    "source_id": f"jobstreet_{job['id']}",
                    "title": job.get("title"),
                    "company": job.get("advertiser", {}).get("description"),
                    "location": job.get("location"),
                    "salary_raw": job.get("salary"),
                    "description": job.get("teaser"),
                    "url": f"https://www.jobstreet.com.ph/job/{job['id']}",
                    "posted_date": job.get("listingDate"),
                    "job_type": job.get("workType"),
                }
            )
        return records

    def _parse_html(self, soup) -> list[dict]:
        records = []
        for article in soup.select("article[data-testid='job-card']"):
            title_el = article.select_one("a[data-automation='jobTitle']")
            company_el = article.select_one("a[data-automation='jobCompany']")
            location_el = article.select_one("span[data-automation='jobLocation']")
            salary_el = article.select_one("span[data-automation='jobSalary']")

            job_id = title_el["href"].split("/")[-1] if title_el else None
            if not job_id:
                continue

            records.append(
                {
                    "source_id": f"jobstreet_{job_id}",
                    "title": title_el.get_text(strip=True) if title_el else None,
                    "company": company_el.get_text(strip=True) if company_el else None,
                    "location": location_el.get_text(strip=True) if location_el else None,
                    "salary_raw": salary_el.get_text(strip=True) if salary_el else None,
                    "url": f"https://www.jobstreet.com.ph{title_el['href']}" if title_el else None,
                }
            )
        return records
```

## 3.5 OnlineJobs.ph Scraper

```python
# scrapers/onlinejobs.py
import logging
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class OnlineJobsScraper(BaseScraper):
    source_name = "onlinejobs"

    def scrape(self) -> list[dict]:
        records = []
        with sync_playwright() as p:
            browser, context = self.get_browser_context(p)
            page = context.new_page()
            try:
                for page_num in range(1, 21):
                    url = f"https://www.onlinejobs.ph/jobseekers/jobsearch?page={page_num}"
                    page.goto(url, wait_until="domcontentloaded")
                    self.random_delay(3, 7)

                    soup = BeautifulSoup(page.content(), "html.parser")
                    cards = soup.select(".card.job-post")
                    if not cards:
                        break

                    for card in cards:
                        record = self._parse_card(card)
                        if record:
                            records.append(record)
            finally:
                browser.close()
        logger.info("Scraped %d jobs from OnlineJobs.ph", len(records))
        return records

    def _parse_card(self, card) -> dict | None:
        try:
            link = card.select_one("h4 a")
            salary_el = card.select_one(".salary-text")
            return {
                "source_id": f"onlinejobs_{link['href'].split('/')[-1]}",
                "title": link.get_text(strip=True),
                "salary_raw": salary_el.get_text(strip=True) if salary_el else None,
                "salary_currency": "USD",
                "url": f"https://www.onlinejobs.ph{link['href']}",
                "is_remote": True,
            }
        except Exception:
            logger.warning("Failed to parse OnlineJobs card", exc_info=True)
            return None
```

## 3.6 Indeed PH Scraper

```python
# scrapers/indeed.py
import logging
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class IndeedScraper(BaseScraper):
    source_name = "indeed"

    def scrape(self) -> list[dict]:
        records = []
        with sync_playwright() as p:
            browser, context = self.get_browser_context(p)
            page = context.new_page()
            try:
                for start in range(0, 300, 10):
                    url = f"https://ph.indeed.com/jobs?l=Philippines&start={start}"
                    page.goto(url, wait_until="domcontentloaded")
                    self.random_delay(4, 10)

                    if "captcha" in page.url.lower() or page.query_selector("#captcha-container"):
                        logger.warning("Indeed CAPTCHA detected at offset %d, stopping", start)
                        break

                    soup = BeautifulSoup(page.content(), "html.parser")
                    cards = soup.select("div.job_seen_beacon")
                    if not cards:
                        break

                    for card in cards:
                        record = self._parse_card(card)
                        if record:
                            records.append(record)
            finally:
                browser.close()
        logger.info("Scraped %d jobs from Indeed PH", len(records))
        return records

    def _parse_card(self, card) -> dict | None:
        try:
            title_el = card.select_one("h2.jobTitle a")
            company_el = card.select_one("[data-testid='company-name']")
            location_el = card.select_one("[data-testid='text-location']")
            salary_el = card.select_one(".salary-snippet-container")

            job_id = title_el.get("data-jk") if title_el else None
            if not job_id:
                href = title_el.get("href", "") if title_el else ""
                job_id = href.split("jk=")[-1].split("&")[0] if "jk=" in href else None
            if not job_id:
                return None

            return {
                "source_id": f"indeed_{job_id}",
                "title": title_el.get_text(strip=True) if title_el else None,
                "company": company_el.get_text(strip=True) if company_el else None,
                "location": location_el.get_text(strip=True) if location_el else None,
                "salary_raw": salary_el.get_text(strip=True) if salary_el else None,
                "url": f"https://ph.indeed.com/viewjob?jk={job_id}",
            }
        except Exception:
            logger.warning("Failed to parse Indeed card", exc_info=True)
            return None
```

## 3.7 Facebook Job Groups Scraper

Facebook is the hardest target. Use saved session cookies. Mark this as optional.

```python
# scrapers/facebook.py
import json
import logging
import os
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

FB_GROUPS = [
    "https://www.facebook.com/groups/itsaboringjob",
    "https://www.facebook.com/groups/phtechtechie",
    "https://www.facebook.com/groups/jobsphilippines2023",
]
COOKIES_PATH = Path(__file__).parent / ".fb_cookies.json"


class FacebookScraper(BaseScraper):
    source_name = "facebook"

    def scrape(self) -> list[dict]:
        if not COOKIES_PATH.exists():
            logger.error(
                "Facebook cookies not found at %s. "
                "Run `python -m scrapers.facebook --login` to generate them.",
                COOKIES_PATH,
            )
            return []

        records = []
        with sync_playwright() as p:
            browser, context = self.get_browser_context(p)
            context.add_cookies(json.loads(COOKIES_PATH.read_text()))
            page = context.new_page()
            try:
                for group_url in FB_GROUPS:
                    group_records = self._scrape_group(page, group_url)
                    records.extend(group_records)
            finally:
                browser.close()
        logger.info("Scraped %d posts from Facebook groups", len(records))
        return records

    def _scrape_group(self, page, group_url: str) -> list[dict]:
        records = []
        page.goto(group_url, wait_until="domcontentloaded")
        self.random_delay(5, 10)

        for _ in range(5):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self.random_delay(3, 6)

        soup = BeautifulSoup(page.content(), "html.parser")
        posts = soup.select("[role='article']")
        for post in posts:
            text = post.get_text(separator="\n", strip=True)
            if not self._looks_like_job_post(text):
                continue
            post_id = post.get("aria-label", "")[:50] or hash(text[:200])
            records.append(
                {
                    "source_id": f"fb_{hash(str(post_id))}",
                    "raw_text": text[:5000],
                    "group_url": group_url,
                }
            )
        return records

    def _looks_like_job_post(self, text: str) -> bool:
        text_lower = text.lower()
        job_keywords = [
            "hiring", "looking for", "we need", "job opening",
            "apply now", "send resume", "send cv", "₱", "salary",
            "full-time", "full time", "part-time", "part time",
        ]
        return any(kw in text_lower for kw in job_keywords)


if __name__ == "__main__":
    import sys
    if "--login" in sys.argv:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://www.facebook.com/login")
            input("Log in to Facebook in the browser, then press Enter here...")
            cookies = context.cookies()
            COOKIES_PATH.write_text(json.dumps(cookies))
            print(f"Cookies saved to {COOKIES_PATH}")
            browser.close()
```

## 3.8 Reddit Salary Scraper (API-based)

```python
# scrapers/reddit.py
import logging
from datetime import datetime, timezone
import requests
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)
SUBREDDIT = "phcareers"
SEARCH_TERMS = ["salary thread", "salary", "compensation", "offer"]


class RedditScraper(BaseScraper):
    source_name = "reddit"

    def scrape(self) -> list[dict]:
        records = []
        headers = {"User-Agent": "PHJobMarketTracker/1.0 (educational project)"}

        for term in SEARCH_TERMS:
            url = (
                f"https://www.reddit.com/r/{SUBREDDIT}/search.json"
                f"?q={term}&restrict_sr=1&sort=new&limit=25"
            )
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 429:
                logger.warning("Reddit rate limited, stopping")
                break
            if resp.status_code != 200:
                logger.warning("Reddit returned %d", resp.status_code)
                continue

            data = resp.json()
            posts = data.get("data", {}).get("children", [])
            for post in posts:
                pd = post["data"]
                records.append(
                    {
                        "source_id": f"reddit_{pd['id']}",
                        "title": pd.get("title"),
                        "selftext": pd.get("selftext", "")[:10000],
                        "score": pd.get("score"),
                        "num_comments": pd.get("num_comments"),
                        "created_utc": datetime.fromtimestamp(
                            pd["created_utc"], tz=timezone.utc
                        ).isoformat(),
                        "url": f"https://www.reddit.com{pd['permalink']}",
                    }
                )
            self.random_delay(2, 4)

        seen = set()
        unique = []
        for r in records:
            if r["source_id"] not in seen:
                seen.add(r["source_id"])
                unique.append(r)

        logger.info("Scraped %d unique posts from r/%s", len(unique), SUBREDDIT)
        return unique
```

## 3.9 Anti-Scraping Strategy

```python
# scrapers/utils/user_agents.py
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

def get_random_ua() -> str:
    return random.choice(USER_AGENTS)
```

| Strategy | Implementation | Why |
|---|---|---|
| Random delays | `random.uniform(2, 6)` between pages | Avoids rate detection patterns |
| User-agent rotation | Pick from 5+ modern UAs per session | Prevents UA-based blocking |
| Session cookies | Playwright contexts with persistent cookies | Looks like a real browser |
| Viewport randomization | Vary width 1280-1920 | Fingerprint diversity |
| Request spacing | Max 1 request per 3 seconds per domain | Stay under rate limits |
| Page limits | Cap at 20-50 pages per source per run | Don't vacuum entire sites |
| CAPTCHA detection | Check for CAPTCHA elements before parsing | Fail gracefully |
| Retry with backoff | Exponential backoff on 429/503 | Recover from temporary blocks |
| Time-of-day scheduling | Run at 2-4 AM Manila time | Lower traffic = less scrutiny |

**Ethical notes for README:**
- PhilJobNet is government data — freely accessible
- All other sites: scrape only public listings, respect robots.txt
- Reddit: use free API with proper User-Agent per Reddit's terms
- Facebook: most gray-area source — document why and mark as optional
