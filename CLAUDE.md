# Instructions for Claude Code (excess-bed-days-dashboard)

## Git rules
- **Do not add attribution lines** to commit messages or pull request descriptions: no `Co-Authored-By`,
  no `Claude-Session`, no "Generated with Claude Code". Write the message and stop.
- Commit as the identity already configured in this repo. Do not change `user.name` or `user.email`.
- Never force-push or rewrite history unless the owner explicitly asks.
- **Before every push:** confirm `.env`, raw data (`data/raw/*`) and `*.duckdb` are not tracked, and scan staged files for keys or tokens.

## Data and privacy
- All data is **synthetic** (Synthea, with a fictional hospital layer). Never add real patient data, real names or real hospital data.
- Raw data stays out of Git; regenerate it from the documented command. Small processed tables in `data/processed/` are committed.

## Working style (the owner is a student and still learning)
- Explain what you are about to do and why, and summarise afterwards. Define new terms in plain language.
- Do not make design, tooling or naming decisions silently: present options, recommend one, and wait for the answer.
- Go step by step; keep the project a small-scale prototype.
- Comments in code should explain *why*, not only *what*.

## Project facts worth knowing
- Pipeline: `src/australianise.py` then `sql/01_expected_los.sql`, `sql/02_readmissions.sql`, then `src/export_tables.py`.
- Metric choices (leave-one-out mean, O/E ratio, minimum peer group 10) are documented in `docs/metric_definitions.md`. Do not change them without discussion.
- Hospital differences are random by design; never describe hospitals as better or worse.
