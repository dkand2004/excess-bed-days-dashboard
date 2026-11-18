"""Planted-excess validation: can the O/E index detect a problem we deliberately create?

IDEA: most dashboards never check whether they would notice a real problem. Here we PLANT a known
amount of extra bed-days into one fictional hospital, re-run the index many times on randomly
re-assigned data, and measure (a) how often it is detected and (b) how often it raises a false alarm.

METHOD (all choices are documented here so they can be questioned):
 - Each repeat re-assigns every stay to one of N hospitals at random (like the data build).
 - Target hospital = hospital 0. Its stays' LOS is multiplied by (1 + effect). Planted values are
   fractional days (so small effects are not erased by rounding to whole days).
 - O/E is recomputed with the SAME leave-one-out method, so the planted stays also contaminate the
   peer benchmark (as a real problem hospital would).
 - Detection threshold is calibrated from the NO-PLANT runs: the 95th percentile of the MAXIMUM
   O/E across all units. A flag therefore has a 5% family-wise false-alarm rate by construction.
 - Two scenarios: (A) hospital-wide excess, flagged at HOSPITAL level;
                  (B) excess in ONE diagnosis category only, flagged at HOSPITAL level vs at
                      HOSPITAL x CATEGORY level (shows why drill-down is needed).
Run: python src/planted_excess_test.py
"""
import os
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
OUT = Path(os.getenv("PROCESSED_DATA_DIR", "data/processed"))
R = 2000                      # repeats per setting
EFFECTS = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40]
TARGET_CATEGORY = "Cardiovascular"
rng = np.random.default_rng(42)  # fixed seed: results are repeatable

con = duckdb.connect(os.getenv("DUCKDB_PATH", "data/ebd.duckdb"))
d = con.execute("select los_days, diagnosis_category, age_band from fact_separation").df()
n = len(d)
n_hosp = con.execute("select count(*) from dim_hospital").fetchone()[0]
cat_codes, cat_names = pd.factorize(d["diagnosis_category"])
g = pd.factorize(d["diagnosis_category"] + "|" + d["age_band"])[0]   # peer-group id
los0 = d["los_days"].to_numpy(float)
n_g = np.bincount(g)
scored = n_g[g] >= 10                       # same minimum-group-size rule as the SQL
target_cat = int(np.where(cat_names == TARGET_CATEGORY)[0][0])
n_cat = len(cat_names)


def one_run(effect, scenario):
    """Return (hospital-level max O/E, target hospital O/E, cell-level max O/E, target cell O/E)."""
    hosp = rng.integers(0, n_hosp, n)
    los = los0.copy()
    if scenario == "A":
        los[hosp == 0] *= 1 + effect
    else:
        los[(hosp == 0) & (cat_codes == target_cat)] *= 1 + effect
    s_g = np.bincount(g, weights=los)
    exp = np.where(scored, (s_g[g] - los) / np.maximum(n_g[g] - 1, 1), 0.0)
    obs = np.where(scored, los, 0.0)
    h_obs = np.bincount(hosp, weights=obs, minlength=n_hosp)
    h_exp = np.bincount(hosp, weights=exp, minlength=n_hosp)
    h_oe = h_obs / h_exp
    cell = hosp * n_cat + cat_codes
    c_obs = np.bincount(cell, weights=obs, minlength=n_hosp * n_cat)
    c_exp = np.bincount(cell, weights=exp, minlength=n_hosp * n_cat)
    with np.errstate(invalid="ignore", divide="ignore"):
        c_oe = np.where(c_exp > 0, c_obs / c_exp, np.nan)
    # Ignore tiny cells (< 20 scored stays) so single-stay noise is not flagged.
    c_n = np.bincount(cell, weights=scored.astype(float), minlength=n_hosp * n_cat)
    c_oe = np.where(c_n >= 20, c_oe, np.nan)
    return h_oe.max(), h_oe[0], np.nanmax(c_oe), c_oe[0 * n_cat + target_cat]


rows = []
for scenario in ["A", "B"]:
    null = np.array([one_run(0.0, scenario) for _ in range(R)])
    thr_h = np.percentile(null[:, 0], 95)          # hospital-level threshold
    thr_c = np.nanpercentile(null[:, 2], 95)       # cell-level threshold
    for e in EFFECTS:
        res = np.array([one_run(e, scenario) for _ in range(R)])
        rows.append({
            "scenario": "A: hospital-wide" if scenario == "A" else f"B: {TARGET_CATEGORY} only",
            "planted_effect_pct": int(e * 100),
            "mean_target_oe_hospital": round(res[:, 1].mean(), 3),
            "detect_rate_hospital_level_pct": round(100 * (res[:, 1] > thr_h).mean(), 1),
            "detect_rate_hospital_x_category_pct": round(100 * (res[:, 3] > thr_c).mean(), 1),
            "hospital_threshold_oe": round(thr_h, 3),
            "cell_threshold_oe": round(thr_c, 3),
        })

out = pd.DataFrame(rows)
out.to_csv(OUT / "planted_excess_power.csv", index=False)
print(f"{n} stays, {n_hosp} hospitals, {R} repeats per setting, seed 42\n")
print(out.to_string(index=False))
