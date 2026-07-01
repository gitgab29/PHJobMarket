# PH Job Market Tracker — Project Review & Interview Prep

> **Purpose of this document:** A complete, plain-English refresher on everything you built, written so you can (1) re-understand the project end to end, and (2) confidently present it to employers and answer their follow-up questions. Read it top to bottom once; then keep the "Likely interview questions" section open during interviews.

---

## 1. The 30-second pitch

> "I built an end-to-end data pipeline that tracks the Philippine job market. It scrapes job postings from 6 different job sites, stores the raw data in PostgreSQL, transforms it into a clean analytics warehouse with dbt, serves it through a Django REST API, and visualizes salary and skill trends in a React dashboard. The whole thing is orchestrated by Airflow to run nightly and runs in Docker."

If you only remember one sentence in the interview, remember that one. Everything below is the detail behind it.

---

## 2. What problem does it solve?

Job seekers and analysts in the Philippines have no single place to answer questions like:
- What's the average salary for a given role or experience level?
- Which cities pay the most?
- How many jobs are remote vs. on-site?
- Which skills are most in demand?

The data exists, but it's scattered across many job boards in inconsistent formats. This project **collects, standardizes, and analyzes** that data into one queryable warehouse and dashboard.

---

## 3. The big picture — how data flows

```
  6 job sites
      │   (Playwright browser automation — scrapers/)
      ▼
  raw.job_postings  ←─ raw JSONB, untouched         [PostgreSQL · "raw" schema]
      │   (dbt: staging → intermediate → marts)
      ▼
  Star schema warehouse                              [PostgreSQL · "warehouse" schema]
   ├─ dim_companies, dim_locations, dim_skills, dim_date   (the "who/where/what/when")
   └─ fct_job_postings, fct_skill_demand                   (the "facts"/measurements)
      │   (Django REST Framework — api/)
      ▼
  REST API  (12 endpoints, /api/v1/...)
      │   (Axios)
      ▼
  React + Recharts dashboard                         [frontend/]

  Orchestration:  Airflow runs scrapers nightly → triggers dbt → validates with Great Expectations
  Packaging:      Everything containerized with Docker Compose
```

**The mental model that ties it together:** raw data comes in messy and is *never* edited in place; every transformation is a *new* layer built on top of the previous one. You can always trace a number on the dashboard back through the API → a warehouse table → a dbt model → the original raw JSON. That traceability is the whole point of the architecture.

---

## 4. Tech stack & why each choice

