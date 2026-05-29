-- assert_salary_range_valid.sql
--
-- Custom dbt test: checks that salary_max is never LESS than salary_min.
-- A salary range like "₱80K-₱20K" would be nonsense — this catches that.
--
-- How dbt singular tests work:
-- dbt expects this query to return ZERO rows when data is valid.
-- If any rows are returned, the test FAILS and dbt reports an error.
-- Think of it as: "find me any bad data — I expect to find nothing."
--
-- This test only runs after dbt run creates fct_job_postings (Week 3+).
-- For Week 2, just make sure this file exists; the test will be usable later.

select
    job_key,
    salary_min,
    salary_max
from {{ ref('fct_job_postings') }}
where salary_min  is not null
  and salary_max  is not null
  and salary_max  < salary_min   -- bad data: max is lower than min
