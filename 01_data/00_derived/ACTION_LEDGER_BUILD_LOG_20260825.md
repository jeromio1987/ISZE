# ACTION LEDGER BUILD LOG — 2026-08-25

**Prompt:** `C:\Users\jerom\Desktop\claude\ISZE\00_docs\PROMPT_ACTION_LEDGER_P8.md`  
**Executor:** Cursor (full P8 execution, not hub-only)  
**Workspace:** `C:\Users\jerom\Desktop\claude\ISZE`

---

## Scope contract (restated before further code)

1. **VRAAG** — Opportunity → Action → Outcome spine over existing green derived surfaces. Not a new analysis. Not a new KPI.
2. **BRON** — only the nine §5 files under `01_data/00_derived/` and `01_data/17_interactions/`. No file outside that list enters v1.
3. **METHODE** — euros unchanged from source columns. Ledger re-states; it does not re-compute. No margin convention applied here.
4. **BUITEN SCOPE** — §11 / §13 of the prompt (Book B allocation, shared, mail LLM/P2b, new KPIs, raw sales XLSX, tenth adapter, etc.).

---

## Data-sufficiency verdict (§2 — own words)

**Sufficient to build and backfill.** `sales_fact.parquet` covers billing from **2023-01-03 through 2026-03-31**; the nine action-bearing surfaces already carry euro (or explicitly null) columns; adapters can raise a stable opportunity set today.

**Insufficient for measurable realised outcomes past the billing horizon.** Billing ends **2026-03-31**. Anything whose measurement window cannot close against that horizon stays `outcome_status = NOT_MEASURABLE` with `realised_eur` / `drift_adjusted_eur` empty. No modelling, interpolation, or forecast of a realised euro — an empty cell is the correct answer.

**Deliberate exclusion:** `portfolio_triage_20260819.csv` is **not** an adapter. It is a rollup of early_warning + account_health and would double-count. Exclusion is intentional and logged by the builder.

---

## A. Inventory — §8 paths + S1–S10

| Item | Status | Evidence |
|------|--------|----------|
| `01_data/91_build/action_ledger_adapters.py` | **DONE** | 22,526 bytes; nine adapters; count_in/count_out logged |
| `01_data/91_build/build_action_ledger.py` | **DONE** | 54k+ bytes; `--dry-run` / `--all --backfill` / `--test` |
| `01_data/00_derived/action_ledger.parquet` | **DONE** | 23,236 opportunity rows |
| `action_ledger_history.parquet` | **DONE** | 23,307 observation rows (append-only; backfill flagged) |
| `action_ledger_open.csv` | **DONE** | ~6.1 MB; open sorted by € |
| `action_ledger_decisions.csv` | **DONE** | Header-only human file (64 bytes); builder never writes states |
| `action_ledger_decisions.template.csv` | **DONE** | Template present |
| `action_ledger_rejects.csv` | **DONE** | Exists; 0 data rows; `reason` column present |
| `action_ledger.meta.json` | **DONE** | run stats, horizons, excluded list, sufficiency verdict |
| `ACTION_LEDGER_REVIEW_20260825.md` | **DONE** | Memo with sourced counts only |
| `02_dashboards/ops/ISZE_Action_Ledger.html` | **DONE** | Four tabs; SSR bars; Command Center shell |
| `02_dashboards/ops/OPEN_ACTION_LEDGER.cmd` | **DONE** | Launches sibling HTML |
| Verify checks in `verify_derived_pipeline.py` | **DONE** | six `action_ledger.*` checks |
| `AUTOMATION_REGISTER.md` | **DONE** | cadence, owner, monitor, **retirement condition** |
| `DATA_MANIFEST.md` | **DONE** | P8 entry 2026-08-25 |
| `ROUTING.yaml` `action_ledger:` | **DONE** | task key present |
| Hub HTML (`ISZE_Action_Ledger_Hub.html`) | EXTRA only | Does **not** replace §8 deliverables |

### S1–S10

| Step | Status | Path / evidence |
|------|--------|-----------------|
| S1 adapters | **DONE** | `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\action_ledger_adapters.py` |
| S2 dry-run | **DONE** | pasted below; writes nothing |
| S3 full build | **DONE** | parquet + CSVs + meta |
| S4 backfill | **DONE** | dated sources replayed; history includes BACKFILL observations |
| S5 outcomes | **DONE** | engine present; 0 outcomes until human ACTIONED decisions |
| S6 review memo | **DONE** | `...\ACTION_LEDGER_REVIEW_20260825.md` |
| S7 HTML + cmd | **DONE** | `...\02_dashboards\ops\ISZE_Action_Ledger.html` + `OPEN_ACTION_LEDGER.cmd` |
| S8 verify checks | **DONE** | `action_ledger.*` in verify report |
| S9 automation register | **DONE** | retirement condition present |
| S10 manifest + routing | **DONE** | both updated |

---

## B. Commands run this session

