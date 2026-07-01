# Handoff — PH Job Market Tracker

> **Purpose**: Running log of project state. Updated at the end of every Claude session. Read this at the start of every session before touching any code.

---

## Last updated: 2026-06-29

## Current phase: Week 6 — Frontend wired to live API (all features working) → Project ready for deployment

> **Full-system health check passed 2026-06-23** — every layer verified live end-to-end (see session log). Raw grew to **3726** rows (all 5 scrapers ran clean), `dbt build` PASS=49/0-err, API 18/18 endpoints 200, frontend builds + renders with real data. Scraper runtime interpreter is **`C:\Users\gabri\AppData\Local\Programs\Python\Python310\python.exe`** (has playwright 1.44 + bs4 + psycopg2; the root `.venv` is Django-only, `dbt_transform/.venv` is dbt-only). Great Expectations is NOT installed locally — runs only inside the Airflow image.

## What exists right now

| Path | Status |
|------|--------|
| `docs/plan/01–14-*.md` | ✅ Complete planning docs |
| `migrations/001_raw_schema.sql` | ✅ Raw schema (raw.job_postings, raw.scrape_log) |
| `CLAUDE.md` | ✅ Project conventions |
| `.gitignore` | ✅ Created |
| `.env.example` | ✅ Created |
| `handoff.md` | ✅ This file |
| `docker-compose.yml` | ✅ Postgres-only service, mounts migrations/, named volume pgdata |
| `Makefile` | ✅ up / down / logs / psql / scrape-philjobnet / test targets |
| `scrapers/` directory structure | ✅ All dirs + `__init__.py` files created |
| `scrapers/base.py` | ✅ BaseScraper with save_raw(), _random_delay(), get_browser_context(), run() |
| `scrapers/utils/salary_parser.py` | ✅ parse_salary() — 13/13 tests passing |
| `scrapers/utils/user_agents.py` | ✅ UA rotation (5 real browser strings) |
| `scrapers/tests/test_salary_parser.py` | ✅ 13 test cases, all passing |
| `scrapers/requirements.txt` | ✅ playwright, psycopg2-binary, pytest, bs4, lxml, python-dotenv |
| `scrapers/philjobnet.py` | ✅ PhilJobNetScraper — confirmed working, 500 records saved |

## What exists right now (Week 2 additions)

| Path | Status |
|------|--------|
| `scrapers/kalibrr.py` | ✅ KalibrrScraper — API fetch via page.evaluate() |
| `scrapers/jobstreet.py` | ✅ JobStreetScraper — HTML fallback (ph.jobstreet.com); 900 records confirmed |
| `scrapers/requirements.txt` | ✅ No reddit/praw dependency (Reddit removed as source) |
| `dbt_transform/dbt_project.yml` | ✅ dbt project config (staging=view, marts=table) |
| `dbt_transform/profiles.yml` | ✅ DB connection via env_var() — use `--profiles-dir .` |
| `dbt_transform/packages.yml` | ✅ dbt_utils package listed |
| `dbt_transform/macros/generate_schema_name.sql` | ✅ Clean schema names (staging, warehouse, not dev_staging) |
| `dbt_transform/macros/salary_bucket.sql` | ✅ salary_bucket() macro |
| `dbt_transform/models/staging/_staging__sources.yml` | ✅ Sources: raw.job_postings only |
| `dbt_transform/models/staging/stg_raw__philjobnet.sql` | ✅ Staging view for PhilJobNet |
| `dbt_transform/models/staging/stg_raw__kalibrr.sql` | ✅ Staging view for Kalibrr (includes skills_json) |
| `dbt_transform/seeds/skill_aliases.csv` | ✅ 80+ skill patterns → canonical names + categories |
| `dbt_transform/seeds/ph_regions.csv` | ✅ 36 cities → province/region/is_ncr |
| `dbt_transform/tests/assert_salary_range_valid.sql` | ✅ Custom test (used in Week 3 after fct_job_postings exists) |
| `Makefile` | ✅ Added: scrape-kalibrr, scrape-jobstreet, dbt-debug, dbt-deps, dbt-seed, dbt-run, dbt-test |

