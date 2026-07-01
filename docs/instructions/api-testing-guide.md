# API Testing Guide — 12 Endpoints

This guide provides curl commands and expected outputs for testing all 12 API endpoints.

## Prerequisites

```bash
# Start Postgres and other services
make up

# Install Django dependencies
pip install -r api/requirements.txt

# (Optional) Run database migrations for Django internal tables
cd api && python manage.py migrate

# Start the API server
make api-run
# Should output: "Starting development server at http://127.0.0.1:8000/"
```

## Testing All Endpoints

All commands assume API is running at `http://127.0.0.1:8000/`

### 1. Jobs — List

```bash
curl "http://127.0.0.1:8000/api/v1/jobs/"
```

**Expected**: Paginated list of 25 jobs with fields:
- `job_key`, `source`, `title`, `company_name`, `city`, `region`
- `salary_min`, `salary_max`, `salary_currency`, `salary_period`
- `employment_type`, `experience_level`, `is_remote`, `date_posted_key`, `url`
- `count`: total number of jobs
- `next`, `previous`: pagination links

**With filters**:
```bash
# Filter by source
curl "http://127.0.0.1:8000/api/v1/jobs/?source=philjobnet"

# Filter by salary range (min >= 30000)
curl "http://127.0.0.1:8000/api/v1/jobs/?salary_min_gte=30000"

# Filter by remote jobs
curl "http://127.0.0.1:8000/api/v1/jobs/?is_remote=true"

# Filter by location
curl "http://127.0.0.1:8000/api/v1/jobs/?city=Manila"

# Search by title or description
curl "http://127.0.0.1:8000/api/v1/jobs/?search=Python"

# Combine filters
curl "http://127.0.0.1:8000/api/v1/jobs/?source=jobstreet&is_remote=true&city=Manila"

# Order by salary (ascending)
curl "http://127.0.0.1:8000/api/v1/jobs/?ordering=salary_min"

# Order by date (descending) — default
curl "http://127.0.0.1:8000/api/v1/jobs/?ordering=-date_posted_key"

# Pagination (page 2, 25 per page)
curl "http://127.0.0.1:8000/api/v1/jobs/?page=2"
```

### 2. Jobs — Detail

```bash
curl "http://127.0.0.1:8000/api/v1/jobs/1/"
```

**Expected**: Single job object with nested company and location:
```json
{
  "job_key": 1,
  "source": "philjobnet",
  "source_id": "...",
  "title": "Senior Python Developer",
  "description": "...",
  "company": {
    "company_key": 1,
    "company_name": "Acme Corp",
    "company_slug": "acme-corp",
    "first_seen_at": "2026-01-15",
    "last_seen_at": "2026-05-30",
    "total_postings": 5
  },
  "location": {
    "location_key": 1,
    "raw_location": "Manila, Metro Manila",
    "city": "Manila",
    "province": "Metro Manila",
    "region": "NCR",
    "is_remote": false,
    "is_metro_manila": true
  },
  ...
}
```

### 3. Companies — List

```bash
curl "http://127.0.0.1:8000/api/v1/companies/"
```

**Expected**: Paginated list with fields:
- `company_key`, `company_name`, `company_slug`, `total_postings`
- `first_seen_at`, `last_seen_at`

**With search**:
```bash
curl "http://127.0.0.1:8000/api/v1/companies/?search=Acme"

# Order by posting count (descending) — default
curl "http://127.0.0.1:8000/api/v1/companies/"

# Order by name
curl "http://127.0.0.1:8000/api/v1/companies/?ordering=company_name"
```

### 4. Locations — List

```bash
curl "http://127.0.0.1:8000/api/v1/locations/"
```

**Expected**: List of locations with fields:
- `location_key`, `raw_location`, `city`, `province`, `region`
- `is_remote`, `is_metro_manila`

**With filters**:
```bash
# Remote jobs only
curl "http://127.0.0.1:8000/api/v1/locations/?is_remote=true"

# Metro Manila only
curl "http://127.0.0.1:8000/api/v1/locations/?is_metro_manila=true"

# By region
curl "http://127.0.0.1:8000/api/v1/locations/?region=NCR"

# Search
curl "http://127.0.0.1:8000/api/v1/locations/?search=Manila"
```

### 5. Skills — List

```bash
curl "http://127.0.0.1:8000/api/v1/skills/"
```

**Expected**: Paginated list with fields:
- `skill_key`, `skill_name`, `skill_category`

**Search by name**:
```bash
curl "http://127.0.0.1:8000/api/v1/skills/?search=Python"
```

### 6. Skills — Top Demand

```bash
curl "http://127.0.0.1:8000/api/v1/skills/top/"
```

**Expected**: Top 20 skills by posting count (latest snapshot):
```json
[
  {
    "id": 1,
    "snapshot_date": "2026-05-30",
    "skill_name": "Python",
    "skill_category": "Programming",
    "posting_count": 285,
    "avg_salary_min": 40000,
    "avg_salary_max": 120000,
    "source": null
  },
  ...
]
```

**With parameters**:
```bash
# Top 10 only
curl "http://127.0.0.1:8000/api/v1/skills/top/?limit=10"

# Top skills for a specific source
curl "http://127.0.0.1:8000/api/v1/skills/top/?source=jobstreet&limit=15"
```

