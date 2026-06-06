# Week 6: React Frontend — Complete Guide

## Overview

The PH Job Market Tracker is now **fully integrated**: PostgreSQL database → dbt warehouse → Airflow orchestration → Django REST API → React + Recharts dashboard.

This guide walks you through running the entire stack for local development and testing.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          React Frontend                          │
│                    (Vite, TailwindCSS, Recharts)                 │
│                     http://localhost:5173                        │
└────────────────────────────┬────────────────────────────────────┘
                             │ (fetch)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Django REST API                              │
│                      (DRF, unmanaged)                            │
│                  http://localhost:8000/api/v1                    │
└────────────────────────────┬────────────────────────────────────┘
                             │ (SQL queries)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PostgreSQL Data Warehouse                       │
│           (dbt star schema: dims + facts in warehouse)           │
│                    localhost:15432/phjobmarket                   │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start (Local Dev)

### 1. Start the Database

```bash
# From project root
docker compose up -d postgres
```

Postgres is now at `localhost:15432` (user: `postgres`, pass: `postgres`).

### 2. Run Migrations & Load Warehouse

```bash
# Load raw schema
make psql < migrations/001_raw_schema.sql

# Or manually:
docker compose exec postgres psql -U postgres -d phjobmarket < migrations/001_raw_schema.sql
```

### 3. Populate Raw Data (Choose One)

**Option A: Use Airflow (orchestrated)**

```bash
docker compose up -d airflow-webserver airflow-scheduler
# UI at http://localhost:8080 (admin/admin)
# Trigger DAG: scrape_all_sources → dbt_transform
```

**Option B: Run Scrapers + dbt Manually (faster for testing)**

```bash
cd scrapers
python -m playwright install  # one-time
python -c "from philjobnet import PhilJobNetScraper; s = PhilJobNetScraper(); s.run()"
# Repeat for other scrapers: kalibrr, jobstreet, onlinejobs, indeed

cd ../dbt_transform
dbt deps
dbt seed
dbt run
dbt test
```

Verify data loaded:

```bash
docker compose exec postgres psql -U postgres -d phjobmarket -c "SELECT COUNT(*) FROM raw.job_postings;"
# Should show: 2000+ records

docker compose exec postgres psql -U postgres -d phjobmarket -c "SELECT COUNT(*) FROM warehouse.fct_job_postings;"
# Should show: 1500-2000 unique deduplicated jobs
```

### 4. Start Django API

```bash
cd api
pip install -r requirements.txt
python manage.py runserver 0.0.0.0:8000
```

API is now at `http://localhost:8000`. Test it:

```bash
curl http://localhost:8000/api/v1/jobs/ | jq '.results | length'
# Should return count of jobs
```

### 5. Start React Frontend

```bash
cd frontend
npm install  # if first time
npm run dev
```

Frontend is now at `http://localhost:5173`.

## Manual Testing

### Jobs Page (http://localhost:5173)

1. **Search**: Type a job title in the search bar → results update
2. **Filters**:
   - Set salary range (e.g., 30000-100000)
   - Pick a location from dropdown
   - Select an employment type
   - Toggle remote
   - All filters work together (AND logic)
3. **Sort**: Change sort order → results re-order
4. **Pagination**: Navigate between pages
5. **Detail**: Click any job → drawer slides in with full info + apply link

### Dashboard Page (http://localhost:5173/dashboard)

1. **Summary cards** load with total jobs, avg/max salary, top location/company
2. **Charts** render:
   - Salary by location (bar chart, only cities with ≥8 jobs)
   - Jobs by source (pie chart showing all 6 sources)
   - Remote vs onsite (donut)
   - Salary by experience (bar chart by level)
   - Top 10 skills (bar chart)
3. Hover over charts → tooltips appear
4. All data is read from Django API (no hard-coded mock data)

## API Endpoint Reference

### Jobs

```
GET /api/v1/jobs/
  ?page=1
  &search=senior
  &salary_min=50000&salary_max=200000
  &employment_type=fulltime
  &location=Manila
  &company_name=Google
  &source=indeed
  &is_remote=true
  &ordering=-date_posted
```

Returns: `{count, next, previous, results: [...]}`

```
GET /api/v1/jobs/{id}/
```

Returns: Job detail (same fields + full posting URL).

### Master Data

```
GET /api/v1/companies/
GET /api/v1/locations/
GET /api/v1/skills/
GET /api/v1/skills/top/?limit=20
```

### Analytics

```
GET /api/v1/analytics/dashboard_summary/
GET /api/v1/analytics/salary_by_location/
GET /api/v1/analytics/salary_by_experience/
GET /api/v1/analytics/jobs_by_source/
GET /api/v1/analytics/remote_vs_onsite/
GET /api/v1/analytics/skill_trends/
```

