-- fct_job_postings.sql  (FACT — the center of the star schema)
--
-- Grain: ONE row per deduped job posting. This is the table the API and
-- dashboard query most. It carries the measurements (salary numbers) and small
-- integer foreign keys pointing at the dimensions (company, location, date).
--
-- THE JOINS, and why each is a LEFT join:
--   • salaries  — only jobs with a parseable salary appear in int_salaries__parsed,
--                 so LEFT keeps salary-less jobs (their salary_* come back NULL).
--   • companies — LEFT so a job with a missing/blank company still survives
--                 (company_key NULL). Joined on the lowercased name.
--   • locations — LEFT so remote/locationless jobs (e.g. OnlineJobs) survive.
-- A LEFT join never drops the job; worst case a key is NULL. We sanity-check
-- the NULL-key counts after the run.
--
-- DATE KEYS: integers shaped YYYYMMDD that line up with dim_date.date_key.
--   date_posted_key uses posted_date, falling back to scrape day when the source
--   didn't give a usable post date.
--
-- is_remote: prefer the job's own explicit flag (OnlineJobs sets it true), else
--   fall back to what we inferred from the location text, else false.

with jobs as (
    select * from {{ ref('int_jobs__deduped') }}
),

salaries as (
    select * from {{ ref('int_salaries__parsed') }}
),

companies as (
    select * from {{ ref('dim_companies') }}
),

locations as (
    select * from {{ ref('dim_locations') }}
)

select
    j.raw_id        as job_key,
    j.source,
    j.source_id,
    j.title,
    j.description,

    c.company_key,
    l.location_key,

    to_char(coalesce(j.posted_date, j.scraped_at::date), 'YYYYMMDD')::integer as date_posted_key,
    to_char(j.scraped_at::date, 'YYYYMMDD')::integer                          as date_scraped_key,

    s.salary_min,
    s.salary_max,
    coalesce(s.salary_currency, 'PHP') as salary_currency,
    s.salary_period,

    j.employment_type,
    j.experience_level,
    coalesce(j.is_remote, l.is_remote, false) as is_remote,
    j.url

from jobs j
left join salaries  s on j.raw_id = s.raw_id
left join companies c on lower(trim(j.company)) = c.company_lower
left join locations l on j.location_raw = l.location_raw
