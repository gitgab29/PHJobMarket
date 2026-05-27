# PH Job Market Tracker

## Session protocol (mandatory)

**At the start of every conversation:** Read `handoff.md` before doing anything else. It tells you the current phase, what exists, and what's next.

**At the end of every conversation:** Append a row to the `## Session log` table in `handoff.md` with today's date and a one-line summary of what changed. Then update the `## What exists right now` and `## Next steps` sections to reflect the new state.

If the user has not asked you to do anything and you haven't read `handoff.md` yet, read it now.

## What this is
ETL pipeline: 7 PH job sources → Playwright/BS4 scrapers → PostgreSQL raw (JSONB) → dbt Core (star schema) → Django REST API → React+Recharts dashboard. Orchestrated by Airflow, containerized with Docker Compose.

## Project structure
- `scrapers/` — Python scraper modules inheriting from `scrapers.base.BaseScraper`
- `dbt_transform/` — dbt project (staging → intermediate → marts)
- `airflow/dags/` — Airflow DAG definitions
- `api/` — Django REST Framework (unmanaged models reading warehouse schema)
- `frontend/` — React + Vite + TailwindCSS + Recharts
- `migrations/` — raw SQL for initial schema setup
- `docs/plan/` — detailed implementation plan split by topic

## Conventions
- Raw data stored as JSONB in `raw` schema; never transform in scrapers
- dbt owns all warehouse tables; Django models use `managed = False`
- Salary amounts default to PHP monthly unless explicitly marked otherwise
- Skill matching uses word-boundary regex, not substring matching
- Scrapers must respect rate limits: random 2-6s delays, max 50 pages per source

## Plan reference
Read only the section you need from `docs/plan/`:
01-architecture.md, 02-directory-structure.md, 03-scrapers.md,
04-database-schema.md, 05-dbt-models.md, 06-airflow-dags.md,
07-salary-parsing.md, 08-django-api.md, 09-react-dashboard.md,
10-docker-compose.md, 11-ci-cd.md, 12-timeline.md, 13-readme-guide.md,
14-pitfalls.md
