# Planted-excess validation

**Question:** if a hospital really did keep patients longer than expected, would the O/E index notice?

**Method** (`src/planted_excess_test.py`, seed 42, 2,000 repeats per setting): stays are randomly
assigned to 10 hospitals; one hospital's stays are lengthened by a known percentage; the O/E index
is recomputed (same leave-one-out method). The flag threshold is the 95th percentile of the
*highest* O/E across all hospitals when nothing is planted, so a false alarm anywhere has a 5% chance.
Planted lengths are fractional days so small effects are not lost to rounding.

## Results (data: 2,182 stays, 2021 onward)
| Planted excess | Hospital-wide: detected | One category only (Cardiovascular): flagged at hospital level | ...flagged at hospital x category level |
|---|---|---|---|
| 0% (nothing) | 0.3% (false alarm) | 0.4% | 0.2% |
| 10% | 9.8% | 0.6% | 2.2% |
| 20% | 47.8% | 1.5% | 6.0% |
| 30% | 87.8% | 2.4% | 14.2% |
| 40% | 98.6% | 3.0% | 23.5% |

## What it means
- A **hospital-wide** problem needs to add roughly **25-30% to stay lengths** before the index flags it
  reliably (about 80% or more of the time). Smaller problems are usually missed.
- A problem **concentrated in one diagnosis category** is almost invisible at hospital level (3% even at +40%)
  and hard to see even when drilling into hospital x category (24% at +40%), because each cell has few stays.
- **Therefore:** a "no flag" result does **not** mean "no problem". The dashboard should show how
  much data each number rests on, and the README must not claim the index finds all problems.

## Limits
Synthetic data; random assignment; one planting pattern per scenario; fixed thresholds; results depend on sample size.