```text
python 01_data/91_build/build_action_ledger.py --dry-run
python 01_data/91_build/build_action_ledger.py --all --backfill
python 01_data/91_build/build_action_ledger.py --test
powershell -File 02_dashboards/_build/ship_gate_check.ps1
python 03_analytics/Isuzu/prism/scripts/verify_derived_pipeline.py
```

Fix applied mid-session: Windows cp1252 crash on printing build log arrow (`→` → ASCII `->` + safe print fallback) in `build_action_ledger.py`.

---

## Dry-run output (S2 / pasted)

```
============================================================
DATA-SUFFICIENCY VERDICT (§2)
Sufficient to build and backfill: sales_fact.parquet holds billing 2023-01-03 to 2026-03-31; pipeline verification green; nine action-bearing surfaces exist with euro columns attached.
Insufficient for outcomes past the horizon: billing ends 2026-03-31. Anything raised after that date has outcome_status=NOT_MEASURABLE and realised_eur=NULL. No modelling, interpolation, or forecast of realised euro.
============================================================
ADAPTER dealer_leakage_ituk: count_in=260 count_out=260
ADAPTER revision_exception_queue: count_in=20572 count_out=20572
ADAPTER replenishment_exceptions_cy2025: count_in=1595 count_out=1595
ADAPTER early_warning: count_in=19 count_out=19
ADAPTER defection_alerts: count_in=265 count_out=265
ADAPTER no_pr00_gap_cy2025_ranked: count_in=31 count_out=31
ADAPTER revision_book_b_top_review: count_in=500 count_out=500
ADAPTER leakage_monday_actions: count_in=40 count_out=40
ADAPTER account_health_latest_flagged: count_in=16 count_out=16
EXCLUDED: portfolio_triage_20260819.csv — rollup of early_warning + account_health; excluded to avoid double-count
DRY-RUN schema cols: ['opportunity_id', 'signal_type', 'db_code', 'entity_key', 'entity_grain', 'eur_at_stake', 'eur_basis', 'source_file', 'source_column', 'source_as_of', 'raised_on', 'last_seen_on', 'recommended_action', 'also_seen_in', 'evidence_ref', 'adapter_name', 'horizon_date', 'count_basis_n']
DRY-RUN total rows from adapters: 23298
DRY-RUN unique opportunity_id: 23236
```

---

## C. Acceptance tests §10 (11.1–11.11)

### 11.1 Id stability — **PASS**

```
PASS 11.1 id_stability: n1=23236 n2=23236
```

Two consecutive builds: identical `opportunity_id` set (23,236).

### 11.2 No recomputation — **PASS**

Built-in sample:

```
PASS 11.2 no_recomputation: sampled=21
```

Hand lineage sample across all nine adapters (20 rows): **20 MATCHES / 0 FAILS**

```
SAMPLED=20 MATCHES=20 FAILS=0
OK id=11ea6a381f77d5a4 file=dealer_leakage_ituk.csv col=gap_eur ledger=4177.71 source=4177.71 entity=MOTUS GROUP UK LTD|fuel_filter
OK id=d918c191844b497b file=dealer_leakage_ituk.csv col=gap_eur ledger=2767.62 source=2767.62 entity=MOTUS GROUP UK LTD|air_filter
OK id=e4e3387aad5f261e file=dealer_leakage_ituk.csv col=gap_eur ledger=2519.37 source=2519.37 entity=FERNDOWN COMMERCIALS LTD|fuel_filter
OK id=bef135fb3741f975 file=revision_exception_queue.csv col=pr00_eur ledger=15.69 source=15.69 entity=8970202502
OK id=30f955273d49b65e file=revision_exception_queue.csv col=pr00_eur ledger=41.83 source=41.83 entity=8972067730
OK id=55a67cb49d4ae1e4 file=revision_exception_queue.csv col=pr00_eur ledger=68.28 source=68.28 entity=8972067753
OK id=649994d6ca42ceb4 file=replenishment_exceptions_cy2025.csv col=bill_eur ledger=10835.1 source=10835.1 entity=8982705240
OK id=a3d51d10cb45c2f4 file=replenishment_exceptions_cy2025.csv col=bill_eur ledger=9961.0 source=9961.0 entity=5876150170
OK id=8829f730982f8c4f file=early_warning.csv col=eur_exposed ledger=80246.81 source=80246.81 entity=UTI
OK id=dc63c8390cd4e1fd file=early_warning.csv col=eur_exposed ledger=48149.32 source=48149.32 entity=UMI
OK id=fad8d66d7dae84ab file=defection_alerts.csv col=trailing_12m_rev_eur ledger=0.0 source=0.0 entity=SWEDEN|brake_pad
OK id=dff06d23a122a7e5 file=defection_alerts.csv col=trailing_12m_rev_eur ledger=0.0 source=0.0 entity=FINLAND|clutch_kit
OK id=32169937e7643606 file=no_pr00_gap_cy2025_ranked.csv col=cy2025_eur ledger=433820.16 source=433820.16 entity=550047337
OK id=fd1411878dc7a315 file=no_pr00_gap_cy2025_ranked.csv col=cy2025_eur ledger=75636.08 source=75636.08 entity=550047252
OK id=17357ba97729e0ed file=revision_book_b_top_review.csv col=l12m_eur ledger=45746.11 source=45746.11 entity=8944627340
OK id=02f63c0f73c7dcf8 file=revision_book_b_top_review.csv col=l12m_eur ledger=204375.72 source=204375.72 entity=8982705240
OK id=6c3c303de5745166 file=leakage_monday_actions_20260819.csv col=gap_eur ledger=64906.0 source=64906.0 entity=8983300950
OK id=95979c6ca2b74036 file=leakage_monday_actions_20260819.csv col=gap_eur ledger=50853.0 source=50853.0 entity=8983615741
OK id=add8810383bd2dba file=account_health_latest_flagged.csv col=None ledger=None source=None ACCOUNT_HEALTH eur must be NULL
OK id=8471b3179b57644e file=account_health_latest_flagged.csv col=None ledger=None source=None ACCOUNT_HEALTH eur must be NULL
```

