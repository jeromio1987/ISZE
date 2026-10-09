# P08 — Dealer identity table

> Read `00_START_HERE.md` first. Needs P02. Plan mode, then build.

## Goal
A table that says which dealer is which across sources: the name in the sales-to-dealer file, the name in IDS, and, where it exists, the SAP customer number. Matching is **proposed**, never auto-approved.

## Why
Without it, per-dealer sell-through is impossible (65,619 rows read "not computable at dealer grain") and IDS cannot be joined to sales. ITUK 2025: 64 names in the sales file, 44 in IDS; 16 match exactly, about 34 overlap strongly, about 20 have no plausible match. Sales names carry branch suffixes that IDS splits into separate rows.

## Read first
Spec §13. `Isuzu Universe/01_Strategy/UNIVERSE_PILOT_EVIDENCE_PACK_2026-09-21.md` §3–§4 and §8. `01_data/00_derived/dealer_sellout_long_ITUK_CY2025.csv`; IDS report inputs under `01_data/08_Distributor/IDS_2026/` (read through the existing report outputs and payloads, not the raw dealer files).

## Build
`04_tools/partner_intake/identity.py`, table `dealer_identity.parquet` (+ CSV) with the columns in spec §13, CLI `identity propose|review|approve|history`.
- Normalise names (case, punctuation, legal suffixes, branch words); score with a transparent method (token overlap plus an edit-distance measure); write top candidates with their score and the reason.
- Three outcomes only: `EXACT`, `CANDIDATE` (needs a person), `NO_MATCH`. Approval is a separate command that records approver and date; history is append-only (rename, merge, close, transfer).
- A review queue CSV for Jerome: one row per candidate with both names side by side.
- Never fabricate an identifier. Where a dealer has several sites, keep them separate and say so.

## Acceptance tests
1. On the ITUK 2025 file against the IDS list: 16 `EXACT` (assert the count), the rest `CANDIDATE` or `NO_MATCH`, none auto-approved.
2. A renamed dealer keeps its id; the old name stays in history.
3. Approval without an approver name fails.
4. No dealer-level euro or fleet figure is derived from a national total anywhere.
5. Real names stay in git-ignored output folders; tests use synthetic names.

## Return packet
Counts per outcome, the review queue location, three hardest cases with the reasoning.
