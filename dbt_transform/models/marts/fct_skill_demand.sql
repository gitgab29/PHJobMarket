-- fct_skill_demand.sql  (FACT — an aggregate / summary fact)
--
-- Grain: ONE row per (snapshot_date, skill, source). Unlike fct_job_postings
-- (one row per event), this is a pre-aggregated fact answering "how many jobs
-- demanded skill X on day D from source Y, and what did they pay?". It powers
-- the "most in-demand skills" and "skill vs. salary" charts directly, without
-- the dashboard having to aggregate at query time.
--
-- snapshot_date = the scrape day. As we re-scrape over time, this table grows a
-- time series you can trend.
--
-- We join the (job, skill) pairs from int_skills__extracted up to dim_skills to
-- get skill_key, and LEFT join parsed salaries so skills on salary-less jobs
-- still count toward posting_count (avg simply ignores the NULLs).

with skill_jobs as (
    select
        sk.skill_name,
        j.source,
        j.scraped_at::date as snapshot_date,
        j.raw_id
    from {{ ref('int_skills__extracted') }} sk
    inner join {{ ref('int_jobs__deduped') }} j
        on sk.raw_id = j.raw_id and sk.source = j.source
),

salaries as (
    select * from {{ ref('int_salaries__parsed') }}
),

skills_dim as (
    select * from {{ ref('dim_skills') }}
)

select
    row_number() over (order by sj.snapshot_date, sd.skill_key, sj.source) as id,
    sj.snapshot_date,
    sd.skill_key,
    sj.source,
    count(distinct sj.raw_id) as posting_count,
    avg(sal.salary_min)       as avg_salary_min,
    avg(sal.salary_max)       as avg_salary_max
from skill_jobs sj
inner join skills_dim sd on sj.skill_name = sd.skill_name
left join salaries sal on sj.raw_id = sal.raw_id
group by sj.snapshot_date, sd.skill_key, sj.source
