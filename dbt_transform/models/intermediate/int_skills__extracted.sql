-- int_skills__extracted.sql
--
-- Finds which skills each job mentions. Output grain: one row per (job, skill).
--
-- HOW IT WORKS:
--   skill_aliases (a seed CSV) lists ~80 patterns → canonical names, e.g.
--     pattern "JS" → canonical "JavaScript", pattern "python3" → "Python".
--   We CROSS JOIN every job against every pattern (jobs × patterns) and keep
--   the pairs where the job text actually contains the pattern.
--
-- WHY WORD-BOUNDARY REGEX (a locked project decision):
--   Plain substring matching is wrong — "Java" lives inside "JavaScript", and
--   "Go" lives inside "Google". Postgres's \m (start of word) and \M (end of
--   word) anchors force a whole-word match, so 'Java' won't fire on 'JavaScript'.
--
-- WHERE WE LOOK:
--   1. the job title, 2. the description (when present), and
--   3. for Kalibrr, the explicit skills_json array (["Python","React",...]) —
--      we unnest it with jsonb_array_elements_text and match each element.
--
-- The cross join is ~2,000 jobs × ~80 patterns ≈ 160k cheap regex checks — fine
-- at this scale. distinct collapses the case where title AND description both
-- mention the same skill.

with jobs as (
    select raw_id, source, source_id, title, description, skills_json
    from {{ ref('int_jobs__deduped') }}
),

skills as (
    select pattern, canonical_name, category
    from {{ ref('skill_aliases') }}
)

select distinct
    j.raw_id,
    j.source,
    j.source_id,
    s.canonical_name as skill_name,
    s.category       as skill_category
from jobs j
cross join skills s
where
    (j.title ~* ('\m' || s.pattern || '\M'))
    or (j.description is not null and j.description ~* ('\m' || s.pattern || '\M'))
    or (
        j.skills_json is not null
        and exists (
            select 1
            from jsonb_array_elements_text(j.skills_json) as elem
            where elem ~* ('\m' || s.pattern || '\M')
        )
    )
