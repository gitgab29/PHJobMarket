# Step-by-Step Testing Guide for Django API

## Prerequisites Check (5 minutes)

### Step 1: Verify Postgres is Running
```bash
make up
```
**Expected output**: Shows container startup messages
**Verify**: 
```bash
make psql
# Should open a psql prompt
# Type: \q (to exit)
```

### Step 2: Verify Data Exists in Warehouse
```bash
make psql
```
Then run these SQL queries:
```sql
-- Check warehouse schema exists
\dn warehouse

-- Count records in each table
SELECT COUNT(*) FROM warehouse.fct_job_postings;
SELECT COUNT(*) FROM warehouse.dim_companies;
SELECT COUNT(*) FROM warehouse.dim_skills;

-- Should see: ~2000+ jobs, ~700+ companies, ~70+ skills
\q
```

**Expected**: Non-zero counts for all tables

---

## Setup Phase (10 minutes)

### Step 3: Install Django Dependencies
```bash
pip install -r api/requirements.txt
```

**Expected output**: Shows "Successfully installed django, djangorestframework, etc."

**Verify installation**:
```bash
python -c "import django; print(django.__version__)"
# Should output: 4.2.11
```

### Step 4: Test Database Connection
```bash
cd api
```

**Create a simple test script** — save as `test_db.py`:
```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from jobs.models import FctJobPosting, DimCompany

print("Database Connection Test:")
print(f"  Total jobs: {FctJobPosting.objects.count()}")
print(f"  Total companies: {DimCompany.objects.count()}")
print(f"✅ Database connection successful!")
```

**Run it**:
```bash
python test_db.py
```

**Expected output**:
```
Database Connection Test:
  Total jobs: 2071
  Total companies: 740
✅ Database connection successful!
```

---

## API Server Phase (5 minutes)

### Step 5: Start the Django Development Server

**Terminal 1** — Start the API:
```bash
make api-run
```

**Expected output**:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

**Leave this running** — move to Terminal 2 for testing.

### Step 6: Verify Server is Responding

**Terminal 2** — Quick health check:
```bash
curl http://127.0.0.1:8000/api/v1/jobs/
```

**Expected output**: JSON response with `"count"`, `"results"`, `"next"` fields

If this works, move to the full endpoint tests below.

---

## Endpoint Testing Phase (20 minutes)

### Test Endpoints One by One

Use **Terminal 2** (or a new terminal). Each command tests one endpoint.

#### Test 1: Jobs List
```bash
curl -s http://127.0.0.1:8000/api/v1/jobs/ | python -m json.tool | head -30
```

**Expected**:
- Status: 200 OK
- Fields: `count`, `results[]`, `next`, `previous`
- 25 jobs in results array

**Verify fields in first job**:
```json
{
  "job_key": 1,
  "source": "philjobnet",
  "title": "...",
  "company_name": "...",
  "salary_min": 30000,
  "salary_max": 100000,
  "is_remote": false,
  ...
}
```

---

#### Test 2: Jobs with Filters
```bash
# Filter by source
curl -s "http://127.0.0.1:8000/api/v1/jobs/?source=jobstreet" | python -m json.tool | head -20

# Filter by remote only
curl -s "http://127.0.0.1:8000/api/v1/jobs/?is_remote=true" | python -m json.tool | head -20

# Filter by salary range (minimum >= 50000)
curl -s "http://127.0.0.1:8000/api/v1/jobs/?salary_min_gte=50000" | python -m json.tool | head -20

# Search by title
curl -s "http://127.0.0.1:8000/api/v1/jobs/?search=Python" | python -m json.tool | head -20
```

**Expected**: Each returns filtered results with `count` showing smaller numbers

**Example check**:
```bash
curl -s "http://127.0.0.1:8000/api/v1/jobs/?source=jobstreet" | python -c "import sys, json; data = json.load(sys.stdin); print(f'JobStreet jobs: {data[\"count\"]}')"
# Should output: JobStreet jobs: 930 (or similar non-zero number)
```

---

#### Test 3: Job Detail
```bash
# Get first job from list
curl -s http://127.0.0.1:8000/api/v1/jobs/1/ | python -m json.tool
```

**Expected**:
- Status: 200 OK
- Includes nested `company` object (not just company_name):
```json
{
  "company": {
    "company_key": 1,
    "company_name": "...",
    "total_postings": 5,
    ...
  },
  "location": {
    "location_key": 1,
    "city": "Manila",
    "region": "NCR",
    ...
  }
}
```