## Troubleshooting

### Frontend shows "Error: Network Error"

**Cause**: Django API not running or CORS misconfigured.

**Fix**:
```bash
# Check API is running
curl http://localhost:8000/api/v1/jobs/

# If 404 or timeout, start Django:
cd api && python manage.py runserver
```

### Dashboard charts are empty

**Cause**: No data in database (scrapers didn't run).

**Fix**: Run scrapers + dbt:
```bash
cd scrapers && python philjobnet.py  # or other source
cd ../dbt_transform && dbt run
```

### "CORS origin not allowed"

**Cause**: API CORS settings only allow `localhost` but you're running on different port.

**Fix**: Django settings already include `http://localhost:*`. If issue persists, check `api/config/settings.py` and adjust `CORS_ALLOWED_ORIGINS`.

### Vite dev server shows blank page

**Cause**: React component render error (check browser DevTools console).

**Fix**:
```bash
npm run build  # test production build
# If build fails, fix the error
npm run dev    # restart dev server
```

## Performance Notes

- **Frontend build size**: ~625KB gzipped (Recharts is the bulk)
- **API response time**: <100ms for /jobs/ endpoint (Postgres index on source/salary/location)
- **Dashboard chart render**: <500ms (5 charts in parallel)
- **Pagination**: 25 results per page (set in Django settings)

## Development Workflow

1. Make a change in `frontend/src/`
2. Vite auto-reloads in browser (HMR)
3. Test against live API at `http://localhost:8000`
4. If adding a new filter/feature:
   - Update `JobsPage.jsx` (UI + state)
   - Ensure Django endpoint supports the parameter
   - Test in browser

## Production Deployment

### Frontend

```bash
npm run build
# dist/ contains production files
# Serve with nginx/apache or upload to static hosting
```

### Backend Stack

Use Docker Compose:

```bash
docker compose -f docker-compose.yml up -d
# Includes: postgres, airflow-webserver, airflow-scheduler
# Start Django separately or add to compose file
```

### Data Refresh

Schedule Airflow DAG (`scrape_all_sources` → `dbt_transform`) to run nightly:

1. Open Airflow UI: http://localhost:8080
2. Enable `scrape_all_sources` DAG
3. Set schedule: `@daily` (1am UTC)
4. dbt_transform runs automatically after scraping completes

## Key Decisions Locked In

| Decision | Rationale |
|----------|-----------|
| Unmanaged Django models | dbt owns warehouse schema; Django is read-only |
| OKLCH color space | Perceptually uniform, accent hue-swap friendly |
| Monospace for data | "IBM Plex Mono" gives data portal credibility |
| No external image CDN | All icons/placeholders are SVG or semantic HTML |
| Recharts over D3 | React-native, automatic responsive, minimal bundle bloat |
| 25-item pagination | API default; balance between UX and server load |

## What's Included

✅ **Database**: PostgreSQL with dbt star schema (dims + facts)
✅ **Scrapers**: 5 live sources (PhilJobNet, Kalibrr, JobStreet, OnlineJobs, Indeed)
✅ **Orchestration**: Airflow DAGs + Great Expectations data quality checks
✅ **API**: Django REST Framework with 12 endpoints (jobs, analytics, master data)
✅ **Frontend**: React + Recharts dashboard with full search/filter/sort
✅ **Responsive**: Desktop-first, tested on 1240px+ down to 400px mobile

## What's Not Included (Optional)

- ❌ Facebook scraper (requires manual login cookie capture)
- ❌ Authentication/authorization (read-only public API)
- ❌ Admin panel (dbt + Airflow UIs are the admin interface)
- ❌ Email notifications (Airflow can be wired to Slack/email if desired)
- ❌ Frontend unit tests (can be added with Vitest)

## Next Steps

1. **Test locally**: Follow "Quick Start" above
2. **Verify data**: Confirm all 5 scrapers populated raw.job_postings
3. **Check API**: Curl a few endpoints to ensure responses are correct
4. **Explore dashboard**: Navigate the frontend, inspect charts
5. **Deploy**: Bundle frontend build + Django + Airflow to production server
6. **Monitor**: Set up alerts on Airflow DAG failures and API error rates

## Support

For issues:
1. Check handoff.md for project state
2. Review docs/plan/ for architecture decisions
3. Check Django logs: `python manage.py runserver --verbosity 3`
4. Check Airflow logs: UI → DAG Runs → Task Logs
5. Check dbt build: `dbt build --select fct_job_postings`
