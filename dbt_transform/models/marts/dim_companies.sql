-- dim_companies.sql  (DIMENSION)
--
-- One row per distinct company. A "dimension" holds the descriptive context
-- you slice facts by — here, who posted the job.
--
-- SURROGATE KEY: company_key = row_number(). The fact table stores this small
-- integer instead of repeating the full company name on every job row. We also
-- keep company_lower as the natural join key so fct_job_postings can match a
-- job's company to its dimension row deterministically.
--
-- IMPORTANT — we group by lower(trim(company)), not the raw text. If "ABC Corp"
-- and "abc corp" were separate rows, the case-insensitive join in the fact model
-- would match BOTH and duplicate the job. Collapsing on the lowercased name
-- guarantees exactly one dimension row per company key.

with companies as (
    select
        lower(trim(company))   as company_lower,
        max(trim(company))     as company_name,        -- representative display form
        min(scraped_at::date)  as first_seen_at,
        max(scraped_at::date)  as last_seen_at,
        count(*)               as total_postings
    from {{ ref('int_jobs__deduped') }}
    where company is not null and trim(company) <> ''
    group by lower(trim(company))
)

select
    row_number() over (order by company_lower) as company_key,
    company_name,
    company_lower,
    lower(regexp_replace(company_name, '\s+', '-', 'g')) as company_slug,
    first_seen_at,
    last_seen_at,
    total_postings
from companies
