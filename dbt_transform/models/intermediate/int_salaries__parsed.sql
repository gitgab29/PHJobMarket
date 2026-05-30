-- int_salaries__parsed.sql
--
-- Turns free-text salary strings into structured numbers + currency + period.
-- Examples of what comes in (salary_raw) and what we want out:
--   "₱50,000 - ₱80,000/month"  → min 50000, max 80000, PHP, monthly
--   "$1,500 - $2,500"          → min 1500,  max 2500,  USD, monthly
--   "30k - 50k"                → min 30000, max 50000, PHP, monthly
--   "PHP 25,000"               → min 25000, max NULL,  PHP, monthly
--   "Competitive"              → min NULL,  max NULL  (kept, just no amounts)
--
-- DESIGN NOTES (why this differs from the draft in docs/plan/05):
--   1. We strip thousands separators BEFORE reading digits. The naive approach
--      replaces commas with spaces, which turns "50,000" into "50 000" and then
--      reads only "50". We remove commas/symbols entirely first.
--   2. We use substring(text from 'regex') — a SCALAR function that returns NULL
--      when nothing matches — instead of regexp_matches(), which is SET-returning
--      and would silently DROP rows with no number (or duplicate rows). Data
--      integrity > cleverness.
--   3. Currency = coalesce(explicit flag, guessed from text, 'PHP'). OnlineJobs
--      stamps 'USD' explicitly upstream, so we trust that first (CLAUDE.md rule).

with jobs as (
    select raw_id, source, source_id, salary_raw, salary_currency
    from {{ ref('int_jobs__deduped') }}
    where salary_raw is not null and trim(salary_raw) <> ''
),

normalized as (
    select
        raw_id, source, source_id, salary_raw, salary_currency,

        -- CRITICAL: cut the string at the first '+'. In this data '+' always
        -- means "plus perks", never a salary range: "PHP45K + PHP20K incentives",
        -- "Up to PHP55K + Day 1 HMO", "215k - 230k p.m. + allowance". The real
        -- pay is always BEFORE the '+'. Truncating stops the incentive figure
        -- from leaking into the salary (and from gluing onto it).
        --
        -- Is the amount in "k" shorthand (30k)? Checked on the pre-'+' part.
        (split_part(lower(salary_raw), '+', 1) ~* '\d\s*k') as is_k,

        -- Build a clean numeric string from the pre-'+' part:
        --   1. drop thousands commas so "45,000" stays one number (not "45 000")
        --   2. turn real range markers (" to ", dashes, tilde) into a single "~"
        --   3. replace every other junk run with ONE space — keeps distinct
        --      numbers apart instead of gluing them (the 4.5-billion bug)
        --   4. drop the "k" (its multiplier is already captured in is_k)
        regexp_replace(
            regexp_replace(
                regexp_replace(
                    replace(split_part(lower(salary_raw), '+', 1), ',', ''),
                '(\s+to\s+|–|—|~|-)', '~', 'g'),
                '[^0-9k.~]+', ' ', 'g'
            ),
            'k', '', 'g'
        ) as digits
    from jobs
),

amounts as (
    select
        raw_id, source, source_id, salary_raw, salary_currency, is_k,

        -- first number in the string
        substring(digits from '(\d+(?:\.\d+)?)')        as min_txt,
        -- number that appears right after the range marker "~" (NULL if no range)
        substring(digits from '~\s*(\d+(?:\.\d+)?)')     as max_txt
    from normalized
),

computed as (
    select
        raw_id, source, source_id, salary_raw,

        -- currency: explicit upstream flag wins, else sniff the text, else PHP
        coalesce(
            nullif(salary_currency, ''),
            case
                when salary_raw ~* '(php|₱)'                    then 'PHP'
                when salary_raw ~* '(usd|\$|us\s*dollar|dollar)' then 'USD'
                else null
            end,
            'PHP'
        ) as salary_currency,

        -- period: monthly is the default per CLAUDE.md
        case
            when salary_raw ~* '(per\s*hour|/hr|hourly|/hour)'                 then 'hourly'
            when salary_raw ~* '(per\s*day|daily|/day)'                        then 'daily'
            when salary_raw ~* '(per\s*year|yearly|annual|/yr|/year|p\.a\.)'   then 'yearly'
            else 'monthly'
        end as salary_period,

        (min_txt::numeric * case when is_k then 1000 else 1 end) as min_val,
        (max_txt::numeric * case when is_k then 1000 else 1 end) as max_val,

        -- Does the string actually look like pay? A currency symbol, "k"
        -- shorthand, or a per-period marker all signal a real salary. Strings
        -- like "Day 1 HMO, Weekends Off" have none — the "1" there is noise,
        -- not a wage, so we must NOT treat it as salary.
        (
            is_k
            or salary_raw ~* '(php|usd|peso|dollar|\$|₱|£|€)'
            or salary_raw ~* '(/hr|/hour|per\s*hour|hourly|/mo|/month|per\s*month|monthly|/yr|/year|per\s*year|yearly|annual|p\.a\.)'
        ) as has_money_signal
    from amounts
)

select
    raw_id,
    source,
    source_id,
    salary_raw,
    salary_currency,
    salary_period,

    -- Keep the number only if it's a believable salary: either the string
    -- carried a money signal, or the bare amount is large enough to be one
    -- (>= 1000). Also drop 0 ("₱0.00" = undisclosed). Otherwise NULL.
    case
        when min_val is not null and min_val > 0
             and (has_money_signal or min_val >= 1000)
        then min_val
    end as salary_min,

    case
        when max_val is not null and max_val > 0
             and (has_money_signal or max_val >= 1000)
        then max_val
    end as salary_max

from computed
