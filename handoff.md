# Handoff — PH Job Market Tracker

> **Purpose**: Running log of project state. Updated at the end of every Claude session. Read this at the start of every session before touching any code.

---

## Last updated: 2026-05-27

## Current phase: Week 1 — Foundation (not yet started)

## What exists right now

| Path | Status |
|------|--------|
| `docs/plan/01–14-*.md` | ✅ Complete planning docs |
| `migrations/001_raw_schema.sql` | ✅ Raw schema (raw.job_postings, raw.reddit_posts, raw.scrape_log) |
| `CLAUDE.md` | ✅ Project conventions |
| `.gitignore` | ✅ Created |
| `.env.example` | ✅ Created |
| `handoff.md` | ✅ This file |

## What does NOT exist yet (everything else)

- No scrapers (`scrapers/` directory empty)
- No dbt project (`dbt_transform/` empty)
- No Airflow DAGs (`airflow/` empty)
- No Django API (`api/` empty)
- No React frontend (`frontend/` empty)
- No `docker-compose.yml`
- No `Makefile`
- No `README.md`

## Next steps (Week 1 tasks in priority order)

1. Create directory scaffolding matching `docs/plan/02-directory-structure.md`
2. Write `docker-compose.yml` (Postgres only at first — see `docs/plan/10-docker-compose.md`)
3. Implement `scrapers/base.py` — `BaseScraper` abstract class
4. Implement `scrapers/utils/salary_parser.py` + tests
5. Implement `scrapers/philjobnet.py` — first real scraper
6. Test: run PhilJobNet scraper → confirm JSONB rows in `raw.job_postings`

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
