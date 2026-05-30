-- dim_locations.sql  (DIMENSION)
--
-- One row per distinct raw location string seen in the jobs. Free-text locations
-- like "Makati City, Metro Manila" or "BGC, Taguig" get normalized to a canonical
-- city, then enriched with province/region by joining the ph_regions seed.
--
-- WHY a regex city map? Sources spell places a hundred ways ("QC", "Quezon City",
-- "Q.C."). We fold those variants onto one canonical city so the dashboard can
-- group cleanly. ph_regions then attaches province + region (e.g. NCR) and lets
-- us flag Metro Manila.
--
-- The fact table joins back on location_raw (the exact original string), which is
-- unique here, so each job maps to exactly one location row.

with locations as (
    select distinct location_raw
    from {{ ref('int_jobs__deduped') }}
    where location_raw is not null and trim(location_raw) <> ''
),

ph_regions as (
    select * from {{ ref('ph_regions') }}
),

mapped as (
    select
        l.location_raw,
        case
            when l.location_raw ~* 'makati'                      then 'Makati'
            when l.location_raw ~* 'bgc|bonifacio|taguig'        then 'Taguig'
            when l.location_raw ~* 'quezon\s*city|\mqc\M'        then 'Quezon City'
            when l.location_raw ~* 'manila'                      then 'Manila'
            when l.location_raw ~* 'ortigas|pasig'               then 'Pasig'
            when l.location_raw ~* 'mandaluyong'                 then 'Mandaluyong'
            when l.location_raw ~* 'alabang|muntinlupa'          then 'Muntinlupa'
            when l.location_raw ~* 'cebu'                        then 'Cebu City'
            when l.location_raw ~* 'davao'                       then 'Davao City'
            when l.location_raw ~* 'clark|pampanga|angeles'      then 'Clark'
            when l.location_raw ~* 'iloilo'                      then 'Iloilo City'
            else trim(l.location_raw)
        end as city,
        (l.location_raw ~* '(remote|wfh|work from home|anywhere)') as is_remote
    from locations l
)

select
    row_number() over (order by m.location_raw) as location_key,
    m.location_raw,
    m.city,
    r.province,
    r.region,
    m.is_remote,
    coalesce(r.is_ncr, false) as is_metro_manila
from mapped m
left join ph_regions r on lower(m.city) = lower(r.city)
