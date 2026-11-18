-- 02_readmissions.sql
-- GOAL: flag 30-day readmissions, then ask: do stays that run LONGER than expected
-- have different readmission rates from stays that run shorter or as expected?
--
-- DEFINITION: a 30-day readmission = the same patient is admitted again (to any of our
-- hospitals) 1-30 days after separation. Same-day (0 day) next admissions are EXCLUDED:
-- they are continuations of care / transfers between episodes, which standard readmission
-- definitions do not count (in this data ~48% of cardiovascular 'next admissions' were same-day).
-- All-cause: we cannot tell planned (e.g. scheduled treatment cycles) from unplanned in
-- synthetic data, so we do not pretend to. This is a documented limitation.
--
-- WINDOW FUNCTION (LEAD): "lead(admission_ts) over (partition by patient_id order by
-- admission_ts)" means: within each patient's own stays, sorted by time, give me the NEXT
-- stay's admission time. That is how we find what happened after each discharge.

create or replace table stay_readmission as
with ordered as (
    select
        e.*,
        lead(admission_ts) over (partition by patient_id order by admission_ts) as next_admission_ts
    from stay_expected e
),
data_end as (
    -- Latest separation in the data. Stays ending within 30 days of this have an
    -- incomplete follow-up period (CENSORING), so we must not count them as "no readmission".
    select max(separation_ts)::date as last_day from fact_separation
)
select
    o.episode_id, o.patient_id, o.hospital_id, o.hospital_name, o.state, o.remoteness,
    o.admission_ts, o.diagnosis_category, o.age_band, o.mode_of_separation,
    o.los_days, o.expected_los, o.excess_days, o.oe_ratio,
    date_diff('day', f.separation_ts::date, o.next_admission_ts::date) as days_to_next_admission,
    -- Eligible = survived the stay AND a full 30-day follow-up exists in the data.
    (o.mode_of_separation <> 'Died'
       and f.separation_ts::date <= d.last_day - 30)                   as eligible_for_readmission,
    (o.next_admission_ts is not null
       and date_diff('day', f.separation_ts::date, o.next_admission_ts::date) between 1 and 30) as readmitted_30d,
    -- Bands for the comparison. Cut-offs (20% shorter / longer than expected) are a
    -- judgement call; documented in docs/metric_definitions.md.
    case when o.oe_ratio is null then null
         when o.oe_ratio < 0.8  then '1. Shorter than expected (O/E < 0.8)'
         when o.oe_ratio <= 1.2 then '2. As expected (0.8-1.2)'
         else                        '3. Longer than expected (O/E > 1.2)' end as stay_band
from ordered o
join fact_separation f using (episode_id)
cross join data_end d;

create or replace table readmit_by_stay_band as
select
    stay_band,
    count(*)                                         as stays,
    sum(readmitted_30d::int)                         as readmissions,
    round(100.0 * avg(readmitted_30d::int), 1)       as readmit_rate_pct,
    -- Approximate 95% confidence interval (normal approximation). Wide interval = weak evidence.
    round(100.0 * 1.96 * sqrt(avg(readmitted_30d::int) * (1 - avg(readmitted_30d::int)) / count(*)), 1) as ci_pm_pct
from stay_readmission
where eligible_for_readmission and stay_band is not null
group by stay_band
order by stay_band;
