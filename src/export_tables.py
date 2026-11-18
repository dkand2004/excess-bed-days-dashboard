"""Export small, Tableau-ready CSV tables from the DuckDB database and sanity-check them.

Run after: python src/australianise.py, python src/run_sql.py sql/01_expected_los.sql,
           python src/run_sql.py sql/02_readmissions.sql
Usage:     python src/export_tables.py
"""
import os
from pathlib import Path

import duckdb
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
OUT = Path(os.getenv("PROCESSED_DATA_DIR", "data/processed"))
con = duckdb.connect(os.getenv("DUCKDB_PATH", "data/ebd.duckdb"))

# 1. Hospital summary. O/E for a hospital = total observed days / total expected days over
#    SCORED stays only (peer groups with >= 10 stays), so numerator and denominator match.
con.execute(f"""
copy (
  select hospital_id, hospital_name, state, remoteness,
         count(*)                                         as stays,
         count(expected_los)                              as scored_stays,
         round(sum(los_days) filter (where expected_los is not null), 1)  as observed_days,
         round(sum(expected_los), 1)                      as expected_days,
         round(sum(excess_days), 1)                       as excess_bed_days,
         round(sum(los_days) filter (where expected_los is not null) / sum(expected_los), 3) as oe_ratio
  from stay_readmission group by all order by hospital_id
) to '{OUT}/hospital_summary.csv' (header)""")

# 2. Peer-group (diagnosis category x age band) summary.
con.execute(f"""
copy (
  select diagnosis_category, age_band, count(*) as stays,
         round(avg(los_days), 2) as mean_los, round(median(los_days), 1) as median_los,
         round(sum(excess_days), 1) as excess_bed_days,
         (count(expected_los) > 0) as scored
  from stay_readmission group by all order by 1, 2
) to '{OUT}/category_age_summary.csv' (header)""")

# 3. Monthly trend of admissions and separations by state. The last month is partial.
con.execute(f"""
copy (
  with adm as (select date_trunc('month', admission_ts)::date as month, state, count(*) as admissions
               from fact_separation group by all),
       sep as (select date_trunc('month', separation_ts)::date as month, state, count(*) as separations
               from fact_separation group by all)
  select coalesce(a.month, s.month) as month, coalesce(a.state, s.state) as state,
         coalesce(admissions, 0) as admissions, coalesce(separations, 0) as separations,
         (coalesce(a.month, s.month) >= date_trunc('month', (select max(separation_ts) from fact_separation))) as is_partial_month
  from adm a full outer join sep s on a.month = s.month and a.state = s.state
  order by 1, 2
) to '{OUT}/monthly_trend.csv' (header)""")

# 4. Readmission summary: by category and stay band (compare WITHIN category).
con.execute(f"""
copy (
  select diagnosis_category, likely_planned_pathway, stay_band, count(*) as stays,
         sum(readmitted_30d::int) as readmissions,
         round(100.0 * avg(readmitted_30d::int), 1) as readmit_rate_pct
  from stay_readmission where eligible_for_readmission and stay_band is not null
  group by all order by 1, 3
) to '{OUT}/readmission_summary.csv' (header)""")

# 5. Stay-level table for drill-down (synthetic IDs only; no names or addresses exist).
con.execute(f"""
copy (select episode_id, hospital_id, hospital_name, state, remoteness, admission_ts::date as admission_date,
             diagnosis_category, diagnosis_name, age_band, sex, mode_of_separation, los_days,
             expected_los, excess_days, oe_ratio, stay_band, eligible_for_readmission,
             readmitted_30d, likely_planned_pathway
      from stay_readmission order by admission_ts) to '{OUT}/stay_level.csv' (header)""")

# ---------- SANITY CHECKS: recompute independently in pandas and compare ----------
f = con.execute("select * from fact_separation").df()
g = f.groupby(["diagnosis_category", "age_band"])["los_days"].agg(["sum", "count"]).reset_index()
f = f.merge(g, on=["diagnosis_category", "age_band"])
f = f[f["count"] >= 10].copy()
f["exp"] = (f["sum"] - f["los_days"]) / (f["count"] - 1)          # leave-one-out mean
pandas_oe = f.groupby("hospital_id").apply(lambda d: d["los_days"].sum() / d["exp"].sum(), include_groups=False)
sql_oe = pd.read_csv(OUT / "hospital_summary.csv").set_index("hospital_id")["oe_ratio"]
diff = (pandas_oe - sql_oe).abs().max()
assert diff < 0.002, f"O/E mismatch between pandas and SQL: {diff}"
hs = pd.read_csv(OUT / "hospital_summary.csv")
assert hs["stays"].sum() == len(pd.read_csv(OUT / "stay_level.csv")) == con.execute("select count(*) from fact_separation").fetchone()[0]
assert abs(hs["excess_bed_days"].sum()) < 1.0, "excess should sum to ~0"
mt = pd.read_csv(OUT / "monthly_trend.csv")
assert mt["admissions"].sum() == hs["stays"].sum() and mt["separations"].sum() == hs["stays"].sum()
print(f"SANITY CHECKS PASSED. max |pandas - SQL| hospital O/E difference = {diff:.5f}")
for name in ["hospital_summary", "category_age_summary", "monthly_trend", "readmission_summary", "stay_level"]:
    p = OUT / f"{name}.csv"
    print(f"{name:22s} {len(pd.read_csv(p)):5d} rows  {p.stat().st_size/1024:6.0f} KB")