### 7. Analytics — Summary

```bash
curl "http://127.0.0.1:8000/api/v1/analytics/summary/"
```

**Expected**: Dashboard metrics:
```json
{
  "total_jobs": 2071,
  "jobs_with_salary": 767,
  "remote_jobs": 142,
  "active_sources": 5,
  "avg_salary_min_php": 38000,
  "avg_salary_max_php": 98000
}
```

### 8. Analytics — Salary by Location

```bash
curl "http://127.0.0.1:8000/api/v1/analytics/salary-by-location/"
```

**Expected**: List of locations with salary stats (min 5 jobs):
```json
[
  {
    "location__city": "Manila",
    "location__region": "NCR",
    "avg_min": 45000,
    "avg_max": 110000,
    "job_count": 286
  },
  {
    "location__city": "Quezon City",
    "location__region": "NCR",
    "avg_min": 42000,
    "avg_max": 105000,
    "job_count": 198
  },
  ...
]
```

### 9. Analytics — Salary by Experience

```bash
curl "http://127.0.0.1:8000/api/v1/analytics/salary-by-experience/"
```

**Expected**: Salary breakdown by experience level:
```json
[
  {
    "experience_level": "Entry Level",
    "avg_min": 25000,
    "avg_max": 50000,
    "job_count": 156
  },
  {
    "experience_level": "Mid Level",
    "avg_min": 45000,
    "avg_max": 100000,
    "job_count": 324
  },
  {
    "experience_level": "Senior",
    "avg_min": 75000,
    "avg_max": 200000,
    "job_count": 187
  }
]
```

### 10. Analytics — Jobs by Source

```bash
curl "http://127.0.0.1:8000/api/v1/analytics/jobs-by-source/"
```

**Expected**: Job count per scraper:
```json
[
  {"source": "jobstreet", "count": 930},
  {"source": "philjobnet", "count": 500},
  {"source": "onlinejobs", "count": 120},
  {"source": "indeed", "count": 32},
  {"source": "kalibrr", "count": 489}
]
```

### 11. Analytics — Remote vs Onsite

```bash
curl "http://127.0.0.1:8000/api/v1/analytics/remote-vs-onsite/"
```

**Expected**: Breakdown:
```json
{
  "remote": 142,
  "onsite": 1929,
  "total": 2071,
  "remote_percentage": 6.9
}
```

### 12. Analytics — Skill Trends

```bash
# Without parameters (top 10 skills over time)
curl "http://127.0.0.1:8000/api/v1/analytics/skill-trends/"

# Filter by skill name
curl "http://127.0.0.1:8000/api/v1/analytics/skill-trends/?skill=Python"

# Limit to 5 skills
curl "http://127.0.0.1:8000/api/v1/analytics/skill-trends/?limit=5"
```

**Expected**: Time-series data for skill demand:
```json
[
  {
    "snapshot_date": "2026-05-27",
    "skill__skill_name": "Python",
    "posting_count": 280,
    "avg_salary_min": 39000,
    "avg_salary_max": 118000
  },
  {
    "snapshot_date": "2026-05-28",
    "skill__skill_name": "Python",
    "posting_count": 283,
    "avg_salary_min": 40000,
    "avg_salary_max": 120000
  },
  ...
]
```

## Error Responses

### 404 Not Found
```bash
curl "http://127.0.0.1:8000/api/v1/jobs/9999999/"
# Response: {"detail":"Not found."}
```

### 400 Bad Request
```bash
curl "http://127.0.0.1:8000/api/v1/jobs/?salary_min_gte=invalid"
# Response: {"salary_min_gte":["A valid number is required."]}
```

## Tools for Testing

### curl (command-line)
```bash
curl "http://127.0.0.1:8000/api/v1/jobs/" | python -m json.tool
```

### HTTPie (simpler curl alternative)
```bash
pip install httpie
http GET http://127.0.0.1:8000/api/v1/jobs/ source==philjobnet
```

### Postman (GUI)
- Import: `GET http://127.0.0.1:8000/api/v1/`
- Create requests for each endpoint above
- Use the "Tests" tab to validate responses

### Python requests library
```python
import requests

resp = requests.get("http://127.0.0.1:8000/api/v1/jobs/", params={"source": "philjobnet"})
print(resp.json())
```

## Performance Notes

- **Jobs list**: Optimized with `select_related("company", "location")` — no N+1 queries
- **Pagination**: 25 items per page by default; adjust with `page` param
- **Analytics**: Aggregation happens in DB, not in Python — fast even with large datasets
- **Skills top**: Filtered to latest snapshot only — O(1) regardless of historical depth

## Integration with Frontend

The React frontend (Week 6) will call:

```javascript
// Fetch jobs with filters
const response = await fetch('/api/v1/jobs/?source=philjobnet&is_remote=true');
const { results, count, next } = await response.json();

// Fetch job detail
const job = await fetch('/api/v1/jobs/123/').then(r => r.json());

// Fetch dashboard metrics
const summary = await fetch('/api/v1/analytics/summary/').then(r => r.json());
```

All endpoints support standard REST conventions: pagination, filtering, searching, and ordering.
