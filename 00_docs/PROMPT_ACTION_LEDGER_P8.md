# PROMPT — ISZE Action Ledger (P8 · Closed Loop)

**For:** Cursor (executor) · **Audited by:** Claude Code · **Mode:** B (internal only)
**Written:** 2026-08-25 · **Workspace root:** `C:\Users\jerom\Desktop\claude\ISZE`
**Roadmap position:** sits above `00_docs/roadmaps/ai_sales_intelligence.md` §17 (P7 Operationalise). P7 registers *pipelines*; P8 registers *euros and decisions*.

---

## 0. The one-line brief

> Build the ledger that turns every "€X is leaking" surface already in this workspace into a dated, owned, state-tracked opportunity — and that measures, on the next data refresh, whether the number actually moved.

Everything in `01_data/00_derived/` today answers **"what is wrong."** Nothing answers **"what did we say we would do about it, and what happened."** That is the gap this closes.

---

## 1. Scope contract — Cursor must restate these four lines before writing code

1. **VRAAG** — Build a persistent Opportunity → Action → Outcome ledger over existing green derived surfaces. Not a new analysis. Not a new KPI. A spine.
2. **BRON** — only the files listed in §5 of this document, all under `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\` and `C:\Users\jerom\Desktop\claude\ISZE\01_data\17_interactions\`. No file outside that list enters v1.
3. **METHODE** — euro figures are carried through **unchanged** from the source column. No rebasing of any kind: sell-out stays sell-out, billing stays billing, a CY figure stays CY. The ledger re-states, it does not re-compute — so no margin convention is applied here at all, because no new euro is calculated.
4. **BUITEN SCOPE** — §13. Read it before starting, not after.

---

## 2. Data-sufficiency verdict — state this in the build log, do not skip it

**Sufficient to build and to backfill.** `01_data/00_derived/sales_fact.parquet` holds 477,505 rows, `billing_date` **2023-01-03 → 2026-03-31** (measured 2026-08-25). Pipeline verification is green: 108 pass / 0 fail (`01_data/00_derived/_verification_report.md`). Nine action-bearing surfaces exist with euro columns already attached.

**Insufficient for one specific thing, and it must be visible in the output:** billing ends **2026-03-31**. Anything raised after that date has **no measurable outcome** until the next SAP extract lands. Those rows carry `outcome_status = NOT_MEASURABLE` and `realised_eur = NULL`.

**Do not model, interpolate, or forecast a realised euro. Ever.** An empty cell is the correct answer. This is the single rule that decides whether the ledger is trusted or thrown away in month two.

---

## 3. Non-negotiables

| # | Rule | Enforcement |
|---|------|-------------|
| 1 | **No euro without lineage.** Every monetary row carries `source_file`, `source_column`, `source_as_of`. | Rows failing this are written to `action_ledger_rejects.csv`, never to the ledger. |
| 2 | **No invented figure.** The ledger re-states source values. It never recomputes, rescales, annualises or blends them. | Unit test §11.2. |
| 3 | **No realised € past the data horizon.** | Unit test §11.4. |
| 4 | **Attribution is co-movement, never causation.** Output wording: "moved with", "co-moved", "no measurable move". Never "delivered", "drove", "caused", "thanks to". | Grep test §11.6. |
| 5 | **Human decisions are human-owned.** The builder reads `action_ledger_decisions.csv` and never writes a state into it. If the file is missing, write `action_ledger_decisions.template.csv` and stop. | Unit test §11.5. |
| 6 | **Append-only history.** `action_ledger_history.parquet` is never rewritten, only appended. Re-running the same day is idempotent (upsert on `(opportunity_id, observed_on)`). | Unit test §11.3. |
| 7 | **Deterministic only.** No LLM, no mail-text model, no P2b dependency — so **no G0b governance gate** is touched. | Design constraint. |
| 8 | **Mode B only.** No IML-facing wording, no personal names, no distributor-visible export, no `07_deploy/` write, no GitHub Pages. | §13 + `.cursor/rules/isze-external-iml-language.mdc`. |
| 9 | **Never open `01_data/raw/sales/*.XLSX`.** Derived parquet/CSV only. | `CLAUDE.md` / `AGENTS.md`. |
| 10 | **Small-n suppression** carries over from roadmap §13: suppress any cell built on fewer than 10 underlying signals; mark `SUPPRESSED_SMALL_N`. | Unit test §11.7. |

---

## 4. Object model

Four tables. Resist a fifth.

### 4.1 `opportunity` — a euro-quantified claim raised by a derived surface

```
opportunity_id        STRING   -- stable hash, see §6
signal_type           STRING   -- LEAKAGE | PRICE_REVISION | REPLENISHMENT | EARLY_WARNING
                               -- | DEFECTION | CATALOGUE_GAP | BOOK_B | ACCOUNT_HEALTH
db_code               STRING   -- distributor; NULL for network-level rows
entity_key            STRING   -- part_number / dealer / pms_category / "NETWORK"
entity_grain          STRING   -- PN | DEALER | CATEGORY | DB | NETWORK
eur_at_stake          DOUBLE   -- carried verbatim from source; NULL allowed (non-monetary signals)
eur_basis             STRING   -- CY2025 | L12M | TRAILING_12M | ANNUALISED_SOURCE — never re-derived
source_file           STRING   -- filename as found in 00_derived / 17_interactions
source_column         STRING   -- the exact column eur_at_stake came from
source_as_of          DATE     -- file mtime or the file's own as_of/meta field, whichever is authoritative
raised_on             DATE     -- first date this opportunity_id appeared in any run
last_seen_on          DATE     -- most recent run that still raised it
recommended_action    STRING   -- verbatim from source where a column exists, else NULL
also_seen_in          STRING   -- semicolon list of other source_files raising the same id (§6.3)
evidence_ref          STRING   -- source_file + row key, enough to find the row again
```

### 4.2 `decision` — the only human-editable artefact

`01_data/00_derived/action_ledger_decisions.csv`

```
opportunity_id, state, owner, due_date, decision_note, decided_on
```

States: `NEW` (implicit — never written by a human) → `TRIAGED` → `ACTIONED` → `CLOSED_REALISED` | `CLOSED_NOT_REALISED` | `CLOSED_REJECTED` | `SUPERSEDED`. Plus builder-only terminal states `EXPIRED` (not seen in N=3 consecutive runs while still open) and `NOT_MEASURABLE` on the outcome side.

Illegal transitions (e.g. `NEW → CLOSED_REALISED` with no `ACTIONED`) are **rejected with a named row in the build log**, not silently accepted.

### 4.3 `observation` — append-only trajectory

```
opportunity_id, observed_on, eur_at_stake, source_as_of, run_id
```

One row per opportunity per run. This is what makes the estate longitudinal instead of a stack of dated snapshots.

### 4.4 `outcome` — measured movement, drift-adjusted

```
opportunity_id
window_from            DATE   -- raised_on (or decided_on where ACTIONED)
window_to              DATE   -- min(latest source_as_of, data_horizon for that source)
eur_at_raise           DOUBLE
eur_at_close           DOUBLE
delta_eur              DOUBLE -- eur_at_raise - eur_at_close  (positive = gap closed)
peer_delta_pct         DOUBLE -- same-signal, same-grain median movement over the same window (§8)
drift_adjusted_eur     DOUBLE -- delta_eur minus the peer-drift share
outcome_status         STRING -- MOVED_WITH | NO_MEASURABLE_MOVE | WORSENED
                              -- | NOT_MEASURABLE | SUPPRESSED_SMALL_N
measurable             BOOL
not_measurable_reason  STRING -- e.g. "billing horizon 2026-03-31 < window_to"
```

---

## 5. Source adapters — v1, exactly these nine, no others

All paths relative to `01_data/00_derived/` unless marked.

| # | Source file | Grain | € column | `signal_type` |
|---|-------------|-------|----------|---------------|
| 1 | `dealer_leakage_ituk.csv` | DEALER × CATEGORY | `gap_eur` | `LEAKAGE` |
| 2 | `revision_exception_queue.csv` | DB × PN | `pr00_eur` | `PRICE_REVISION` |
| 3 | `replenishment_exceptions_cy2025.csv` | DB × PN | `bill_eur` | `REPLENISHMENT` |
| 4 | `early_warning.csv` | DB (entity) | `eur_exposed` | `EARLY_WARNING` |
| 5 | `defection_alerts.csv` | DB × CATEGORY | `trailing_12m_rev_eur` | `DEFECTION` |
| 6 | `no_pr00_gap_cy2025_ranked.csv` | PN | `cy2025_eur` | `CATALOGUE_GAP` |
| 7 | `revision_book_b_top_review.csv` | DB × PN | `l12m_eur` | `BOOK_B` |
| 8 | `leakage_monday_actions_20260819.csv` | DB × PN | `gap_eur` | `LEAKAGE` (dedupes into #1) |
| 9 | `../17_interactions/account_health_latest_flagged.csv` | DB × month | **none** → `eur_at_stake = NULL` | `ACCOUNT_HEALTH` |

**Adapter contract:** one function per source, in `01_data/91_build/action_ledger_adapters.py`. Each returns a DataFrame in the §4.1 schema or raises. **A schema change in a source must fail loudly, not silently drop rows** — count in, count out, and log both.

`portfolio_triage_20260819.csv` is deliberately excluded: it is a rollup of #4 and #9 and would double-count. Note this in the build log so the exclusion is visible, not accidental.

---

## 6. Identity — the part that decides whether this works

### 6.1 Stable id

```
opportunity_id = sha1(f"{signal_type}|{db_code or ''}|{entity_grain}|{entity_key}")[:16]
```

**The euro value is not in the hash.** The same leak next month must be the *same* opportunity with a *new observation* — not a new row. Getting this wrong turns the ledger back into a pile of dated snapshots, which is the exact failure it exists to fix.

### 6.2 Idempotence

Running the builder twice on the same inputs produces byte-identical `action_ledger.parquet` apart from `run_id`/`produced_at`. Verified in §11.1.

### 6.3 Dedupe

When two sources raise the same `(signal_type, db_code, entity_key)`: keep the **tighter grain** (PN beats DEALER beats DB), record the loser in `also_seen_in`, and keep the **higher** `eur_at_stake` with its own lineage. Never sum the two.

---

## 7. Outcome measurement

For each opportunity with a decision state of `ACTIONED` or later:

1. Re-read the **same source column** at the current `source_as_of`. Same file, same column — never a substitute source.
2. `window_to = min(source_as_of, horizon(source))`. Horizons: billing-derived sources → **2026-03-31**; sell-out sources → their own file's stated coverage; mail-derived → `sales_fact` end for any order-joined field.
3. If `window_to <= window_from` → `outcome_status = NOT_MEASURABLE`, `realised/drift_adjusted = NULL`, and `not_measurable_reason` names the horizon and the date. **Do not fall back to an estimate.**
4. `peer_delta_pct` = median movement of all *non-actioned* opportunities of the same `signal_type` and `entity_grain` over the same window. That is the do-nothing baseline.
5. `drift_adjusted_eur = delta_eur - (eur_at_raise × peer_delta_pct)`.
6. Fewer than 10 peers in the comparison set → `SUPPRESSED_SMALL_N`, no drift-adjusted number published.

**Wording in every output, HTML included:** "co-moved with the action window". Never "delivered", "recovered by", "thanks to". The ledger reports observation, not proof — and saying so is what makes the € figure survive a challenge from IML or from Jerome.

---

## 8. Outputs — exact paths

| Path | Role |
|------|------|
| `01_data/00_derived/action_ledger.parquet` | current state, one row per opportunity |
| `01_data/00_derived/action_ledger_history.parquet` | append-only observations |
| `01_data/00_derived/action_ledger_open.csv` | the Monday list — open items, € desc |
| `01_data/00_derived/action_ledger_decisions.csv` | **human-editable**; builder reads only |
| `01_data/00_derived/action_ledger_rejects.csv` | rows dropped, with the reason |
| `01_data/00_derived/action_ledger.meta.json` | run_id, counts in/out per adapter, horizons applied, versions |
| `01_data/00_derived/ACTION_LEDGER_REVIEW_<YYYYMMDD>.md` | "what we said / what happened" memo |
| `02_dashboards/ops/ISZE_Action_Ledger.html` | Mode B surface, SSR at build time |
| `02_dashboards/ops/OPEN_ACTION_LEDGER.cmd` | launcher next to the HTML |

HTML reuses `02_dashboards/_build/tier_a_dashboard_common.py` + `render_ssr_charts.py` — the Command Center shell. **Do not invent a second dashboard pattern.**

Four views on that page, no more: **Open by €** · **Trajectory** (per opportunity, from history) · **Closed — what moved** · **Rejects & not-measurable** (visible, not hidden; the honesty of this page is the product).

---

## 9. Build order

| Step | Deliverable | Gate |
|------|-------------|------|
| S1 | `01_data/91_build/action_ledger_adapters.py` — nine adapters, count-in/count-out logged | Each adapter unit-tested against its real file |
| S2 | `01_data/91_build/build_action_ledger.py --dry-run` — schema + counts, writes nothing | Dry-run output pasted into the build log |
| S3 | Same script without `--dry-run` — parquet + CSVs + meta | §11.1–11.5 pass |
| S4 | Backfill: replay history from dated source files already on disk (`*_20260819.csv` etc.) so day one is not empty | Backfilled rows flagged `run_id = BACKFILL` |
| S5 | Outcome engine + drift adjustment | §11.4, §11.6, §11.7 pass |
| S6 | `ACTION_LEDGER_REVIEW_<date>.md` generator | Memo contains zero unsourced numbers |
| S7 | `02_dashboards/ops/ISZE_Action_Ledger.html` + `.cmd` | `ship_gate_check.ps1` → `SHIP_GATE_OK` |
| S8 | Verification checks appended to `03_analytics/Isuzu/prism/scripts/verify_derived_pipeline.py` | Report stays green, count rises above 108 |
| S9 | `00_docs/AUTOMATION_REGISTER.md` entry — cadence, owner, monitor, **retirement condition** (P7 §17) | Entry present |
| S10 | `01_data/DATA_MANIFEST.md` + `00_docs/ROUTING.yaml` (`action_ledger:` task key) | Both updated |

Commands:

```bash
python 01_data/91_build/build_action_ledger.py --dry-run
```

```bash
python 01_data/91_build/build_action_ledger.py --all --backfill
```

---

## 10. Acceptance criteria — each one is a test that runs, not a claim

| # | Test | Pass condition |
|---|------|----------------|
| 11.1 | **Id stability** — run twice | Identical `opportunity_id` set; parquet identical apart from `run_id` / `produced_at` |
| 11.2 | **No recomputation** — sample 20 rows across all nine adapters | `eur_at_stake` equals the source cell exactly (float equality to source precision) |
| 11.3 | **Append-only** — run, snapshot history, run again | History row count non-decreasing; no prior row mutated |
| 11.4 | **Horizon** | Zero rows with `measurable = True` where `window_to > horizon(source)` |
| 11.5 | **Decisions untouched** — hash the decisions CSV before and after | Identical hash |
| 11.6 | **Language** — grep the HTML, the memo and the CSVs | Zero hits for `delivered by`, `caused`, `drove`, `thanks to`, `attributable to` |
| 11.7 | **Small-n** | Every `drift_adjusted_eur` has ≥ 10 peers, else `SUPPRESSED_SMALL_N` and the value is NULL |
| 11.8 | **Rejects visible** | `action_ledger_rejects.csv` exists (may be empty) and every reject carries a reason string |
| 11.9 | **Ship gate** | `powershell -File 02_dashboards/_build/ship_gate_check.ps1` prints `SHIP_GATE_OK` |
| 11.10 | **Pipeline still green** | `03_analytics/Isuzu/prism/scripts/run_pipeline_and_verify.ps1` — 0 fail, check count > 108 |
| 11.11 | **Rendered paint** | HTML opened and visually checked per `.cursor/rules/isze-verify-rendered-output.mdc` — tables render, no NaN, no empty chart canvas |

---

## 11. Explicitly out of scope — do not touch, do not "improve while you are in there"

- Book B **allocation** (+3% / +4% / +5%) — Tier B, Jerome's decision, not this build.
- Any **Mode A** artefact: IML deck, distributor-facing export, GitHub Pages publish, `07_deploy/` write.
- Any **mail LLM / P2b** enrichment. Deterministic only. G0b stays untouched.
- **New KPIs** in `03_analytics/Isuzu/prism/docs/metric_dictionary.md` — the ledger publishes no new metric; it re-states existing ones.
- **Changing any existing builder's output.** Adapters read; they never rewrite a source.
- **Raw sales XLSX** under `01_data/raw/sales/`.
- **UIO workbook formulas**, `sales_fact.parquet` rebuild, scheduled-task paths.
- **A tenth adapter.** Nine, then stop. Extras go on a list at the bottom of the build log for Jerome.
- **Any euro figure that does not exist in a source file today.**

---

## 12. Audit contract — what will be checked when this comes back

Claude Code audits against this list. Anything unchecked is treated as not done.

1. All eleven tests in §10 actually executed, with output pasted — not asserted.
2. Twenty sampled rows traced by hand from `action_ledger.parquet` back to source file + column + row. Any row that cannot be traced fails the build.
3. `opportunity_id` stability proven by two runs, not by reading the code.
4. Grep for the banned attribution verbs across `.html`, `.md`, `.csv` — zero hits.
5. Every `NOT_MEASURABLE` row carries a reason naming a real horizon date.
6. The decisions CSV is confirmed unmodified by hash.
7. The dashboard opened and looked at — tables painted, no `NaN`, no empty canvas, launcher works from double-click.
8. Scope check: `git status` shows no file touched outside the paths named in §8 and §9.
9. `AUTOMATION_REGISTER.md` entry has all four P7 fields, including a real retirement condition.
10. The build log states the data-sufficiency verdict from §2 in its own words.

---

## 13. Known failure modes in this repo — avoid by name

| Failure | Seen as | Prevention here |
|---------|---------|-----------------|
| Dated one-off CSV that nobody re-runs | `leakage_monday_actions_20260819.csv`, `portfolio_triage_20260819.csv` | Stable ids + append-only history (§6.1) |
| Orphan pipeline in a large derived folder | roadmap §16 risk row; 239 files in `00_derived/` today | P7 register entry is step S9, not optional |
| Number quoted without lineage | the reason `_verification_report.json` exists | `source_file` + `source_column` + `as_of` on every monetary row |
| Silent schema drift dropping rows | count-in ≠ count-out | Adapters log both and fail loudly |
| "Done" claimed on an unopened artefact | `.cursor/rules/isze-ship-gate.mdc` | §10.11 rendered-paint check |
| Credit claimed for market movement | — | Peer-drift baseline (§7.4) + co-movement wording |

---

## 14. Why this one and not another dashboard

The workspace measures the network at €60.2M wallet / €30.8M captured / 51.1% GPS for CY2025 (`metrics_snapshot.json`, as_of 2026-08-17), with 25 active defection alerts and €79,118 of benchmarked ITUK dealer leakage on the board. Nine surfaces already say where the money is.

None of them can answer the question a VP is actually asked: **"what did we do about it, and did it work."**

That answer is not another chart. It is a ledger with stable identity, human-owned decisions, and an honest empty cell wherever the data cannot yet prove a result.
