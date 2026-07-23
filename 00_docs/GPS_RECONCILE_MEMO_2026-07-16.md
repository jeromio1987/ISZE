# GPS Reconciliation — Hard-Fail Memo

**Date:** 2026-07-16 · **Harness:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\gps_reconcile.py` (full run, raw + Kosha)
**Result:** `FAIL` — 19 checks, **8 hard failures**, 3 soft warnings. Identical to the 2026-07-06 run: nothing fixed in 10 days, nothing newly broken.
**Fresh report:** `C:\Users\jerom\AppData\Local\Temp\claude\C--Program-Files-Git\71e12db1-31a9-459b-adc9-72ad41d9f671\scratchpad\recon_2026-07-16.json`
(On-disk `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_reconciliation_report.json` is still the 07-06 run — **not** overwritten.)

---

## Verdict

**The raw→JSON billing spine is clean. Everything downstream of it is stale.** All 8 hard failures are
"artifact built before its input changed" — not arithmetic errors, not an ERP problem.

**The one finding that changes a number you would say out loud:** `ISZE_GPS_v5.xlsx` plans FY2029/FY2030
against a **pre-revision BP the PL Plan no longer contains** — €2.91M of demanded network uplift that
IML's own row 186 already withdrew.

---

## 1. What reconciles cleanly (8 PASS)

Raw = **477,505 lines, 2023-01-03 → 2026-03-31** — row count matches `FACTS.md` §4 exactly.

| Check | Detail |
|-------|--------|
| `billing_json_vs_raw` | all DB×FY cells within €5 |
| `transport_sidecar_vs_raw` | all DB×FY cells within €5 |
| `surcharge_sidecar_vs_raw` | all DB×FY cells within €5 |
| `allcustomers_israel_basis` | Israel totals tie to the dedicated UMI/UTI extract — the 1797/1799 merge fix holds |
| `spu_internal` | SPU / ex-warranty / capture arithmetic consistent across 89 rows |
| `inputs_present` | all derived + presentation inputs found |
| `dashboard_embedded` (fleet ×2) | embedded JS constants match `gps_snapshot.json` |

**Read:** `gps_billing_clean.json` and its sidecars reproduce from raw to the cent. The extraction, the
exclusion taxonomy and the Israel merge are sound. Do not re-litigate them.

---

## 2. What fails (8 HARD)

| # | Check | Real problem |
|---|-------|--------------|
| 1 | `snapshot_copy` | `gps_snapshot.json` (07-03 10:34) never re-copied after `gps_v9_snapshot.json` rebuilt (07-03 15:20) with canonical **rounded rates 296/739/887**; copy still holds **295.68/739.2/887.04** |
| 2 | `dashboard_embedded:gps/…_v9.html` | **orphan file** — BP27 is a pre-10:34 snapshot vintage (see §4b) |
| 3–4 | `dashboard_selfcontained:fleet/ ×2` | **generator emits a broken tag** — real defect |
| 5 | `dashboard_selfcontained:gps/` | same defect, but in the orphan |
| 6 | `waterfall_vs_raw` | 9 stage mismatches vs stored CSV |
| 7 | `allcustomers_vs_raw` | 10 customer×FY cells beyond €5 |
| 8 | `kosha_chain` | Toggle workbook: 11 gross cells ≠ rebuilt billing JSON |

### The dashboards are dead — verified, not inferred

Line 36 of all three, identical:

```html
<script><script src="https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"></script></script>
```

The inner tag is parsed as **text content** of the outer `<script>`, so ECharts never loads and the outer
block throws a SyntaxError. Served at `http://127.0.0.1:8901/gps/ISZE_GPS_Dashboard_v9.html`:

- `typeof echarts` → **`"undefined"`**
- `document.querySelectorAll('canvas').length` → **0**
- total body text → **484 chars**

**Root cause — `02_dashboards\_build\build_gps_dashboards.py`, the double-wrap:**

```python
line 16:  ECHARTS_CDN = '<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"></script>'
line 93:  <script>%%ECHARTS%%</script>          # wraps a value that already carries its own <script> tags
```

It is *also* a CDN reference — two violations of the self-contained rule in one line.

---

## 3. Root cause of 1, 6, 7, 8 — one pattern

Artifacts built **before** the 2026-07-03 source refresh (`CY2024-2025.XLSX` +1,369 rows,
`sales_2026tillApril.XLSX`, CR/RE flag-H exclusion) and never regenerated:

