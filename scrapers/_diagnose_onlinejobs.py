"""
Diagnostic: inspect OnlineJobs.ph page structure.
Run: py -m scrapers._diagnose_onlinejobs
Dumps page HTML to _onlinejobs_page.html so you can open it and find the real selectors.
"""
import os
import time
from playwright.sync_api import sync_playwright

URL = "https://www.onlinejobs.ph/jobseekers/jobsearch"

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={"width": 1366, "height": 768},
        locale="en-PH",
        timezone_id="Asia/Manila",
    )
    page = context.new_page()

    print(f"Loading {URL} ...")
    page.goto(URL, wait_until="load", timeout=45_000)
    time.sleep(5)  # let JS settle

    title = page.title()
    current_url = page.url
    html = page.content()

    print(f"Title   : {title}")
    print(f"Final URL: {current_url}")
    print(f"HTML len : {len(html)}")

    # Try candidate selectors and report counts
    candidates = [
        ".card.job-post",
        ".job-post",
        "[class*='job-post']",
        "[class*='jobpost']",
        "[class*='job_post']",
        ".job-listing",
        ".job-card",
        "[class*='job-card']",
        "[class*='jobListing']",
        "article",
        ".card",
        "li[class*='job']",
        "div[class*='job']",
    ]
    print("\nSelector probe:")
    for sel in candidates:
        count = page.locator(sel).count()
        if count:
            print(f"  {count:3d}  {sel}")
        else:
            print(f"    0  {sel}")

    # Save HTML for manual inspection
    out = "_onlinejobs_page.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\nFull HTML saved to {out}")
    print("Open it in a browser (File → Open) and inspect the job card elements.")

    browser.close()
