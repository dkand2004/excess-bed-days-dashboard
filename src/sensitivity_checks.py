"""Sensitivity checks: does the hospital O/E index change if we exclude deaths or extreme stays?

WHY: benchmarking sources (e.g. Island Health) exclude deaths and unusually long stays; our main index does not.
This script recomputes the SAME leave-one-out O/E from data/processed/stay_level.csv under three rules and compares:
  base           : all stays (reproduces hospital_summary.csv; sanity check)
  no_deaths      : drop stays that ended in death (from both the peer pool and the hospital totals)
  no_long_outliers: drop stays above the 99th percentile of LOS
Run: python src/sensitivity_checks.py
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
OUT = Path(os.getenv("PROCESSED_DATA_DIR", "data/processed"))
d = pd.read_csv(OUT / "stay_level.csv")
MIN_PEER = 10  # same minimum peer-group size as the main method


def hospital_oe(df: pd.DataFrame) -> pd.Series:
    g = df.groupby(["diagnosis_category", "age_band"])["los_days"].agg(["sum", "count"]).rename(columns={"sum": "s", "count": "n"})
    m = df.join(g, on=["diagnosis_category", "age_band"])
    m = m[m["n"] >= MIN_PEER].copy()
    m["exp"] = (m["s"] - m["los_days"]) / (m["n"] - 1)          # leave-one-out mean
    return m.groupby("hospital_name").apply(lambda x: x["los_days"].sum() / x["exp"].sum(), include_groups=False)


p99 = d["los_days"].quantile(0.99)
variants = {
    "base": d,
    "no_deaths": d[d["mode_of_separation"] != "Died"],
    "no_long_outliers": d[d["los_days"] <= p99],
}
res = pd.DataFrame({k: hospital_oe(v) for k, v in variants.items()}).round(3)

# SANITY CHECK: the 'base' column must reproduce the exported hospital summary
hs = pd.read_csv(OUT / "hospital_summary.csv").set_index("hospital_name")["oe_ratio"]
assert (res["base"] - hs).abs().max() < 0.002, "base does not reproduce hospital_summary.csv"

res["diff_no_deaths"] = (res["no_deaths"] - res["base"]).round(3)
res["diff_no_outliers"] = (res["no_long_outliers"] - res["base"]).round(3)
res.to_csv(OUT / "sensitivity_checks.csv")
print(f"stays: base {len(variants['base'])}, no_deaths {len(variants['no_deaths'])} (dropped {len(d)-len(variants['no_deaths'])}), "
      f"no_long_outliers {len(variants['no_long_outliers'])} (dropped {len(d)-len(variants['no_long_outliers'])}; 99th percentile LOS = {p99:.0f} days)")
print(res.to_string())
for k in ["no_deaths", "no_long_outliers"]:
    rho = res["base"].rank().corr(res[k].rank())   # Spearman rank correlation = Pearson correlation of the ranks (no scipy needed)
    print(f"\n{k}: max |change| = {(res[k]-res['base']).abs().max():.3f}; rank correlation with base = {rho:.2f}; "
          f"hospitals above flag line 1.18: {(res[k] > 1.18).sum()} (base: {(res['base'] > 1.18).sum()})")
