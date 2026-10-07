# U26 / C2 — second-day Spareto reading + corroboration arithmetic

Branch `cursor/2026-10-07-universe-u26-market-harvest`. Writes only inside `_u26/C2/`.
Nothing shared was touched (no `crossref_graded.csv`, no `spareto_crossref.csv`, no ledger,
no `page_manifest.csv`).

## Step 1 — dated second pass

- Waited until C1 finished: `u26_c1_spareto_20261007`, 123/123 `ok`, finished 2026-10-07T02:41:00Z.
- My pass label: **`u26_c2_spareto_20261008`** (first candidate; its cache held 0 files at start,
  so pages were genuinely re-read, not replayed from C1's cache).
- My pass: 123/123 `ok`, 2026-10-07T02:42:05Z → 02:48:27Z, 0 refusals, 0 challenges, no 403/429.
- Fetcher: `fetch_polite.PoliteFetcher` via `run_dated_pass.PassFetcher` (consent gate first,
  >= 2.2 s/host, stop on 403/429 or bot challenge). Bot identity unchanged.
- **Day gap: 0.** C1 finished 02:41Z and my pass started 02:42Z on the same UTC date
  (2026-10-07), ~8 minutes apart — not a calendar day. The label was kept as the brief named it.
  A same-day second reading cannot show price movement; it can only show that Spareto's listing
  is stable, which it is.

## Step 2 — corroboration arithmetic (measurement only)

Independent sources are **pipelines** (Eucon, Spareto). C1 and C2 are two readings of ONE source
and count as day stability, never as two witnesses. Eucon-only grading was re-run here and
reconciles to the committed file: **0 tier mismatches of 6455 rows**.

| question | result |
|---|---|
| of 123 numbers with >= 1 Spareto brand pair | **69** |
| of the 112 no-Eucon-crossref with >= 1 pair | **58** |
| ... single-source only (stays CANDIDATE) | **54** |
| ... with >= 1 corroborated pair (2 sources) | **4** |
| Spareto pairs on the 123 | **735** |
| ... corroborated by a 2nd independent source | **156** |
| ... of the 112 | **13** |
| ... single-source pairs (stay candidates) | **579** |
| ... would move an existing Eucon edge up one step (brand agrees) | **155** |
| new pairs not in the graph (merge adds as doubtful) | **579** (546 of the 112) |

Day stability: 735 pairs on both days, 0 on one day only, 0 brand changes between days.

Context of the 112: 5 still carry Eucon UK IAM survey edges in the graph; 0 have 2+ Eucon source
files. So the 112 are "no Eucon Online 2025 cross-reference", not zero-Eucon-evidence.

**A pair from one source stays a candidate.** 579 of the 735 Spareto pairs are Spareto-only and
never move a grade; 155 move an existing Eucon edge up because a second independent source
(the Eucon graph) claims the same pair under an agreeing brand.

## Could not do

- The second reading is ~8 minutes after C1's, not a calendar day later (C1's pass landed at 02:41Z
  and Spareto must not be hit in parallel with C1).
- With only two pipelines (Eucon, Spareto), a number that has a Spareto pair but no Eucon edge
  can never reach two sources in this pass, so 54 of the 58 stay single-source CANDIDATE by
  construction.
