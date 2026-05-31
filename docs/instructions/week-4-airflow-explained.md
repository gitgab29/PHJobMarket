# Week 4: Airflow + Great Expectations (Complete Explanation for Junior DE)

> **For:** 4th-year CompEng student learning data engineering. Read this anytime you need context on why Week 4 exists and how everything connects.

---

## The Problem You're Solving

At the end of Week 3, you have a **complete data pipeline** that works flawlessly — but only when *you* run it manually:

```bash
$ make scrape-philjobnet
$ make scrape-kalibrr
$ make scrape-jobstreet
$ make scrape-onlinejobs
$ make scrape-indeed
$ make dbt-run
$ make dbt-test
```

This is fine for development. But imagine:
- It's 2 AM on a Saturday, and someone checks the dashboard
- The data is 3 days old because you forgot to run the scrapers
- Or worse: a scraper broke silently and the data is corrupt, but you have no way to know

**Week 4 solves this.** After Week 4, the entire pipeline runs *automatically every single night* without you touching anything. And if something breaks, you get a notification. This is what makes a data pipeline **production-grade**.

---

## Part 1: Apache Airflow — The "Head Chef" of Your Pipeline

### What Is It?

Apache Airflow is a **workflow orchestrator**. Think of your data pipeline like a restaurant kitchen:

- **Scrapers** = prep cooks (they gather raw ingredients)
- **dbt** = line cooks (they transform ingredients into dishes)
- **Django API** = waiter (serves the finished dishes to customers)
- **Airflow** = head chef (tells everyone when to start, in what order, and what to do if something burns)

Airflow's job is to:
1. **Schedule tasks** — "Run the scrapers every day at 2 AM Manila time"
2. **Enforce order** — "Don't start dbt until all scrapers finish"
3. **Retry failures** — "If a scraper times out, try again in 5 minutes"
4. **Show history** — "Here's a log of every run for the past 6 months"
5. **Alert on errors** — "Slack message if anything fails"

### Key Concept: DAGs (Directed Acyclic Graphs)

A **DAG** is just a fancy word for a **to-do list with order**. Each item is a **Task**, and arrows show *dependencies* (what must happen before what).

**Example:** Your scraping DAG looks like this:

```
[scrape_philjobnet]  ┐
[scrape_kalibrr]     ├──► [log_run_summary] → done
[scrape_jobstreet]   │
[scrape_onlinejobs]  │
[scrape_indeed]      ┘
```

This means:
- All 5 scrapers run **in parallel** (at the same time, to save time)
- Only after ALL of them finish does `log_run_summary` run
- `log_run_summary` writes how many records each scraper found to a table

### Why Not Just Use `cron`?

You could use Linux `cron` to run a script every night. But cron is dumb — it just runs the script; it doesn't know if the script succeeded or failed. Compare:

| Feature | cron | Airflow |
|---------|------|---------|
| Runs on a schedule | ✅ | ✅ |
| Knows if a task succeeded before running the next one | ❌ | ✅ |
| Retries failed tasks automatically | ❌ | ✅ |
| Visual UI showing history of all runs | ❌ | ✅ |
| Can run one task manually without rerunning everything | ❌ | ✅ |
| Sends Slack alerts on failure | ❌ | ✅ (with config) |

With cron, if a scraper fails, you won't know until someone complains the dashboard is stale. With Airflow, failures are obvious — you can see them in the UI and check the logs immediately.

### Your Airflow DAGs

You'll create **two DAGs** (two separate orchestration workflows):

#### DAG 1: `scrape_all_sources` (runs at 2:00 AM Manila time)

```
Task: scrape_philjobnet
  └─ runs: python scrapers/philjobnet.py
  └─ calls: PhilJobNetScraper().run()
  └─ saves: data to raw.job_postings

Task: scrape_kalibrr
  └─ runs: KalibrrScraper().run()

Task: scrape_jobstreet
  └─ runs: JobStreetScraper().run()

Task: scrape_onlinejobs
  └─ runs: OnlineJobsScraper().run()

Task: scrape_indeed
  └─ runs: IndeedScraper().run()

Task: log_run_summary
  └─ only runs AFTER all scrapers finish
  └─ writes a row to raw.scrape_log with counts
```