| Artifact | Built | Its input now | Stale by |
|----------|-------|---------------|----------|
| `01_data\00_derived\gps_billing_fy_ALLCUSTOMERS.csv` | 07-03 07:30 | billing JSON 07-06 15:30 | 10 cells |
| `01_data\00_derived\gps_billing_fy_waterfall.csv` | 07-03 07:30 | billing JSON 07-06 15:30 | 9 stages |
| `01_data\14_dashboards\kosha\GPS_Kosha_FY2024_2030.xlsx` | 07-03 09:28 | billing JSON 07-06 15:30 | 11 gross cells |
| `01_data\91_build\gps_snapshot.json` | 07-03 10:34 | `gps_v9_snapshot.json` 07-03 15:20 | rates + derived |

Every one is **producer-not-re-run**. None is a logic error.

---

## 4. € gaps

> These are **reconciliation deltas** — stored artifact vs recomputed-from-raw. Not revenue misses.
> Do not quote them as business gaps.

### 4a. `allcustomers_vs_raw` — stored **overstates** in all 10 cells

Source: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_billing_fy_ALLCUSTOMERS.csv`

| DB | FY | Rebuilt € | Stored € | Delta € |
|----|----|----------:|---------:|--------:|
| IUK | 2026 | 5,895,486 | 5,981,960 | −86,474 |
| IUK | 2025 | 7,297,066 | 7,314,795 | −17,730 |
| Imotors | 2026 | 1,813,147 | 1,822,339 | −9,192 |
| ISD | 2026 | 2,641,885 | 2,647,396 | −5,511 |
| ITUK | 2026 | 6,805,720 | 6,808,584 | −2,865 |
| ROM Auto | 2026 | 177,898 | 180,410 | −2,512 |
| Danmark | 2026 | 154,460 | 155,916 | −1,457 |
| Sverige | 2026 | 1,298,276 | 1,299,461 | −1,185 |
| Sverige | 2025 | 1,215,958 | 1,216,816 | −857 |
| Loutsios | 2026 | 401,056 | 401,755 | −699 |
| **Total** | | | | **−128,482** |

Uniformly negative → stored CSV is on a **wider** basis than the current clean taxonomy (consistent with
pre-flag-H, i.e. CR/RE lines still in). IUK FY2026 alone is 67% of it.

### 4b. `gps/ISZE_GPS_Dashboard_v9.html` BP27 — an orphan, not a live error

All 18 DBs differ from `gps_snapshot.json` → `bp27`; dashboard totals **~€36.23M** vs reviewed **~€33.22M** (+~€3.01M).
Biggest: IUK +942,027 · UMI +842,022 · UTI +732,179 · ITUK +451,341 · NORWAY −145,287 · CYPRUS −56,031.

**I tested whether this is the forbidden Kosha sales-share proxy. It is not.**
`GPS_Kosha_FY2024_2030.xlsx` FY2027 ties to the **reviewed** BP to the euro (ITUK 6,974,170 · IUK 6,062,956 ·
UTI 3,098,114 · UMI 2,973,279 · Norway 1,764,800 · Ireland 1,267,443). The Kosha workbook and the snapshot are
**both already correct**.

What actually happened is a clock problem:

| Artifact | Built |
|----------|-------|
| `02_dashboards\gps\ISZE_GPS_Dashboard_v9.html` | 07-03 **08:31** |
| `01_data\91_build\gps_snapshot.json` (regenerated) | 07-03 **10:34** |
| `02_dashboards\fleet\ISZE_GPS_Dashboard*.html` | 07-03 **10:34** ← same second, hence PASS |

`build_gps_dashboards.py:34` is `BP27 = snap["bp27"]` — the builder reads BP27 **from the snapshot**, so it
carries whatever vintage existed at build time. The `gps/` copy simply predates the 10:34 refresh.

**And nothing maintains it.** `build_gps_dashboards.py` writes only to `fleet/` (lines 309–310); no builder
writes `02_dashboards\gps\ISZE_GPS_Dashboard_v9.html`, and `00_docs\CANONICAL.md` does not list it — it is a
leftover from the 2026-06-29 rename into `fleet/`. **Failures 2 and 5 are gating on a file that should not
exist.** The €3.01M is not a live BP dispute; it is a ghost.

### 4c. `waterfall_vs_raw`

Source: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_billing_fy_waterfall.csv`

The line that matters is `clean`: **FY2025 −18,613** (stored 32,358,957 vs recomputed 32,340,344),
**FY2026 −110,153** (stored 33,177,220 vs recomputed 33,067,067). Stage noise is larger (FY2025 gross
+497,837; FY2026 excl_transport +232,623) because the exclusion taxonomy itself moved.

