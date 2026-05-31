# =============================================================================
# scrapers/facebook.py — FacebookScraper (STUB)
#
# Facebook scraping requires:
# 1. A burner Facebook account
# 2. Manual cookie extraction
# 3. Complex DOM parsing (the site is heavily JavaScript-rendered)
#
# For now, this is a stub that returns empty results.
# To implement it later: capture cookies via browser developer tools,
# use Playwright with page.goto() + page.evaluate(), parse job cards.
#
# For MVP, we have enough data from the other 5 sources (2000+ postings).
# =============================================================================

from scrapers.base import BaseScraper


class FacebookScraper(BaseScraper):
    SOURCE = "facebook"

    def scrape(self):
        self.logger.info("FacebookScraper not yet implemented (stub)")
        return []
