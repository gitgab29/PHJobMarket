# =============================================================================
# scrapers/tests/test_salary_parser.py — unit tests for salary_parser.py
#
# WHAT IS THIS FILE?
# ------------------
# Tests verify that parse_salary() correctly handles all the messy salary
# formats we'll encounter across 7 job boards.
#
# HOW TO RUN:
#   cd scrapers
#   python -m pytest tests/test_salary_parser.py -v
#
# The -v flag means "verbose" — it prints each test name and PASSED/FAILED
# instead of just a dot. Much easier to read when debugging.
#
# WHY WRITE TESTS?
# ----------------
# salary_parser.py will be called millions of times by dbt on real data.
# A silent bug here (e.g., treating "25k" as 25 instead of 25000) would
# corrupt salary analytics across the whole project. Tests catch this early.
# =============================================================================

import pytest
# Import the function we're testing. The path works because we run pytest
# from inside the scrapers/ directory (see the Makefile's test target).
from utils.salary_parser import parse_salary


# =============================================================================
# Test cases — PHP ranges
# =============================================================================

def test_peso_sign_range():
    """Standard PhilJobNet / JobStreet format with peso sign."""
    result = parse_salary("₱25,000 - ₱35,000/month")
    assert result["min"] == 25000
    assert result["max"] == 35000
    assert result["currency"] == "PHP"
    assert result["period"] == "monthly"


def test_php_word_range():
    """Some sites spell out "PHP" instead of using the ₱ symbol."""
    result = parse_salary("PHP 25,000 to 35,000 monthly")
    assert result["min"] == 25000
    assert result["max"] == 35000
    assert result["currency"] == "PHP"
    assert result["period"] == "monthly"


def test_k_suffix_range():
    """Kalibrr and OnlineJobs often use "k" shorthand for thousands."""
    result = parse_salary("PHP 25k - 35k")
    assert result["min"] == 25000
    assert result["max"] == 35000
    assert result["currency"] == "PHP"


def test_single_value():
    """Some listings show a single number, not a range."""
    result = parse_salary("₱30,000/month")
    assert result["min"] == 30000
    assert result["max"] == 30000
    assert result["currency"] == "PHP"
    assert result["period"] == "monthly"


def test_annual_salary():
    """Annual salaries appear on some executive listings."""
    result = parse_salary("PHP 600,000 per year")
    assert result["min"] == 600000
    assert result["max"] == 600000
    assert result["currency"] == "PHP"
    assert result["period"] == "annual"


# =============================================================================
# Test cases — USD (OnlineJobs.ph remote jobs)
# =============================================================================

def test_usd_dollar_sign():
    """OnlineJobs.ph lists USD salaries for remote work."""
    result = parse_salary("$500/month")
    assert result["min"] == 500
    assert result["max"] == 500
    assert result["currency"] == "USD"
    assert result["period"] == "monthly"


def test_usd_word_range():
    """Some remote listings spell out USD."""
    result = parse_salary("USD 1,000 - 1,500 monthly")
    assert result["min"] == 1000
    assert result["max"] == 1500
    assert result["currency"] == "USD"
    assert result["period"] == "monthly"


# =============================================================================
# Test cases — unstructured / unparseable
# =============================================================================

def test_competitive_salary():
    """Common placeholder text — no numbers, should return all None."""
    result = parse_salary("Competitive salary")
    assert result["min"] is None
    assert result["max"] is None
    assert result["currency"] is None
    assert result["period"] is None


def test_negotiable():
    """Another common placeholder."""
    result = parse_salary("Negotiable")
    assert result["min"] is None
    assert result["max"] is None


def test_empty_string():
    """Empty string should not crash — return all None."""
    result = parse_salary("")
    assert result["min"] is None
    assert result["max"] is None


def test_none_input():
    """None input should not crash — return all None."""
    result = parse_salary(None)
    assert result["min"] is None
    assert result["max"] is None


# =============================================================================
# Test cases — edge cases
# =============================================================================

def test_decimal_k():
    """
    "25.5k" is unusual but appears on some listings.
    Should parse to 25500, not 25000 or 255000.
    """
    result = parse_salary("PHP 25.5k - 30k")
    assert result["min"] == 25500
    assert result["max"] == 30000


def test_min_max_order():
    """
    If somehow min > max in the string, we should swap them.
    Defensive test — shouldn't happen in practice but good to verify.
    """
    result = parse_salary("₱35,000 - ₱25,000/month")
    assert result["min"] == 25000
    assert result["max"] == 35000