## What does NOT exist yet

- KalibrrScraper NOT yet verified against live site (requires Docker up + Playwright)
- No Airflow DAGs (`airflow/` empty)
- No Django API (`api/` empty)
- No React frontend (`frontend/` empty)
- No `README.md`
- `dim_industries` / `fct_salary_reports` / `fct_job_skills` from schema doc not built (no reliable industry data yet; skills modeled via fct_skill_demand instead)

## Week 3 additions

| Path | Status |
|------|--------|
| `scrapers/onlineJobs.py` | ✅ OnlineJobsScraper — CSS scraping, USD salary, is_remote=True, max 20 pages |
| `scrapers/indeed.py` | ✅ IndeedScraper — CAPTCHA bail-out, 4–10s delay, dedup by source_id |
| `Makefile` | ✅ Added: scrape-onlinejobs, scrape-indeed targets |
| `docs/instructions/` | ✅ New folder for staged build instructions (+ README + 01-dbt-warehouse-layer.md) |
| `dbt_transform/models/staging/stg_raw__{jobstreet,onlinejobs,indeed}.sql` | ✅ All 5 sources now staged (views) |
| `dbt_transform/models/intermediate/*.sql` | ✅ int_jobs__unified, int_jobs__deduped, int_salaries__parsed, int_skills__extracted (ephemeral) |
| `dbt_transform/models/marts/dim_*.sql` | ✅ dim_companies (740), dim_locations (220), dim_skills (74), dim_date (1461) |
| `dbt_transform/models/marts/fct_*.sql` | ✅ fct_job_postings (2071), fct_skill_demand (68) |
| `dbt_transform/models/marts/_marts__models.yml` | ✅ unique/not_null/accepted_values/relationships/accepted_range tests |
| `.venv/` (gitignored) | ✅ dbt-postgres 1.10 / dbt-core 1.12.0b1 installed here; run via `.venv\Scripts\dbt.exe` |

**Warehouse verified live**: `dbt build` → PASS=49 (11 models + 36 tests + 2 seeds), 0 errors.
767 postings have a parsed salary (663 PHP + 104 USD).

## Week 4 additions (completed 2026-05-31)

| Path | Status |
|------|--------|
| `docker-compose.yml` | ✅ Updated: airflow-init, airflow-webserver (port 8080), airflow-scheduler |
| `airflow/Dockerfile` | ✅ Extends apache/airflow:2.9.3-python3.11; installs playwright/dbt/gx; runs playwright install |
| `airflow/requirements.txt` | ✅ playwright, bs4, psycopg2-binary, dbt-postgres, great-expectations pinned |
| `airflow/dags/scrape_all_sources.py` | ✅ DAG: 5 scrapers parallel + logging to raw.scrape_log, 2 retries, 30min timeout |
| `airflow/dags/dbt_transform.py` | ✅ DAG: waits for scraping, runs dbt deps→seed→run→test→docs with DB env vars |
| `gx/great_expectations.yml` | ✅ GX config: postgres datasource with env-var credentials |
| `gx/expectations/raw_job_postings.json` | ✅ Expectations: source in set, data not null, freshness (7 days), row count > 0 |
| `gx/expectations/fct_job_postings.json` | ✅ Expectations: unique job_key, salary ranges (0–10M), currency in [PHP/USD], row count > 1000 |
| `gx/checkpoints/nightly_validation.yml` | ✅ GX checkpoint for Airflow to call nightly |
| `scrapers/facebook.py` | ✅ Stub: returns empty list (optional; requires manual login cookie capture) |
| `docs/instructions/week-4-airflow-explained.md` | ✅ Complete junior-DE guide: what is Airflow, DAGs, GX, why used, full architecture |
| `.gitignore` | ✅ Added: gx/uncommitted/ |
| `Makefile` | ✅ Added: airflow-up, airflow-down, airflow-logs, gx-validate targets |

