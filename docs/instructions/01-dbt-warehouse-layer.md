# Instruction 01 — Build the dbt Warehouse Layer

> ┌─────────────────────────────────────────────────────────────────────┐
> │ **STAGE:** Week 3 — dbt transform (staging → intermediate → marts)    │
> │ **STATUS:** DONE (built & verified 2026-05-30 — dbt build PASS 49/49)  │
> │ **PREREQUISITES:** 5 scrapers loaded into `raw.job_postings` (✅ 2,071 │
> │   rows live); Docker Postgres healthy on port 15432; `dbt deps` unrun. │
> │ **UNBLOCKS:** Django API (Instruction 02) + React dashboard, which     │
> │   read the `warehouse` schema this instruction creates.                │
> │ **REFERENCE SPEC:** `docs/plan/05-dbt-models.md`, `04-database-schema.md` │
> └─────────────────────────────────────────────────────────────────────┘

---

## Context

We have 5 working scrapers writing raw JSONB into `raw.job_postings` (2,071 rows live in
the Docker Postgres: jobstreet 930, philjobnet 500, kalibrr 489, onlinejobs 120, indeed 32).
Right now that data is **trapped in JSON blobs** — one big `raw_data` column per row, with
slightly different field names and shapes per source. You can't easily ask "average salary
for Python jobs in Makati" against it.

dbt's job is to turn that messy raw pile into a clean, query-friendly **star schema** in the
`warehouse` schema, which the Django API and React dashboard will later read from. This is
the "T" (Transform) in ELT. Per `CLAUDE.md`, dbt owns every warehouse table; the API reads
them with `managed = False`.

This instruction completes the **full warehouse**: the 3 missing staging models, all
intermediate models, all dimension + fact tables, and tests. We verify live with
`dbt run`/`dbt test` against the running database.

---

## The architecture (why these 4 layers)

Data flows downhill through layers, each with exactly one responsibility. dbt figures out
the build order automatically from `{{ ref() }}` / `{{ source() }}` calls — that's the DAG.

```
raw.job_postings (JSONB)          ← scrapers wrote this (source of truth, never edited)
        │   {{ source(...) }}
        ▼
STAGING  (views, schema=staging)  ← 1 model per source. Unpack JSON, rename, cast, trim.
        │   {{ ref(...) }}           One job only: make each source look tidy & consistent.
        ▼
INTERMEDIATE (ephemeral)          ← business logic: stack all sources, dedup, parse salary,
        │                            extract skills. "Ephemeral" = no table is created; dbt
        ▼                            inlines these as CTEs inside the marts that use them.
MARTS   (tables, schema=warehouse)← the star schema the dashboard queries. Materialized as
                                     real tables so reads are fast.
```

- **Views for staging**: a view stores no data, it just re-runs its SQL on read. Cheap, and
  always reflects the latest raw rows. Perfect for thin "clean-up" models.
- **Ephemeral for intermediate**: these are stepping-stones nobody queries directly, so we
  don't clutter the database with them — dbt pastes their SQL into downstream models.
- **Tables for marts**: the dashboard hits these constantly, so we pay the build cost once
  and store the result for fast reads.

### Star schema (why facts + dimensions)
A **fact** table holds the *events/measurements* (here: one job posting, with its salary
numbers). **Dimension** tables hold the *descriptive context* you slice by (company,
location, skill, date). Analytics queries become simple `JOIN + GROUP BY`, and the
dashboard's filters map directly onto dimensions. Facts link to dimensions through small
integer **surrogate keys** (`company_key`, `location_key`, …) instead of repeating long
text — faster joins, and the dimension can change without touching the fact rows.

---

## Step 1 — Finish the 3 missing staging models

Existing: `stg_raw__philjobnet.sql`, `stg_raw__kalibrr.sql`. Add three more, same pattern as
the existing ones (filter by `source`, unpack `raw_data ->> 'key'`, trim, cast dates).
Field names confirmed from the scrapers:

| File (new) | Source fields it unpacks | Notes |
|---|---|---|
| `models/staging/stg_raw__jobstreet.sql` | title, company, location, salary_raw, description, posted_date (`listingDate`, ISO), employment_type, url | standard shape |
| `models/staging/stg_raw__onlinejobs.sql` | title, salary_raw, **salary_currency='USD'**, employment_type, **is_remote=true**, url, posted_date | **no** company / location / description → emit `null`. Carry the explicit `salary_currency` and `is_remote` it stamps. |
| `models/staging/stg_raw__indeed.sql` | title, company, location, salary_raw, employment_type, posted_date, url | **no** description → emit `null` |

Each keeps `raw_id, source, source_id, scraped_at` and the `case when posted_date_raw ~ '^\d{4}-\d{2}-\d{2}' …` date guard already used in the existing models. Comment each one in the same teaching style as `stg_raw__philjobnet.sql`.

Also extend `models/staging/_staging__sources.yml` — it already tests `source`/`source_id`/`raw_data`; no change needed unless we add per-source row-count documentation (optional).

## Step 2 — Intermediate models (`models/intermediate/`)

1. **`int_jobs__unified.sql`** — `UNION ALL` of all 5 staging models. The key requirement:
   every branch must select the **same columns in the same order**. We standardize on this
   superset and null-fill what a source lacks:
   `raw_id, source, source_id, scraped_at, title, company, location_raw, salary_raw,
   salary_currency, url, posted_date, description, employment_type, experience_level,
   is_remote, skills_json`.
   - philjobnet/jobstreet/indeed: `null::text salary_currency, null::text experience_level, null::boolean is_remote, null::jsonb skills_json`
   - onlinejobs: real `salary_currency`, `is_remote`; null company/location/skills
   - kalibrr: real `experience_level`, `skills_json`
   Add `row_number() over (partition by source, source_id order by scraped_at desc) as rn`
   so we can keep the freshest copy of each job if a scraper ran twice.

