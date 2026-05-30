-- stg_raw__onlinejobs.sql
--
-- Unpacks OnlineJobs.ph raw JSONB blobs.
--
-- OnlineJobs is the odd one out (written by scrapers/onlineJobs.py):
--   * NO company, NO location, NO description on the listing page → we emit NULL
--     for those so the column shape still lines up with the other sources.
--   * It pays in USD and is remote-only, so the scraper stamps two explicit
--     flags into the blob: salary_currency = 'USD' and is_remote = true.
--     We carry those through verbatim instead of guessing later — this is the
--     "PHP monthly unless marked otherwise" rule from CLAUDE.md in action:
--     here it IS marked otherwise, so we honor the mark.
--
-- The is_remote value arrives as a JSON boolean. raw_data ->> 'is_remote'
-- pulls it out as the TEXT 'true'/'false', so we cast it back to boolean.

with source as (
    select * from {{ source('raw', 'job_postings') }}
    where source = 'onlinejobs'
),

extracted as (
    select
        id          as raw_id,
        source,
        source_id,
        scraped_at,

        raw_data ->> 'title'           as title,
        raw_data ->> 'salary_raw'      as salary_raw,
        raw_data ->> 'salary_currency' as salary_currency,
        raw_data ->> 'url'             as url,
        raw_data ->> 'posted_date'     as posted_date_raw,
        raw_data ->> 'employment_type' as employment_type,
        raw_data ->> 'is_remote'       as is_remote_raw
    from source
)

select
    raw_id,
    source,
    source_id,
    scraped_at,

    trim(title)      as title,
    trim(salary_raw) as salary_raw,
    upper(trim(salary_currency)) as salary_currency,   -- 'USD'
    trim(url)        as url,

    case
        when posted_date_raw ~ '^\d{4}-\d{2}-\d{2}'
        then posted_date_raw::date
        else null
    end as posted_date,

    lower(trim(employment_type)) as employment_type,

    -- explicit remote flag from the scraper; default true since this site is
    -- remote-only, but respect the stored value if present.
    coalesce(is_remote_raw::boolean, true) as is_remote

from extracted
where title is not null   -- skip malformed rows with no title
