# PR 71 fix list — delivery basis (diagnose only, 7 Oct 2026)

PR: https://github.com/jeromio1987/ISZE/pull/71  
Head: `cursor/2026-10-07-universe-u29-b-delivery-basis`  
This note does **not** merge anything.

## What was wrong before

| Fact | Detail |
|---|---|
| Old base | `cursor/2026-10-07-universe-u26-market-harvest` |
| GitHub said | `CONFLICTING` against that base |
| Earlier cherry-pick onto main | Aborted — modify/delete fights on coverage CSVs / parsers that exist on the U26 stack but not on older main |

## What we measured today (trial merge, then aborted)

Trial: merge head of PR 71 into a throwaway worktree at current `origin/main` (`3af2f752`, after PRs 70/72/73/74).

| Check | Result |
|---|---|
| Text conflicts (`git diff --diff-filter=U`) | **None** |
| Merge exit | **0** (clean apply) |
| Size | **631 files**, ~635k insertions — mostly U26 scrape cache under `01_data/90_INBOX/scrape_targets/_probe/` |

So the “conflict” was largely **wrong base**, not a broken delivery-basis patch. After retargeting the PR base to **`main`**, GitHub’s `mergeable` flag may flip to MERGEABLE (recomputed after the edit).

## Why you still should not smash-merge in one click

Even if GitHub says MERGEABLE:

1. **Eligible stays 0** after this land — pages do not state delivery (see `UNIVERSE_U29B_LEDGER_VERIFY_2026-10-07.md`).
2. The PR carries the **whole U26 harvest tree** (HTML cache, probes), not only the small ledger schema change. That is hard to revert and noisy in git history.
3. `price_observations.parquet` is often gitignored — meta/CSV may land without the parquet binary. Rebuild step needed on a machine that has the raw inputs.

## Recommended next pieces (small, in order)

Do these as separate goes so a break is easy to spot.

### Piece A — code-only land (preferred) — OPENED

PR **75**: https://github.com/jeromio1987/ISZE/pull/75  
Branch `cursor/2026-10-07-universe-u29b-pieceA-code` · commit `ab90287e` · **12 files**, no scrape cache.

Checked on the worktree before push:

- `_selftest_schema.py`: SELFTEST PASS
- `_u29b_mutation.py`: eligible 0 → 8 → 7

Not merged until Jerome says merge. Eligible on real UK pages still **0**.

### Piece B — coverage artefacts only — MERGED

PR **76**: https://github.com/jeromio1987/ISZE/pull/76 · merge `545f1a02`.  
6 files: `market_data_gap_coverage_20261007.*`, empty-PNs CSV, `u26_gaps_table_20261007.*`. Eligible still **0**.

### Piece C — scrape cache (optional / local only) — NOT DONE

Keep probe HTML on the machine or in inbox; do **not** force it through `main` unless you explicitly want that bulk.

### Piece D — close PR 71 — DONE

PR **71** closed 7 Oct with pointer to PR 75.

## Do not do next

- Infer delivery/tax from country or site defaults.
- A third Portugal automated sweep (Portugal stays insufficient).
- Claim MARKET-DATA-GAP closed — eligible is still 0 until pages state a basis.

### Piece E — IDS real feed (ITUK + I-Motors) — MERGED

PR **77**: https://github.com/jeromio1987/ISZE/pull/77 · merge `7d2c1630`.
Ferndown 221 answers; Astara Lisboa 194 answers on INTERNAL CONNECT-01.