---

## 5. Kosha / BP coherence — **NO. This is the real finding.**

**PL Plan row 186 (車両部品 / VP parts), read live today:**
`C:\Users\jerom\Desktop\claude\ISZE\01_data\11_planning\ISZE PL Plan FY2026 2027 2028 20260205_2 -.xlsx` · sheet `IX study` · row 186 · cols G–J

| FY | PL Plan row 186 (live) | `build_gps_v5.py:56` + `ISZE_GPS_v5.xlsx` | Delta |
|----|----------------------:|------------------------------------------:|------:|
| 2027 | 35,284,444 | 35,284,400 | −44 (rounding) |
| 2028 | 37,530,115 | 37,530,000 | −115 (rounding) |
| **2029** | **41,530,410** | **42,560,000** | **+1,029,590 (+2.48%)** |
| **2030** | **46,385,705** | **48,270,000** | **+1,884,295 (+4.06%)** |

**Combined FY29+FY30 phantom BP: +€2,913,885.**

`build_gps_kosha_v4.py`'s docstring records the revision — *"FY2029/FY2030 were revised DOWN
(42.56→41.53M / 48.27→46.39M); FY2027/FY2028 unchanged"* — and matches row 186 to the euro. **v5 never got the memo.**

### Why this is not cosmetic

`ISZE_GPS_v5.xlsx` → `Kosha Gap` → row 11 `Gap: GPS Revenue − BP Target` = **0** for FY2028/29/30.
Option A **back-solves uplift X so revenue equals BP by construction**. An inflated BP never surfaces as a
visible gap — it is silently converted into **demanded distributor uplift**. Cells `E6/E8` (42,560,000) and
`F6/F8` (48,270,000) carry it. v5's FY29/FY30 stretch therefore asks the network for €2.91M that IML's
current plan does not.

**Direction: v5 is too harsh, not too soft.** This does not rescue the Kosha €52.1M/FY2031 stance in
`FACTS.md` §7 — row 186 is VP parts only (FY2030 46.4M), a different scope from the €52.1M figure. That
guardrail is untouched.

### The stale BP is the toolchain default

| File | Line | BP FY29 / FY30 | Status |
|------|-----:|----------------|--------|
| `04_tools\build_gps_v5.py` | 56 | 42.56M / 48.27M | ❌ stale — **canonical planning** |
| `04_tools\build_gps_kosha_v3d.py` | 44 | 42.56M / 48.27M | ❌ stale |
| `04_tools\gps_full_run.py` | 54 | 42.56M / 48.27M | ❌ stale |
| `04_tools\build_gps_kosha_v4.py` | 46 `load_bp()` | live row 186 | ✅ correct — **cannot run** |

**The only script that reads BP correctly is the only one that is broken.** `build_gps_kosha_v4.py:36`:

```python
PLAN  = DATA / "ISZE PL Plan FY2026 2027 2028 20260205_2 -.xlsx"   # -> 01_data\ ... does not exist
```

