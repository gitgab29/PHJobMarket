-- int_jobs__unified.sql
--
-- Stacks all 5 per-source staging models into ONE stream of job rows.
--
-- THE GOLDEN RULE OF UNION ALL: every branch must produce the *same columns*,
-- in the *same order*, with *compatible types*. Each source naturally has a
-- different set of fields, so here we pick one canonical 16-column shape and
-- null-fill whatever a given source doesn't provide. The null-fills are cast
-- explicitly (e.g. null::jsonb) so Postgres knows the column's type — without
-- the cast a bare NULL is type "unknown" and the UNION can fail.
--
-- Canonical columns:
--   raw_id, source, source_id, scraped_at,
--   title, company, location_raw, salary_raw, salary_currency, url,
--   posted_date, description, employment_type, experience_level,
--   is_remote, skills_json
--
-- WHY "ephemeral"? This model isn't stored as a table (see dbt_project.yml).
-- dbt inlines it as a CTE inside int_jobs__deduped. It's a stepping stone,
-- not something the dashboard queries directly.
--
-- The row_number() at the end numbers duplicate scrapes of the same job
-- (same source + source_id) newest-first, so the next model can keep only
-- the freshest copy.

with philjobnet as (
    select
        raw_id, source, source_id, scraped_at,
        title, company, location_raw, salary_raw,
        null::text    as salary_currency,
        url, posted_date, description, employment_type,
        null::text    as experience_level,
        null::boolean as is_remote,
        null::jsonb   as skills_json
    from {{ ref('stg_raw__philjobnet') }}
),

kalibrr as (
    select
        raw_id, source, source_id, scraped_at,
        title, company, location_raw, salary_raw,
        null::text    as salary_currency,
        url, posted_date, description, employment_type,
        experience_level,
        null::boolean as is_remote,
        skills_json
    from {{ ref('stg_raw__kalibrr') }}
),

jobstreet as (
    select
        raw_id, source, source_id, scraped_at,
        title, company, location_raw, salary_raw,
        null::text    as salary_currency,
        url, posted_date, description, employment_type,
        null::text    as experience_level,
        null::boolean as is_remote,
        null::jsonb   as skills_json
    from {{ ref('stg_raw__jobstreet') }}
),

onlinejobs as (
    select
        raw_id, source, source_id, scraped_at,
        title,
        null::text as company,        -- not on the listing
        null::text as location_raw,   -- remote-only, no city
        salary_raw,
        salary_currency,              -- explicit 'USD'
        url, posted_date,
        null::text as description,
        employment_type,
        null::text as experience_level,
        is_remote,                    -- explicit true
        null::jsonb as skills_json
    from {{ ref('stg_raw__onlinejobs') }}
),

indeed as (
    select
        raw_id, source, source_id, scraped_at,
        title, company, location_raw, salary_raw,
        null::text    as salary_currency,
        url, posted_date,
        null::text    as description,   -- not on the card
        employment_type,
        null::text    as experience_level,
        null::boolean as is_remote,
        null::jsonb   as skills_json
    from {{ ref('stg_raw__indeed') }}
),

unified as (
    select * from philjobnet
    union all select * from kalibrr
    union all select * from jobstreet
    union all select * from onlinejobs
    union all select * from indeed
)

select
    *,
    row_number() over (
        partition by source, source_id
        order by scraped_at desc
    ) as rn
from unified