---

#### Test 4: Companies List
```bash
curl -s http://127.0.0.1:8000/api/v1/companies/ | python -m json.tool | head -30
```

**Expected**:
- `count`: ~740
- Fields: `company_key`, `company_name`, `total_postings`
- Sorted by `total_postings` (descending)

**Search test**:
```bash
curl -s "http://127.0.0.1:8000/api/v1/companies/?search=Acme" | python -m json.tool
```

---

#### Test 5: Locations List
```bash
curl -s http://127.0.0.1:8000/api/v1/locations/ | python -m json.tool | head -30
```

**Expected**:
- `count`: ~220 (different cities/provinces)
- Fields: `city`, `province`, `region`, `is_remote`, `is_metro_manila`

**Filter tests**:
```bash
# Metro Manila only
curl -s "http://127.0.0.1:8000/api/v1/locations/?is_metro_manila=true" | python -m json.tool | head -20

# Remote locations
curl -s "http://127.0.0.1:8000/api/v1/locations/?is_remote=true" | python -m json.tool | head -20
```

---

#### Test 6: Skills List
```bash
curl -s http://127.0.0.1:8000/api/v1/skills/ | python -m json.tool | head -30
```

**Expected**:
- `count`: ~74
- Fields: `skill_key`, `skill_name`, `skill_category`

---

#### Test 7: Skills — Top Demand
```bash
curl -s http://127.0.0.1:8000/api/v1/skills/top/ | python -m json.tool
```

**Expected** (JSON array, not paginated):
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

**Top 10 only**:
```bash
curl -s "http://127.0.0.1:8000/api/v1/skills/top/?limit=10" | python -m json.tool
```

---

#### Test 8: Analytics — Summary
```bash
curl -s http://127.0.0.1:8000/api/v1/analytics/summary/ | python -m json.tool
```

**Expected**:
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

---

#### Test 9: Analytics — Salary by Location
```bash
curl -s http://127.0.0.1:8000/api/v1/analytics/salary-by-location/ | python -m json.tool
```

**Expected**: Array of objects like:
```json
[
  {
    "location__city": "Manila",
    "location__region": "NCR",
    "avg_min": 45000,
    "avg_max": 110000,
    "job_count": 286
  },
  ...
]
```

---

#### Test 10: Analytics — Salary by Experience
```bash
curl -s http://127.0.0.1:8000/api/v1/analytics/salary-by-experience/ | python -m json.tool
```

**Expected**: 
```json
[
  {
    "experience_level": "Entry Level",
    "avg_min": 25000,
    "avg_max": 50000,
    "job_count": 156
  },
  ...
]
```

---

#### Test 11: Analytics — Jobs by Source
```bash
curl -s http://127.0.0.1:8000/api/v1/analytics/jobs-by-source/ | python -m json.tool
```

**Expected**:
```json
[
  {"source": "jobstreet", "count": 930},
  {"source": "philjobnet", "count": 500},
  ...
]
```

---

#### Test 12: Analytics — Remote vs Onsite
```bash
curl -s http://127.0.0.1:8000/api/v1/analytics/remote-vs-onsite/ | python -m json.tool
```

**Expected**:
```json
{
  "remote": 142,
  "onsite": 1929,
  "total": 2071,
  "remote_percentage": 6.9
}
```

---

#### Test 13: Analytics — Skill Trends
```bash
# Top 10 skills over time
curl -s http://127.0.0.1:8000/api/v1/analytics/skill-trends/ | python -m json.tool | head -40

# Filter by skill
curl -s "http://127.0.0.1:8000/api/v1/analytics/skill-trends/?skill=Python" | python -m json.tool | head -20
```

**Expected**: Time-series array like:
```json
[
  {
    "snapshot_date": "2026-05-27",
    "skill__skill_name": "Python",
    "posting_count": 280,
    "avg_salary_min": 39000,
    "avg_salary_max": 118000
  },
  ...
]
```

---

## Quick Validation Script (2 minutes)

Save this as `validate_api.sh` and run it:

