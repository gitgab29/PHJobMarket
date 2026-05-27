# 7. Salary Parsing Logic

The most underestimated component. PH salary formats are wildly inconsistent.

## Formats you will encounter

```
₱30,000 - ₱50,000 / month
PHP 30,000-50,000
30k-50k
Php30,000.00 ~ Php50,000.00
30,000 to 50,000 monthly
₱30k - ₱50k per month
25000-35000
PHP 15,000 - PHP 25,000 per month
Competitive salary  (not parseable)
Negotiable          (not parseable)
Up to ₱80,000
$500-$800/month     (OnlineJobs.ph, USD)
P30,000             (old peso sign)
```

## Implementation

```python
# scrapers/utils/salary_parser.py
import re
from dataclasses import dataclass


@dataclass
class ParsedSalary:
    min_value: float | None
    max_value: float | None
    currency: str
    period: str  # 'monthly', 'yearly', 'hourly', 'daily'
    raw: str


K_PATTERN = re.compile(r'(\d+(?:\.\d+)?)\s*[kK]')
NUMBER_PATTERN = re.compile(r'(\d+(?:,\d{3})*(?:\.\d+)?)')


def parse_salary(raw: str | None) -> ParsedSalary | None:
    if not raw or not raw.strip():
        return None

    raw = raw.strip()
    raw_lower = raw.lower()

    skip_patterns = [
        'competitive', 'negotiable', 'not disclosed',
        'confidential', 'depends on', 'open', 'doh', 'tbd',
    ]
    if any(p in raw_lower for p in skip_patterns):
        return None

    currency = _detect_currency(raw)
    period = _detect_period(raw)

    # Try K format first (30k-50k)
    k_matches = K_PATTERN.findall(raw)
    if k_matches:
        values = [float(v) * 1000 for v in k_matches]
        return ParsedSalary(
            min_value=values[0],
            max_value=values[1] if len(values) > 1 else None,
            currency=currency, period=period, raw=raw,
        )

    # Standard number extraction
    numbers = NUMBER_PATTERN.findall(raw)
    if numbers:
        values = [float(n.replace(',', '')) for n in numbers]
        values = [v for v in values if v < 50_000_000 and v != 0]
        if not values:
            return None

        if 'up to' in raw_lower and len(values) == 1:
            return ParsedSalary(
                min_value=None, max_value=values[0],
                currency=currency, period=period, raw=raw,
            )

        return ParsedSalary(
            min_value=values[0],
            max_value=values[1] if len(values) > 1 else None,
            currency=currency, period=period, raw=raw,
        )

    return None


def _detect_currency(raw: str) -> str:
    if re.search(r'(\$|USD|US\s*Dollar)', raw, re.IGNORECASE):
        return 'USD'
    if re.search(r'(EUR|€)', raw, re.IGNORECASE):
        return 'EUR'
    return 'PHP'


def _detect_period(raw: str) -> str:
    raw_lower = raw.lower()
    if any(p in raw_lower for p in ['per hour', '/hr', 'hourly', '/hour']):
        return 'hourly'
    if any(p in raw_lower for p in ['per day', '/day', 'daily']):
        return 'daily'
    if any(p in raw_lower for p in ['per year', '/yr', 'yearly', 'annual', 'p.a.', 'per annum']):
        return 'yearly'
    return 'monthly'


def normalize_to_monthly(salary: ParsedSalary) -> ParsedSalary:
    multiplier = {'hourly': 8 * 22, 'daily': 22, 'monthly': 1, 'yearly': 1 / 12}.get(salary.period, 1)
    fx = 56.0 if salary.currency == 'USD' else 1.0
    return ParsedSalary(
        min_value=salary.min_value * multiplier * fx if salary.min_value else None,
        max_value=salary.max_value * multiplier * fx if salary.max_value else None,
        currency='PHP', period='monthly', raw=salary.raw,
    )
```

## Tests

```python
# scrapers/tests/test_salary_parser.py
import pytest
from scrapers.utils.salary_parser import parse_salary, normalize_to_monthly


@pytest.mark.parametrize("raw,expected_min,expected_max,currency,period", [
    ("₱30,000 - ₱50,000 / month", 30000, 50000, "PHP", "monthly"),
    ("PHP 30,000-50,000", 30000, 50000, "PHP", "monthly"),
    ("30k-50k", 30000, 50000, "PHP", "monthly"),
    ("Php30,000.00 ~ Php50,000.00", 30000, 50000, "PHP", "monthly"),
    ("₱30k - ₱50k per month", 30000, 50000, "PHP", "monthly"),
    ("25000-35000", 25000, 35000, "PHP", "monthly"),
    ("Up to ₱80,000", None, 80000, "PHP", "monthly"),
    ("$500-$800/month", 500, 800, "USD", "monthly"),
    ("P30,000", 30000, None, "PHP", "monthly"),
    ("₱15,000 - ₱25,000 per month", 15000, 25000, "PHP", "monthly"),
    ("PHP 500,000 - PHP 800,000 per year", 500000, 800000, "PHP", "yearly"),
    ("$5/hour", 5, None, "USD", "hourly"),
])
def test_parse_salary(raw, expected_min, expected_max, currency, period):
    result = parse_salary(raw)
    assert result is not None
    assert result.min_value == expected_min
    assert result.max_value == expected_max
    assert result.currency == currency
    assert result.period == period


@pytest.mark.parametrize("raw", [
    "Competitive salary", "Negotiable", "Not Disclosed", "", None, "TBD",
])
def test_parse_salary_unparseable(raw):
    assert parse_salary(raw) is None


def test_normalize_usd_to_monthly_php():
    result = parse_salary("$500-$800/month")
    normalized = normalize_to_monthly(result)
    assert normalized.currency == "PHP"
    assert normalized.min_value == 500 * 56.0
    assert normalized.max_value == 800 * 56.0
```
