-- int_jobs__deduped.sql
--
-- One clean row per real job. int_jobs__unified tagged every duplicate scrape
-- of the same (source, source_id) with a row number, newest first; here we
-- simply keep rn = 1 and drop the helper column.
--
-- This is the "spine" model: dim_companies, dim_locations, the salary parser,
-- the skill extractor, and fct_job_postings all build off of it. Keeping the
-- dedup in one place means every downstream model agrees on what "the jobs"
-- are.

select
    raw_id,
    source,
    source_id,
    scraped_at,
    title,
    company,
    location_raw,
    salary_raw,
    salary_currency,
    url,
    posted_date,
    description,
    employment_type,
    experience_level,
    is_remote,
    skills_json
from {{ ref('int_jobs__unified') }}
where rn = 1
