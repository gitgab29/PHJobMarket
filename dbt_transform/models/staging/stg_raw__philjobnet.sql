-- stg_raw__philjobnet.sql
--
-- WHAT THIS MODEL DOES:
-- Takes the raw JSONB blobs from PhilJobNet and unpacks them into clean columns.
--
-- Think of raw.job_postings like a cardboard box where everything is stuffed
-- inside one big JSON field (raw_data). This model "unpacks the box" and puts
-- each item on its own labeled shelf.
--
-- The ->> operator is Postgres's way of pulling a text value out of JSONB:
--   raw_data ->> 'title'   →  the "title" key from the JSON blob, as TEXT
--   raw_data -> 'skills'   →  the "skills" key, kept as JSONB (for arrays/objects)
--
-- WHY A VIEW?
-- Staging models are views by default (set in dbt_project.yml).
-- Views don't store data — they just run the SQL each time they're queried.
-- This is fine at the staging layer because raw.job_postings is the truth.
-- Views also pick up new raw data automatically without needing a re-run.

with source as (
    -- Pull only PhilJobNet rows from the shared job_postings table.
    -- {{ source('raw', 'job_postings') }} is dbt's way of referencing
    -- raw.job_postings — it tracks lineage and lets dbt test the source.
    select * from {{ source('raw', 'job_postings') }}
    where source = 'philjobnet'
),

extracted as (
    -- Unpack JSONB fields into individual columns.
    -- We alias the table's id → raw_id to avoid confusion with source_id.
    select
        id          as raw_id,
        source,
        source_id,
        scraped_at,

        raw_data ->> 'title'           as title,
        raw_data ->> 'company'         as company,
        raw_data ->> 'location'        as location_raw,
        raw_data ->> 'salary_raw'      as salary_raw,
        raw_data ->> 'url'             as url,
        raw_data ->> 'posted_date'     as posted_date_raw,
        raw_data ->> 'description'     as description,
        raw_data ->> 'employment_type' as employment_type,
        raw_data ->> 'education_level' as education_level
    from source
)

select
    raw_id,
    source,
    source_id,
    scraped_at,

    -- Light cleaning: trim whitespace from text fields
    trim(title)         as title,
    trim(company)       as company,
    trim(location_raw)  as location_raw,
    trim(salary_raw)    as salary_raw,
    trim(url)           as url,

    -- Parse the date string only if it looks like YYYY-MM-DD.
    -- PhilJobNet stores dates like "Posted on 5/27/2026" — those won't match
    -- and will become NULL here. That's expected: dbt will flag them as unknown.
    case
        when posted_date_raw ~ '^\d{4}-\d{2}-\d{2}'
        then posted_date_raw::date
        else null
    end as posted_date,

    description,
    lower(trim(employment_type))  as employment_type,
    lower(trim(education_level))  as education_level

from extracted
where title is not null   -- skip malformed rows with no title
