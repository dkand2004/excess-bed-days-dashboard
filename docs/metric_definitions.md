# Metric definitions

| Term | Definition |
|---|---|
| **Separation** | End of an admitted episode of care (Australian term for discharge). |
| **LOS (days)** | Separation date minus admission date; a same-day stay counts as 1 day. *(Common Australian convention; verify before quoting.)* |
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
