-- stg_raw__indeed.sql
--
-- Unpacks Indeed PH raw JSONB blobs.
--
-- Indeed shape (written by scrapers/indeed.py):
--   title, company, location, salary_raw, employment_type, posted_date, url
--   * NO description on the search-results card → we emit NULL for it.
--     (Indeed gates full descriptions behind anti-bot walls; the scraper only
--      reliably gets the card fields. That's fine — description is optional
--      downstream; skill extraction just has less text to match against.)

with source as (
    select * from {{ source('raw', 'job_postings') }}
    where source = 'indeed'
),

extracted as (
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
        raw_data ->> 'employment_type' as employment_type
    from source
)

select
    raw_id,
    source,
    source_id,
    scraped_at,

    trim(title)        as title,
    trim(company)      as company,
    trim(location_raw) as location_raw,
    trim(salary_raw)   as salary_raw,
    trim(url)          as url,

    case
        when posted_date_raw ~ '^\d{4}-\d{2}-\d{2}'
        then posted_date_raw::date
        else null
    end as posted_date,

    -- NOTE: no description column here — Indeed cards don't carry one.
    -- int_jobs__unified null-fills description for this source.
    lower(trim(employment_type)) as employment_type

from extracted
where title is not null   -- skip malformed rows with no title