The PL Plan lives in `01_data\11_planning\`. `load_bp()` raises `FileNotFoundError`. The 2026-07-16 dedupe
(`92_archive\dedupe_2026-07-16\`) archived a `- Copy` of this workbook — consistent with a tidy-up having
moved the original out from under a hardcoded path.

---

## 6. Exact next fix

**Fix 1 — unblocks everything. `C:\Users\jerom\Desktop\claude\ISZE\04_tools\build_gps_kosha_v4.py`, `load_bp()` (line 46), constant line 36:**

```python
PLAN = DATA / "11_planning" / "ISZE PL Plan FY2026 2027 2028 20260205_2 -.xlsx"
```

Nothing can be re-derived from row 186 until this resolves. `load_bp()` itself is correct — verified live:
returns 35,284,444.24 / 37,530,114.84 / 41,530,410 / 46,385,705.

**Fix 2 — the number that matters. `C:\Users\jerom\Desktop\claude\ISZE\04_tools\build_gps_v5.py` line 56:**
delete the hardcoded `BP` dict, call `load_bp()`, re-run `build_gps_v5.py` to regenerate `ISZE_GPS_v5.xlsx`.
Moves FY29/FY30 Kosha Gap onto live row 186 and relaxes solved uplift X. Hoisting `load_bp()` into a shared
loader (mirroring `91_build\load_bp_fy27.py` for per-DB FY27) is the right shape so v5 / v3d / `gps_full_run`
stop each carrying a copy — **but that is a refactor this memo does not authorise.** Minimum correct fix is v5 alone.

**Fix 3 — dashboards. `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\_build\build_gps_dashboards.py` line 16:**
stop emitting a tag; hold the library *source* instead, so the existing `<script>%%ECHARTS%%</script>` at
line 93 becomes correct **and** self-contained in one change:

```python
# line 16 — was: ECHARTS_CDN = '<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"></script>'
ECHARTS_JS = (UI_DIR / "echarts.min.js").read_text(encoding="utf-8")
```

A complete 1,029,203-byte Apache ECharts build already exists at `90_archive\root_files\echarts.min.js` →
copy to `02_dashboards\_ui\echarts.min.js` (`_ui\` already vendors `plotly.min.js`, 4.8MB — same pattern).
⚠ Verify its version before trusting it: the CDN pinned **5.5.1**, the archived copy's banner does not state a version.

**Fix 4 — delete the ghost.** `02_dashboards\gps\ISZE_GPS_Dashboard_v9.html` is an unmaintained orphan
(§4b). Remove it, and drop its entry from the `DASHBOARDS` list at `04_tools\gps_reconcile.py` lines 61–65 —
otherwise the harness keeps gating on a file no builder owns. Clears failures 2 and 5 outright.
(The other files in `02_dashboards\gps\` are live — the kickback proposal is 07-06 — so the folder stays.)

**Fix 5 — regenerate, in this order, only after 1–3.**
`gps_reconcile.py --rebuild` → clears 6, 7. Then `03_analytics\build_gps_kosha.py` → clears 8. Then
`copy 91_build\gps_v9_snapshot.json → 91_build\gps_snapshot.json` → clears 1 — **and this will flip the two
currently-PASSing fleet `dashboard_embedded` checks to FAIL**, because those dashboards are pinned to the old
295.68 rates. They must be rebuilt in the same pass via `build_gps_dashboards.py` (Fix 3). Sequence matters.

**Not touched, deliberately:** did not run `--rebuild`, did not overwrite
`01_data\00_derived\gps_reconciliation_report.json`, did not edit any builder or delete any file. Every fix
above writes to a canonical artifact and needs your go-ahead.

---

## 7. Doc / memory corrections

- **`ISZE_GPS_Calculator_v10.xlsx` is dead.** Claude auto-memory `project_ituk_target_study.md` asserted
  "CANONICAL IS NOW v10 … v7/v8/v9 moved to 92_archive". False as of today: v10 sits in
  `01_data\14_dashboards\kosha\_archive\`; root holds `ISZE_GPS_Calculator_v9.xlsx` (07-03). The resolution is
  in `project_gps_kosha_capture_model.md`: **v5 replaced GPS_Calculator_v10 on 2026-06-30** and archived it —
  v10 was canonical for roughly one day. `00_docs\CANONICAL.md`, updated today, declares `_v9` canonical for the
  calculator role and `ISZE_GPS_v5.xlsx` for planning — **your brief was right on both counts.** Memory corrected.
- **Anything sourced from `07_deploy\GPS_Visual_v10\`** (net 50.7% ex-warr / ITUK 45.6%) was built off a
  workbook that has been archived for two weeks. Re-derive before reuse.
- **`00_docs\CANONICAL.md` line 27** still lists `01_data/raw/sales/CY2025.XLSX` as current SAP billing.
  `FACTS.md` (2026-07-03) supersedes it with `CY2024-2025.XLSX` and says CY2025 is no longer loaded. FACTS wins.
- **`gps_reconcile.py` docstring lines 5–7** lists raw inputs as `12_raw/sales/CY2023-2024.XLSX, CY2025.XLSX` —
  neither is what `load_all_billing()` reads today. Cosmetic, but it is the first thing an agent reads.

---

## Soft warnings (informational — did not gate)

- `unmapped_payers`: `UNK_2686` = **€360** (FY2026), below the €5,000 hard threshold. One payer code missing
  from `PAYER_DB` — worth a name, not an alarm.
- `spu_vs_snapshot_cy2025`: 6 DBs >2% (ITUK −3.6% · FINLAND −2.8% · ICELAND −2.3% · IRELAND −2.2% · UTI −2.1% · UMI −2.0%).
- `snapshot_vs_raw_cy2025`: 12 DBs >2%, **UMI −20.0%** and UTI −7.5% the outliers — the known
  "v9 snapshot is a hardcoded ERP extract" issue, CY2025 stale pending your re-base decision. Cross-basis by
  design (parquet vs ERP, calendar vs fiscal). Not evidence of a billing error.
