# =============================================================================
# scrapers/utils/salary_parser.py — parse raw salary strings into numbers
#
# WHAT IS THIS FILE?
# ------------------
# Job listings show salary in all kinds of formats:
#   "₱25,000 - ₱35,000/month"
#   "PHP 25k to 35k monthly"
#   "$500/month"
#   "Competitive salary"
#
# This file has ONE function: parse_salary(). It takes that messy raw string
# and returns a clean Python dict with min, max, currency, and period.
#
# WHERE IS THIS USED?
# -------------------
# NOT inside the scrapers. Scrapers store the raw salary string as-is.
# This function is called by dbt's intermediate models (Week 3) when we
# transform raw data into the warehouse schema.
#
# We write and test it now because:
# - Pure functions are easy to test in isolation
# - Getting it right early avoids downstream data quality issues
# =============================================================================

import re   # Python's regular expression library — for pattern matching in strings


def parse_salary(raw_str: str) -> dict:
    """
    Parse a raw salary string into structured fields.

    Parameters
    ----------
    raw_str : the salary string exactly as it appeared on the job listing

    Returns
    -------
    A dict with these keys:
        min      : int or None — lower bound in base currency units
        max      : int or None — upper bound (same as min if single value)
        currency : "PHP" or "USD" or None
        period   : "monthly" or "annual" or None

    Examples
    --------
    >>> parse_salary("₱25,000 - ₱35,000/month")
    {'min': 25000, 'max': 35000, 'currency': 'PHP', 'period': 'monthly'}

    >>> parse_salary("Competitive salary")
    {'min': None, 'max': None, 'currency': None, 'period': None}
    """
    # Return the "I don't know" result immediately if the string is empty or None
    if not raw_str or not raw_str.strip():
        return _empty()

    # Normalize: lowercase and strip whitespace so all our patterns work
    # regardless of how the site formatted the string
    text = raw_str.strip().lower()

    # -------------------------------------------------------------------------
    # Step 1: Detect currency
    # -------------------------------------------------------------------------
    currency = _detect_currency(text)

    # -------------------------------------------------------------------------
    # Step 2: Detect period (monthly vs annual)
    # -------------------------------------------------------------------------
    period = _detect_period(text)

    # -------------------------------------------------------------------------
    # Step 3: Extract the numbers
    # -------------------------------------------------------------------------
    # Remove currency symbols and word "php"/"usd" so they don't confuse the
    # number extractor
    cleaned = re.sub(r'[₱$]', '', text)
    cleaned = re.sub(r'\b(php|usd)\b', '', cleaned)

    numbers = _extract_numbers(cleaned)

    if not numbers:
        # No numbers found — "competitive salary", "negotiable", etc.
        return _empty()

    # If we found two numbers, they're the min and max of a range.
    # If we only found one, use it as both min and max.
    salary_min = numbers[0]
    salary_max = numbers[1] if len(numbers) >= 2 else numbers[0]

    # Sanity check: min should never be greater than max
    if salary_min > salary_max:
        salary_min, salary_max = salary_max, salary_min

    return {
        "min":      salary_min,
        "max":      salary_max,
        "currency": currency,
        "period":   period,
    }


# =============================================================================
# Helper functions (private — prefixed with _ by convention)
# =============================================================================

def _empty() -> dict:
    """Returns the "unknown salary" result."""
    return {"min": None, "max": None, "currency": None, "period": None}


def _detect_currency(text: str) -> str | None:
    """
    Returns "PHP", "USD", or None based on symbols and keywords in the text.

    We check for the peso sign (₱), the dollar sign ($), and the words
    "php" and "usd". If none are found, we default to PHP because this
    project focuses on the Philippine job market.
    """
    if "₱" in text or "php" in text:
        return "PHP"
    if "$" in text or "usd" in text or "dollar" in text:
        return "USD"
    # Default: assume PHP for PH job boards
    return "PHP"


def _detect_period(text: str) -> str | None:
    """
    Returns "monthly", "annual", or None.

    Most PH job boards show monthly salary. We check for annual keywords
    first since they're less common and easy to miss.
    """
    if any(word in text for word in ["annual", "yearly", "per year", "/year", "yr"]):
        return "annual"
    if any(word in text for word in ["month", "/mo", "mo.", "monthly"]):
        return "monthly"
    # Default: assume monthly for PH job boards
    return "monthly"


def _extract_numbers(text: str) -> list[int]:
    """
    Finds all salary numbers in a string and returns them as a list of ints.

    Handles:
    - "25,000"     → 25000   (comma separators)
    - "25k"        → 25000   (k suffix = thousands)
    - "25.5k"      → 25500   (decimal thousands)
    - "25000"      → 25000   (plain number)

    Returns up to 2 numbers (min and max of a range). Any additional numbers
    are ignored (e.g., "25k - 35k monthly, up to 50k with bonus" → [25000, 35000]).
    """
    numbers = []

    # Pattern explanation:
    # (\d{1,3}(?:,\d{3})*)  → matches numbers like 25,000 or 1,000,000
    #                          \d{1,3} = 1-3 digits, (?:,\d{3})* = optional comma groups
    # (?:\.\d+)?             → optional decimal part like .5 in "25.5k"
    # (?:k\b)?               → optional "k" suffix (thousands), \b = word boundary
    pattern = r'(\d{1,3}(?:,\d{3})*)(?:\.\d+)?(?:k\b)?'

    for match in re.finditer(pattern, text):
        full_match = match.group(0)        # the entire matched text, e.g. "25.5k"
        number_str = match.group(1)        # just the digit part, e.g. "25"

        # Remove commas: "25,000" → "25000"
        number_str = number_str.replace(",", "")
        value = float(number_str)

        # Check if there's a decimal part attached to the original match
        decimal_match = re.search(r'\.(\d+)', full_match)
        if decimal_match:
            decimal_part = float("0." + decimal_match.group(1))
            value += decimal_part

        # If the original match had a "k" suffix, multiply by 1000
        if full_match.endswith("k"):
            value *= 1000

        # Round to nearest integer (no fractional pesos)
        numbers.append(round(value))

        # We only need 2 numbers (min and max)
        if len(numbers) == 2:
            break

    return numbers