### 11.3 Append-only — **PASS**

```
PASS 11.3 append_only: n 23307→23307 mutated=False
```

History row count non-decreasing; prior-day rows not mutated (same-day upsert on `(opportunity_id, observed_on)`).

### 11.4 Horizon — **PASS**

```
PASS 11.4 horizon: bad_measurable_past_horizon=0
```

Zero measurable outcomes with `window_to` past source horizon. No ACTIONED decisions yet → outcomes empty (correct).

### 11.5 Decisions untouched — **PASS**

```
DECISIONS_HASH_BEFORE=564B750249FC6659B7440CE51BBD2767F581B15F4A29841CFA2E91D327B1ECEB
DECISIONS_HASH_AFTER =564B750249FC6659B7440CE51BBD2767F581B15F4A29841CFA2E91D327B1ECEB
HASH_MATCH=True
PASS 11.5 decisions_untouched: 564b750249fc6659
```

### 11.6 Language — **PASS**

Grep of HTML + memo + open/rejects/decisions CSVs for: `delivered by`, `caused`, `drove`, `thanks to`, `attributable to`

```
TOTAL_HITS=0
PASS 11.6 language: []
```

### 11.7 Small-n — **PASS**

```
PASS 11.7 small_n: drift_adjusted only when not SUPPRESSED
```

No published `drift_adjusted_eur` under `SUPPRESSED_SMALL_N` (no outcomes yet).

### 11.8 Rejects visible — **PASS**

```
PASS 11.8 rejects_visible: exists rows=0
```

File exists with `reason` column; currently empty (0 rejects this run).

### 11.9 Ship gate — **PASS**

```
Running verify_aftermarket_bi_command_center.py ...
OK — SSR smoke checks passed
Running verify_tier_a_html_json.py ...
Running verify_action_ledger.py ...
ISZE_Action_Ledger.html: OK (SSR bars=22, table sections=3)
SHIP_GATE_OK
EXIT=0
```

### 11.10 Pipeline verify — **PASS with documented pre-existing fail**

```
Verification: 114 pass, 1 warn, 1 fail
Report: C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_verification_report.md
  [FAIL] config.data_status: Missing flags: ['raw_cy2025']
  [WARN] uio.stale_copies: Stale UIO copies on disk: [...\UIO_v17.xlsx]
```

- Check count **116** (114+1+1) **> 108**
- All six `action_ledger.*` checks **green** (artefacts, nonempty, lineage, rejects, language, html)
- Sole FAIL is **`config.data_status` / `raw_cy2025`** — pre-existing config flag, **unrelated to Action Ledger**
- WARN is stale UIO copy — also unrelated to P8

### 11.11 Rendered paint — **PASS**

- Static probe: 4 tabs present; 3 tables; 205 `<tr>`; 30 SSR bar-rows; **zero `\bNaN\b`**; no empty canvas
- Edge headless screenshot written to `01_data/00_derived/_p8_paint_check.png` (256,567 bytes)
- Visual: Open-by-€ paints; KPI strip shows 23236 open / €22111k / horizon 2026-03-31; co-moved wording in lead; bars and signal table visible
- Localhost server used only for paint check, then stopped (no casual HTML spawn left running)
- Cursor browser MCP could not hold a stable tab this session; Edge headless + static checks used instead

---

## Meta snapshot (latest successful build)

- `run_id` examples this session: `20260825T162909Z_63892c`, `20260825T162949Z_ba0e3c`
- Adapter in→out: 23298→23298 lineage-kept; dedupe → **23236** unique ids
- Outcomes: **0** (no human ACTIONED rows yet — expected)
- History: **23307** rows

---

## Remaining gaps (honest)

1. **No human decisions yet** — `action_ledger_decisions.csv` is header-only. Outcomes / Closed tab stay empty until Jerome triages. This is by design, not a builder defect.
2. **Pipeline verify not fully green** — one pre-existing `raw_cy2025` config fail (not introduced by P8). Action-ledger checks themselves pass.
3. **Hub HTML** exists as an optional navigator; §8 ledger HTML is the product surface.

---

## Tenth-adapter wishlist (not built — §13)

None requested. Stop at nine.

---

_End of build log · 2026-08-25_
