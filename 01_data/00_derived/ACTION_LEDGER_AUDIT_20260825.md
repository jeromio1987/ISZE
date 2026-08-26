# ACTION LEDGER P8 — Independent Audit

**Auditor:** composer-2.5-fast (Cursor subagent)  
**Date:** 2026-08-25  
**Source of truth:** `C:\Users\jerom\Desktop\claude\ISZE\00_docs\PROMPT_ACTION_LEDGER_P8.md`  
**Build log reviewed:** `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\ACTION_LEDGER_BUILD_LOG_20260825.md`  
**Mode:** B only · no `07_deploy/` · no raw sales XLSX · auditor re-verified; did not rebuild deliverables except one `--all --backfill` for decisions-hash check

---

## Overall verdict: **PASS WITH GAPS**

Core P8 spine is built, on-disk, and testable. §8 artefacts exist; nine adapters run; lineage holds on sampled rows; id stability and decisions immutability proven; ship gate passes; banned attribution language absent from ledger outputs. Gaps: pipeline verify is not fully green (pre-existing `raw_cy2025` fail); 11.11 paint check is static-only in this audit; `NOT_MEASURABLE` reason strings untested (zero outcome rows); hand lineage sample hit 7/9 adapters (built-in 11.2 covers all nine).

---

## Audit items (§12 contract)

| # | Item | Verdict | Evidence |
|---|------|---------|----------|
| **1** | All eleven §10 tests executed with output | **PARTIAL** | **Re-run (auditor):** `$env:PYTHONIOENCODING='utf-8'; python 01_data/91_build/build_action_ledger.py --test` → `PASS 11.1` … `PASS 11.8`, `Tests: 9 pass / 0 fail`. **11.9 (ship gate):** `powershell -File 02_dashboards/_build/ship_gate_check.ps1` → `ISZE_Action_Ledger.html: OK (SSR bars=22, table sections=3)` + `SHIP_GATE_OK` (exit 0). **11.10:** `python 03_analytics/Isuzu/prism/scripts/verify_derived_pipeline.py` → `Verification: 114 pass, 1 warn, 1 fail`; `[FAIL] config.data_status: Missing flags: ['raw_cy2025']`; all six `action_ledger.*` checks green in `_verification_report.md`. **11.11:** static HTML probe (this audit) — see item 7. **Gap:** `--test` covers 11.1–11.8 only; 11.9 inside `--test` is artefact-existence not full ship gate; 11.10 fails strict “0 fail”; first `--test` on default cp1252 crashed on Unicode arrow in 11.3 print (passes with UTF-8). |
| **2** | 20 rows traced to source file + column + row | **PASS** | Independent trace via `evidence_ref` `#row=N` against source CSVs: `SAMPLED=20 MATCHES=20 FAILS=0`. Example: `OK id=11ea6a381f77d5a4 file=dealer_leakage_ituk.csv col=gap_eur row=0 ledger=4177.71 source=4177.71`. Covered 7 adapters in this sample; built-in 11.2 reports `sampled=21` across all nine (build log lines 124–147). **Note:** no untraceable row found. |
| **3** | `opportunity_id` stability — two runs | **PASS** | `--test` runs two full builds and compares sets: `PASS 11.1 id_stability: n1=23236 n2=23236`. Meta after auditor run: `run_id=20260825T164543Z_09fef7`, counts unchanged `after_dedupe=23236`. |
| **4** | Banned attribution verbs grep | **PASS** | `rg -i "delivered by\|caused\|drove\|thanks to\|attributable to"` on ledger outputs (`action_ledger_open.csv`, `action_ledger_rejects.csv`, `action_ledger_decisions.csv`, `ACTION_LEDGER_REVIEW_20260825.md`, `ISZE_Action_Ledger.html`) → **0 hits** (exit 1). Built-in: `PASS 11.6 language: []`. **Excluded:** `ACTION_LEDGER_BUILD_LOG_20260825.md` (lists search terms). **Extra hub:** `ISZE_Action_Ledger_Hub.html` line 180 contains negated rule text `never delivered/caused/drove` — not §8 product surface; not counted as attribution. |
| **5** | Every `NOT_MEASURABLE` row names horizon date | **PASS (N/A)** | `action_ledger.parquet` has no outcome columns populated; `meta.json` → `"outcomes": 0`. No `NOT_MEASURABLE` rows exist to inspect. Horizon rule documented in meta/build log (`billing_horizon: 2026-03-31`). **Gap:** reason-string rule not exercised on live outcome rows until human ACTIONED decisions exist. |
| **6** | Decisions CSV unmodified — hash | **PASS** | `Get-FileHash SHA256 action_ledger_decisions.csv` before/after `python build_action_ledger.py --all --backfill`: `DECISIONS_HASH_BEFORE=564B750249FC6659B7440CE51BBD2767F581B15F4A29841CFA2E91D327B1ECEB` / `AFTER=` same / `HASH_MATCH=True`. File content: header-only (`opportunity_id,state,owner,due_date,decision_note,decided_on`). `--test`: `PASS 11.5 decisions_untouched: 564b750249fc6659`. |
| **7** | Dashboard paint | **PARTIAL** | **Static (auditor, no browser left open):** `TABS(data-tab)=4`, `TABLES=3`, `TR_ROWS=205`, `SSR_BAR_ROWS=22`, `NAN_HITS=0`, `EMPTY_CANVAS=0`; `OPEN_ACTION_LEDGER.cmd` exists and launches sibling HTML. Ship gate: `verify_action_ledger.py` → `SSR bars=22, table sections=3`. Build log cites Edge headless screenshot `_p8_paint_check.png` (256,567 bytes) — not re-run this audit. **Gap:** no live rendered paint verification in this audit session. |
| **8** | Scope — action_ledger-related files | **PASS** | `git status --porcelain \| Select-String action_ledger` → P8 files under allowed paths: `01_data/91_build/action_ledger_adapters.py`, `build_action_ledger.py` (S1); `01_data/00_derived/action_ledger*` + review/build log (§8); `02_dashboards/ops/ISZE_Action_Ledger.html` + `OPEN_ACTION_LEDGER.cmd` (§8); `02_dashboards/_build/verify_action_ledger.py` (S7/S8 support); `00_docs/PROMPT_ACTION_LEDGER_P8.md`. Modified in scope: `AUTOMATION_REGISTER.md`, `ROUTING.yaml`, `DATA_MANIFEST.md`, `verify_derived_pipeline.py`. **Extra (allowed):** `build_action_ledger_hub.py`, `ISZE_Action_Ledger_Hub.html`, `OPEN_ACTION_LEDGER_HUB.cmd`. **Not flagged as P8 scope violation.** (Broader repo has many unrelated dirty files; not attributed to P8.) |
| **9** | `AUTOMATION_REGISTER.md` — four P7 fields + retirement | **PASS** | Row `action_ledger` at `00_docs/AUTOMATION_REGISTER.md:41`: **Cadence** = “After each derived refresh (or weekly Mon with open-loops)”; **Owner** = Jerome; **Monitor** = `verify_derived_pipeline.py` `action_ledger.*` + `verify_action_ledger.py` in ship gate; **Retirement condition** = “Retire when a CRM/work-management system owns opportunity state end-to-end *and* every monetary row still carries source_file+column+as_of lineage into that system — until then the ledger stays”. |
| **10** | Build log states §2 data-sufficiency in own words | **PASS** | `ACTION_LEDGER_BUILD_LOG_20260825.md` §“Data-sufficiency verdict (§2 — own words)”: billing **2026-03-31** horizon; `NOT_MEASURABLE` / empty realised €; “No modelling, interpolation, or forecast of a realised euro”. Matches `action_ledger.meta.json` → `"data_sufficiency_verdict"`. |

