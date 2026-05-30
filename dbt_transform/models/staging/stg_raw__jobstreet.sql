-- stg_raw__jobstreet.sql
--
-- Unpacks JobStreet's raw JSONB blobs into clean columns.
-- Same recipe as stg_raw__philjobnet.sql: filter to one source, pull each JSON
-- key out with ->>, trim text, guard the date cast.
--
-- JobStreet shape (written by scrapers/jobstreet.py):
--   title, company, location, salary_raw, description,
--   posted_date (the site's "listingDate", an ISO timestamp like
--   "2024-05-01T00:00:00Z"), employment_type, url
--
-- JobStreet has no skills array and no explicit experience/seniority field,
-- so those columns simply don't exist here — int_jobs__unified will null-fill
-- them when it stacks all sources together.

with source as (
    select * from {{ source('raw', 'job_postings') }}
    where source = 'jobstreet'
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
        raw_data ->> 'description'     as description,
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

    -- listingDate is ISO ("2024-05-01T00:00:00Z"); the prefix matches the
    -- guard and ::date keeps just the calendar day. Anything else → NULL.
    case
        when posted_date_raw ~ '^\d{4}-\d{2}-\d{2}'
        then posted_date_raw::date
        else null
    end as posted_date,

    description,
    lower(trim(employment_type)) as employment_type

from extracted
where title is not null   -- skip malformed rows with no title