Each scraper:
- Has a **timeout** (if it hangs for >30 min, kill it)
- Has **retries** (if it fails, try again in 5 minutes, max 3 times)
- Runs **in parallel** with the others (max 3 at once, so you don't hammer the websites)

#### DAG 2: `dbt_transform` (runs at 4:00 AM Manila time, waits for DAG 1)

```
Task: wait_for_scrape_all_sources
  └─ watches DAG 1
  └─ only proceeds when DAG 1 finishes successfully

Task: dbt_deps
  └─ downloads dbt packages (dbt_utils)

Task: dbt_seed
  └─ loads skill_aliases.csv and ph_regions.csv into the database

Task: dbt_run
  └─ runs all 11 dbt models
  └─ rebuilds staging → intermediate → marts

Task: dbt_test
  └─ runs all 36 dbt tests
  └─ checks for nulls, duplicates, valid ranges, etc.

Task: gx_validate_raw
  └─ Great Expectations: validates raw.job_postings
  └─ (more on this below)

Task: gx_validate_warehouse
  └─ Great Expectations: validates the final warehouse tables

Task: dbt_docs_generate
  └─ generates dbt lineage documentation
```

### The Data Flow

Here's what happens every night:

```
2:00 AM:  All scrapers start in parallel
2:30 AM:  All scrapers finish
2:35 AM:  log_run_summary writes to raw.scrape_log
4:00 AM:  dbt_transform DAG starts
4:05 AM:  dbt deps, seed, run, test complete
4:10 AM:  Great Expectations validates everything
4:15 AM:  warehouse is fresh, clean, documented
4:30 AM:  Django API can read from warehouse with confidence
```

---

## Part 2: Great Expectations — "Unit Tests for Your Data"

### What Is It?

Great Expectations (GX) is a Python library that lets you write **data quality checks**. Think of it as "unit tests for data":

```python
# This is an "expectation" (a data quality rule):
"The salary_min column should never be negative"

# When GX validates your data:
✅ PASSED — all 2,071 job postings have salary_min >= 0
❌ FAILED — 3 rows have salary_min = -500 (error!)
```

### Key Expectations You'll Write

For **raw.job_postings** (right after scraping):
- ✅ `source` must be one of: `philjobnet`, `kalibrr`, `jobstreet`, `onlinejobs`, `indeed`
- ✅ `data` (the JSONB blob) must never be NULL
- ✅ `scraped_at` must be within the last 7 days (freshness check)
- ✅ row count must be > 0 (proves the scraper returned data)

For **fct_job_postings** (the final warehouse table):
- ✅ `job_key` must be unique and not NULL
- ✅ `title` must not be NULL
- ✅ `salary_min` must be ≥ 0 when not NULL (no negative salaries)
- ✅ `salary_currency` must be in `['PHP', 'USD']`
- ✅ row count must be > 1000 (sanity check: we expect lots of jobs)

### Why Not Just Use dbt Tests?

You already have 36 dbt tests. Good question. Here's the difference:

| | dbt tests | Great Expectations |
|--|-----------|-------------------|
| When do they run? | After transformation (on clean data) | Before AND after transformation |
| Can they test raw data? | No | Yes |
| Can they generate HTML reports? | No | Yes (nice for non-engineers) |
| Industry standard for data quality? | Somewhat | Yes (GX is the gold standard) |
| Can they test statistical distributions? | No | Yes |

**The key insight:** dbt tests catch bugs *after* your data is cleaned. GX catches bugs *at the source*. 

Example:
- If `Indeed` suddenly returns all salary data as `NULL` (due to a website change), dbt tests might not catch it because `salary_min` is allowed to be NULL.
- GX would catch it with an expectation like "at least 80% of jobs should have a salary" — when this drops to 0%, GX alerts you immediately.

### Data Docs: The Beautiful Report

GX generates an HTML report called "Data Docs" that shows:
- Which expectations passed/failed
- How many rows violated each rule
- Sample rows that broke the rules

You can open this in a browser and share it with non-technical people (product managers, business analysts) — they don't need to read SQL to understand data quality.

---

## Part 3: How Everything Fits Together

### The Complete Weekly Cycle

```
SUNDAY 2026-05-31, 2:00 AM Manila time
├─ Airflow scheduler wakes up
├─ Starts scrape_all_sources DAG
├─ All 5 scrapers run in parallel
│  ├─ PhilJobNetScraper() fetches from phil-jobnet.com
│  ├─ KalibrrScraper() calls Kalibrr API
│  ├─ JobStreetScraper() scrapes jobstreet.com
│  ├─ OnlineJobsScraper() scrapes onlinejobs.ph
│  └─ IndeedScraper() scrapes indeed.com/PH
├─ All scrapers write raw JSONB to raw.job_postings
├─ log_run_summary counts records (e.g., "philjobnet: 500, kalibrr: 120, ...")
├─ raw.scrape_log gets 1 new row with timestamp, record counts, status='success'
│
│ [2:35 AM — scrapers done]
│
├─ dbt_transform DAG waits until scrape_all_sources is COMPLETE
├─ dbt deps → dbt seed → dbt run → dbt test all pass
├─ Great Expectations validates raw.job_postings:
│  ✅ All rows have source in allowed list
│  ✅ All rows have data != NULL
│  ✅ All rows have scraped_at from today
│  ✅ Row count is > 0
├─ Great Expectations validates fct_job_postings:
│  ✅ All job_keys are unique
│  ✅ No negative salaries
│  ✅ All currencies are PHP or USD
│  ✅ Row count > 1000
├─ dbt docs generate updates lineage docs
│
│ [4:15 AM — warehouse is fresh and validated]
│
└─ Django API wakes up, reads from warehouse.fct_job_postings
   ├─ Serves job data to React frontend
   └─ Frontend shows updated dashboards to users
```

### Files You'll Create/Modify

1. **`docker-compose.yml`** — Add Airflow services (webserver, scheduler, init)
2. **`airflow/Dockerfile`** — New Dockerfile extending Airflow's official image
3. **`airflow/requirements.txt`** — Python packages for Airflow container
4. **`airflow/dags/scrape_all_sources.py`** — DAG 1 (the scraping orchestration)
5. **`airflow/dags/dbt_transform.py`** — DAG 2 (the dbt orchestration)
6. **`gx/great_expectations.yml`** — GX config (where to find your database)
7. **`gx/expectations/raw_job_postings.json`** — GX rules for raw data
8. **`gx/expectations/fct_job_postings.json`** — GX rules for warehouse
9. **`gx/checkpoints/nightly_validation.yml`** — GX checkpoint (what Airflow calls)
10. **`Makefile`** — Add `airflow-up`, `airflow-down`, `gx-validate` targets

---

## Part 4: Why This Matters for Your Portfolio

After Week 4, your portfolio project has:

✅ **Production-grade orchestration** — Airflow is what Netflix, Spotify, and every major tech company use
✅ **Data quality validation** — Great Expectations is the industry standard
✅ **Automated monitoring** — You'll know immediately if a scraper breaks
✅ **Transparency** — A clear audit trail of every run in the Airflow UI

When a recruiter asks "How do you ensure data quality in your pipeline?", you can say:
> "I use dbt tests to validate transformations, Great Expectations to validate raw and processed data, and Airflow to orchestrate everything with monitoring and retries."

This shows you understand **enterprise data engineering**, not just "I learned SQL and dbt."

---

## Part 5: What Week 5 Unlocks

After Week 4 is done:
- The warehouse is **auto-refreshed nightly**
- Data quality is **automatically validated**
- Failures are **immediately visible** in the Airflow UI
- You have **6+ months of run history**

Week 5 (Django API) just reads from `warehouse.*` tables — they're guaranteed to be fresh and clean because Airflow + GX + dbt ensure it. This is the luxury of a properly orchestrated pipeline.

---

## Quick Reference: The Three Layers

| Layer | Tools | What it does |
|-------|-------|-------------|
| **Ingestion** | Scrapers (Playwright) | Fetches raw HTML/JSON from 5 job sites, stores as JSONB |
| **Transformation** | dbt (SQL) | Cleans, dedupes, structures data into star schema |
| **Orchestration** | Airflow (Python) | Runs everything on schedule, monitors, retries, alerts |
| **Quality** | Great Expectations (Python) | Validates raw + processed data, generates reports |
| **API** | Django REST (Python) | Reads warehouse, serves JSON to frontend |
| **Dashboard** | React (TypeScript) | Fetches from API, displays charts and tables |

**Week 4 adds layers 3 & 4. Weeks 1–3 built layers 1 & 2. Week 5 adds layer 5. Week 6–7 add layer 6.**

---

## Still Confused?

Read the timeline again: `docs/plan/12-timeline.md` — Week 4 is Airflow + Data Quality. Week 5 is Django API. They were originally confused in `handoff.md`, but the canonical source is the timeline doc.
