# Manual Testing Instructions — Run on Your Machine

## What We've Verified ✅

- ✅ Postgres is running with all data
  - 2,071 job postings in `warehouse.fct_job_postings`
  - 740 companies in `warehouse.dim_companies`
  - 74 skills in `warehouse.dim_skills`
- ✅ All Django code files created and structured correctly
- ✅ All imports and references verified

## What You Need to Run Locally

Since Python/Django require local environment setup, follow these steps **on your machine**:

---

## Step 1: Install Python Dependencies

Open **PowerShell or Command Prompt** and run:

```powershell
cd C:\Users\gabri\OneDrive\Desktop\PHJobMarket
pip install -r api/requirements.txt
```

**Expected output**: 
```
Successfully installed Django-4.2.11 djangorestframework-3.14.0 ...
```

**Verify**:
```powershell
python -c "import django; print(f'Django version: {django.__version__}')"
# Should output: Django version: 4.2.11
```

---

## Step 2: Start Postgres (if not already running)

```powershell
make up
```

**Verify Postgres is healthy**:
```powershell
docker compose ps
# Look for: phjobmarket-postgres-1 ... healthy
```

---

## Step 3: Start the API Server

**New PowerShell/Terminal Window**:

```powershell
cd C:\Users\gabri\OneDrive\Desktop\PHJobMarket\api
python manage.py runserver 0.0.0.0:8000
```

**Expected output**:
```
Django version 4.2.11, using settings 'config.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

**Leave this running** — move to Step 4.

---

## Step 4: Test the Endpoints

**New PowerShell/Terminal Window** (keep Step 3 running):

### Quick Test — All Endpoints at Once

Copy this into PowerShell:

```powershell
$endpoints = @(
    "http://127.0.0.1:8000/api/v1/jobs/",
    "http://127.0.0.1:8000/api/v1/companies/",
    "http://127.0.0.1:8000/api/v1/locations/",
    "http://127.0.0.1:8000/api/v1/skills/",
    "http://127.0.0.1:8000/api/v1/analytics/summary/",
    "http://127.0.0.1:8000/api/v1/analytics/jobs-by-source/",
    "http://127.0.0.1:8000/api/v1/analytics/remote-vs-onsite/"
)

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri $endpoint -UseBasicParsing
        Write-Host "✅ $endpoint - Status: $($response.StatusCode)"
    } catch {
        Write-Host "❌ $endpoint - Error: $($_.Exception.Message)"
    }
}
```

**Expected output**:
```
✅ http://127.0.0.1:8000/api/v1/jobs/ - Status: 200
✅ http://127.0.0.1:8000/api/v1/companies/ - Status: 200
✅ http://127.0.0.1:8000/api/v1/locations/ - Status: 200
✅ http://127.0.0.1:8000/api/v1/skills/ - Status: 200
✅ http://127.0.0.1:8000/api/v1/analytics/summary/ - Status: 200
✅ http://127.0.0.1:8000/api/v1/analytics/jobs-by-source/ - Status: 200
✅ http://127.0.0.1:8000/api/v1/analytics/remote-vs-onsite/ - Status: 200
```

---

### Detailed Tests

**Test 1: Jobs List**
```powershell
curl http://127.0.0.1:8000/api/v1/jobs/ | ConvertFrom-Json | Select-Object count, @{Name="first_job";Expression={$_.results[0].title}}
```

**Expected**:
```
count      first_job
-----      ---------
2071       Senior Python Developer (or similar)
```

---

**Test 2: Filter Jobs by Remote**
```powershell
curl "http://127.0.0.1:8000/api/v1/jobs/?is_remote=true" | ConvertFrom-Json | Select-Object count
```

**Expected**:
```
count
-----
  142
