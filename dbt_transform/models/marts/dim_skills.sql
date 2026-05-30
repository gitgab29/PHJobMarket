-- dim_skills.sql  (DIMENSION)
--
-- One row per canonical skill. Built straight from the skill_aliases seed by
-- collapsing its many patterns down to the distinct canonical names + category
-- (e.g. patterns "JS", "JavaScript" both → one "JavaScript" row).
--
-- fct_skill_demand joins to this on skill_name to attach the surrogate skill_key
-- (and to give every chart a stable, deduplicated skill list to group by).

with distinct_skills as (
    -- one row per canonical_name. group (not distinct) so a name that appears
    -- with two categories in the seed can't produce two rows and double-count
    -- downstream — we pick one category deterministically.
    select canonical_name, max(category) as category
    from {{ ref('skill_aliases') }}
    group by canonical_name
)

select
    row_number() over (order by canonical_name) as skill_key,
    canonical_name as skill_name,
    category       as skill_category
from distinct_skills