2. **`int_jobs__deduped.sql`** — `select … where rn = 1`. One clean row per real job.

3. **`int_salaries__parsed.sql`** — turn `salary_raw` text into numbers. Follows
   `docs/plan/05-dbt-models.md` §5.4: detect currency, period (monthly/hourly/yearly),
   handle `k` shorthand and ranges. **Design tweak**: currency = `coalesce(explicit
   salary_currency from staging, regex-derived, 'PHP')` so onlinejobs' USD flag is respected
   (matches the `CLAUDE.md` "PHP monthly unless marked otherwise" rule).

4. **`int_skills__extracted.sql`** — `cross join` deduped jobs against the `skill_aliases`
   seed, matching with **word-boundary regex** `('\m' || pattern || '\M')` against title +
   description, plus a `jsonb_array_elements_text(skills_json)` match for kalibrr. Emits one
   row per (job, skill). Word-boundary matching is a locked decision (so "Java" ≠ "JavaScript").

## Step 3 — Dimension models (`models/marts/`)

| Model | Grain / source | Notes |
|---|---|---|
| `dim_companies.sql` | one row per distinct company name from deduped | `company_key = row_number()`, slug, placeholder first/last_seen |
| `dim_locations.sql` | one row per distinct `location_raw` | regex maps raw text → city, left-join `ph_regions` seed for province/region, `is_metro_manila = region='NCR'`, `is_remote` from text |
| `dim_skills.sql` | **new** — distinct `canonical_name`,`category` from `skill_aliases` seed | `skill_key = row_number()`. Needed by `fct_skill_demand`. |
| `dim_date.sql` | **new** — `generate_series('2024-01-01','2027-12-31')` | `date_key = YYYYMMDD::int`, plus day/month/quarter/year/weekend columns. A calendar table so the dashboard can group by month/quarter without date math. |

## Step 4 — Fact models (`models/marts/`)

1. **`fct_job_postings.sql`** — grain = one deduped job. Joins deduped jobs → parsed salaries
   (on `raw_id`) → `dim_companies` (on lower(company)) → `dim_locations` (on `location_raw`).
   `date_posted_key`/`date_scraped_key` built with `to_char(…,'YYYYMMDD')::int` so they line
   up with `dim_date.date_key`. **Tweak**: `is_remote = coalesce(job.is_remote, location.is_remote)`
   so onlinejobs (no location, explicit remote flag) is correct.

2. **`fct_skill_demand.sql`** — grain = one row per (snapshot_date, skill, source). Aggregates
   `int_skills__extracted` joined to `dim_skills` and parsed salaries: `count(distinct raw_id)
   as posting_count`, `avg(salary_min/max)`. Powers the "most in-demand skills" chart.

## Step 5 — Tests & docs

- `models/marts/_marts__models.yml` (new): `unique`+`not_null` on each `*_key`,
  `accepted_values` on `source`, `dbt_utils.accepted_range` on `salary_min` (0–10M).
- `tests/assert_salary_range_valid.sql` already exists (asserts `salary_max >= salary_min`);
  it activates automatically once `fct_job_postings` exists.

## Existing pieces reused (don't rebuild)
- Seeds: `seeds/skill_aliases.csv` (80+ patterns), `seeds/ph_regions.csv` (36 cities).
- Macros: `macros/salary_bucket.sql`, `macros/generate_schema_name.sql`.
- Config: `dbt_project.yml` already sets staging=view / intermediate=ephemeral / marts=table.

---

## Verification (live, against the running DB)

Env vars must point at the Docker DB (note **port 15432**, not 5432):
`DB_HOST=localhost DB_PORT=15432 DB_USER=phjobmarket DB_PASSWORD=phjobmarket DB_NAME=phjobmarket`.
profiles.yml uses `port: 5432` hardcoded per `docs/plan/05` — confirm/patch it to read
`env_var('DB_PORT', '5432')` or set host port mapping, else dbt won't connect.

From `dbt_transform/` (profiles in-repo, so `--profiles-dir .`):
1. `dbt deps`   — install dbt_utils (handoff says not yet run).
2. `dbt seed`   — load skill_aliases + ph_regions into the DB.
3. `dbt run`    — build everything. Expect ~13 models built (5 staging views, 5 marts tables; intermediate are ephemeral so they don't show as relations).
4. `dbt test`   — all source + mart tests pass.
5. Sanity SQL via `docker exec phjobmarket-postgres-1 psql`:
   - `select count(*) from warehouse.fct_job_postings;` → near the deduped raw total (~2,000).
   - `select skill_name, sum(posting_count) from warehouse.fct_skill_demand fsd join warehouse.dim_skills d using(skill_key) group by 1 order by 2 desc limit 10;`
   - spot-check a few `salary_min/max/currency` rows incl. an onlinejobs USD row.

## Handoff update (end of session, per CLAUDE.md)
Append a Session log row dated 2026-05-30, and move the dbt mart/intermediate items from
"What does NOT exist yet" into "What exists right now".

## Risks / watch-outs
- **profiles.yml port** mismatch (5432 vs 15432) is the most likely first failure.
- `dim_companies`/`dim_locations` join on text (`lower(company)`, `location_raw`); whitespace
  or case drift can drop fact rows to null keys — sanity-check the null-key count after run.
- Salary regex is best-effort; many rows will have null salary, which is fine (tests use
  `where salary_min is not null`).
