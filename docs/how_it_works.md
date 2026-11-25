# How Project 1 works: a teaching guide

Read this in order (about 20 minutes). By the end you should be able to explain every number on the dashboard
and answer the questions at the bottom. Everything here uses **synthetic data**.

---

## 1. The one-minute version
Hospitals often report an *average length of stay*. That number can mislead: a cardiac ward may stay longer simply
because its patients are sicker. This project asks a fairer question: **"Is this stay longer than expected for
patients like this one?"** It compares every stay with similar stays (same diagnosis group and age band), adds up the
difference as **excess bed-days**, and shows it on a Tableau dashboard. It also **tests itself**: we plant a known
problem and check whether the method finds it.

Say it like this: *"I benchmarked each hospital stay against similar patients, flagged only what rose above the
noise, and tested the flag by planting a known problem to see if it would be detected."*

---

## 2. The pipeline, step by step
| Step | What happens | File |
|---|---|---|
| 1. Generate | Synthea (a free simulator of fake patients) produces patient records | Synthea jar, command in README |
| 2. Australian layer | Re-label the data: 10 fictional hospitals, Australian terms, personal details dropped | `src/australianise.py` |
| 3. Database | The result is a table, one row per hospital stay, in DuckDB | `fact_separation` |
| 4. Expected stay | For each stay, work out the typical stay of its peers | `sql/01_expected_los.sql` |
| 5. Readmissions | Flag who came back within 30 days | `sql/02_readmissions.sql` |
| 6. Export | Write small CSV tables, and check them again independently in pandas | `src/export_tables.py` |
| 7. Self-test | Plant a known problem and measure how often it is detected | `src/planted_excess_test.py` |
| 8. Dashboard | Tableau Public charts built from the CSVs | `tableau/`, `docs/tableau_view_plan.md` |

---

## 3. The data, and why it is safe
- **Synthea** generates fake but plausible patients. No real person is involved. It is built around the United States,
  and we used its default (Massachusetts).
- **The Australian layer** is a re-labelling, not a re-modelling. Patients are spread across **10 fictional hospitals**
  (5 Queensland, 1 NSW, 2 Victoria, 1 WA, 1 SA) using a repeatable hash of the patient ID. Names, SSN, addresses and
  race/ethnicity are dropped (race categories follow US census groups and cannot honestly be translated to
  Aboriginal and Torres Strait Islander status).
- **Size:** 2,182 inpatient stays from 2021 onward, about 170 to 310 per hospital.
- **Important limit:** the clinical content is still US-modelled, and hospital assignment is **random**. So any
  difference between hospitals is noise by design. The project demonstrates a *method*, not a finding.

---

## 4. The core idea: "longer than expected for whom?"
**Peers.** Stays with the same diagnosis category (9 groups) and the same age band (0-17, 18-39, 40-64, 65+).

**Expected stay.** The average length of stay of a stay's peers, **leaving that stay out** (leave-one-out).
Why leave it out? Otherwise the stay helps set its own benchmark, which shrinks its difference towards zero.

**Worked example (made-up numbers).** A peer group has four stays: 2, 3, 4 and 7 days.

| Stay | Peers' average (without it) | Excess (actual - expected) | O/E (actual / expected) |
|---|---|---|---|
| 2 days | (3+4+7)/3 = 4.67 | -2.67 | 0.43 |
| 3 days | (2+4+7)/3 = 4.33 | -1.33 | 0.69 |
| 4 days | (2+3+7)/3 = 4.00 | 0.00 | 1.00 |
| 7 days | (2+3+4)/3 = 3.00 | +4.00 | 2.33 |

Check: -2.67 - 1.33 + 0 + 4.00 = 0.
The excess values add up to **zero** inside every peer group. That is why a fair "total excess" can be summed per
hospital: only differences between groups of patients stay in the number.

**O/E ratio** = observed days / expected days. 1.00 means "as expected"; 1.20 means "20% longer than expected".
For a hospital we add up all its observed days and divide by all its expected days.

**Rules and why:**
- **Mean, not median.** Stay lengths are right-skewed, so a median makes almost every group look like it has
  "excess" days. The mean makes excess add up to zero.
