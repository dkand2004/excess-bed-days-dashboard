# Metric definitions

| Term | Definition |
|---|---|
| **Separation** | End of an admitted episode of care (Australian term for discharge). |
| **LOS (days)** | Separation date minus admission date; a same-day stay counts as 1 day. *(Verified against the Queensland QHAPDC Manual 2026-27, section 3.8.1: LOS = separation date minus admission date minus leave days; admitted and separated on the same date counts as one patient day; the separation day itself is not counted. Our synthetic data has no leave days.)* |
| **Peer group** | Stays with the same diagnosis category and age band (0-17, 18-39, 40-64, 65+). |
| **Expected LOS** | Mean LOS of the peer group **excluding the stay itself** (leave-one-out). Not computed if the group has fewer than 10 stays. |
| **Excess days** | Observed LOS minus expected LOS. Within a peer group these sum to zero. |
| **O/E ratio** | Observed LOS divided by expected LOS. 1.00 = as expected. For a hospital: total observed days / total expected days. |

## Why these choices (bias)
- **Mean, not median:** LOS is right-skewed; a median benchmark makes nearly every group look like it has excess days.
- **Leave-one-out:** stops a stay from helping set its own benchmark.
- **Minimum group size 10:** avoids benchmarks built on a handful of stays.

## Known limits
- Peer groups use diagnosis category and age band only (not severity, comorbidity or sex).
- Hospital assignment in this synthetic data is random, so hospital differences are noise by design.
- Outlier-heavy groups inflate the mean; the median is kept for reference.

## Readmission (sql/02_readmissions.sql)
| Term | Definition |
|---|---|
| **30-day readmission** | Same patient admitted again to any hospital **1-30 days** after separation. All-cause. |
| **Excluded** | Same-day (0 day) next admissions (continuation of care / transfer); stays ending in death; stays within 30 days of the end of the data (follow-up incomplete, called *censoring*). |
| **Stay bands** | O/E < 0.8 shorter than expected; 0.8-1.2 as expected; > 1.2 longer than expected. Cut-offs are a judgement call. |

### Known limits of the readmission view
- Planned and unplanned readmissions cannot be separated in synthetic data. Synthea's cancer
  pathways generate repeat admissions that look like scheduled treatment cycles (~30% in every
  stay band), so they dominate the overall rate.
- Readmissions are concentrated in two categories (Cancer, Cardiovascular); other categories are
  near 0%. Always compare **within** a category, never across the whole pooled dataset.
- In this synthetic data, longer-than-expected stays are **not** associated with higher
  readmission. This is a demonstration of the method, not a clinical finding.

### Decision: cancer is kept in the readmission view
Cancer admissions are retained because repeat admissions are a genuine feature of cancer care.
They are flagged `likely_planned_pathway = true` so the dashboard can show them separately and
the README states that planned and unplanned readmissions cannot be distinguished in synthetic data.

## Sensitivity checks (`src/sensitivity_checks.py`)
Benchmarking sources (for example Island Health) exclude deaths and unusually long stays; our main index does not. The same leave-one-out O/E was recomputed under two exclusion rules. The base column reproduces `hospital_summary.csv`.

| Rule | Stays dropped | Largest change in a hospital's O/E | Rank correlation with base | Hospitals above the 1.18 flag line |
|---|---|---|---|---|
| Base (all stays) | 0 | n/a | n/a | 0 |
| Exclude stays ending in death | 33 | 0.015 | 0.99 | 0 |
| Exclude stays above the 99th percentile of LOS (26 days) | 17 | 0.067 | 0.82 | 0 |

**Reading it:** excluding deaths barely changes anything. Excluding the longest 1% of stays moves Wattle Gully from 1.153 to 1.086, the largest change, and shuffles the middle of the ranking a little. No version flags any hospital. Because hospital assignment is random here, small reshuffles are expected. Full results: `data/processed/sensitivity_checks.csv`.
