# 5. dbt Model Structure

## 5.1 Project Configuration

```yaml
# dbt_transform/dbt_project.yml
name: ph_job_market
version: "1.0.0"
config-version: 2
profile: ph_job_market
model-paths: ["models"]
seed-paths: ["seeds"]
test-paths: ["tests"]
macro-paths: ["macros"]

models:
  ph_job_market:
    staging:
      +materialized: view
      +schema: staging
    intermediate:
      +materialized: ephemeral
    marts:
      +materialized: table
      +schema: warehouse
```

```yaml
# dbt_transform/profiles.yml
ph_job_market:
  target: dev
  outputs:
    dev:
      type: postgres
      host: "{{ env_var('DB_HOST', 'localhost') }}"
      port: 5432
      user: "{{ env_var('DB_USER', 'phjobmarket') }}"
      pass: "{{ env_var('DB_PASSWORD', 'phjobmarket') }}"
      dbname: "{{ env_var('DB_NAME', 'phjobmarket') }}"
      schema: public
      threads: 4
```

```yaml
# dbt_transform/packages.yml
packages:
  - package: dbt-labs/dbt_utils
    version: ">=1.1.0"
```

## 5.2 Sources

```yaml
# dbt_transform/models/staging/_staging__sources.yml
version: 2
sources:
  - name: raw
    schema: raw
    tables:
      - name: job_postings
        description: Raw scraped job postings as JSONB blobs
        columns:
          - name: source
            tests:
              - not_null
              - accepted_values:
                  values: ['philjobnet', 'kalibrr', 'jobstreet', 'onlinejobs', 'indeed', 'facebook']
          - name: source_id
            tests:
              - not_null
```

## 5.3 Staging Models

```sql
-- dbt_transform/models/staging/stg_raw__philjobnet.sql
with source as (
    select * from {{ source('raw', 'job_postings') }}
    where source = 'philjobnet'
),
extracted as (
    select
        id as raw_id, source, source_id, scraped_at,
        raw_data ->> 'title'       as title,
        raw_data ->> 'company'     as company,
        raw_data ->> 'location'    as location_raw,
        raw_data ->> 'salary_raw'  as salary_raw,
        raw_data ->> 'url'         as url,
        raw_data ->> 'posted_date' as posted_date_raw,
        raw_data ->> 'description' as description,
        raw_data ->> 'employment_type' as employment_type
    from source
)
select
    raw_id, source, source_id, scraped_at,
    trim(title) as title,
    trim(company) as company,
    trim(location_raw) as location_raw,
    trim(salary_raw) as salary_raw,
    url,
    case when posted_date_raw ~ '^\d{4}-\d{2}-\d{2}' then posted_date_raw::date else null end as posted_date,
    description,
    lower(trim(employment_type)) as employment_type
from extracted
where title is not null
```

```sql
-- dbt_transform/models/staging/stg_raw__kalibrr.sql
with source as (
    select * from {{ source('raw', 'job_postings') }}
    where source = 'kalibrr'
),
extracted as (
    select
        id as raw_id, source, source_id, scraped_at,
        raw_data ->> 'title'             as title,
        raw_data ->> 'company'           as company,
        raw_data ->> 'location'          as location_raw,
        raw_data ->> 'salary_raw'        as salary_raw,
        raw_data ->> 'url'               as url,
        raw_data ->> 'posted_date'       as posted_date_raw,
        raw_data ->> 'description'       as description,
        raw_data ->> 'employment_type'   as employment_type,
        raw_data ->> 'experience_level'  as experience_level,
        raw_data -> 'skills'             as skills_json
    from source
)
select
    raw_id, source, source_id, scraped_at,
    trim(title) as title, trim(company) as company,
    trim(location_raw) as location_raw, trim(salary_raw) as salary_raw,
    url,
    case when posted_date_raw ~ '^\d{4}-\d{2}-\d{2}' then posted_date_raw::date else null end as posted_date,
    description,
    lower(trim(employment_type)) as employment_type,
    lower(trim(experience_level)) as experience_level,
    skills_json
from extracted
where title is not null
```

```sql
-- dbt_transform/models/staging/stg_raw__reddit_salaries.sql
with source as (
    select * from {{ source('raw', 'reddit_posts') }}
),
extracted as (
    select
        id as raw_id, source_id, scraped_at,
        raw_data ->> 'title'         as title,
        raw_data ->> 'selftext'      as selftext,
        raw_data ->> 'score'         as score,
        raw_data ->> 'num_comments'  as num_comments,
        raw_data ->> 'created_utc'   as created_utc,
        raw_data ->> 'url'           as url
    from source
)
select
    raw_id, source_id, scraped_at, title, selftext,
    score::integer as score,
    num_comments::integer as num_comments,
    created_utc::timestamptz as posted_at, url
from extracted
```

Pattern for other staging models: same structure, filter by `source = 'jobstreet'` etc., extract fields from JSONB.