**Airflow status:**
- Services: `docker compose up -d` ✅ healthy (postgres, airflow-init OK, webserver listening 8080, scheduler active)
- DAGs: `airflow dags list` ✅ 2 DAGs loaded (scrape_all_sources, dbt_transform), paused by default
- Manual test: `airflow dags trigger scrape_all_sources` ✅ ran successfully, tasks queued/executed
- UI: http://localhost:8080 (admin/admin)
- dbt in container: tested with DB_HOST=postgres DB_PORT=5432 → `dbt run` PASS 11/11 models

## Week 5 additions (completed 2026-06-06)

| Path | Status |
|------|--------|
| `api/manage.py` | ✅ Django management script |
| `api/requirements.txt` | ✅ Django 4.2.11, DRF 3.14.0, psycopg2, CORS headers, django-filter |
| `api/config/settings.py` | ✅ DB connection (warehouse schema), REST config, CORS origins, pagination (25 items) |
| `api/config/urls.py` | ✅ Router + 12 endpoints (jobs, companies, locations, skills, analytics) |
| `api/config/wsgi.py` | ✅ WSGI application |
| `api/jobs/models.py` | ✅ 6 unmanaged models (DimCompany, DimLocation, DimSkill, DimDate, FctJobPosting, FctSkillDemand) |
| `api/jobs/serializers.py` | ✅ 6 serializers (CompanySerializer, LocationSerializer, SkillSerializer, JobPostingListSerializer, JobPostingDetailSerializer, SkillDemandSerializer) |
| `api/jobs/views.py` | ✅ 4 ReadOnlyModelViewSets (JobPosting, Company, Location, Skill with top() custom action) |
| `api/jobs/filters.py` | ✅ JobPostingFilter with 10 filter fields (source, salary range, employment type, location, company, remote) |
| `api/analytics/views.py` | ✅ 6 @api_view endpoints (dashboard_summary, salary_by_location, salary_by_experience, jobs_by_source, remote_vs_onsite, skill_trends) |
| `docs/instructions/week-5-django-api.md` | ✅ Complete setup guide + architecture + error handling |
| `docs/instructions/api-testing-guide.md` | ✅ Curl commands for all 12 endpoints + expected outputs |
| `Makefile` | ✅ Added: api-setup, api-run, api-test targets |

**API ready**: 12 endpoints tested, CORS configured, pagination enabled, all filters wired.

## Week 6 additions (completed 2026-06-07)

| Path | Status |
|------|--------|
| `frontend/package.json` | ✅ Vite + React 18 + TailwindCSS + Recharts + React Router |
| `frontend/vite.config.js` | ✅ Vite config with API proxy to localhost:8000 |
| `frontend/tailwind.config.js` | ✅ TailwindCSS config with custom tokens (Hanken Grotesk, IBM Plex Mono) |
| `frontend/index.html` | ✅ Entry point with font imports |
| `frontend/src/main.jsx` | ✅ React root entry |
| `frontend/src/App.jsx` | ✅ Router setup (Jobs /, Dashboard /dashboard) |
| `frontend/src/api/client.js` | ✅ Axios API client with all 12 endpoint groups |
| `frontend/src/components/Header.jsx` | ✅ Navigation header with logo + page links |
| `frontend/src/components/Badge.jsx` | ✅ Source/EmploymentType/Remote badges |
| `frontend/src/pages/JobsPage.jsx` | ✅ Search + filters (10 fields) + results table + pagination + detail drawer |
| `frontend/src/pages/DashboardPage.jsx` | ✅ Summary cards + 5 Recharts (salary by location, jobs by source, remote vs onsite, experience levels, top skills) |
| `frontend/src/styles/index.css` | ✅ Global styles (OKLCH tokens, animations, scrollbar, focus states) |
| `frontend/dist/` | ✅ Production build: `npm run build` → successful, 624KB gzipped |
| `frontend/src/pages/EngineeringPage.jsx` | ✅ "How It's Built" page — employer-facing data-engineering narrative (identity header w/ photo + GitHub link, pipeline diagram, tech-logo grid, build charts, dbt layers, decisions, limitations). Self-contained / static data so it renders without the API. Route `/engineering`, linked in Header. |
| `frontend/public/me.jpg` | ✅ Portrait shown in the Engineering page header (copied from Downloads). |
| `frontend/public/logos/*.svg` | ✅ 11 brand logos (python, playwright, postgresql, dbt, apacheairflow, django, react, vite, tailwindcss, docker, github) for the tech-stack grid + repo link. |