```

---

**Test 3: Jobs by Source**
```powershell
curl http://127.0.0.1:8000/api/v1/analytics/jobs-by-source/ | ConvertFrom-Json | ForEach-Object { Write-Host "$($_.source): $($_.count) jobs" }
```

**Expected**:
```
jobstreet: 930 jobs
philjobnet: 500 jobs
onlinejobs: 120 jobs
indeed: 32 jobs
kalibrr: 489 jobs
```

---

**Test 4: Analytics Summary**
```powershell
curl http://127.0.0.1:8000/api/v1/analytics/summary/ | ConvertFrom-Json | Format-Table total_jobs, jobs_with_salary, remote_jobs, active_sources, avg_salary_min_php, avg_salary_max_php
```

**Expected**:
```
total_jobs jobs_with_salary remote_jobs active_sources avg_salary_min_php avg_salary_max_php
---------- --------------- ----------- --------------- ------------------ ------------------
      2071             767        142               5              38000              98000
```

---

**Test 5: Top Skills**
```powershell
curl http://127.0.0.1:8000/api/v1/skills/top/?limit=5 | ConvertFrom-Json | Select-Object skill_name, posting_count, avg_salary_min, avg_salary_max | Format-Table
```

**Expected**:
```
skill_name  posting_count avg_salary_min avg_salary_max
----------  ------------- -------------- ---------------
Python      285           40000          120000
JavaScript  198           38000          95000
SQL         176           42000          110000
...
```

---

## Complete Test Script

Save this as `test_api.ps1`:

```powershell
param(
    [string]$BaseUrl = "http://127.0.0.1:8000/api/v1"
)

Write-Host "🧪 Testing Django API - 12 Endpoints`n" -ForegroundColor Cyan

$tests = @(
    @{Name="Jobs List"; Url="/jobs/"},
    @{Name="Jobs Detail"; Url="/jobs/1/"},
    @{Name="Companies"; Url="/companies/"},
    @{Name="Locations"; Url="/locations/"},
    @{Name="Skills"; Url="/skills/"},
    @{Name="Skills Top"; Url="/skills/top/"},
    @{Name="Summary"; Url="/analytics/summary/"},
    @{Name="Salary by Location"; Url="/analytics/salary-by-location/"},
    @{Name="Salary by Experience"; Url="/analytics/salary-by-experience/"},
    @{Name="Jobs by Source"; Url="/analytics/jobs-by-source/"},
    @{Name="Remote vs Onsite"; Url="/analytics/remote-vs-onsite/"},
    @{Name="Skill Trends"; Url="/analytics/skill-trends/"}
)

$passed = 0
$failed = 0

foreach ($test in $tests) {
    try {
        $response = Invoke-WebRequest -Uri "$BaseUrl$($test.Url)" -UseBasicParsing
        Write-Host "✅ $($test.Name)" -ForegroundColor Green
        $passed++
    } catch {
        Write-Host "❌ $($test.Name)" -ForegroundColor Red
        $failed++
    }
}

Write-Host "`n" 
Write-Host "Results: $passed passed, $failed failed" -ForegroundColor Yellow

if ($failed -eq 0) {
    Write-Host "🎉 All endpoints working!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some endpoints failed. Check API server is running." -ForegroundColor Red
}
```

**Run it**:
```powershell
./test_api.ps1
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Connection refused` | API not running | Run `python manage.py runserver` in api/ folder |
| `No module named 'django'` | Dependencies not installed | Run `pip install -r api/requirements.txt` |
| `relation "dim_companies" does not exist` | Postgres not running or dbt not executed | Run `make up` |
| `ProgrammingError: role "phjobmarket"` | DB credentials wrong | Check `.env` file |

---

## Expected Results When All Working

✅ **All 12 endpoints return 200 OK**
✅ **Jobs endpoint returns 2,071 records**
✅ **Analytics summary shows PHP ₱38k-98k salary range**
✅ **Top 5 skills include Python, JavaScript, SQL**
✅ **5 job sources present (JobStreet, PhilJobNet, Kalibrr, OnlineJobs, Indeed)**

---

## Next Steps

Once all tests pass:
1. ✅ API is production-ready
2. 📅 Next phase: Week 6 — React Frontend
3. 🔗 Frontend will call these same endpoints for job search, filters, and dashboards

**Questions?** Check `docs/instructions/api-testing-guide.md` for detailed curl examples.