## 5.4 Intermediate Models

```sql
-- dbt_transform/models/intermediate/int_jobs__unified.sql
with philjobnet as (
    select raw_id, source, source_id, scraped_at, title, company, location_raw, salary_raw,
        url, posted_date, description, employment_type,
        null::text as experience_level, null::jsonb as skills_json
    from {{ ref('stg_raw__philjobnet') }}
),
kalibrr as (
    select raw_id, source, source_id, scraped_at, title, company, location_raw, salary_raw,
        url, posted_date, description, employment_type, experience_level, skills_json
    from {{ ref('stg_raw__kalibrr') }}
),
-- Add jobstreet, onlinejobs, indeed with same column shape...
unified as (
    select * from philjobnet
    union all select * from kalibrr
    -- union all select * from jobstreet ...
)
select *, row_number() over (partition by source, source_id order by scraped_at desc) as rn
from unified
```

```sql
-- dbt_transform/models/intermediate/int_jobs__deduped.sql
select raw_id, source, source_id, scraped_at, title, company, location_raw, salary_raw,
    url, posted_date, description, employment_type, experience_level, skills_json
from {{ ref('int_jobs__unified') }}
where rn = 1
```

```sql
-- dbt_transform/models/intermediate/int_salaries__parsed.sql
with jobs as (
    select * from {{ ref('int_jobs__deduped') }}
    where salary_raw is not null and trim(salary_raw) != ''
),
parsed as (
    select raw_id, source, source_id, salary_raw,
        case
            when salary_raw ~* '(PHP|₱|Php)' then 'PHP'
            when salary_raw ~* '(USD|\$|US)' then 'USD'
            else 'PHP'
        end as salary_currency,
        case
            when salary_raw ~* '(per hour|/hr|hourly)' then 'hourly'
            when salary_raw ~* '(per year|yearly|annual|/yr|p\.a\.)' then 'yearly'
            else 'monthly'
        end as salary_period
    from jobs
)
select raw_id, source, source_id, salary_raw, salary_currency, salary_period,
    case
        when salary_raw ~* '(\d+)\s*[kK]'
        then (regexp_matches(salary_raw, '(\d+)\s*[kK]', 'i'))[1]::numeric * 1000
        else (regexp_matches(regexp_replace(salary_raw, '[^0-9.\-–]', ' ', 'g'), '(\d+(?:\.\d+)?)'))[1]::numeric
    end as salary_min,
    case
        when salary_raw ~ '[\-–~to]+.*\d' then
            case
                when salary_raw ~* '(\d+)\s*[kK]\s*[\-–~to]+\s*(\d+)\s*[kK]'
                then (regexp_matches(salary_raw, '[\-–~to]+\s*(\d+)\s*[kK]', 'i'))[1]::numeric * 1000
                else (regexp_matches(regexp_replace(salary_raw, '[^0-9.\-–]', ' ', 'g'), '\d+(?:\.\d+)?\s+(\d+(?:\.\d+)?)'))[1]::numeric
            end
        else null
    end as salary_max
from parsed
```

```sql
-- dbt_transform/models/intermediate/int_skills__extracted.sql
with jobs as (select * from {{ ref('int_jobs__deduped') }}),
skill_list as (select * from {{ ref('skill_aliases') }}),
matched as (
    select j.raw_id, j.source, j.source_id, s.canonical_name as skill_name, s.category as skill_category
    from jobs j cross join skill_list s
    where j.title ~* ('\m' || s.pattern || '\M')
       or coalesce(j.description, '') ~* ('\m' || s.pattern || '\M')
       or (j.skills_json is not null and exists (
            select 1 from jsonb_array_elements_text(j.skills_json) as elem
            where lower(elem) = lower(s.canonical_name) or lower(elem) ~ lower(s.pattern)
       ))
)
select distinct raw_id, source, source_id, skill_name, skill_category from matched
```

## 5.5 Mart Models

```sql
-- dbt_transform/models/marts/dim_companies.sql
with companies as (
    select distinct company, lower(regexp_replace(trim(company), '\s+', '-', 'g')) as company_slug
    from {{ ref('int_jobs__deduped') }} where company is not null
)
select row_number() over (order by company) as company_key,
    company as company_name, company_slug,
    current_date as first_seen_at, current_date as last_seen_at, 0 as total_postings
from companies
```

