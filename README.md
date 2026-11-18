# Excess Bed-Days Dashboard: EMR Analytics

> Synthetic-EMR patient flow dashboard (SQL, Python, Tableau) measuring how much longer patients stay than peers with similar conditions.

**Status:** 🚧 In progress (started 18 Nov 2026).

## The healthcare problem
_To be written: why unexplained long stays matter (bed access, discharge delays, patient flow)._

## What this project does
- Builds an **excess length-of-stay index**: actual stay vs. the expected stay for peers with the same condition and age band.
- Adds a **readmission link**: do patients with excess stays return within 30 days more often?
- Presents results in a Tableau Public dashboard.

## Tech
SQL (DuckDB), Python (pandas), Tableau Public.

## Data, privacy and ethics
- **All data is synthetic** (generated with [Synthea](https://synthetichealth.github.io/synthea/)). No real patient data is used or included.
- Raw data is not committed; see _How to reproduce_ (to be written).
- Findings describe a **method**. Synthetic data does not reflect real hospital performance.

## Repo structure
| Folder | Purpose |
|---|---|
| `sql/` | Numbered SQL queries |
| `notebooks/` | Exploration and sanity checks |
| `src/` | Load and export scripts |
| `data/processed/` | Small cleaned tables used by Tableau |
| `tableau/` | Dashboard screenshot and link |
| `docs/` | Clinical context, metric definitions, ethics |

## How to reproduce
_To be written._

## Licence
MIT, see [LICENSE](LICENSE).
