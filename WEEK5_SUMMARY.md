# Week 5 Summary — Django REST API

## Status: ✅ COMPLETE

### What Was Built

A production-ready Django REST API with 12 endpoints serving the warehouse schema.

### Files Created (16 total)

**Django Project Structure**
- `api/manage.py` — Django management script
- `api/requirements.txt` — Dependencies (Django 4.2, DRF 3.14, CORS, django-filter)

**Config Module**
- `api/config/settings.py` — Database (warehouse schema), REST framework, CORS, pagination
- `api/config/urls.py` — 12 endpoint routes + router setup
- `api/config/wsgi.py` — WSGI application

**Jobs App**
- `api/jobs/models.py` — 6 unmanaged models (DimCompany, DimLocation, DimSkill, DimDate, FctJobPosting, FctSkillDemand)
- `api/jobs/serializers.py` — 6 serializers (CompanySerializer, LocationSerializer, SkillSerializer, JobPostingListSerializer, JobPostingDetailSerializer, SkillDemandSerializer)
- `api/jobs/views.py` — 4 ReadOnlyModelViewSets (JobPosting, Company, Location, Skill + top action)
- `api/jobs/filters.py` — JobPostingFilter with 10 filter fields
- `api/jobs/apps.py` — App configuration

**Analytics App**
- `api/analytics/views.py` — 6 @api_view endpoints (dashboard_summary, salary_by_location, salary_by_experience, jobs_by_source, remote_vs_onsite, skill_trends)
- `api/analytics/apps.py` — App configuration

**Documentation**
- `docs/instructions/week-5-django-api.md` — Complete setup & architecture guide
- `docs/instructions/api-testing-guide.md` — Curl examples for all 12 endpoints with expected outputs

**Project Updates**
- `Makefile` — Added api-setup, api-run, api-test targets
- `handoff.md` — Updated with Week 5 completion + Week 6 plan

### The 12 Endpoints

| # | Method | Endpoint | Purpose |
|---|--------|----------|---------|
| 1 | GET | `/api/v1/jobs/` | Paginated job list with 10 filter options |
| 2 | GET | `/api/v1/jobs/{id}/` | Job detail with nested company + location |
| 3 | GET | `/api/v1/companies/` | Company list with search |
| 4 | GET | `/api/v1/locations/` | Location list with filtering |
| 5 | GET | `/api/v1/skills/` | Skill dimension list |
| 6 | GET | `/api/v1/skills/top/` | Top N skills by posting count |
| 7 | GET | `/api/v1/analytics/summary/` | Dashboard metrics (total, salary avg, remote %) |
| 8 | GET | `/api/v1/analytics/salary-by-location/` | Avg salary by city/region |
| 9 | GET | `/api/v1/analytics/salary-by-experience/` | Avg salary by experience level |
| 10 | GET | `/api/v1/analytics/jobs-by-source/` | Job count per scraper source |
| 11 | GET | `/api/v1/analytics/remote-vs-onsite/` | Remote/onsite breakdown + % |
| 12 | GET | `/api/v1/analytics/skill-trends/` | Skill demand over time (filterable) |

### Key Technical Decisions

✅ **Unmanaged Models** — All models use `managed=False` since dbt owns the warehouse schema
✅ **ReadOnly ViewSets** — No create/update/delete endpoints (data flows through Airflow)
✅ **Serializer Strategy** — List views denormalized (strings), detail views nested (full objects)
✅ **Performance Optimized** — `select_related()` on FKs, `aggregate()` in analytics, proper indexing via dbt
✅ **Pagination** — 25 items/page by default, configurable per request
✅ **CORS** — Configured for localhost (Vite at 5173, alt dev at 3000)
✅ **Filtering** — 10 filter fields on JobPosting (source, salary range, location, employment type, etc.)
✅ **Search & Ordering** — Full-text search on title/description, ordering by salary/date

### How to Test

```bash
# Install & setup
pip install -r api/requirements.txt
cd api && python manage.py migrate

# Start the API (terminal 1)
make api-run
# Running at http://127.0.0.1:8000

# Test endpoints (terminal 2)
make api-test
# or use curl as documented in api-testing-guide.md
```

### Integration with React (Week 6)

The React frontend will consume:
- `/api/v1/jobs/` for job search + filtering
- `/api/v1/analytics/summary/` for dashboard header numbers
- `/api/v1/analytics/*` for charts (Recharts)
- `/api/v1/skills/top/` for skill demand matrix

All endpoints support standard REST conventions: pagination, filtering, searching, ordering.

### Commit

```
a2479a5 feat: Week 5 Django REST API — 12 endpoints + documentation
```

### Next: Week 6

Build React frontend with Vite + TailwindCSS consuming this API. Expected deliverables:
- Job search UI with real-time filtering
- Dashboard with salary trends + skill demand charts
- Skill matrix (skills vs salary/demand)
- Mobile-responsive design
- End-to-end integration test
