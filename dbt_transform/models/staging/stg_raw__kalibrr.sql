-- stg_raw__kalibrr.sql
--
-- Same pattern as stg_raw__philjobnet.sql — unpacks Kalibrr's JSONB blobs.
--
-- Kalibrr-specific additions:
--   experience_level — seniority (e.g. "entry level", "mid level", "senior")
--   skills_json      — kept as JSONB array so int_skills__extracted can join it
--                      (we need the array structure, not a plain text string)
--
-- The -> operator (no second >) keeps the value as JSONB instead of converting
-- to text. We need this for skills because it's a JSON array like:
--   ["Python", "React", "PostgreSQL"]
-- Keeping it as JSONB lets later models use jsonb_array_elements_text() on it.

with source as (
    select * from {{ source('raw', 'job_postings') }}
    where source = 'kalibrr'
),

extracted as (
    select
        id          as raw_id,
        source,
        source_id,
        scraped_at,

        raw_data ->> 'title'            as title,
        raw_data ->> 'company'          as company,
        raw_data ->> 'location'         as location_raw,
        raw_data ->> 'salary_raw'       as salary_raw,
        raw_data ->> 'url'              as url,
        raw_data ->> 'posted_date'      as posted_date_raw,
        raw_data ->> 'description'      as description,
        raw_data ->> 'employment_type'  as employment_type,
        raw_data ->> 'experience_level' as experience_level,
        raw_data -> 'skills'            as skills_json   -- keep as JSONB array
    from source
)

select
    raw_id,
    source,
    source_id,
    scraped_at,

    trim(title)            as title,
    trim(company)          as company,
    trim(location_raw)     as location_raw,
    trim(salary_raw)       as salary_raw,
    trim(url)              as url,

    case
        when posted_date_raw ~ '^\d{4}-\d{2}-\d{2}'
        then posted_date_raw::date
        else null
    end as posted_date,

    description,
    lower(trim(employment_type))  as employment_type,
    lower(trim(experience_level)) as experience_level,
    skills_json

from extracted
where title is not null
