# Handoff — PH Job Market Tracker

> **Purpose**: Running log of project state. Updated at the end of every Claude session. Read this at the start of every session before touching any code.

---

## Last updated: 2026-05-30

## Current phase: Week 3 — dbt Warehouse COMPLETE → next is Week 4 (Django API)

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

## Next steps (Week 4 — Django API)

1. (Optional) Pin dbt-core to a stable 1.x (currently a beta resolved by pip); silence the generic-test `arguments:` deprecation warnings.
2. Build the Django REST API in `api/` with `managed = False` models reading the `warehouse` schema (see `docs/plan/08-django-api.md`).
3. Consider a `dim_industries` source + an `int_salaries__parsed` currency-normalization step (avg salary currently mixes hourly-USD with monthly-PHP).

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
