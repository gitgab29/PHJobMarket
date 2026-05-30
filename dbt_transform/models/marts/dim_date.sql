-- dim_date.sql  (DIMENSION)
--
-- A calendar table: one row per day from 2024-01-01 through 2027-12-31.
--
-- WHY build a date dimension instead of just storing dates on the fact?
-- Because the dashboard wants to group by month, quarter, weekday, "is it a
-- weekend", etc. Doing that math in every query is repetitive and slow. A date
-- dimension precomputes those attributes once; charts just JOIN and GROUP BY
-- month_name / quarter / year.
--
-- date_key is the integer YYYYMMDD (e.g. 20260530). The fact table stores that
-- same integer for date_posted_key / date_scraped_key, so they join directly.
-- generate_series() is Postgres's row-generator: give it start, stop, step and
-- it emits one row per step.

with dates as (
    select generate_series(
        '2024-01-01'::date,
        '2027-12-31'::date,
        interval '1 day'
    )::date as full_date
)

select
    to_char(full_date, 'YYYYMMDD')::integer as date_key,
    full_date,
    extract(isodow from full_date)::smallint as day_of_week,   -- 1=Mon … 7=Sun
    trim(to_char(full_date, 'Day'))          as day_name,
    extract(month from full_date)::smallint  as month,
    trim(to_char(full_date, 'Month'))        as month_name,
    extract(quarter from full_date)::smallint as quarter,
    extract(year from full_date)::smallint   as year,
    (extract(isodow from full_date) in (6, 7)) as is_weekend
from dates
