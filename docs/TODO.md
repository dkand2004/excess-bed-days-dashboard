# To do

## Wednesday: references check (planned)
Goal: back the Project 1 definitions with real sources, and align where an official definition differs.

- [x] Official definition of **length of stay** read in the Queensland QHAPDC Manual 2026-27 (section 3.8.1); same-day convention verified. (METEOR/AIHW pages optional.) (AIHW or similar), including how **same-day stays** are counted.
      Currently we count a same-day stay as 1 day; this is marked "verify before quoting".
- [~] Official analogues read: NSW Health RSI and Victorian Auditor-General (see `docs/references.md`). Queensland Health source still to be obtained.
- [x] Found sources on **observed-to-expected (O/E) ratios** in hospital benchmarking (abstracts read; see `docs/references.md`).
- [ ] Cite only what was actually read. Mark anything unread as unverified.

### How to handle differences
- **Definition differs** (e.g. LOS counting): change our SQL to match, then re-run the pipeline, re-export the CSVs and refresh Tableau.
- **Method differs** (O/E, peers, leave-one-out, minimum group sizes): keep it, and document it honestly as our own design.
- Never claim the dashboard follows an official method unless a source says so.

## Tableau (planned)
- [x] Chart 3: monthly admissions and separations (partial November 2026 month excluded)
- [x] Chart 4: where readmissions come from (by diagnosis group; Cancer labelled "likely planned")
- [x] Chart 5: planted-excess "how much to trust this" chart
- [x] Assemble the dashboard (note: five diagnosis groups have no hospital cell with 20+ stays)
- [x] Published to Tableau Public; link added to the README
- [x] Added `tableau/dashboard.png` and showed it in the README

## Learning guide (requested by the owner)
- [x] (First full version written) `docs/how_it_works.md`: a plain-language teaching guide to Project 1 (pipeline, O/E ratio with a worked example, readmission logic, planted-excess test, calculated fields, limits, likely questions with answers, glossary), so the owner can answer questions about it. **Keep it updated after each milestone** (add charts 3 to 5, any definition changes from the Wednesday references check).

## Demo video (stretch, only if time allows)
- [ ] One short video (about 3 minutes) for ONE scenario: a manager asks whether one hospital keeps patients too long. Show chart 1 (nothing flagged), explain the threshold, drill into chart 2, then show what the planted-excess test says a real problem would look like.
- Synthetic data only; no real hospital names; do not show `.env` or any key.