```sql
-- dbt_transform/models/marts/dim_locations.sql
with locations as (
    select distinct location_raw from {{ ref('int_jobs__deduped') }} where location_raw is not null
),
ph_regions as (select * from {{ ref('ph_regions') }}),
mapped as (
    select l.location_raw,
        case
            when l.location_raw ~* 'makati' then 'Makati'
            when l.location_raw ~* 'bgc|bonifacio|taguig' then 'Taguig'
            when l.location_raw ~* 'quezon\s*city|qc' then 'Quezon City'
            when l.location_raw ~* 'manila(?!\s*(city|metro))' then 'Manila'
            when l.location_raw ~* 'pasig' then 'Pasig'
            when l.location_raw ~* 'mandaluyong' then 'Mandaluyong'
            when l.location_raw ~* 'ortigas' then 'Pasig'
            when l.location_raw ~* 'alabang|muntinlupa' then 'Muntinlupa'
            when l.location_raw ~* 'cebu' then 'Cebu City'
            when l.location_raw ~* 'davao' then 'Davao City'
            when l.location_raw ~* 'clark|pampanga|angeles' then 'Clark'
            when l.location_raw ~* 'iloilo' then 'Iloilo City'
            else trim(l.location_raw)
        end as city,
        l.location_raw ~* '(remote|wfh|work from home|anywhere)' as is_remote
    from locations l
)
select row_number() over (order by city) as location_key,
    location_raw, city, r.province, r.region, is_remote,
    r.region = 'NCR' as is_metro_manila
from mapped m left join ph_regions r on lower(m.city) = lower(r.city)
```

```sql
-- dbt_transform/models/marts/fct_job_postings.sql
with jobs as (select * from {{ ref('int_jobs__deduped') }}),
salaries as (select * from {{ ref('int_salaries__parsed') }}),
companies as (select * from {{ ref('dim_companies') }}),
locations as (select * from {{ ref('dim_locations') }})
select
    j.raw_id as job_key, j.source, j.source_id, j.title, j.description,
    c.company_key, l.location_key,
    to_char(coalesce(j.posted_date, j.scraped_at::date), 'YYYYMMDD')::integer as date_posted_key,
    to_char(j.scraped_at::date, 'YYYYMMDD')::integer as date_scraped_key,
    s.salary_min, s.salary_max, s.salary_currency, s.salary_period,
    j.employment_type, j.experience_level, l.is_remote, j.url
from jobs j
left join salaries s on j.raw_id = s.raw_id
left join companies c on lower(trim(j.company)) = lower(c.company_name)
left join locations l on j.location_raw = l.location_raw
```

```sql
-- dbt_transform/models/marts/fct_skill_demand.sql
with skill_jobs as (
    select sk.skill_name, sk.skill_category, j.source,
        j.scraped_at::date as snapshot_date, j.raw_id
    from {{ ref('int_skills__extracted') }} sk
    inner join {{ ref('int_jobs__deduped') }} j on sk.raw_id = j.raw_id and sk.source = j.source
),
salaries as (select * from {{ ref('int_salaries__parsed') }}),
skills_dim as (select * from {{ ref('dim_skills') }})
select
    row_number() over () as id, sj.snapshot_date, sd.skill_key,
    count(distinct sj.raw_id) as posting_count,
    avg(sal.salary_min) as avg_salary_min, avg(sal.salary_max) as avg_salary_max,
    sj.source
from skill_jobs sj
inner join skills_dim sd on sj.skill_name = sd.skill_name
left join salaries sal on sj.raw_id = sal.raw_id
group by sj.snapshot_date, sd.skill_key, sj.source
```

## 5.6 Tests

```yaml
# dbt_transform/models/marts/_marts__models.yml
version: 2
models:
  - name: fct_job_postings
    columns:
      - name: job_key
        tests: [unique, not_null]
      - name: source
        tests:
          - not_null
          - accepted_values:
              values: ['philjobnet', 'kalibrr', 'jobstreet', 'onlinejobs', 'indeed', 'facebook']
      - name: title
        tests: [not_null]
      - name: salary_min
        tests:
          - dbt_utils.accepted_range:
              min_value: 0
              max_value: 10000000
              where: "salary_min is not null"
  - name: dim_companies
    columns:
      - name: company_key
        tests: [unique, not_null]
      - name: company_name
        tests: [not_null]
```

```sql
-- dbt_transform/tests/assert_salary_range_valid.sql
select job_key, salary_min, salary_max
from {{ ref('fct_job_postings') }}
where salary_min is not null and salary_max is not null and salary_max < salary_min
```

## 5.7 Seeds

See `dbt_transform/seeds/ph_regions.csv` and `dbt_transform/seeds/skill_aliases.csv` in the full plan (04-database-schema.md appendix or create directly from the directory structure).

## 5.8 Macros

```sql
-- dbt_transform/macros/salary_bucket.sql
{% macro salary_bucket(salary_column) %}
    case
        when {{ salary_column }} is null then 'Not disclosed'
        when {{ salary_column }} < 15000 then 'Below ₱15K'
        when {{ salary_column }} < 25000 then '₱15K-25K'
        when {{ salary_column }} < 40000 then '₱25K-40K'
        when {{ salary_column }} < 60000 then '₱40K-60K'
        when {{ salary_column }} < 80000 then '₱60K-80K'
        when {{ salary_column }} < 100000 then '₱80K-100K'
        when {{ salary_column }} < 150000 then '₱100K-150K'
        else '₱150K+'
    end
{% endmacro %}
```
