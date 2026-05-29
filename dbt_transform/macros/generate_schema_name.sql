-- generate_schema_name.sql
--
-- By default dbt creates schemas named like "dev_staging" and "dev_warehouse"
-- (it prefixes everything with the target schema from profiles.yml).
-- This macro overrides that behavior to use clean schema names:
--   staging models  → "staging"
--   mart models     → "warehouse"
--   everything else → the default target schema ("dev")
--
-- This is a standard dbt pattern — see dbt docs: "Understanding custom schemas"

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
