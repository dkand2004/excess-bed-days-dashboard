-- 01_expected_los.sql
-- GOAL: for every hospital stay, work out how much longer (or shorter) it was than the
-- typical stay for "peers" = same diagnosis category and same age band.
--
-- DESIGN CHOICES (chosen to minimise statistical bias):
--  1. MEAN, not median, as the benchmark. LOS is right-skewed, so a median sits below the
--     mean and makes almost every group look like it has "excess" days. The mean makes
--     excess add up to zero across a peer group, so hospital totals are fair.
--  2. LEAVE-ONE-OUT: a stay's expected value excludes the stay itself. Otherwise each stay
--     helps set its own benchmark and its excess is shrunk toward zero.
--  3. O/E RATIO (observed / expected): a standard healthcare benchmarking measure.
--     1.00 = as expected; 1.20 = 20% longer than expected.
--  4. Peer groups with < 10 stays are NOT scored (NULL): too noisy to trust.
--
-- WHAT IS A CTE? A CTE (Common Table Expression) is a named temporary result defined with
-- WITH ... AS (...). It lets us build the answer in readable steps. 'peer_totals' below is a
-- CTE; the final SELECT reuses it by name.

create or replace table stay_expected as
with peer_totals as (
    -- Step 1: totals per peer group (needed to compute "everyone except me").
    select
        diagnosis_category,
        age_band,
        count(*)       as n_peer,
        sum(los_days)  as sum_los,
        median(los_days) as median_los   -- informational only (outlier spotting), never aggregated
    from fact_separation
    group by diagnosis_category, age_band
),
scored as (
    -- Step 2: leave-one-out expected LOS = (group total - my LOS) / (group size - 1).
    select
        f.*,
        p.n_peer,
        p.median_los,
        case when p.n_peer >= 10
             then (p.sum_los - f.los_days) / (p.n_peer - 1) end as expected_los
    from fact_separation f
    join peer_totals p using (diagnosis_category, age_band)
)
select
    episode_id, patient_id, hospital_id, hospital_name, state, remoteness,
    admission_ts, diagnosis_category, diagnosis_name, reason_type, age_band, sex,
    mode_of_separation, los_days, n_peer,
    round(expected_los, 3)                  as expected_los,
    round(los_days - expected_los, 3)       as excess_days,    -- observed - expected
    round(los_days / expected_los, 3)       as oe_ratio,       -- observed / expected
    median_los                              as peer_median_los -- context only
from scored;