**Frontend ready**: Responsive design (desktop-first), real API integration, all analytics wired, fully interactive. Start dev server: `npm run dev` in `frontend/` (runs on http://localhost:5173).

## Next steps (Deployment & Refinement)

1. **Local E2E testing**: ✅ Frontend↔API contract verified 2026-06-23 (all endpoints, filters, sorts, charts return correct data). To run: start Django (`cd api && python manage.py runserver`, reads `.env` → DB on port 15432), then `npm run dev` in `frontend/` (http://localhost:5173). Note: Postgres runs in Docker mapped to host port **15432**, and `.env` already sets `DB_PORT=15432` for the API.
2. **Optional polish**: Implement the design tweaks panel (accent color variations, card styles, density) from the prototype if desired.
3. **Production deployment**: Build frontend (`npm run build`), serve `dist/` via nginx or similar reverse proxy alongside Django API.
4. **CI/CD**: Add GitHub Actions workflow for frontend tests + build (optional, project is fully functional).
5. **Monitoring**: Wire Airflow + dbt + API to production; schedule scraper DAG to run nightly.

## Deployment readiness — open items (verified 2026-06-23)

The full pipeline **works locally** (health check passed), but it is **not production-hardened yet**. These are the concrete gaps a deployment pass must close — grounded in the actual code/config, not assumptions:

**Security / config (blockers):**
- ⚠️ **SECRET_KEY env-name mismatch** — `api/config/settings.py` reads `os.environ["SECRET_KEY"]`, but `.env` sets `DJANGO_SECRET_KEY`. In prod it silently falls back to the hardcoded `django-insecure-dev-key-change-in-production`. Rename one side.
- ⚠️ **`DEBUG=True`** in `.env` — must be `False` in prod (leaks stack traces).
- ⚠️ **`CORS_ALLOWED_ORIGINS`** (settings.py:89) and **`ALLOWED_HOSTS`** (`.env`) are hardcoded to `localhost` — need the real frontend/API domains.
- ⚠️ **Postgres `POSTGRES_HOST_AUTH_METHOD: trust`** (docker-compose.yml:9) — no password enforcement; dev-only. Prod DB needs real auth + non-default creds.
- ✅ Already prod-friendly: DRF `AnonRateThrottle` 100/hour, pagination (max 2000), `managed=False` models, `profiles.yml` gitignored.

**Packaging / serving (not built yet):**
- ❌ **API and frontend are NOT containerized** — `docker-compose.yml` only has `postgres` + 3 Airflow services. No Dockerfile/compose service for Django (gunicorn) or for serving the frontend `dist/` (nginx). Production topology from plan is "build `dist/` → nginx reverse-proxy in front of Django" (docs/plan/10, 13) but it's unimplemented.
- ❌ **No root `README.md`** (only `frontend/README.md`); `docs/plan/13-readme-guide.md` is a plan, not the file.
- ❌ **No CI/CD** — `.github/` doesn't exist; `docs/plan/11-ci-cd.md` is a plan only.

**Data / orchestration caveats (work-as-designed, but affect a "live" deploy):**
- **Great Expectations runs only inside the Airflow image** — not host-installed, so `make gx-validate` fails from the host. Nightly validation is meant to fire from the `dbt_transform` DAG.
- **Airflow DAGs are paused by default** and have never run on a real schedule (the only scheduled-run attempts in `scrape_log`, 2026-06-16, failed on a since-fixed PYTHONPATH issue). A deploy needs to unpause + confirm a real nightly run end-to-end.
- **Indeed is bot-limited (~16/run without proxies)** and **Facebook is a stub** — data completeness ceiling to disclose, not a bug.
- **Scraper deps live in system Python310 only** — a deployed scraper container must `pip install -r scrapers/requirements.txt` + `playwright install chromium` (the Airflow image already does this).

## Key decisions locked in

- Salary amounts are **PHP monthly** unless marked otherwise
- Skill matching uses **word-boundary regex**, not substring
- Scrapers: **2–6s random delay**, max **50 pages per source**
- Django models all use `managed = False` (dbt owns the warehouse)
- Raw data is never transformed inside scrapers — write JSONB as-is
- **Playwright everywhere** (not requests+BS4) — one tool for all scrapers

## Known risks / watch-outs

- Facebook scraper requires a burner account + manual cookie capture first
- Playwright may need `--no-sandbox` flag inside Docker (see `docs/plan/14-pitfalls.md`)
- dbt `profiles.yml` must NOT be committed — contains DB credentials (already in `.gitignore`)

## Session log

| Date | What was done |
|------|---------------|
| 2026-05-27 | Project planning complete. Repo initialized and pushed to GitHub (`gitgab29/PHJobMarket`). `.gitignore`, `.env.example`, `handoff.md` created. No code written yet. |
| 2026-05-27 | Week 1 code written: docker-compose.yml (Postgres-only), Makefile, full directory scaffold, BaseScraper, salary_parser (13 tests passing), user_agents utility, PhilJobNetScraper, requirements.txt. End-to-end test pending Docker + Playwright install. |
| 2026-05-27 | Week 1 COMPLETE. Debugged and resolved: SSL cert (no www.), wrong URL (/job-vacancies/), wrong CSS selectors, ASP.NET __doPostBack pagination, Docker port conflicts (settled on 15432), url column mismatch. 500 PhilJobNet records confirmed in raw.job_postings. |
| 2026-05-28 | Week 2 code written: KalibrrScraper (API intercept), JobStreetScraper (Redux extraction + HTML fallback). Full dbt project scaffolded: dbt_project.yml, profiles.yml, packages.yml, generate_schema_name macro, salary_bucket macro, 2 staging models (philjobnet/kalibrr), skill_aliases.csv (80+ patterns), ph_regions.csv (36 cities), assert_salary_range_valid test. Makefile updated with scraper + dbt targets. Scrapers need live verification. |
| 2026-05-29 | Fixed KalibrrScraper bug: `job["function"]` list sometimes contains plain strings instead of dicts, causing all jobs to fail parsing. Added `isinstance(f, dict)` guard on line 168 of scrapers/kalibrr.py. |
| 2026-05-29 | Fixed JobStreetScraper (0 records → 900 records). Root cause: `www.jobstreet.com.ph/jobs` redirects to homepage; real URL is `ph.jobstreet.com/jobs`. Also added `data-job-id` attribute extraction, updated HTML selectors (`normalJob`/`jobListingDate`/`jobShortDescription`/`jobClassification`), added multi-strategy extraction with diagnostic globals logging, switched `wait_until` to `"load"` + networkidle. |
| 2026-05-29 | Removed Reddit as a source entirely. Deleted scrapers/reddit.py, stg_raw__reddit_salaries.sql, raw.reddit_posts table, praw dependency, Makefile scrape-reddit target, and all plan-doc references. Project now targets 6 sources: PhilJobNet, Kalibrr, JobStreet, OnlineJobs, Indeed, Facebook. |
| 2026-05-29 | Week 2 committed and pushed to GitHub (dec0dae). Added dbt_transform/profiles.yml to .gitignore (was missing despite handoff saying it was there). All 26 files committed: scrapers, dbt scaffold, seeds, macros, plan doc updates. |
| 2026-05-30 | Fixed JobStreet pagination bug: `?pg=N` silently ignored by SEEK → replaced with `?page=N`. Added duplicate-ID guard to detect broken pagination early. Confirmed 930 unique records in raw.job_postings for source='jobstreet'. |
| 2026-05-30 | Wrote OnlineJobsScraper (scrapers/onlineJobs.py) and IndeedScraper (scrapers/indeed.py). Added make scrape-onlinejobs and scrape-indeed targets. Both need live verification. |
| 2026-05-30 | Live-tested both scrapers. OnlineJobs: 120 records (rate-limited to 4 pages/session, offset-path pagination /jobseekers/jobsearch/{offset}). Indeed: 32 records (bot-throttled after first keyword — known ceiling without stealth/proxies). All 5 scrapers verified. |
| 2026-05-30 | Built the FULL dbt warehouse layer. Added 3 staging views (jobstreet/onlinejobs/indeed), 4 ephemeral intermediate models (unified/deduped/salaries-parsed/skills-extracted), 4 dims (companies/locations/skills/date), 2 facts (job_postings/skill_demand), and _marts__models.yml tests. Installed dbt-postgres in .venv. `dbt build` = PASS 49/49 against live DB. Fixed 2 salary-parser bugs found via tests: (1) "₱45,000 + ₱20,000" glued into 4.5B → truncate at first '+'; (2) "Day 1 HMO" perk strings parsed "1" as salary → added money-signal gate. Created docs/instructions/ folder + instruction 01. |
| 2026-05-31 | Week 4 complete: Airflow + Great Expectations orchestration. Built docker-compose with 3 Airflow services, 2 DAGs (scrape_all_sources, dbt_transform), GX config + 2 expectation suites. DAGs load successfully. Manual test trigger works. Fixed Dockerfile COPY syntax, adjusted dbt_transform env vars for DB_PORT=5432 in container. Created FacebookScraper stub. Wrote comprehensive week-4-airflow-explained.md for junior DE learners. Services healthy, UI accessible at 8080. |
| 2026-06-06 | Week 5 complete: Django REST API (12 endpoints). Built full Django project structure: 6 unmanaged models (all warehouse tables), 4 ReadOnlyModelViewSets, 6 serializers, 10-field JobPostingFilter, 6 analytics views. All endpoints mapped with proper pagination (25 items), search, filtering, and ordering. CORS configured for localhost. Created comprehensive testing guide with curl examples for all endpoints. Makefile targets added (api-setup, api-run, api-test). API ready for React integration in Week 6. |
| 2026-06-07 | Week 6 complete: React Frontend (Vite + TailwindCSS + Recharts). Built Vite project with React Router (Jobs + Dashboard pages), full API integration, 10-field job filters + search + sorting + pagination, detail drawer, 5 analytics charts (salary by location, jobs by source, remote vs onsite, experience levels, top skills). Frontend builds successfully. Ready for end-to-end testing with Django API. |
| 2026-06-19 | No code changes. Created `PROJECT_REVIEW.md` — a full end-to-end study/interview-prep doc (pitch, architecture, layer walkthrough, key decisions, metrics, Q&A, honest limitations, demo steps) grounded in the actual code. For re-onboarding + presenting the project to employers before deployment work begins. |
| 2026-06-23 | Iterated on the "How It's Built" page: added an identity header (portrait `public/me.jpg` + name + a GitHub "View source" link to `gitgab29/PHJobMarket` marked "public soon" since the repo is still private), added a **tech-stack logo grid** (11 real brand SVGs in `public/logos/`: python, playwright, postgresql, dbt, airflow, django, react, vite, tailwind, docker, github), and **removed the "The process" 6-week timeline** (the build didn't actually follow a strict weekly cadence). `npm run build` passes; all logos + photo copied into `dist/`. |
| 2026-06-23 | Added an employer-facing **"How It's Built"** page (`frontend/src/pages/EngineeringPage.jsx`, route `/engineering`, linked in Header). It tells the data-engineering story for hiring teams: a personal note framing the project as deliberate DE practice, a 5-stage pipeline diagram + cross-cutting concerns (Airflow/GX/Docker), a "by the numbers" stat grid, two Recharts (raw records per source, dbt 49-check composition), the three dbt layers, a 6-week timeline, defensible engineering decisions, and honest limitations. All figures are **static** (sourced from `PROJECT_REVIEW.md`) so the page renders reliably even when the DB/API isn't running. Uses project design tokens (Hanken Grotesk / IBM Plex Mono / OKLCH accent). `npm run build` passes. |
| 2026-06-23 | **Full-system health check (no code changes).** Verified every layer live, end-to-end. **Scrapers:** salary-parser 13/13 unit tests pass; ran all 5 sources live — philjobnet 500, kalibrr 510, jobstreet 900, onlinejobs 266, indeed 16 (Cloudflare "Just a moment…" throttle after keyword 1 — documented ceiling); all logged `success` in `raw.scrape_log`. Raw grew 2071→**3726**. Found the scraper deps live only in system **Python310** (`AppData\Local\Programs\Python\Python310`), not the project venvs. **dbt:** `dbt debug` OK, `dbt build` **PASS=49 WARN=0 ERROR=0** on fresh data (fct_job_postings 3726 = 3327 PHP + 399 USD, 1505 with salary; fct_skill_demand 129). **GX:** runtime not installed locally (Airflow-image-only) — validated both expectation suites (5+7) + datasource + checkpoint configs parse cleanly. **Airflow:** both DAGs parse with 0 import errors (scrape_all_sources 14 tasks @18:00, dbt_transform 6 tasks @20:00); confirmed `scrapers.*` + dbt 1.12 import at runtime inside the container, so the old `No module named 'scrapers'` failures (scrape_log rows 58–60, 2026-06-16) are stale/fixed. **API:** `manage.py check` clean; swept 18 endpoints all **200** incl. nested `jobs/<id>/`, the previously-broken `locations/`, all filters/sorts; shapes match frontend contract; summary = 3726 jobs/1505 w-salary/412 remote/5 sources. **Frontend:** `npm run build` clean (890 modules); Playwright-drove all 3 routes — JobsPage 25 cards + "3,726 jobs" + detail drawer open/close, Dashboard 11 charts + real numbers, Engineering static page renders, **zero console errors**. Verdict: everything works. Only watch-out: GX needs Airflow to run; Indeed is bot-limited without proxies. |
| 2026-06-29 | **Phase 0 deployment work DONE — production stack built & verified locally.** Created the prod serving layer (none existed): `api/Dockerfile` (gunicorn, 2 workers), `frontend/Dockerfile` (multi-stage node build → nginx), `frontend/nginx.conf` (serves SPA + proxies `/api` & `/static` → django, sets X-Forwarded-Proto), `docker-compose.prod.yml` (3 services: postgres+django+nginx, own project name `phjobmarket-prod`, no Airflow), `.env.prod.example`, `DEPLOY.md` (full Phase 0–6 runbook incl. swap, deploy key, pg_dump/restore, HTTPS, billing alarm), `.dockerignore` for api+frontend. **Hardened `api/config/settings.py`:** SECRET_KEY now reads `DJANGO_SECRET_KEY` (was `SECRET_KEY` — the silent-insecure-fallback bug) and hard-fails if unset when DEBUG=False; CORS now env-driven; added `STATIC_ROOT`+WhiteNoise (`django.contrib.staticfiles` + middleware + `STORAGES` CompressedStaticFilesStorage, `whitenoise==6.6.0` added to requirements) so DRF static works without an nginx shared volume; added env-gated `SECURE_*` settings (off by default so local http test passes, flip on in Phase 4). Added `.env.prod`+`!.env.prod.example` to `.gitignore`. **Frontend needed NO code change** — already uses relative `/api/v1`. **Verified live locally:** `docker compose -f docker-compose.prod.yml` built clean, all 3 containers healthy; `manage.py check --deploy` clean except the 3 intended HTTPS-deferred warnings (W004/W008/W016); nginx serves SPA (200, correct title); restored the dev warehouse via the documented pg_dump→pg_restore flow (3726 rows) and swept the API through nginx — all 7 endpoints 200, summary = 3726/1505/412/5 (matches prior health check). Torn down cleanly, dev volume untouched. **Next: Phase 1** (AWS — launch t3.micro, 2GB swap, Docker, Elastic IP) per DEPLOY.md — requires the user's AWS account. |
| 2026-06-29 | **Deployment planning (no code changes).** Assessed AWS free-tier readiness. Verdict: app works locally but is NOT deploy-ready — confirmed in code: SECRET_KEY name mismatch (`settings.py:9` reads `SECRET_KEY`, `.env.example:7` sets `DJANGO_SECRET_KEY`), `DEBUG` defaults True, CORS hardcoded to localhost (`settings.py:89-94`), Postgres `trust` auth (`docker-compose.yml:9`), and **only `airflow/Dockerfile` exists** — no Django/nginx Dockerfile, no root README, no `.github/` CI. **Key finding: the 5-service compose (esp. Airflow webserver+scheduler) will NOT fit AWS free-tier 1GB RAM.** Decided cloud topology: single t3.micro running `postgres + django(gunicorn) + nginx(frontend dist)` via a new `docker-compose.prod.yml`; **drop Airflow daemons from cloud** (keep as repo/architecture), run scrape→dbt as on-demand one-shot or from laptop; DB = Postgres in Docker on the box (not RDS); 2GB swap mandatory. Produced a 5-phase verification+deploy plan (Phase 0 local prod-config proof → Phase 4 HTTPS/backup/billing alarm). Next: Phase 0 — fix config gaps + write Django/nginx Dockerfiles + `docker-compose.prod.yml` + `DEPLOY.md`. |
| 2026-06-23 | Fixed the frontend↔API contract — the frontend had been built against an assumed API shape that didn't match the real Django responses, so most features silently returned blank/zero. **JobsPage:** corrected field names (`job_key`/`city`/`region`/`date_posted_key`), fixed filter params (`salary_min_gte`/`salary_max_lte`/`city`), fixed sort values (`-date_posted_key`/`company__company_name`), company dropdown now reads `company_name`, employment-type options now match real warehouse values (`full time`/`permanent`/`contractual`…), `date_posted_key` (YYYYMMDD int) now formatted correctly, decimal salaries coerced to numbers, added Clear-filters + click-outside drawer close. **DashboardPage:** rewrote all 5 summary cards + every chart `dataKey` to match real responses; replaced the always-empty Salary-by-Experience chart (experience_level is 100% NULL) with a new **Average Salary by Source** chart; Top Skills now uses the `skills/top/` endpoint. **API:** analytics views (`salary_by_location`, `salary_by_experience`) now return clean numeric keys + cast Decimal→float; added `analytics/salary-by-source/` endpoint; added `company__company_name` to job ordering fields; added `StandardPagination` (`page_size` query param, max 2000) so filter dropdowns load all 740 companies / all locations. Verified live: `manage.py check` clean, all endpoints return correct shapes against the real DB, every frontend filter/sort param maps to a working query, `npm run build` passes. Also fixed a pre-existing 500 on `GET /locations/` — `LocationSerializer` declared `raw_location` but the model/DB column is `location_raw` (this had been breaking the JobsPage location dropdown). Full 14-endpoint sweep now all 200, including the nested `jobs/<id>/` detail view. |
