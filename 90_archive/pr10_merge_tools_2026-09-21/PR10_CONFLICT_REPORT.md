# PR 10 — merge conflict resolution

**Prepared:** 2026-09-21
**Pull request:** https://github.com/jeromio1987/ISZE/pull/10
**Branch:** `cursor/isze-exec-sales-paper-prompt-8dc1` → base `main`
**Worktree used:** `C:\Users\jerom\Desktop\claude\ISZE_worktree_pr10` (separate, detached)

**Status: merge staged in the worktree, NOT committed, NOT pushed. The pull request was not touched.**

---

## 1. `gh pr view 10` output (verbatim)

```
{"baseRefName":"main","files":null,"headRefName":"cursor/isze-exec-sales-paper-prompt-8dc1",
 "mergeStateStatus":"DIRTY","mergeable":"CONFLICTING",
 "title":"Sync two weeks of dashboard, IDS, pricing and analysis work",
 "url":"https://github.com/jeromio1987/ISZE/pull/10"}
```

PR body says it sweeps two weeks of uncommitted work into the repo — 4,363 files, 3,838 added,
521 modified, 4 deleted. Its own "worth flagging" list includes an explicit warning about the
GPT-safe pack being included.

## 2. Merge base and divergence

```
merge base = e9edb8c6ddb463b6984ef0e3571ea0948c40911b
main ahead of base: 56 commits, 211 files changed
PR ahead of base:    6 commits, 4248 files changed
overlapping files changed on both sides: 113
```

`main` advanced by merging PRs #1, #3 and #8, which carry overlapping work. 75 files conflicted.

## 3. Conflict table

### Complicating factors — reported, NOT resolved

These are the ones where resolving either way would silently undo a deliberate decision, or where
the two sides carry different numbers or different instructions for the same thing.