| Layer | Tool | Why this one (your talking point) |
|---|---|---|
| Scraping | **Playwright** | Many PH job sites are JavaScript-heavy (React/Redux apps). Plain `requests`+BeautifulSoup can't see content rendered by JS. Playwright drives a real browser, so it sees what a human sees. Used for *all* scrapers for consistency. |
| Raw storage | **PostgreSQL + JSONB** | Store the scraped data exactly as-is, schema-less, in a JSONB column. Lets you re-process data later without re-scraping if you change your parsing logic. |
| Transformation | **dbt Core** | Industry-standard for analytics engineering. Turns SQL transformations into version-controlled, tested, documented models with dependency tracking. Builds the star schema. |
| Warehouse modeling | **Star schema** (Kimball) | Dimensions + facts is the standard for analytics. Fast aggregations, easy for a BI tool or API to query, intuitive to reason about. |
| API | **Django REST Framework** | You already know Django. DRF gives serialization, pagination, filtering, and a browsable API almost for free. Models are read-only (`managed = False`). |
| Frontend | **React + Vite + Tailwind + Recharts** | React for the UI, Vite for fast builds, Tailwind for styling, Recharts for the charts. |
| Orchestration | **Airflow** | Schedules the nightly run, handles retries, tracks task dependencies (don't run dbt until scraping finishes), and gives a UI to monitor pipeline health. |
| Data quality | **Great Expectations** | Automated checks (e.g. "salaries are between 0 and 10M", "no nulls in key columns") that fail loudly if the data goes bad. |
| Packaging | **Docker Compose** | One command spins up Postgres + Airflow. Reproducible environment. |

---

## 5. Layer-by-layer walkthrough

### 5.1 Scrapers (`scrapers/`)

**The pattern:** There's a `BaseScraper` abstract class (`scrapers/base.py`) that every scraper inherits from. This is the textbook **Template Method pattern**.

- `BaseScraper` handles all the shared plumbing: opening the browser, random delays, connecting to Postgres, saving raw data, and logging the run.
- Each specific scraper only implements **one method**, `scrape()`, which returns a list of job dicts.
- You call `.run()`, and the base class does: `scrape()` → `save_raw()` → write a row to `scrape_log` → return the count.

**Why this matters (talking point):** "I didn't want to copy-paste the same browser/database boilerplate into 6 files. The base class enforces a contract — every scraper must define a `SOURCE` name and a `scrape()` method — and centralizes the parts that should behave identically everywhere, like rate limiting and error logging."

**The 6 sources:**
| Source | Technique | Notes |
|---|---|---|
| PhilJobNet | HTML scraping | Government site; had to handle ASP.NET `__doPostBack` pagination and a misconfigured SSL cert. ~500 records. |
| Kalibrr | API interception | Caught the site's internal JSON API via `page.evaluate()` instead of parsing HTML. |
| JobStreet | HTML + Redux extraction | ~900 records. Tricky: the public URL redirected to homepage; real one was `ph.jobstreet.com/jobs`. |
| OnlineJobs | CSS scraping | Remote/USD jobs; flags `is_remote=True`. ~120 records (rate-limited). |
| Indeed | HTML w/ CAPTCHA bail-out | Heavily bot-protected; ~32 records is the realistic ceiling without proxies. |
| Facebook | Stub only | Returns empty list; would need a burner account + manual cookie capture. Intentionally left as a stub. |

**Anti-bot measures you implemented (good talking points):**
- **Random 2–6 second delays** between page requests (a fixed delay is easy to detect).
- **User-Agent rotation** — one realistic browser UA per session (changing it every request is *more* suspicious, not less).
- **Realistic browser context** — Manila timezone, PH locale, desktop viewport, so the browser fingerprint looks like a real Filipino user.
- **Max page limits** (50 pages cap) and respect for the sites.

**Idempotency (important concept):** `save_raw()` uses `INSERT ... ON CONFLICT (source, source_id) DO UPDATE`. This means re-running a scraper never creates duplicates — it updates the existing row. Safe to re-run anytime.

### 5.2 Raw layer (`migrations/001_raw_schema.sql`)

Two tables in a `raw` schema:
- `raw.job_postings` — `(id, source, source_id, scraped_at, raw_data JSONB)`, with a `UNIQUE(source, source_id)` constraint (that's what powers the idempotent upsert). Indexed on `source`, `scraped_at`, and a **GIN index** on the JSONB for fast queries inside the JSON.
- `raw.scrape_log` — one row per scraper run (source, timestamps, record count, status, error message). This is your **pipeline observability** — you can see at a glance if a scraper stopped producing data.

**Key principle:** Raw data is *never* transformed in the scrapers. The scraper's only job is to fetch and store. All cleaning happens later, in dbt. (This is why the salary parser, even though it lives in `scrapers/utils/`, is actually *called by dbt*, not by the scrapers.)

### 5.3 dbt transformation (`dbt_transform/`)

This is the heart of the "data engineering" story. dbt models are organized in three layers (this is the standard dbt pattern):

**Staging (`models/staging/`)** — one view per source. Each `stg_raw__<source>.sql` pulls fields out of the JSONB blob and renames them to a consistent set of columns. Materialized as **views** (cheap, always fresh).

**Intermediate (`models/intermediate/`)** — the business logic, materialized as **ephemeral** models (they become CTEs inlined into downstream models, not physical tables):
- `int_jobs__unified` — stacks all 6 staging models into one table, tagging duplicates with a row number (newest first).
- `int_jobs__deduped` — keeps only `rn = 1`, giving **one clean row per real job**. This is described in the code as the "spine" — everything downstream builds off it.
- `int_salaries__parsed` — runs the salary parsing logic.
- `int_skills__extracted` — word-boundary regex matching of skills against the `skill_aliases` seed.

**Marts (`models/marts/`)** — the final star schema, materialized as **tables**:
- **Dimensions:** `dim_companies` (~740), `dim_locations` (~220), `dim_skills` (~74), `dim_date` (1461 days).
- **Facts:** `fct_job_postings` (~2071 rows — the center of the star) and `fct_skill_demand` (~68).

**How the fact table joins (study `fct_job_postings.sql`):** It takes the deduped jobs and **LEFT joins** the salary data and the dimension tables. The joins are *all* LEFT joins on purpose — a LEFT join never drops a job. Worst case, a job with no salary or a blank company just gets a NULL key. (Talking point: "I used left joins so the fact table is complete — a remote job with no city, or a posting with no parseable salary, still appears. I'd rather have a NULL key than silently lose rows.")

**Seeds (CSV reference data):**
- `skill_aliases.csv` — 80+ patterns mapping variations ("js", "javascript", "node") → canonical skill names + categories.
- `ph_regions.csv` — 36 cities → province/region/NCR flag, so locations get geographically standardized.

**Testing:** dbt has built-in tests declared in `_marts__models.yml` — `unique`, `not_null`, `accepted_values`, `relationships` (foreign key integrity), and `accepted_range`. Plus a custom test `assert_salary_range_valid.sql`. **`dbt build` = 49 checks passing (11 models + 36 tests + 2 seeds).** That number is a great thing to cite.

### 5.4 The salary parser (`scrapers/utils/salary_parser.py`)

A pure function, `parse_salary()`, with **13 unit tests, all passing**. It takes a messy string like `"₱25,000 - ₱35,000/month"` or `"PHP 25k to 35k monthly"` and returns `{min, max, currency, period}`.

It handles: comma separators, the `k` suffix (25k → 25000), decimal thousands (25.5k → 25500), ranges vs. single values, currency detection (₱/$/PHP/USD, defaults to PHP), and period detection (monthly vs. annual, defaults to monthly).

**Two real bugs you found via tests** (great "I write tests that catch real bugs" story):
1. `"₱45,000 + ₱20,000"` was being glued into one giant number (4.5 billion). Fix: truncate at the first `+`.
2. `"Day 1 HMO"` (a benefits perk, not a salary) parsed the "1" as a salary. Fix: added a "money signal" gate so it only parses when there's an actual currency/number cue.

**Talking point:** "It's a pure function with no side effects, which is why it was easy to unit-test thoroughly. Testing it in isolation caught two data-quality bugs before they ever hit the warehouse."

### 5.5 Airflow orchestration (`airflow/dags/`)

Two DAGs (Directed Acyclic Graphs = workflows):

- **`scrape_all_sources`** — runs nightly at 6pm (`0 18 * * *`). Loops over all 6 scrapers, runs up to 3 in parallel (`max_active_tasks=3`), with **2 retries and exponential backoff**, a 30-min timeout per task, and a failure callback that logs errors to `raw.scrape_log`. Each scraper has a `scrape_X >> log_X` flow.
- **`dbt_transform`** — waits for scraping to finish, then runs `dbt deps → seed → run → test → docs`.

**Talking point:** "Airflow gives me three things I'd otherwise hand-roll: scheduling, automatic retries with backoff, and dependency management — dbt should never run on half-scraped data, so the transform DAG depends on the scrape DAG. The UI also lets me see run history and failures."

### 5.6 Data quality — Great Expectations (`gx/`)

Two expectation suites that run nightly:
- `raw_job_postings` — source is in the allowed set, key fields not null, data freshness (within 7 days), row count > 0.
- `fct_job_postings` — unique job keys, salary in 0–10M range, currency is PHP or USD, row count > 1000.

**Talking point:** "dbt tests check structural integrity; Great Expectations checks *business* expectations — like 'we should always have more than 1000 jobs' and 'no salary should be 50 million pesos a month.' If the data silently breaks, the pipeline fails loudly instead of serving garbage to the dashboard."

### 5.7 Django REST API (`api/`)

**The key architectural decision:** Django models use `managed = False` (see `api/jobs/models.py`). This means **dbt owns the warehouse tables, and Django only reads them.** Django never creates or migrates these tables — it just maps Python classes onto tables dbt already built. This cleanly separates the "who builds the data" (dbt) from "who serves the data" (Django) concern.

**Structure:**
- 6 unmanaged models mirroring the warehouse tables, with proper foreign keys (e.g. `FctJobPosting.company → DimCompany`).
- 6 serializers (separate list vs. detail serializers for job postings — lighter payload for the table view).
- 4 `ReadOnlyModelViewSet`s (jobs, companies, locations, skills) — read-only because it's an analytics API; nobody should POST.
- A `JobPostingFilter` with **10 filter fields** (source, salary range, employment type, location, company, remote, etc.) via `django-filter`.
- 6 custom analytics endpoints (`api/analytics/views.py`) that do the aggregation in the database with Django's ORM (`Avg`, `Count`, `annotate`).

**The 12 endpoints:**
```
/api/v1/jobs/                          list + filter + search + sort + paginate
/api/v1/jobs/{id}/                     job detail
/api/v1/companies/                     companies
/api/v1/locations/                     locations
/api/v1/skills/   (+ /skills/top/)     skills, plus a "top skills" action
/api/v1/analytics/summary/             headline KPIs (totals, avg salary)
/api/v1/analytics/salary-by-location/  avg salary per city (≥5 jobs)
/api/v1/analytics/salary-by-experience/avg salary per experience level
/api/v1/analytics/jobs-by-source/      count per source
/api/v1/analytics/remote-vs-onsite/    remote split + percentage
/api/v1/analytics/skill-trends/        skill demand over time
```

**Smart details to mention:** `salary_by_location` only includes cities with **≥5 jobs** (avoids misleading averages from a single outlier). The summary endpoint filters to `PHP monthly` before averaging salaries (don't mix currencies/periods in an average). Pagination is 25 items. CORS is configured for the React dev server.

### 5.8 React dashboard (`frontend/`)

Vite + React 18 + React Router + Tailwind + Recharts. Two pages:
- **Jobs page** (`/`) — search box, 10 filter fields, results table, pagination, and a detail drawer that slides out when you click a job.
- **Dashboard page** (`/dashboard`) — summary KPI cards plus **5 Recharts visualizations**: salary by location, jobs by source, remote vs. on-site, salary by experience level, and top skills.

`src/api/client.js` is a single Axios client wrapping all 12 endpoint groups. Builds to a 624KB-gzipped production bundle.

---

## 6. The decisions you should be ready to defend

These are deliberate engineering choices. Each one is a potential interview question — know the *why*.

| Decision | Why |
|---|---|
| **Store raw JSONB, never transform in the scraper** | Decouples collection from processing. If I improve the salary parser, I re-run dbt — I don't have to re-scrape the internet. |
| **dbt owns tables, Django reads them (`managed=False`)** | Single source of truth for the schema. Avoids two tools fighting over migrations. Clear ownership boundary. |
| **Star schema instead of one big table** | Fast aggregations, no repeated text, intuitive for analytics, plays well with BI tools. |
| **LEFT joins in the fact table** | Completeness over convenience — never silently drop a job because it's missing a salary or city. |
| **Word-boundary regex for skill matching** | Substring matching gives false positives — "java" would match "javascript", "R" would match every word with an r. Word boundaries fix that. |
| **Idempotent upserts (`ON CONFLICT`)** | Re-running a scraper is always safe; no duplicates, no crashes. |
| **Read-only API** | It's an analytics product — there's no reason to allow writes, so don't expose the attack surface. |
| **Playwright for everything** | Consistency. One tool, one mental model, and it handles JS-heavy sites that `requests` can't. |
| **Airflow for orchestration** | Scheduling + retries + dependency ordering + observability, instead of a fragile cron script. |

---

## 7. Numbers to cite (memorize a few)

- **6 job sources** scraped (PhilJobNet, Kalibrr, JobStreet, OnlineJobs, Indeed; Facebook stubbed).
- **~2,071 job postings** in the fact table; **767 with a parsed salary** (663 PHP + 104 USD).
- **~740 companies, ~220 locations, ~74 skills** in the dimensions.
- **dbt build: 49 checks pass** (11 models + 36 tests + 2 seeds), 0 errors.
- **Salary parser: 13/13 unit tests pass.**
- **API: 12 endpoints**, 10 filter fields.
- **Dashboard: 5 charts** + KPI cards.
- **6-week build**, one week per layer (scrapers → dbt → orchestration → API → frontend).

---

## 8. Likely interview questions — with answers

**Q: Walk me through the architecture.**
Use the diagram in §3. "Scrapers pull from 6 sites with Playwright, store raw JSON in Postgres untouched, dbt transforms it into a star schema warehouse, Django serves it over a REST API, React visualizes it. Airflow runs it nightly, Great Expectations validates it, Docker packages it."

**Q: Why store raw JSON instead of cleaning it as you scrape?**
"Separation of concerns and re-processability. The scraper's job is to fetch reliably. If my parsing logic has a bug or I want a new field, I re-run dbt over data I already have — I don't hammer the source sites again. Raw is the immutable record of truth."

**Q: What's a star schema and why use it?**
"It's a modeling pattern with fact tables (measurements — here, job postings and their salaries) surrounded by dimension tables (the descriptive context — company, location, skill, date). The fact table holds small integer foreign keys instead of repeating text. It makes aggregation queries fast and intuitive, which is exactly what an analytics dashboard needs."

**Q: How do you handle duplicate jobs?**
"Two levels. At the raw layer, a `UNIQUE(source, source_id)` constraint plus an `ON CONFLICT DO UPDATE` upsert means re-scraping updates instead of duplicating. At the transform layer, `int_jobs__unified` row-numbers duplicate scrapes of the same job (newest first) and `int_jobs__deduped` keeps only the latest. That deduped model is the spine everything else builds on."

**Q: How does the salary parser work, and how did you test it?**
"It's a pure function that normalizes messy strings into `{min, max, currency, period}`. It handles commas, k-suffixes, decimals, ranges, and currency/period detection with sensible PH defaults. I wrote 13 unit tests, and they caught two real bugs — a `+` sign gluing two numbers together, and a benefits string being misread as a salary."

**Q: Why is the Django model `managed = False`?**
"Because dbt owns those tables, not Django. dbt builds and tests the warehouse schema; Django just maps onto it to serve reads. If I let Django manage them, I'd have two systems trying to own the same schema. This keeps a single source of truth."

**Q: How do you avoid getting blocked while scraping?**
"Random 2–6 second delays, one rotated User-Agent per session, a realistic browser context (Manila timezone, PH locale, desktop viewport), and page caps. I also detect CAPTCHA/bot-walls and bail out gracefully rather than hammering. I respect that some sources, like Indeed, just have a low ceiling without residential proxies — and I'm honest about that."

**Q: What happens if a scraper fails at 3am?**
"Airflow retries it twice with exponential backoff. If it still fails, a failure callback logs the error to `raw.scrape_log`, and the failure is visible in the Airflow UI. The dbt transform DAG only runs on success, so a failed scrape never corrupts the warehouse. And Great Expectations would catch it if row counts dropped below threshold."

**Q: How would you scale or extend this?**
"Adding a 7th source is just a new subclass of `BaseScraper` plus one staging model — the architecture was designed for that. To scale data volume, I'd move from full refresh to dbt incremental models, partition the raw table by scrape date, and possibly move the warehouse to a columnar store like BigQuery or Snowflake. For serving, I'd add caching (Redis) on the analytics endpoints since they're read-heavy and change only nightly."

**Q: What was the hardest part?**
Pick a real one: the JobStreet redirect bug (public URL silently redirected to homepage, giving 0 records until I found `ph.jobstreet.com/jobs`), or the salary parser edge cases, or PhilJobNet's ASP.NET `__doPostBack` pagination. Tell it as a debugging story: symptom → investigation → root cause → fix.

---

## 9. Honest limitations (don't get caught off guard)

Being upfront about these makes you look *more* senior, not less:

- **Data volume is modest** (~2k jobs) and some sources are heavily rate-limited (Indeed ~32, OnlineJobs ~120). Realistic given no paid proxies.
- **Facebook source is a stub** — not implemented; it needs manual cookie capture and raises ethical/ToS questions.
- **`fct_skill_demand` is a single snapshot**, so "skill trends over time" doesn't have much history yet — it needs the pipeline to run for weeks to accumulate.
- **No production deployment yet** — it runs locally via Docker Compose; it hasn't been deployed to a cloud host with a real domain/HTTPS.
- **No authentication on the API** — fine for a public read-only analytics API, but I'd add rate limiting before exposing it publicly.
- **Scraping legality/ToS** — for a portfolio project this is fine, but in production I'd check each site's terms and `robots.txt` and prefer official APIs where they exist.

---

## 10. How to demo it live

If an employer wants to see it run:

1. `make up` — starts Postgres (and Airflow) in Docker.
2. `python api/manage.py runserver` — starts the Django API on `:8000`.
3. `cd frontend && npm run dev` — starts the dashboard on `:5173`.
4. Open the dashboard, show the charts, click into a job, show the filters working.
5. Optionally open Airflow at `localhost:8080` (admin/admin) to show the DAGs and run history.
6. Optionally hit a raw API endpoint (e.g. `localhost:8000/api/v1/analytics/summary/`) to show the data behind the charts.

> Note: per the project's `TESTING_STEPS.md`, the warehouse must already be populated (`dbt build` has run) for the API and dashboard to show data. If demoing cold, run the scrapers + dbt first, or restore a populated database.

---

## 11. One-paragraph version (for a resume bullet or LinkedIn)

> Built an end-to-end data pipeline tracking the Philippine job market: 6 web scrapers (Playwright) feeding a PostgreSQL raw layer, transformed into a tested dbt star-schema warehouse, served via a 12-endpoint Django REST API, and visualized in a React + Recharts dashboard. Orchestrated nightly with Airflow (retries, dependency ordering), validated with Great Expectations, and containerized with Docker Compose. ~2k job postings across the pipeline; 49 passing dbt tests; idempotent, re-runnable scrapers.

---

*This document is a study aid generated from the project's actual code and `handoff.md`. If you change the architecture, update this file too.*