- **Minimum 10 stays per peer group.** A benchmark from a handful of stays is mostly noise, so we refuse to score it.
- **Same-day stays count as 1 day**, as in the Queensland QHAPDC Manual 2026-27 (section 3.8.1). Length of stay is separation
  date minus admission date (minus leave days, of which our synthetic data has none). In this data every stay is overnight anyway.

---

## 5. Readmissions
**30-day readmission:** the same patient is admitted again 1 to 30 days after leaving.
**Excluded:** same-day "next admissions" (continuation of care, not a readmission), stays ending in death, and stays
too close to the end of the data to have a full 30 days of follow-up (called *censoring*).

**What we found:** about 9.6% overall, but almost all of it is **Cancer** (about 30%) versus about 2% for everything
else. Cancer pathways in Synthea look like scheduled treatment cycles, so they are *likely planned*, not unplanned
returns. We keep cancer (it reflects real complexity) but flag it. We found **no consistent link** between stay
length and readmission in this data.

---

## 6. Can the index find a real problem? (the planted-excess test)
**Idea:** most dashboards never check whether they would notice a real problem. Here we lengthen one hospital's
stays by a known percentage, recompute the index, repeat 2,000 times, and count how often it is caught.
**Flag threshold:** the 95th percentile of the highest hospital's O/E when *nothing* is wrong. That gives a 5% chance
of a false alarm anywhere.

| Planted excess | Hospital-wide problem: caught | Problem in one diagnosis group only: caught at hospital level |
|---|---|---|
| 0% (nothing) | 0.3% (false alarm) | 0.4% |
| 10% | 9.8% | 0.6% |
| 20% | 47.8% | 1.5% |
| 30% | 87.8% | 2.4% |
| 40% | 98.6% | 3.0% |

**What it means**
- A hospital-wide problem needs to add roughly **25 to 30%** to stay lengths before it is flagged reliably.
- A problem confined to **one diagnosis group** is nearly invisible at hospital level, and still hard to see even
  in the hospital x diagnosis view (about 24% caught at +40%), because each cell is small.
- So "no flag" does **not** mean "no problem".

**The numbers on the dashboard:** the hospital flag line is **1.18**; the cell-level flag line is **1.47**
(higher, because cells are smaller and noisier).

---

## 7. The dashboard
| Chart | Question | What it shows |
|---|---|---|
| 1. Hospital O/E dot plot | Is any hospital well above what its case-mix predicts? | 10 dots, reference lines at 1.00 and 1.18. None crosses. |
| 2. Hospital x diagnosis heatmap | Where within hospitals do stays run longer? | 28 cells with 20+ stays; the rest blank. The highest is about 1.20, well below 1.47. |
| 3. Monthly lines | How many patients are admitted and separated each month? | 70 months, about 16 to 47 a month; November 2026 left out (incomplete). |
| 4. Readmissions by diagnosis group | Where do 30-day readmissions come from? | Cancer about 30% (86% of all readmissions), cardiovascular about 4.7%, the rest near 0%. |
| 5. Planted-excess detection | How big a problem can this dashboard catch? | Shows the table in section 6 as a chart, with an 80% line. |

The finished dashboard is published on Tableau Public (link in the README).

**Calculated fields (in Tableau)**
| Field | Formula | Purpose |
|---|---|---|
| Above threshold | `[Oe Ratio] > 1.18` | Colours a hospital orange only if it crosses the flag line |
| Cell O/E | `IF COUNT([Expected Los]) >= 20 THEN SUM(IF NOT ISNULL([Expected Los]) THEN [Los Days] END) / SUM([Expected Los]) END` | O/E for one hospital x diagnosis cell; blank if under 20 stays |
| Hospital (short) | `LEFT([Hospital Name], FIND([Hospital Name], ' ') - 1)` | First word of the hospital name, so headers fit |
| Scored stays | `COUNT([Expected Los])` | How many stays a cell rests on |

**Design rules (from your experience of dense clinical systems):** one screen, no tabs, few controls, colour
reserved for what needs attention, every number shows how many stays it rests on.

---

