-- salary_bucket.sql
--
-- A reusable macro that bins a salary column into human-readable PHP brackets.
-- "Macro" = a SQL function you can call inside other dbt models using Jinja.
--
-- Usage: {{ salary_bucket('salary_min') }}
-- This expands to the full CASE WHEN ... END block inline in the query.
--
-- Example: salary_min = 45000 → '₱40K-60K'

{% macro salary_bucket(salary_column) %}
    case
        when {{ salary_column }} is null           then 'Not disclosed'
        when {{ salary_column }} < 15000           then 'Below ₱15K'
        when {{ salary_column }} < 25000           then '₱15K-25K'
        when {{ salary_column }} < 40000           then '₱25K-40K'
        when {{ salary_column }} < 60000           then '₱40K-60K'
        when {{ salary_column }} < 80000           then '₱60K-80K'
        when {{ salary_column }} < 100000          then '₱80K-100K'
        when {{ salary_column }} < 150000          then '₱100K-150K'
        else                                            '₱150K+'
    end
{% endmacro %}
