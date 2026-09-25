# SUPERSEDED — `01_data/00_derived/tender_pipeline.csv`

**Status:** retired. Nothing reads this file any more. It is kept on disk on purpose and
must not be deleted.

## What it was

A flattened table of scored public-tender opportunities, built by
`03_analytics/Isuzu/prism/scripts/build_tender_pipeline.py` and last written on
**29 May 2026** (708 data rows, 255,643 bytes).

## Date it stopped being read

**24 September 2026.** On that date the three remaining readers were pointed at the
weekly live tender feed instead.

## What replaced it

`01_data/14_dashboards/tender_data.json` — the feed written weekly by the *ISZE Tender
Monitor* task (last generated 2026-09-22T17:24:26Z, 619 rows under `opportunities`).
There is exactly one reader of it: `03_analytics/Isuzu/prism/modules/tender_feed.py`,
function `load_feed()`. PRISM's Tender Pipeline page, the PRISM tender charts, the
Evidence app's tender page, `scripts/export_tender_pipeline.py` and
`scripts/sync_evidence_derived.py` all go through it.

## Why: the counts disagree

These are the same two words, counted off two different files. The live feed is correct;
this one is six weeks behind it and predates the June feed changes.

| File | Rows | Actionable | R&M contracts |
|---|---|---|---|
| `tender_pipeline.csv` (this file, superseded) | 708 | **400** | **352** |
| `tender_data.json` (live feed, correct) | 619 | **281** | **279** |

"Actionable" means the decision is Attack, Selective or Watch. Do not quote 400 or 352
as a current figure.

## The three readers that were repointed

1. `03_analytics/Isuzu/prism/scripts/export_tender_pipeline.py` — the Excel and PDF it writes.
2. `03_analytics/Isuzu/prism/scripts/sync_evidence_derived.py` — no longer copies this
   file into the Evidence app; it writes the live feed there instead.
3. The Evidence app's tender page — `evidence-app/sources/prism/tender_pipeline.sql`
   (used by `evidence-app/pages/tender.md` and `evidence-app/pages/aim-leakage.md`),
   now reading `evidence-app/data/derived/tender_feed.csv`.

## Not to be confused with

`tender_pipeline_90d` in `01_data/14_dashboards/viz/risk_cockpit.json` is a different
thing — a count of tenders inside a 90-day horizon, read from the live feed by
`scripts/build_risk_cockpit_viz.py`. It is unrelated to this table.
