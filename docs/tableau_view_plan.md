# Tableau view plan (build guide)

Everything is built from the CSVs in `data/processed/`. Tableau Public cannot read the DuckDB file, so we use
CSVs. Connect **each CSV as its own data source** and use the right file for each chart (no joins needed).

## Design rules (from the author's experience of dense clinical systems)
| Problem with typical clinical screens | Rule here |
|---|---|
| Too many tabs | **One dashboard, one screen, no tabs.** Detail appears by clicking a chart, not by switching pages. |
| Too many low-level buttons | **Controls budget: 2 filters** (diagnosis category, year) **plus click-to-filter** on the hospital chart. No other buttons. |
| Too many colour codes | **Colour budget: grey for everything, one accent colour for "above threshold".** No traffic lights, no rainbow. |
| Numbers shown without context | **Every number shows how many stays it rests on.** Cells with fewer than 10 scored stays are greyed and labelled "not enough data". |
| Charts that invite over-reading | Titles are **questions**, with the honest answer underneath. |

Suggested palette (colour-blind safe): text/neutral `#374151`, mid grey `#9CA3AF`, light grey `#E5E7EB`, one accent `#D55E00`. Background white.

## Layout (suggested size 1200 x 800, fixed)
```
+-------------------------------------------------------------+
| Title + one-line caveat: SYNTHETIC DATA - method demo       |
| [3 numbers: Stays 2,182 | Avg stay 5.0 d | 30-day readmit]  |
+--------------------------------+----------------------------+
| 1. Hospital O/E (click to      | 2. Hospital x diagnosis    |
|    filter the rest)            |    O/E heatmap             |
+--------------------------------+----------------------------+
| 3. Monthly admissions &        | 4. 30-day readmission by   |
|    separations                 |    category and stay band  |
+--------------------------------+----------------------------+
| 5. How far to trust this (planted-excess result) + method   |
+-------------------------------------------------------------+
```

## Charts: question, file, fields
| # | Question (chart title) | File | Build |
|---|---|---|---|
| 0 | Header numbers | `stay_level.csv` | Stays = `COUNT([episode_id])`; avg stay = `AVG([los_days])`; readmission = share where `[eligible_for_readmission]` and `[readmitted_30d]` |
| 1 | **Is any hospital's stay length well above what its case-mix predicts?** | `hospital_summary.csv` | Dot plot: `hospital_name` rows, `oe_ratio` columns, sorted. **Reference line at 1.00** ("as expected") and **at 1.18** ("flag threshold" from the planted-excess test). Dots grey; **accent only if `oe_ratio` > 1.18**. Label each with `scored_stays`. Today the highest is 1.15, so none is flagged, and that is the honest answer. |
| 2 | **Where within hospitals do stays run longer than expected?** | `stay_level.csv` | Heatmap: `Diagnosis Category` rows, `Hospital Name` columns; colour and label = `Cell O/E` (O/E only when a cell has 20 or more scored stays, otherwise blank). Orange sequential palette, start 1.00, end 1.47 (the cell-level flag threshold from the planted-excess test). 28 of 90 cells have enough data; none is flagged. Exploratory only: cell-level detection power is low. |
| 3 | **How busy is each month?** | `monthly_trend.csv` | Two lines: `admissions`, `separations` (greys). **Show the last month dashed/greyed** (`is_partial_month`). Filter by `state` optional. |
| 4 | **Do longer-than-expected stays come back more often?** | `readmission_summary.csv` | Bars: `readmit_rate_pct` by `stay_band`, one panel each for **Cardiovascular**, **Cancer** and "everything else". Label bars with `stays`. **Cancer panel carries a note: "likely planned treatment cycles"** (`likely_planned_pathway`). Honest answer: no consistent link in this data. |
| 5 | **How much should you trust this dashboard?** | `planted_excess_power.csv` | Small table or line: detection rate vs planted excess. Message: a hospital-wide problem needs ~25-30% longer stays to be flagged reliably; a problem confined to one diagnosis group is almost invisible at hospital level. |

## Calculated fields (copy into Tableau)
```
// O/E for any grouping built from stay_level.csv (only stays with an expected value)
O/E := SUM(IF NOT ISNULL([expected_los]) THEN [los_days] END) / SUM([expected_los])

// Accent flag for chart 1
Above threshold := [oe_ratio] > 1.18

// Grey-out rule for heatmap cells
Enough data := COUNT(IF NOT ISNULL([expected_los]) THEN [episode_id] END) >= 10
```

## Interaction
- **Click a hospital** in chart 1 to filter charts 2-4 (Dashboard > Actions > Filter, source = chart 1, target = others).
- **Tooltips** (not extra buttons) hold the detail: stays, observed days, expected days, excess days.
- Optional hidden detail: clicking a heatmap cell shows the top stays by excess in the tooltip.

## Honesty checklist before publishing
- [ ] "Synthetic data, demonstrates a method" is visible without scrolling.
- [ ] Hospital differences are not described as better or worse (assignment was random).
- [ ] Cancer readmissions labelled likely planned.
- [ ] Every chart shows how many stays it rests on.
- [ ] Only one accent colour used; nothing red.
- [ ] Partial last month marked.
- [ ] A screenshot saved in `tableau/` and the Tableau Public link added to the README.

## Suggested sessions
| Session | Tasks | Time |
|---|---|---|
| Sat 21 Nov | Set up Tableau Public; connect the CSVs; build charts 1 and 2 | ~2 h |
| Mon 23 Nov | Charts 3, 4, 5; assemble the dashboard; click actions | ~2 h |
| Tue 24 Nov | Polish against the checklist; publish; save screenshot; add link to README | ~1 h |

## Interview talking points
- Why leave-one-out O/E instead of average stay (bias).
- Why the dashboard shows a flag threshold, and what the planted-excess test says it can and cannot detect.
- Why one screen, one accent colour and no tabs (clinical usability).

## Change log
- **Chart 2 changed** after a sanity check: the original idea (average excess days by diagnosis x age band) would show only zeros,
  because excess days sum to zero inside every peer group by construction (largest cell value 0.0003). Replaced by the hospital x diagnosis O/E heatmap.
- **Calculated field for chart 2:** `IF COUNT([Expected Los]) >= 20 THEN SUM(IF NOT ISNULL([Expected Los]) THEN [Los Days] END) / SUM([Expected Los]) END`