## 8. What this does NOT show (limits)
- No real patients, no real hospitals, no Queensland data. The Queensland flavour is labels only.
- Peers use diagnosis group and age only, not severity, comorbidities or sex.
- Hospital differences are random, so no hospital is "better" or "worse".
- Planned and unplanned readmissions cannot be separated.
- Only 2,182 stays, so cells are small.
- **Sensitivity checks:** excluding deaths (33 stays) or the longest 1% of stays (17 stays) changes a hospital's O/E by at most 0.015 and 0.067, and still flags no hospital (see `docs/metric_definitions.md`).
- The method is my own design based on common benchmarking ideas; **no official source has been checked yet**
  (a Wednesday task in `docs/TODO.md`).

---

## 9. Mistakes caught along the way (good interview stories)
1. **The empty heatmap.** My first idea for chart 2 (average excess by diagnosis and age) would have shown only
   zeros, because excess sums to zero in every peer group. A sanity check caught it before we built it.
2. **Same-day "readmissions".** About half of the cardiovascular "next admissions" started the same day. Those are
   continuations of care, so we excluded them.
3. **A silent crash.** A line-ending mismatch in a mapping file made a script fail quietly; a safety check that lists
   unmapped diagnoses exposed it.
4. **Median vs mean.** The first version used the median and made every group look like it had excess days.

---

## 10. Questions you might be asked
**Is this real data? Is it Queensland data?** No. It is synthetic (Synthea) with a fictional hospital layer.
The Queensland flavour is in the labels only.

**Why synthetic?** Privacy and ethics. No real patient data should ever be used for a portfolio project.

**What is an O/E ratio?** Observed divided by expected. 1.00 is as expected; 1.20 is 20% longer than expected.

**Why not just compare average stay?** A ward with sicker patients stays longer for good reasons. Comparing each stay
with similar patients adjusts for that.

**Why leave-one-out?** So a stay does not help set its own benchmark.

**Why the mean and not the median?** Stay lengths are skewed. A median benchmark makes nearly every group look like it
has excess days; the mean makes excess add up to zero, which is fair for totals.

**Where do 1.18 and 1.47 come from?** From the planted-excess test: the level the highest hospital (or cell) reaches
5% of the time when nothing is wrong.

**Does the dashboard prove a hospital is worse?** No. Differences here are random by design. In real data, a flag
would be a prompt to investigate, not a verdict.

**Why keep cancer in the readmission view?** Repeat admissions are a real feature of cancer care. They are flagged as
likely planned so they do not distort the comparison.

**What would you change with real data?** Adjust for severity and comorbidity, use proper casemix groups, separate
planned from unplanned readmissions, obtain ethics and governance approval, and validate the method with clinicians.

**What did the planted-excess test teach you?** The index needs about a 25 to 30% rise to flag a hospital-wide problem,
and it can miss a problem concentrated in one diagnosis group. So "no flag" is not proof of "no problem".

**How does this relate to the ieMR?** The ieMR shows each patient's length of stay, but not whether it is longer than
expected for their condition. This adds that comparison. (The ieMR comparison comes from my student-nurse experience,
not from a source I have verified.)

**What were the main ethical considerations?** Synthetic data only, dropped identifiers, no real hospital names, race
not mapped to Indigenous status, and honest labelling of limits.

---

## 11. Glossary
- **Separation:** the end of an admitted episode of care (discharge, transfer or death).
- **LOS:** length of stay in days.
- **Peer group:** stays with the same diagnosis category and age band.
- **Expected LOS:** the average of a stay's peers, excluding the stay itself.
- **Excess days:** actual minus expected.
- **O/E ratio:** observed divided by expected.
- **Leave-one-out:** computing a benchmark without the item being judged.
- **CTE:** a named temporary step inside a SQL query, which makes a long query readable.
- **Window function (LEAD):** looks at the next row for the same patient, used to find the next admission.
- **Censoring:** when follow-up is incomplete (for example, near the end of the data).
- **Synthetic data:** artificial data that looks realistic but describes no real person.
- **Noise band:** how far a value can drift from the truth by chance alone.
- **Planted excess:** a known problem added on purpose to test whether a method detects it.