| File | Type | What each side intended | Why it is a complicating factor | Resolution |
|---|---|---|---|---|
| `01_data/00_derived/pr00_classification.csv` | data, 52 hunks | PR: two weeks of reclassification (5,194 rows changed). Main: `7b4baa3` "Fill 158 empty PR-00 fig-keys from IE40" | The two sides hold **different classifications for the same part numbers** (e.g. `1096752290` = "Competitive parts / Air hose" on the PR vs "Hardware & consumables / Bolt" on main). PR has 3,522 empty fig-keys, main 3,508 — dropping main's version **silently reverses the documented 158-key fill** | **Reported, not resolved.** Took main's version as the interim state so the merge completes; the PR's 5,194-row reclassification is now silently dropped and needs a decision |
| `01_data/00_derived/dealer_sellout_aim_mix_2025.csv` | data | PR: 69 rows of real dealer-level sell-out. Main: `e99f16b` rebuilt to 5 network-aggregate rows | Same measure, **different rows and different totals**: PR has 68 dealer rows + Portugal; main has 5 aggregates including `ITUK 145,791` where the PR has no ITUK aggregate at all | **Reported, not resolved.** Took main's version |
| `01_data/00_derived/dealer_sellout_gps_2025.csv` | data | as above | Same conflict plus the GPS columns | **Reported, not resolved.** Took main's version |
| `01_data/00_derived/sellout_aim_by_*_2025.csv` (aim_l1, pms, subgroup, top_pn, network_mix) | data | Both regenerated the AIM/PMS mix, PR with Portugal added | `sellout_aim_by_pms` and `by_subgroup` are **strict supersets on the PR side** (Portugal only). `by_aim_l1` and `top_pn` **both diverge**, and common rows carry different quantities (GREECE Wheels Hub qty 813 PR vs 827 main) | **Reported, not resolved.** Took main's version for all five |
| `01_data/00_derived/price_elasticity_db_dlr_network.csv`, `..._ituk_uti.csv` | data | Main: `178828a` "Fix sales-to-dealer annual qty: use the year total only". PR: full sample | Main's fix is in the sample size itself (IUK `n_pns` 56 → 52, `sellout_qty_total` 16,136 → 15,852). **Restoring the PR numbers would undo an annualisation correction** | **Reported, not resolved.** Took main's version |
| `01_data/00_derived/replenishment_exceptions_cy2025.csv`, `revision_exception_queue.csv` | data | Same sources on both sides | Both carry rows the other lacks (14,336 each way in the exception queue), so neither is the newer regeneration. Changed values on common keys (planned SP % 13.761 vs 12.843) | **Reported, not resolved.** Took main's version |
| `01_data/00_derived/db_dlr_commercial_stack.meta.json` | metadata | PR: `bridge_rows` 84,826 / `dealer_rows` 65,619. Main: 80,219 / **0** | Main deliberately reads **zero dealer rows**; the PR's 65,619 dealer rows are exactly the sell-out grain main de-scoped | **Reported, not resolved.** Took main's version |
| `00_docs/ISZE_OS_DATA_MAP.yaml` | doc, 1 hunk | PR: `artefact: pn_coverage_classification.csv` + grain/market/geo/entity. Main: `ask: Get a list price on the money (cabs first)` + `artefact: NO_PR00_HARDWARE_FY2026.md` | **Two different instructions and two different files.** `NO_PR00_HARDWARE_FY2026.md` does not exist on the PR branch. The YAML schema later in the same file *does* use the PR's six keys, so the PR's shape is the live convention — but main's change is a deliberate retarget of the ask | **Reported, not resolved.** Kept the PR's block |
| `03_analytics/Isuzu/prism/CHANGELOG.md` | doc | PR: 2026-09-17/18 entries (LD split, NON_PARTS leak, parts-base bridge). Main: one 2026-09-14 entry | Different dates and subjects, not a superset — **taking either side drops that side's documented fixes** | **Reported, not resolved.** Kept both, newest first |
| `00_docs/agent/STATE_PACKET.md` | doc | PR: 2026-09-19/20 log (508 lines). Main: the 2026-09-14 built/snapshot/open list (37 lines) | The PR's replacement **drops main's whole factual snapshot** (Nordics keys DONE, 23,236 open, SaTy 92.9%, ES PLACSP LIVE, Decision pack not applied) — several of which are flagged elsewhere as never-re-ask | **Reported, not resolved.** Kept the PR's log and restored main's snapshot as labelled sections |
| `04_tools/db_sales_review/build_full_deck.py` | code | Main adds a `skip_gps_pct` branch that **suppresses the GPS percentage when capture is over 100%** (Ireland-class). PR keeps the plain two-line fiscal-year chart | Main's change is the guard the PR's version would silently remove; the PR has no equivalent branch to compose with | **Reported, not resolved.** Took main's version |
| `03_analytics/Isuzu/prism/scripts/build_dealer_sellout_aim_gps.py` | code | Main rewrote the page to the "sales to dealer" wording. PR uses the banned words *sell-out* and *AIM* | The PR's wording **reintroduces "sell-out"**, which is banned in anything Jerome opens. Composing is a reword of a whole page, not a merge | **Reported, not resolved.** Took main's version |
| `04_tools/ISZE_Tender_Monitor_Install/_source_health.json` | data | PR: Spain "WAF-denied". Main: `b427d22` "Mark Spain PLACSP Atom live and correct hub tender coverage" | **Direct contradiction of the same source's state.** Main's correction came from a live 200; the PR's note is older | **Reported, not resolved.** Took main's version |
| `01_data/00_derived/action_ledger_open.csv` | data | Main: `ca0fa9b` seeds 5 rows to TRIAGED. PR: full regeneration | The PR **downgrades all five back to NEW** — it would silently undo a deliberate triage decision. The CSV header also differs (the PR adds a `builder_state` column) | **Reported, not resolved.** Took main's version; the triage survives, the PR's new column is dropped |
| `02_dashboards/ops/ISZE_Action_Ledger.html` | generated HTML | as above: PR re-renders the same five as NEW | Same reversal, rendered | **Reported, not resolved.** Took main's version |
| `02_dashboards/sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html` | generated HTML | Same page, rebuilt on both sides | **Different figures for the same KPIs** (open items 23,763 vs 23,236) | **Reported, not resolved.** Took main's version |
| `04_tools/db_sales_review/build_deck.py` | code, 1 hunk | Main: `gps_wallet` / `gps_uio` (respects the GPS master override). PR: `gps['wallet_2025']` / `gps['uio_2025']` (hardcoded) | Main's variables were introduced by main's own GPS-master work. **Taking the PR's lines silently discards the master-override correction** for the fleet-potential bullet | Mechanical choice made (main's variable names kept, PR's extra "Captured / Uncaptured" bullet kept too), but **flagged for review** because the number under it moves |
| `.cursor/rules/isze-pricing-no-street-ui.mdc` | rule | Auto-merged, no hunk | Same family as the `Mode A` cases below: main's copy uses **Mode A** where the PR uses **shared** — and the rule's whole subject is which words are allowed | **Reported, not resolved** |

