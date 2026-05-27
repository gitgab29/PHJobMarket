# Handoff — PH Job Market Tracker

> **Purpose**: Running log of project state. Updated at the end of every Claude session. Read this at the start of every session before touching any code.

---

## Last updated: 2026-05-27

## Current phase: Week 1 — Foundation (COMPLETE ✅)

## What exists right now

| Path | Status |
|------|--------|
| `docs/plan/01–14-*.md` | ✅ Complete planning docs |
| `migrations/001_raw_schema.sql` | ✅ Raw schema (raw.job_postings, raw.reddit_posts, raw.scrape_log) |
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

## What does NOT exist yet

- No dbt project (`dbt_transform/` empty)
- No Airflow DAGs (`airflow/` empty)
- No Django API (`api/` empty)
- No React frontend (`frontend/` empty)
- No `README.md`

## Next steps (Week 2)

1. Implement `KalibrrScraper` (API intercept via Playwright)
2. Implement `JobStreetScraper` (extract `window.__SEEK_REDUX_DATA__`)
3. Implement `RedditScraper` (JSON API, no browser needed)
4. Set up dbt project structure + `profiles.yml`
5. Write staging models for PhilJobNet + Kalibrr
6. Run `dbt run` → verify staging views compile

## Key decisions locked in

- Salary amounts are **PHP monthly** unless marked otherwise
- Skill matching uses **word-boundary regex**, not substring
- Scrapers: **2–6s random delay**, max **50 pages per source**
- Django models all use `managed = False` (dbt owns the warehouse)
- Raw data is never transformed inside scrapers — write JSONB as-is
- **Playwright everywhere** (not requests+BS4) — one tool for all 7 scrapers

## Key decisions locked in

- Salary amounts are **PHP monthly** unless marked otherwise
- Skill matching uses **word-boundary regex**, not substring
- Scrapers: **2–6s random delay**, max **50 pages per source**
- Django models all use `managed = False` (dbt owns the warehouse)
- Raw data is never transformed inside scrapers — write JSONB as-is

## Known risks / watch-outs

- Facebook scraper requires a burner account + manual cookie capture first
- Playwright may need `--no-sandbox` flag inside Docker (see `docs/plan/14-pitfalls.md`)
- dbt `profiles.yml` must NOT be committed — contains DB credentials (already in `.gitignore`)
- Reddit API rate limit: 60 requests/min — build in backoff

## Session log

| Date | What was done |
|------|---------------|
| 2026-05-27 | Project planning complete. Repo initialized and pushed to GitHub (`gitgab29/PHJobMarket`). `.gitignore`, `.env.example`, `handoff.md` created. No code written yet. |
| 2026-05-27 | Week 1 code written: docker-compose.yml (Postgres-only), Makefile, full directory scaffold, BaseScraper, salary_parser (13 tests passing), user_agents utility, PhilJobNetScraper, requirements.txt. End-to-end test pending Docker + Playwright install. |
| 2026-05-27 | Week 1 COMPLETE. Debugged and resolved: SSL cert (no www.), wrong URL (/job-vacancies/), wrong CSS selectors, ASP.NET __doPostBack pagination, Docker port conflicts (settled on 15432), url column mismatch. 500 PhilJobNet records confirmed in raw.job_postings. |
