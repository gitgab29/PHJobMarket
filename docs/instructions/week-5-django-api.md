# Week 5 — Django REST API

## What we built

A production-ready REST API that reads from the warehouse schema (all tables are unmanaged — dbt owns the data). The API serves 12 endpoints:

### Job Endpoints
- `GET /api/v1/jobs/` — paginated job list with filters
- `GET /api/v1/jobs/{id}/` — job detail with company + location expanded

### Master Data
- `GET /api/v1/companies/` — company list with search
- `GET /api/v1/locations/` — location list with filtering
- `GET /api/v1/skills/` — skill dimension

### Analytics Endpoints
- `GET /api/v1/analytics/summary/` — dashboard numbers (total jobs, salary avg, remote %)
- `GET /api/v1/analytics/salary-by-location/` — avg salary by city/region
- `GET /api/v1/analytics/salary-by-experience/` — avg salary by experience level
- `GET /api/v1/analytics/jobs-by-source/` — job count per scraper source
- `GET /api/v1/analytics/remote-vs-onsite/` — remote/onsite breakdown
- `GET /api/v1/analytics/skill-trends/` — skill demand over time (filterable by skill)

### Skill Demand
- `GET /api/v1/skills/top/?limit=20` — top skills by posting count

## Architecture

```
api/
├── manage.py                           # Django management script
├── requirements.txt                    # pip dependencies
├── config/                             # Project settings
│   ├── settings.py                    # Django config (database, CORS, DRF)
│   ├── urls.py                        # Route definitions + router setup
│   └── wsgi.py                        # WSGI application
├── jobs/                              # Main app (models, serializers, views)
│   ├── models.py                      # 5 unmanaged models (DimCompany, DimLocation, etc.)
│   ├── serializers.py                 # 6 serializers (list/detail variants)
│   ├── views.py                       # 4 ReadOnlyModelViewSets
│   ├── filters.py                     # JobPostingFilter with 10 filter fields
│   └── apps.py
└── analytics/                         # Secondary app (analytics views only)
    ├── views.py                       # 6 @api_view functions
    └── apps.py
```

## Setup

### 1. Install dependencies
```bash
pip install -r api/requirements.txt
```

### 2. Generate Django tables (optional — we don't create any)
```bash
cd api && python manage.py migrate
```
This creates Django's internal tables (sessions, permissions, etc.) but NOT our warehouse tables — those are managed by dbt.

### 3. Start the development server
```bash
make api-run
# or:
cd api && python manage.py runserver 0.0.0.0:8000
```
Server runs at http://127.0.0.1:8000

## Testing

### Quick smoke test
```bash
make api-test
```
Hits a few endpoints with curl and validates JSON output.

### Detailed testing with curl
```bash
# List jobs with filters
curl "http://127.0.0.1:8000/api/v1/jobs/?source=philjobnet&is_remote=true"

# Job detail
curl http://127.0.0.1:8000/api/v1/jobs/1/

# Top skills (limit=10)
curl "http://127.0.0.1:8000/api/v1/skills/top/?limit=10"

# Analytics dashboard
curl http://127.0.0.1:8000/api/v1/analytics/summary/

# Skill trends for Python
curl "http://127.0.0.1:8000/api/v1/analytics/skill-trends/?skill=Python"
```

### With Postman or HTTPie
```bash
# HTTPie (simpler syntax)
pip install httpie
http GET http://127.0.0.1:8000/api/v1/jobs/ source==philjobnet

# Postman: import base URL http://127.0.0.1:8000, create requests per endpoint above
```

## Key design choices

- **Unmanaged models**: All 5 models use `managed = False` because dbt owns the warehouse schema. Django never creates or migrates these tables.
- **ReadOnlyModelViewSet**: All viewsets inherit from `ReadOnlyModelViewSet`, not `ModelViewSet`. The API is read-only (no POST/PUT/DELETE).
- **Nested serializers**: Job list excludes nested objects (just company_name string); job detail expands company + location objects for richer context.
- **Pagination**: 25 items per page by default (configurable in settings.py).
- **Filters**: JobPosting supports filtering by source, salary range, employment type, experience, location, company, and remote status.
- **CORS**: Configured for localhost:5173 (Vite frontend) and localhost:3000 (alternative React dev server).

## Common errors & fixes

### `OperationalError: role "phjobmarket" does not exist`
- **Cause**: Postgres not running or DB not created.
- **Fix**: `make up` to start Postgres container.

### `ProgrammingError: relation "dim_companies" does not exist`
- **Cause**: dbt hasn't built the warehouse yet.
- **Fix**: Run `make dbt-run` to create all tables.

### `relation "schema" does not exist`
- **Cause**: dbt tables are in the `warehouse` schema, but Django can't find them.
- **Fix**: Check `DB_HOST`, `DB_PORT`, `DB_NAME` in `.env` match what dbt uses. The `OPTIONS` line in settings.py (`-c search_path=warehouse,public`) should set the schema.

### `CORS error from frontend`
- **Cause**: Frontend URL not in `CORS_ALLOWED_ORIGINS`.
- **Fix**: Add your frontend URL to `config/settings.py` under `CORS_ALLOWED_ORIGINS`.

## Performance notes

- Job list queries use `select_related("company", "location")` to avoid N+1 queries.
- Analytics endpoints use `aggregate()` and `annotate()` for efficient grouping.
- All endpoints are paginated (25 per page) except analytics, which return full datasets.

## Next: Week 6 — React Frontend

The React dashboard will import from this API. It will:
1. Call `/api/v1/jobs/` for the job table + filters
2. Call analytics endpoints for dashboard charts
3. Implement a skills matrix and salary trends chart

The API is now production-ready for the frontend team.