### Simple conflicts — resolved

| File(s) | Count | Type | Resolution and why it is mechanical |
|---|---|---|---|
| `02_dashboards/ids/**` dealer-compare pages + Portugal map + `IDS_all_dashboards_2026-08-19/**` | 44 | generated HTML | The PR changed **3 lines** in each vs main's **764**. Content is identical on both sides; the only real difference is main's newer build (offline Leaflet instead of a CDN link). Took main's version. **Caveat below.** |
| `02_dashboards/ids/IDS_2026_dealer_compare.html` (root) | 1 | generated HTML | Both changed substantially (PR +842, main +764) but they are the same page on different builds: main added offline Leaflet over the PR's own inlined Leaflet, and main's one real improvement is the map background colour. Took main's version — the PR's genuine changes on this page are cosmetic wording |
| `02_dashboards/Data/14_dashboards/dealer_sellout_aim_gps.json`, `02_dashboards/Data/90_INBOX/IDS_2026/**` | 3 | generated mirror | Modify/delete: the PR **deliberately untracked** `02_dashboards/Data/` (its commit `9672452`, "Untrack raw billing, the Data mirror and render intermediates"). Took the deletion; `sync_to_deploys.ps1` regenerates `Data/` |
| `01_data/14_dashboards/dealer_sellout_aim_gps.json` | 1 | generated JSON | Structured diff taken for review; content sits on the contested sell-out rebuild above. Took main's version as the interim state |
| `01_data/00_derived/action_ledger.meta.json` | 1 | metadata | Straight superset on the PR side — same fields, newer run id, larger counts. Took main's as interim (the CSV on the same snapshot wins) |
| `01_data/00_derived/action_ledger_open.csv`, `revision_exception_queue.csv` (the rest of the file) | — | data | Newest-vintage regeneration, not a semantic choice — but parked with the contested set above |
| `AGENTS.md` | 1 | doc | Both changed the audience section. **Composed both:** the PR's shared/internal wording (the live rule) with main's genuine addition of the `jerome-brief-plain.mdc` pointer, reworded so it carries no A/B label |
| `INDEX.md` | 1 | doc | Both are **additive**: the PR adds the retro and gate for the Exec paper plus an IAM page, main adds the Decision pack and the BI framework. Kept both sets |
| `00_docs/ISZE_ROADMAP.md` | 2 | doc | Main's side had **duplicated** items 13/14 (base copy plus a re-added copy) and an older `Last updated` header; the PR's copy is the current one and main's new rows added nothing. Kept the PR's header and rows 13–16 |
| `03_analytics/Isuzu/prism/.gitignore` | 1 | config | Both added un-ignore lines. **Composed:** kept main's two new lines and kept the PR's removal of the `sales_detailed_for_claude_full_fixed.tsv` un-ignore (the PR is right — that line was re-adding 44 MB of line-level billing to git) |
| `04_tools/ids_dealer_ranking/build_ids_country_packs_v13.py` | 1 | code, localised-composition | Same docstring line changed on both sides. **Composed:** main's map description (offline tiles, correct) with the PR's shared-not-Mode-A wording (correct). |
| `02_dashboards/ids/**` (41 pages) | 41 | generated HTML, one identical line | After taking main's build, the banned label `Mode A` returned in one identical comment line in each of 41 pages. The PR had already replaced it with `shared`. Restored the PR's wording — one line, identical in every file, no other change |

