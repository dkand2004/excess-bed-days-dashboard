-- 01_expected_los.sql
-- GOAL: for every hospital stay, work out how much longer (or shorter) it was than
-- the typical stay for "peers" = patients with the same diagnosis category and age band.
--
-- WHAT IS A CTE? A CTE (Common Table Expression) is a named temporary result you define
-- with WITH ... AS (...). It lets us build the answer in readable steps instead of one
-- giant nested query. Step 1 below (peer_stats) is a CTE; step 2 reuses it by name.

create or replace table stay_expected as
with peer_stats as (
    -- Step 1: summarise each peer group once.
    select
        diagnosis_category,
        age_band,
        count(*)               as n_peer,       -- how many stays the group is based on
        avg(los_days)          as mean_los,
        median(los_days)       as median_los    -- median resists a few very long stays
    from fact_separation
    group by diagnosis_category, age_band
)
-- Step 2: attach the group's typical stay to each individual stay and subtract.
select
    f.episode_id,
    f.patient_id,
    f.hospital_id,
    f.hospital_name,
    f.state,
    f.remoteness,
    f.admission_ts,
    f.diagnosis_category,
    f.diagnosis_name,
    f.age_band,
    f.sex,
    f.mode_of_separation,
    f.los_days,
    p.n_peer,
    round(p.mean_los, 2)    as expected_los_mean,
    p.median_los            as expected_los_median,
    -- Why NULL for small groups? An "expected" value based on <10 stays is mostly noise,
    -- so we refuse to compute an index there instead of showing a misleading number.
    case when p.n_peer >= 10 then round(f.los_days - p.median_los, 2) end as excess_days_median,
    case when p.n_peer >= 10 then round(f.los_days - p.mean_los, 2)   end as excess_days_mean
from fact_separation f
join peer_stats p
  on p.diagnosis_category = f.diagnosis_category
 and p.age_band           = f.age_band;
