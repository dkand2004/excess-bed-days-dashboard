# To do

## Wednesday: references check (planned)
Goal: back the Project 1 definitions with real sources, and align where an official definition differs.

- [ ] Find and read the official definition of **length of stay** (AIHW or similar), including how **same-day stays** are counted.
      Currently we count a same-day stay as 1 day; this is marked "verify before quoting".
- [ ] Find a source on how **Queensland Health / Hospital and Health Services** measure and compare stay length.
- [ ] Find a source on **observed-to-expected (O/E) ratios** in hospital benchmarking.
- [ ] Cite only what was actually read. Mark anything unread as unverified.

### How to handle differences
- **Definition differs** (e.g. LOS counting): change our SQL to match, then re-run the pipeline, re-export the CSVs and refresh Tableau.
- **Method differs** (O/E, peers, leave-one-out, minimum group sizes): keep it, and document it honestly as our own design.
- Never claim the dashboard follows an official method unless a source says so.

## Tableau (planned)
- [ ] Chart 3: monthly admissions and separations (mark the partial November 2026 month)
- [ ] Chart 4: 30-day readmission by stay band (Cancer labelled "likely planned")
- [ ] Chart 5: planted-excess "how much to trust this" table
- [ ] Assemble the dashboard (note: five diagnosis groups have no hospital cell with 20+ stays)
- [ ] Publish, screenshot, add the link to the README