## 4. Commands run

```
# inspection, in the main tree (read-only)
git status --porcelain=v1
git stash list
git worktree list
git branch -a
gh pr view 10 --json headRefName,baseRefName,mergeable,mergeStateStatus,files,title,url
gh pr view 10 --comments
gh pr view 10 --json title,body,... 

# fetch both sides
git fetch origin main
git fetch origin cursor/isze-exec-sales-paper-prompt-8dc1

# isolated worktree, detached at the PR tip (the worktree cannot check out
# the branch name, because the main tree already has it checked out)
git worktree add --detach "C:\Users\jerom\Desktop\claude\ISZE_worktree_pr10" \
    origin/cursor/isze-exec-sales-paper-prompt-8dc1

# the merge — inside the worktree only
git merge --no-commit --no-ff origin/main

# resolution
git checkout --theirs -- <60 files>
git add -- <60 files>
git rm -- <3 mirror files>
# 12 files composed by hand, then:
git add -- <12 files>
```

Nothing was committed. `MERGE_HEAD` is still present, so the merge is left staged for review:
`C:/Users/jerom/Desktop/claude/ISZE/.git/worktrees/ISZE_worktree_pr10/MERGE_HEAD` = `87c7907`.

## 5. Safety — the main working tree

Measured before and after with `git status --porcelain=v1`, recorded to
`C:\Users\jerom\Desktop\claude\pr10_baseline_git_status.txt` and `pr10_after_git_status.txt`:

| | Before | After |
|---|---|---|
| total entries | 188 | 188 |
| modified | 126 | 126 |
| untracked | 57 | 57 |
| deleted | 5 | 5 |
| branch | `cursor/isze-exec-sales-paper-prompt-8dc1` | `cursor/isze-exec-sales-paper-prompt-8dc1` |
| `HEAD` | `9672452` | `9672452` |

`git stash list` empty before and after. No `git clean`, no `git reset`, no `git checkout --`
against a modified path, no `git stash drop`, no force push, no branch delete. The PR branch is
checked out in the main tree and was **never checked out or switched** there — the merge ran in a
separate worktree.

## 6. What was not done

- **Nothing committed or pushed.** The merge is staged only.
- **The pull request was not edited, opened or merged.**
- **19 files are reported, not resolved** (the complicating list above). The merge currently carries
  **main's version** for the contested data and code files, which means the PR's changes on those
  files are dropped from this resolution until someone decides.
- **The IDS map decision is unresolved.** Main's build uses an offline bundled Leaflet with no tile
  service; the PR's generator and the PR's pages expected the online CARTO/OpenStreetMap tiles. I
  took main's pages because 44 of them are otherwise byte-identical and main's build is newer, but
  main's own generator now expects different markup than its pages contain. **The pages have not
  been opened or rendered to check that the map paints.**
- **No pipeline, verifier or ship gate was run.** The numbers in the contested files were compared,
  not recomputed.

## 7. Verified vs assumed

**Verified by running a command:** every count, figure and code snippet quoted above comes from
`git show :1/:2/:3:<path>`, `git diff`, `git log -S`, `git log --oneline <base>..<ref> -- <path>`,
`git cat-file`, or a Python comparison of the three merge stages. The before/after main-tree counts
are measured, not asserted. `py_compile`, `yaml.safe_load` and `json.load` were run on the files I
edited and all pass.

**Not verified:** which side is *commercially correct* for any contested number — I established that
the sides differ and which side carried the deliberate correction's wording, not which value is
right. The IDS maps were not rendered. No test suite was run.