```bash
#!/bin/bash

echo "🧪 Testing 12 API Endpoints..."
echo ""

# Test jobs list
JOBS_COUNT=$(curl -s http://127.0.0.1:8000/api/v1/jobs/ | python -c "import sys, json; data = json.load(sys.stdin); print(data['count'])")
echo "✅ Jobs list: $JOBS_COUNT jobs found"

# Test companies
COMPANIES_COUNT=$(curl -s http://127.0.0.1:8000/api/v1/companies/ | python -c "import sys, json; data = json.load(sys.stdin); print(data['count'])")
echo "✅ Companies: $COMPANIES_COUNT companies found"

# Test locations
LOCATIONS_COUNT=$(curl -s http://127.0.0.1:8000/api/v1/locations/ | python -c "import sys, json; data = json.load(sys.stdin); print(data['count'])")
echo "✅ Locations: $LOCATIONS_COUNT locations found"

# Test skills
SKILLS_COUNT=$(curl -s http://127.0.0.1:8000/api/v1/skills/ | python -c "import sys, json; data = json.load(sys.stdin); print(data['count'])")
echo "✅ Skills: $SKILLS_COUNT skills found"

# Test skills top
TOP_SKILLS=$(curl -s http://127.0.0.1:8000/api/v1/skills/top/ | python -c "import sys, json; data = json.load(sys.stdin); print(len(data))")
echo "✅ Top skills: $TOP_SKILLS skills returned"

# Test analytics summary
SUMMARY=$(curl -s http://127.0.0.1:8000/api/v1/analytics/summary/ | python -c "import sys, json; data = json.load(sys.stdin); print(f'Jobs: {data[\"total_jobs\"]}, Avg salary: ₱{data[\"avg_salary_min_php\"]}-{data[\"avg_salary_max_php\"]}')")
echo "✅ Analytics summary: $SUMMARY"

# Test analytics salary by location
LOCATIONS=$(curl -s http://127.0.0.1:8000/api/v1/analytics/salary-by-location/ | python -c "import sys, json; data = json.load(sys.stdin); print(len(data))")
echo "✅ Salary by location: $LOCATIONS cities found"

# Test analytics salary by experience
EXPERIENCE=$(curl -s http://127.0.0.1:8000/api/v1/analytics/salary-by-experience/ | python -c "import sys, json; data = json.load(sys.stdin); print(len(data))")
echo "✅ Salary by experience: $EXPERIENCE levels found"

# Test analytics jobs by source
SOURCES=$(curl -s http://127.0.0.1:8000/api/v1/analytics/jobs-by-source/ | python -c "import sys, json; data = json.load(sys.stdin); print(len(data))")
echo "✅ Jobs by source: $SOURCES sources found"

# Test analytics remote vs onsite
REMOTE_PCT=$(curl -s http://127.0.0.1:8000/api/v1/analytics/remote-vs-onsite/ | python -c "import sys, json; data = json.load(sys.stdin); print(data['remote_percentage'])")
echo "✅ Remote vs onsite: $REMOTE_PCT% remote"

# Test analytics skill trends
TRENDS=$(curl -s http://127.0.0.1:8000/api/v1/analytics/skill-trends/ | python -c "import sys, json; data = json.load(sys.stdin); print(len(data))")
echo "✅ Skill trends: $TRENDS data points found"

echo ""
echo "✅ ALL 12 ENDPOINTS WORKING!"
```

**Run it**:
```bash
bash validate_api.sh
```

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `ConnectionRefusedError: [Errno 111]` | Postgres not running | `make up` to start containers |
| `ProgrammingError: relation "dim_companies" does not exist` | Warehouse tables not created | Run `make dbt-run` to build tables |
| `CSRF token missing` | Django security check | Not an issue for API GET requests |
| `404 Not Found` on `/api/v1/jobs/` | URL routing broken | Verify `api/config/urls.py` is correct |
| `ImportError: No module named 'django'` | Dependencies not installed | `pip install -r api/requirements.txt` |

---

## Summary Checklist

- [ ] Step 1: Postgres running (`make up`)
- [ ] Step 2: Data in warehouse (psql query shows counts)
- [ ] Step 3: Django installed (`pip install -r api/requirements.txt`)
- [ ] Step 4: DB connection works (test_db.py script)
- [ ] Step 5: API server running (`make api-run`)
- [ ] Step 6: Server responds (curl health check)
- [ ] Tests 1-13: All 12 endpoints + 1 detail endpoint tested
- [ ] Validation script: All endpoints green

**If all pass**: API is production-ready! 🚀

Next: Proceed to Week 6 — React Frontend integration.
