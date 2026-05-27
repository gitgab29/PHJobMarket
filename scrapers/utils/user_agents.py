# =============================================================================
# scrapers/utils/user_agents.py — realistic browser User-Agent strings
#
# WHAT IS A USER-AGENT?
# ---------------------
# Every browser identifies itself to websites using a "User-Agent" (UA) string.
# For example, Chrome on Windows sends something like:
#   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ..."
#
# Playwright's default UA is obviously a bot. If we use it, sites can
# immediately detect we're scraping and block us. We rotate through real
# browser UAs to look like different human users.
#
# These are real UA strings from Chrome 125, Firefox 127, and Safari 17.
# =============================================================================

import random

USER_AGENTS = [
    # Chrome 125 on Windows 11
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",

    # Safari 17.5 on macOS Sonoma
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.5 Safari/605.1.15",

    # Firefox 127 on Windows 11
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) "
    "Gecko/20100101 Firefox/127.0",

    # Chrome 125 on Linux (common for developers)
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",

    # Chrome 125 on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]


def get_random_ua() -> str:
    """Returns a randomly chosen User-Agent string."""
    return random.choice(USER_AGENTS)
