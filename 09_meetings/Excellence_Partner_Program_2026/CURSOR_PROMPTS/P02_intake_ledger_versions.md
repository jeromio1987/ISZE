# P02 — Intake, ledger, versioning, normalisation

> Read `00_START_HERE.md` first. Needs P01. Plan mode, then build.

## Goal
Receive a file from a drop folder, store it immutably, validate it with P01, record its state in a ledger, mark the active version, and — only if it passes — normalise it into the canonical long format that the rest of ISZE already reads.

## Why
Corrections must be visible and reversible, history must never be overwritten, and a rejected file must never leak into the numbers. The ledger is the single answer to "what did we receive, and what is active".

## Read first
Spec §3 (architecture), §6 (lifecycle and ledger). `DEALER_SELL_OUT.md` (canonical long schema, flags, rollup grain rule). `dealer_sales_loader.py` (`load_sellout_long_pn`, the year-grain rule). One adapter in `01_data/91_build/` for the output shape.

## Build
Add to `04_tools/partner_intake/`: `intake.py`, `registry.py` (ledger on parquet, atomic writes), `normalise.py`, CLI commands `ingest`, `status`, `accept`, `history`.
- Drop: `01_data/90_INBOX/partner_intake/<DB>/`. Raw copy: `01_data/12_raw/dealer_sales/<DB>/<period>/<name>__v<n>.<ext>` (immutable, read-only after write). Never delete or edit a raw file.
- States: RECEIVED → VALIDATED_PASS | VALIDATED_FAIL → ACCEPTED → SUPERSEDED. SHA-256 per file; identical re-import adds nothing and creates no version.
- A new version of the same distributor and period supersedes the previous accepted one. The receipt lists which downstream results changed.
- Normalise to `01_data/00_derived/dealer_sellout_long_<DB>_CY<yyyy>.csv` using the existing columns exactly (`distributor_code, source_file, grain, year, period, period_grain, part_number, part_number_raw, description, qty, dealer_name, vehicle_scope, flags`). `grain` is `dealer_pn` when per-dealer detail exists, else `network_pn`. Set `partial_year` for a year in progress.
- **Do not modify the existing loader or the existing adapters.** If you find a defect (the `ytd` rollup grain mismatch is a known latent one, see the docstring of the Romania adapter), report it; do not fix it silently.
- Ledger columns as in spec §6. Every state change writes an audit line (who, when, what, why).

## Acceptance tests
1. Ingest the same file twice → one ledger row, no second version.
2. Ingest a corrected file for the same period → v2 ACCEPTED, v1 SUPERSEDED, v1 still on disk, receipt lists changed totals.
3. A failing file never appears in the canonical long CSV.
4. After normalising twelve synthetic months, `load_sellout_long_pn` returns the year totals once (no double count of year plus months).
5. UTI and UMI drops never write into the same long file.
6. Ledger survives a crash between copy and validate (re-run completes without a duplicate).
7. `history <DB> <period>` prints the full chain.
8. PRISM suite still passes; no existing derived file changed byte for byte when ingesting only synthetic data into a temp root.

## Constraints
Use a temp ISZE root in tests (copy of the needed folder skeleton), never the real `01_data`. Git-ignored folders stay ignored.

## Return packet
As in `00_START_HERE.md`, plus a diagram of the state machine as implemented.