---

## S1–S10 deliverable path check

| Step | Path | Exists |
|------|------|--------|
| S1 | `01_data/91_build/action_ledger_adapters.py` | ✅ |
| S1 | `01_data/91_build/build_action_ledger.py` | ✅ |
| S3 | `01_data/00_derived/action_ledger.parquet` (931,932 bytes; 23,236 rows) | ✅ |
| S3 | `01_data/00_derived/action_ledger_history.parquet` (457,286 bytes; 23,307 rows) | ✅ |
| S3 | `01_data/00_derived/action_ledger_open.csv` | ✅ |
| S3 | `01_data/00_derived/action_ledger_decisions.csv` | ✅ |
| S3 | `01_data/00_derived/action_ledger_rejects.csv` | ✅ |
| S3 | `01_data/00_derived/action_ledger.meta.json` | ✅ |
| S6 | `01_data/00_derived/ACTION_LEDGER_REVIEW_20260825.md` | ✅ |
| S7 | `02_dashboards/ops/ISZE_Action_Ledger.html` | ✅ |
| S7 | `02_dashboards/ops/OPEN_ACTION_LEDGER.cmd` | ✅ |
| S8 | `03_analytics/Isuzu/prism/scripts/verify_derived_pipeline.py` (contains `check_action_ledger`) | ✅ |
| S9 | `00_docs/AUTOMATION_REGISTER.md` | ✅ |
| S10 | `01_data/DATA_MANIFEST.md` | ✅ |
| S10 | `00_docs/ROUTING.yaml` (`action_ledger:` key) | ✅ |

---

## Honest gaps (not rubber-stamped)

1. **Pipeline verify not fully green** — `config.data_status` / `raw_cy2025` fail predates P8; action_ledger checks are green but §10.11.10 strict “0 fail” is not met.
2. **Outcomes untested end-to-end** — header-only decisions → 0 outcomes; Closed tab and `NOT_MEASURABLE` reason strings are design-ready, not demonstrated.
3. **Paint check** — static HTML sufficient for structure/NaN/bars; live browser paint not re-run this audit.
4. **Test harness fragility** — Windows cp1252 UnicodeEncodeError on `--test` without `PYTHONIOENCODING=utf-8`.
5. **Hub HTML** — optional navigator outside §8; contains negated banned-verb examples in footer copy.

---

## Auditor commands log (reproducible)

```powershell
Set-Location C:\Users\jerom\Desktop\claude\ISZE
$env:PYTHONIOENCODING='utf-8'
python 01_data/91_build/build_action_ledger.py --test
powershell -File 02_dashboards/_build/ship_gate_check.ps1
python 03_analytics/Isuzu/prism/scripts/verify_derived_pipeline.py
# decisions hash:
$h1 = (Get-FileHash -Algorithm SHA256 01_data\00_derived\action_ledger_decisions.csv).Hash
python 01_data/91_build/build_action_ledger.py --all --backfill
$h2 = (Get-FileHash -Algorithm SHA256 01_data\00_derived\action_ledger_decisions.csv).Hash
```

---

_End of audit · 2026-08-25_
