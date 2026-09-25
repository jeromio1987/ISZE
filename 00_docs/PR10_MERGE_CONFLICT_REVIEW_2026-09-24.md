# PR #10 — merge conflict review (branch vs `main`)

Read-only review. Date 2026-09-24. Done in a throwaway worktree; nothing was committed or pushed.

**PR:** [#10 Sync two weeks of dashboard, IDS, pricing and analysis work](https://github.com/jeromio1987/ISZE/pull/10)
**Base:** `main` @ `87c7907b` — **Head:** `cursor/isze-exec-sales-paper-prompt-8dc1` @ `132068d1`
**Merge base:** `e9edb8c6` (2026-09-16). Branch is 29 commits ahead, 56 behind.
**Conflicted paths: 86.** Both refs were fetched fresh before this review.

## Verdict

**85 of the 86 are not simple conflicts.** Each side holds content the other does not; on only one
path is the resolution mechanical.

The branch and `main` have both moved independently since the merge base, in both cases by a lot.
Neither side is uniformly the newer one. On `pr00_classification.csv` the branch changes 3,556 lines
against `main`'s 158; on other files `main` holds additions the branch lacks. So there is no safe
blanket rule ("take ours" / "take theirs") for this pair.

## Counts

| Class | Count | Note |
|---|---|---|
| Line endings only | 1 | `monday_pn_opportunity_crosswalk_20260914.csv`, add/add, identical text, CRLF vs LF |
| Binary | 1 | `parts_catalog_dimension.parquet` |
| Generated artefact, both sides differ | 68 | HTML / CSV / JSON |
| Hand-written source, both sides differ | 16 | docs, rules, Python |
| **Total** | **86** | |

**No file is a one-sided superset.** For all 86, both `branch-only` and `main-only` content is
non-empty, so neither "ours" nor "theirs" can be taken wholesale.

How far apart the two tips are overall (blob-by-blob, whole tree):

| | files |
|---|---|
| identical content | 4,032 |
| differing content | 617 |
| present only on the branch | 5,007 |
| present only on `main` | 1,360 |

## Complicating factors

### 1. The markers are the "both added" form
`<<<<<<< HEAD` / `=======` / `>>>>>>> origin/main`, with **no `|||||||` base block**. The merge base
does not contain these files, so there is no ancestor text to three-way merge against. Every hunk has
to be decided on intent. This is also why git cannot auto-resolve any of them.

### 2. `main` would re-introduce raw line-level billing, against a written rule
The most serious item, and it is verified in bytes, not inferred.

- Branch commit `96724527` — *"Untrack raw billing, the Data mirror and render intermediates"* —
  untracked `03_analytics/Isuzu/prism/data/sales_detailed_for_claude_full_fixed.tsv`.
- That file is **still tracked on `main`**: 45,824,574 bytes.
- Its header is `sold_to, billing_date, part_number, description, billed_qty, net_sales_value, year`
  and the first row is `UNIVERSAL MOTORS ISRAEL LTD, 22/07/2025, 7552221470, RESISTOR; BLOWER UNIT, 4, 48.32, 2025`.
  That is dealer-level billing, per part number.
- The branch's `.gitignore` states the reason: the exception "was re-including line-level billing
  (44 MB of sold_to / billing_date / part_number / net_sales_value rows) into git. ISZE policy is
  never to commit raw billing."
- `AGENTS.md` carries the same rule: never commit or paste `01_data/raw/sales/*` line-level billing.
- `main` also re-adds `!data/sap_sold_to_mapping.csv` and `!data/fig_key_pn_overrides.csv`. Both of
  those are tracked on *both* sides, so the gap is inconsistent either way — an exception list that
  also white-lists the billing TSV conflicts with the stated policy.

**Merging `main` in as-is would put raw billing back on this branch.** Only Jerome can settle it.

### 3. `main` carries wording that a standing rule bans (4 hunks)
Where `main`'s side uses a term the workspace rules forbid and the branch's side does not:

| File | Main side contains | Rule |
|---|---|---|
| `AGENTS.md` | "not sell-out or markup factors" | `isze-spoken-labels.mdc` — sell-out is banned |
| `INDEX.md` | "Exec aftersales paper (Mode A HTML)" | Mode A/B banned as an audience label |
| `04_tools/db_sales_review/build_full_deck.py` | "so Mode A never plots a GPS percentage" | same |
| `04_tools/ids_dealer_ranking/build_ids_country_packs_v13.py` | "Mode A colleague pack" | same |

The branch is the corrected side in all four. `AGENTS.md` and `INDEX.md` each also have a second
hunk that is **already resolved**: `main` holds the old and the new line as duplicates, the branch
holds the new line once. Those two hunks are clean; the four above are not.

### 4. Two independent rewrites of the same tool
`04_tools/spa_application/build_spa_application.py` — **53 hunks**, the worst file by far.

Both sides built this app separately: `main` is 938 lines, the branch is 2,494. The two commits
`f49be3f9` and `514d5ee4` exist on the branch *and* an identically-titled pair exists on `main`, so
the same work was authored twice rather than one side extending the other. The function sets have
diverged, not just the bodies — `main` has `patch_form`, `recalc_and_check`, `write_waterfall_csv`,
`main`; the branch has `remap_optimizer_columns`, `write_ladder_note`, `build_pending_sheet`,
`load_line_context`, `_bottom_line_checks`. Not mergeable hunk by hunk: one implementation has to be
chosen and the other's improvements ported by hand.

### 5. Resolution order is not free
The two sides changed the same generated files against the same base, in opposite directions. One
concrete example: `01_data/00_derived/dealer_sellout_aim_mix_2025.csv` is 70 lines on the branch and
6 on `main`; the branch's extra row is **PORTUGAL**, and the base had neither Portugal nor ITUK.

So data additions must be **unioned** and then re-measured, not chosen. `main` is the line that has
been through review and carries the corrected FY wording, which makes it the sensible base — with
the branch's Portugal row and similar additions carried onto it. Deciding that file by file is a
judgement about which numbers are current, not a text merge.

### 6. 42 of the 86 conflicts are one IDS page set
They sit under `02_dashboards/ids/` (and its archived copy). The same pages also exist as copies
under `01_data/08_Distributor/IDS_2026/` and `02_dashboards/Data/…`, which are in the conflict list
too. Each copy must resolve to identical content or the set goes internally inconsistent. The two
sides also differ on how the map basemap works (branch: Leaflet + online tiles; `main`: bundled,
offline, no external tile service) — a behavioural difference, not a formatting one.

## What I did

- Fetched `origin`; both the PR branch and `main` were already current. The checkout **was already**
  the PR head, so no checkout was needed.
- Enumerated conflicts read-only with `git merge-tree --write-tree`.
- Ran a real `git merge --no-commit` in a throwaway worktree at
  `Desktop\claude\ISZE_pr10_conflict_merge` placed on a **detached** HEAD, read the conflicted content
  there, then `git merge --abort` and removed the worktree.
- **Nothing committed, nothing pushed, no markers resolved.** HEAD is still `132068d1`; PR #10 is
  still `OPEN` / `CONFLICTING` / `DIRTY` with `headRefOid 132068d1`.
- Jerome's 139 uncommitted files were never at risk: no uncommitted path is also a conflicted path,
  and no incoming path from `main` is an untracked file on disk (0 collisions).

## The one thing safe to fix mechanically

`01_data/00_derived/monday_pn_opportunity_crosswalk_20260914.csv` — both sides added an identical
file; only the line endings differ (41 lines, add/add). Either side is fine.

## Recommendation

Do not merge this branch into `main` as it stands. `main` is the reviewed line and holds the
corrected wording in four places; a merge would either revert those corrections or force 86 hand
decisions with no base to arbitrate from, including two that are policy questions rather than
merge questions:

1. the raw-billing file (factor 2) — merge would undo a stated policy; and
2. which SPA builder survives (factor 4).

The strategic call is whether this branch should be merged at all, or retired in favour of the line
already on `main` with the branch's genuinely new material (the Portugal sell-out row, the AIM
tiers, the pricing work) pulled across deliberately.

## Evidence files (read-only, newly written)

- `01_data/91_build/_pr10_conflict_detail.py` — per-file size and conflict shape
- `01_data/91_build/_pr10_classify.py` — superset analysis (proves no one-sided files)
- `01_data/91_build/_pr10_trivial.py` — identical / EOL-only / whitespace-only detection
- `01_data/91_build/_pr10_rule_hunks.py` → `_pr10_rule_hunks.txt` — rule-decided hunks
- `01_data/91_build/_pr10_src_hunks.py` → `_pr10_src_hunks.txt` — every source-file hunk
- `01_data/91_build/_pr10_gen_delta.py` → `_pr10_gen_delta.txt` — generated-file line deltas
