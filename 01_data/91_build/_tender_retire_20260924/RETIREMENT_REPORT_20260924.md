# Tender table retirement — report, 24 September 2026

Work order: `04_tools/delegation/CURSOR_WORK_ORDER_UNIVERSE_2026-09-24.md` (rules followed).
Scope: the three readers Block A left behind, all still on the flattened table.

## Before and after, counted from each reader

Measured by `probe_counts.py`, which calls each reader rather than re-implementing it.

| Reader | Before (rows / actionable / R&M) | After | Where it reads now |
|---|---|---|---|
| 1 `scripts/export_tender_pipeline.py` | 708 / **400** / **352** | 619 / **281** / **279** | `modules.tender_feed.load_feed()` |
| 2 `scripts/sync_evidence_derived.py` | 708 / **400** / **352** | 619 / **281** / **279** | same loader, written to `tender_feed.csv` |
| 3 Evidence app tender page (DuckDB) | 708 / **400** / **352** | 619 / **281** / **279** | `evidence-app/data/derived/tender_feed.csv` |
| live feed (truth) | — | 619 / **281** / **279** | `01_data/14_dashboards/tender_data.json` |

Feed date 22 Sep 2026 (`meta.generated_at` 2026-09-22T17:24:26.467020Z).

## The three readers, one at a time

**1. `scripts/export_tender_pipeline.py`.** Now imports `coverage`, `feed_date_label`,
`feed_path`, `load_feed` from `modules.tender_feed`; `SRC` is the feed path. It used to
`pd.read_csv` the old table and re-guess the `actionable` flag itself. The PDF title no
longer says "520 scored notices" — it counts the rows and names the feed date. Run on
today's feed it prints `rows 619 actionable 281 R&M 279` and `value 31, deadline 128,
fleet size 16, outcome 0`; the Excel and PDF both wrote.

**2. `scripts/sync_evidence_derived.py`.** `tender_pipeline.csv` was removed from its copy
list. It now writes `tender_feed.csv` into the app, produced by `load_feed()` — the JSON
is not re-parsed and "actionable" is not re-derived. A short `tender_feed.meta.json`
records the source, feed date and counts. The other 32 mirrors copy as before. Run:
`32 files -> evidence-app/data/derived`, `tender -> tender_feed.csv (619 rows,
281 actionable, 279 R&M, feed 2026-09-22…)`.

**3. The Evidence app tender page.** `sources/prism/tender_pipeline.sql` now reads
`data/derived/tender_feed.csv`. It feeds `pages/tender.md` and the tender block on
`pages/aim-leakage.md`. Both pages carried the old counts in static text and both were
corrected: "520 scored" is gone, the superseded history is stated, and the
"value on 12 of 520 / deadlines on 55" sentence now counts from the file
(value on 31 of 619, deadlines on 128). `npm run sources` built 619 rows; the parquet
under `.evidence/` holds 619 / 281 / 279 / 31 / 128.

## Proof the disagreement is gone

`probe_counts.py --phase before` and `--phase after`, plus a read of the built Evidence
parquet. All three readers and the feed now report 281 actionable and 279 R&M. Nothing
anywhere still reads the 400/352 file.

## Rendered, and read

`shot_evidence_pages.py` (Playwright, system Chrome) loaded both pages and read the text.
The tender page paints 619 Opportunities, €174,564,002 of published value, 281 Actionable,
and the "Superseded" note. The aim-leakage tender block paints 619 / 281 / 46% parts
signal / 45% R&M with the counted sentence beneath it. No error element on either page.
Screenshots: `evidence_tender_full.png`, `evidence_aim-leakage_full.png`.

One defect I introduced and fixed: the first `tender_head` query compared a date column to
`''`, which DuckDB rejected with a conversion error and which blanked the four tiles until
it was corrected to a null check.

## Tests

`pytest tests` in `03_analytics/Isuzu/prism`: **13 failed, 91 passed**, plus the same 1
collection error (`test_fig_key_catalog.py`). The 13 and the collection error are exactly
the pre-existing set the work order named — `test_risk_cockpit_viz` (6),
`test_validate_supersession_epc` (6), `test_ui_links` (1) — so nothing was added. All 20
page smoke tests pass, including `14_Tender_Pipeline.py`.

## Not deleted, not touched

Still on disk: `01_data/00_derived/tender_pipeline.csv`, the app's copy at
`evidence-app/data/derived/tender_pipeline.csv`, and `scripts/build_tender_pipeline.py`.
The retirement is written down in `01_data/00_derived/_SUPERSEDED_tender_pipeline.md`.

Untouched: `modules/tender_feed.py`, `pages/14_Tender_Pipeline.py`,
`modules/advanced_visuals.py` (mtimes 21:01–21:10, Block A's), the pillar board and its
builder, every scheduled task, mail, and publishing.

## Left open

1. `npm install` was run once in the Evidence app — `node_modules` was absent, so the app
   could not be built or rendered without it. No file was added to the repo by it
   (`node_modules` and `.evidence` are gitignored).
2. The same run refreshed the 32 files under `evidence-app/data/derived` from their
   current `01_data` sources. Those mirrors now differ from the 29 May committed copies.
   That is a side effect of the sync, not of the tender change.
3. Nothing else reads the old table: the `tender_pipeline_90d` value in
   `viz/risk_cockpit.json` is a different thing (a 90-day horizon count read from the live
   feed by `build_risk_cockpit_viz.py`), and `ISZE_Commercial_Model_Map.html` links to
   reader 1's own PDF output.
