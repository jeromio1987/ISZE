# ISZE Data manifest — sort-by-topic map

**Last updated:** 2026-07-24 (IDS NL/DK/LUX drop — DK dealers filed + outputs rebuilt; LUX Autopolis staged) · **Root:** `01_data/` (under `$env:ISZE_ROOT`)

This is the **data map**. Each subject has a numbered folder under `01_data/` — drop new files into the matching one (§1). A small **wired working-set stays flat at root** because build scripts read it from there (§3).

**Legend:** ★ canonical working file · ⚙ read by a script/skill — **do not move/rename** · 🔒 line-level / billing / customer — never paste to chat or GPT · 📄 method doc, not data · ⚠ stray / duplicate / version conflict (see §7)

---

## §0 — The one rule: dump into INBOX, never into `01_data/` root

**New / unsorted files go to `01_data/90_INBOX/` — nothing else.** The root of `01_data/` is **not** a drop zone; it holds only the wired working-set (§3) and these docs.

**Dump-then-sort workflow (works for Cursor *and* Claude Desktop):**

1. **Drop** any new export/download into `01_data/90_INBOX/` (subfolders allowed, e.g. `90_INBOX/IDS_2026/`).
2. Nothing downstream (PRISM, build scripts, dashboards) ever reads from `90_INBOX/` — it is a **staging area only**.
3. **Sort** on cadence or on request: an agent moves each file to its numbered home (§1), updates this manifest, and archives superseded versions to `92_archive/` (older) — keeping the **newest** as canonical.
4. A **non-empty `90_INBOX/` means "sorting owed."** Target steady state: empty.

> If you (or an agent) find loose files sitting directly in `01_data/`, that is the bug — re-file them per §1 and remind the dropper to use `90_INBOX/` next time.

---

## §1 — Sort-by-topic index

### 01 · Pricing → `01_Pricing/`
| File | Path | Flag |
|------|------|------|
| IE40 Price list …PR00_3_level_classified_GPT.xlsx | `01_data/` (root, wired) | ⚙ `04_tools/autodoc_scraper/aim_gap_closer.py` |
| Price file 2026_full.xlsx · preliminary_pricefile2026.xlsx · BPFY2027.XLSX · SPA_2026_UTI_… | `01_data/01_Pricing/` | pricing drop zone |
| Margin analysis report.xlsx · Customer order sales - VP.xlsx | `01_data/raw/reference/` | 🔒 |
| **Code/tool:** SPA/NOx optimizer | `04_tools/isze-tools/pages/5_NOx_SPA_Optimizer.py` | |

### 02 · GPS → `02_GPS/`
| File | Path | Flag |
|------|------|------|
| **ISZE_GPS_v5.xlsx** | `01_data/` (root, wired) | ★ **planning workbook** — `04_tools/build_gps_v5.py` · FY27 reviewed BP per DB |
| ISZE_GPS_Kickback_Stretch_Proposal_FY27 _V4.xlsx | `01_data/` (root) | ★ **newest** kickback+stretch working copy (V3 archived 2026-07-16) |
| Sales-share stretch pilots (AllDB FY26, UTI TESTCASE, IUK v5, IUK-UMI v3) | `01_data/02_GPS/` | ★ newest per family — older versions archived; IUK-UMI `v2` → `92_archive/` 2026-07-17. IUK-only `v6`/`v7` may still sit at root. |
| GPS_FILE_LINEAGE.md | `01_data/91_build/` | 📄 **mandatory read** before any GPS file edit — v5 vs v9 vs kickback |
| ISZE_GPS_Kickback_Stretch_Proposal_FY27.xlsx | `01_data/91_build/` | ★ canonical kickback — `build_gps_kickback_proposal.py` |
| budget_per_DB_reviewed_24042026.xlsx | `01_data/11_planning/` | ★⚙ reviewed BP FY27 source · `load_bp_fy27.py` (root space-named dup archived 2026-07-16) |
| ISZE_GPS_Calculator_v9.xlsx | `01_data/` (root) | ★⚙ **canonical** (build output of `91_build/build_gps_v9.py`; versioned name intentional). CANONICAL.md corrected 2026-07-16 — no unversioned copy is read by any code. |
| GPS_Kosha_* / v3c / v3d | `01_data/14_dashboards/kosha/` | ⚙ Kosha toggle + projection workbooks |
| **Code:** GPS builders | `03_analytics/build_gps*.py`, `04_tools/build_gps_v5.py` | |
| **Roadmap:** | `00_docs/roadmaps/gps.md` | |

**GPS derived chain (two documented bases — do not cross-compare):**
| File | Path | Basis / producer |
|------|------|------------------|
| gps_billing_clean.json (+ sidecars) | `01_data/00_derived/` | ⚙ **Kosha basis** — `04_tools/rebuild_gps_billing_and_surcharge_check.py` |
| gps_billing_fy_ALLCUSTOMERS.csv · _waterfall.csv | `01_data/00_derived/` | ⚙ **full GPS-clean basis** — `04_tools/gps_reconcile.py --rebuild` |
| gps_spu_by_distributor.csv | `01_data/00_derived/` | PRISM parquet basis — PRISM GPS page + `enrich_gps_spu_v9.py` |
| gps_snapshot.json (= gps_v9_snapshot.json) | `01_data/91_build/` | ⚙ `91_build/build_gps_v9.py` — embedded in GPS dashboard HTML |
| gps_reconciliation_report.json | `01_data/00_derived/` | ⚙ `gps_reconcile.py` — run after every GPS upload |

### 03 · PMS → `03_PMS/`
| File | Path | Flag |
|------|------|------|
| PMS SPA study_ISZE.xlsx · PMS meeting feedback pdf · ITUK PMS trip report | `01_data/03_PMS/` | PMS studies + minutes |
| **Service maintenance schedules** (GIDSS_maint_F/N_MY14/MY24.pdf, RG/RG21/RT56/RT88_93) | `01_data/03_PMS/service_schedules/` | 📄 OEM service intervals feeding PMS interval assumptions (filed 2026-07-16) |
| **Code:** PMS pilot · OKF assessment | `03_analytics/Isuzu/pms-pilot/` · `03_analytics/Isuzu/_OKF_assessment/` | |

### 04 · Sales / billing 🔒 (never move — pipeline + never share line-level)
| File | Path | Flag |
|------|------|------|
| CY2023-2024.XLSX · CY2025.XLSX | `01_data/raw/sales/` | ⚙ PRISM Phase 1 · 🔒 |
| Sales CY25.XLSX | `01_data/` (root, wired) | ⚙ Streamlit ISZE_Dashboard + GPT briefing |
| sales_2026tillApril.XLSX | `01_data/` (root, wired) | ⚙ `build_gps_billing.py`, `build_gps.py` |
| Sales_israel_1799&_1797.XLSX | `01_data/` (root, wired) | ⚙ `build_gps*.py` (UTI 1799 / UMI 1797) |
| CY2024-2025.XLSX | `01_data/` (root, wired) | ⚙ more-complete 2025 re-export (supersedes CY2025 in pipeline) |
| Extra ad-hoc billing extracts | `01_data/04_sales/` | topic drop (not `12_raw/sales/`) |

### 05 · Dealer sell-out → `05_Dealer_sellout/`
| File | Path | Flag |
|------|------|------|
| UTIPartSales_2025-* | `01_data/raw/dealer_sales/UTI/` | ⚙ sell-out pipeline |
| DEALER_SELL_OUT.md | `01_data/raw/dealer_sales/` | 📄 method + BVP rules |

### 06 · Warranty (⚙ all read by warranty/GPS builds — do not move)
| File | Path | Flag |
|------|------|------|
| Warranty_CV_2025.xlsx · Warranty_LCV_2025.xlsx | `01_data/06_Warranty/` (+ root wired copies) | ⚙ `extract_*`, `build_gps_v8.py` |
| ExportClaimAssessment*.xlsx | `01_data/` (root, wired) | ⚙ `extract_warranty_all.py` |
| UMI warranty data 202301 - 202605 (1).xlsx | `01_data/` (root, wired) | ⚙ `extract_warranty_all.py` — the "(1)" is the current working copy |
| Final_Complete_Warranty_Pricing_2026.xlsx | `01_data/` (root, wired) | ⚙ UTI dashboard build |
| DISTRIBUTOR_WARRANTY_EXPENSE.md · Warranty_CY2025_by_DB.md | `01_data/06_Warranty/` | 📄 method |

### 07 · UIO / parc → `07_UIO/`
| File | Path | Flag |
|------|------|------|
| ISUZU_UIO_Overview_2026.xlsx | `06_uio/_CURRENT/` | ★⚙ **canonical = v19** (CANONICAL.md, PRISM `config.py`, uio-staleness-alert) |
| ISUZU_UIO_Overview_2026_v19.xlsx | `01_data/` (root) | ⚙ versioned fallback — `config.py` / `gps_v9_loaders.py` (only if `_CURRENT` missing) |
| ISUZU_UIO_Overview_2026_v18.xlsx | `01_data/92_archive/` | archived 2026-07-17 — **not** load-bearing; fallbacks re-pointed v18→v19 |
| isuzuregdata.xlsx | `01_data/07_UIO/` | DVLA reg source |
| **Scripts:** | `06_uio/_Scripts/build_isuzu_uio.py` | |
| **ITUK UIO (PRISM capture lane):** | keep **23,068** | `verification_fixtures.yaml` / `facts_anchor.yaml` aligned. IML §1 / `iml_v7_ituk_cy2025.yaml` may stay **22,389** (DVLA) separately — do not force-merge. |

### 08 · Distributor / entity docs → `08_Distributor/` (IML · IMIT · ITUK · UTI · UMI · MIDI)
| File | Path | Flag |
|------|------|------|
| ITUK Parts Sales Target Study.xlsx | `01_data/08_Distributor/` | ★ **newest (2026-07-16)** promoted to canonical; prior + `(1)` archived |
| ITUK_ExecutiveSummary_Jan2026.pptx | `01_data/08_Distributor/` | also Meetings (§09) |
| Imotors_Portugal_UIO_GPS_PMS_Study.xlsx | `01_data/08_Distributor/` | Portugal (Imotors) study (filed 2026-07-16) |
| BO OVERVIEW - UNIVERSAL TRUCKS ISRAEL LTD 01-07-2026 (1).xlsx | `01_data/08_Distributor/` | Israel/UTI back-order overview (filed 2026-07-16) |
| **IDS 2026 dealer eval packs** (NL / DK / LUX drop 2026-07-24) | `01_data/90_INBOX/IDS_2026/` | ⚙ `04_tools/ids_dealer_ranking/` — NL unchanged (identical); DK 20 dealers filed; LUX Autopolis in `LUX/` pending BE/Benelux mapping |
| **Meetings prep per DB:** | `09_meetings/Preparation Meetings/<DB>/` | |

### 09 · Meetings & minutes → `09_meetings/`
| File | Path | Flag |
|------|------|------|
| evaluaties · Financial_business plan · FY27_Review_Draft · Preparation Meetings · UTI_Presentation | `09_meetings/` | decks, minutes, business plans |
| **European Conference 2026 (Mainz) material** (11 PDFs: DB Awards, LCV final, PMS standardization workshop, opening/welcome, service dept, etc.) | `09_meetings/European_Conference_2026_Mainz/` | conference pack (filed 2026-07-16) |

### 10 · Tender → `10_Tender/`
| File | Path | Flag |
|------|------|------|
| ISZE_TenderIntelligence_StrategyBrief_v6.pdf | `01_data/10_Tender/` | |
| tender_data.json | `01_data/14_dashboards/` (alias `01_data/dashboards/`) | ⚙ live feed |
| **Code / roadmap:** | `04_tools/` scrapers · `00_docs/roadmaps/scrapers.md` | |

### 11 · Planning / KPI → `11_planning/`
| File | Path | Flag |
|------|------|------|
| KPI Master File june 2026.xlsx | `01_data/11_planning/` | ★ **newest** KPI master (april archived 2026-07-16) |
| budget_per_DB_reviewed_24042026.xlsx | `01_data/11_planning/` | ★⚙ `load_bp_fy27.py` |
| Action plan FY2027 VPACC_April update.xlsx · ISZE_DB_KPI_Targets_FY2627_v1.xlsx | `01_data/11_planning/` | |
| ISZE PL Plan FY2026 2027 2028 20260205_2.xlsx | `01_data/11_planning/` | ★ ("- Copy" archived 2026-07-16) |

---

## §2 — Physical folder layout (numbered)

| # | Folder | Purpose |
|---|--------|---------|
| 00 | `00_derived/` | Machine exports: `sales_fact.parquet`, phase summaries, verify reports |
| 01 | `01_Pricing/` | Price lists, SPA, BPFY (topic drop zone) |
| 02 | `02_GPS/` | GPS working files — sales-share stretch pilots (newest per family) |
| 03 | `03_PMS/` | PMS studies, meeting feedback, **`service_schedules/`** (OEM PDFs) |
| 04 | `04_sales/` | Extra billing extracts (not `12_raw/sales/`) |
| 05 | `05_Dealer_sellout/` | Dealer sell-out topic files |
| 06 | `06_Warranty/` | Warranty exports + method docs (wired copies may stay at root §3) |
| 07 | `07_UIO/` | UIO/reg topic files (canonical workbook: `06_uio/_CURRENT/`) |
| 08 | `08_Distributor/` | Per-DB distributor docs + studies |
| 10 | `10_Tender/` | Tender strategy briefs |
| 11 | `11_planning/` | KPI Master, VPACC action plan, PL plan, reviewed BP |
| 12 | `12_raw/` | Immutable billing (`sales/`), dealer sell-out, reference catalog |
| 13 | `13_models/` | Phase 1–3 Excel living models |
| 14 | `14_dashboards/` | `isze_data.json`, `tender_data.json`, **`kosha/`** — alias junction `dashboards/` (§6) |
| 15 | `15_gpt_safe/` | Small MD/CSV only — the **only** source for GPT uploads |
| 16 | `16_exports/` | Ad-hoc exports |
| 90 | `90_INBOX/` | **Drop zone** for all new files — sort per §1 (see §0) |
| 91 | `91_build/` | One-off extract/build scripts (GPS v9, warranty extractors, BP loader) |
| 92 | `92_archive/` | Deduped / superseded data files (general) |

**Also present:** `_archive/` — a **separate, GPS-lineage-only** archive holding `ISZE_GPS_v6_mistaken_fork_2026-07-03.xlsx`, referenced by name in `91_build/GPS_FILE_LINEAGE.md`. Left as-is to avoid editing that authority doc; all **new** archival goes to `92_archive/`.

---

## §3 — Wired-file watchlist (DO NOT MOVE / RENAME)

These sit at `01_data/` root because code reads them from `DATA_ROOT`. Moving them breaks the script named.

| File | Read by |
|------|---------|
| `IE40 Price list …GPT.xlsx` | `04_tools/autodoc_scraper/aim_gap_closer.py` |
| `Warranty_CV_2025.xlsx`, `Warranty_LCV_2025.xlsx` | `_build/build_gps_v8.py`, `extract_*` |
| `ExportClaimAssessment*.xlsx`, `UMI warranty data …(1).xlsx` | `_build/extract_warranty_all.py` |
| `Final_Complete_Warranty_Pricing_2026.xlsx` | UTI dashboard build |
| `sales_2026tillApril.XLSX`, `Sales_israel_1799&_1797.XLSX`, `CY2024-2025.XLSX` | `03_analytics/build_gps_billing.py`, `build_gps.py` |
| `Sales CY25.XLSX` | Streamlit ISZE_Dashboard |
| `ISUZU_UIO_Overview_2026_v19.xlsx` | PRISM `config.py` + `91_build/gps_v9_loaders.py` fallbacks (canonical is `06_uio/_CURRENT/`) |
| `ISZE_GPS_v5.xlsx` | `04_tools/build_gps_v5.py` (canonical planning) |
| `ISZE_GPS_Calculator_v9.xlsx` | GPS calculator ★ (versioned name intentional — see CANONICAL.md) |

---

## §4 — 3-phase pipeline

1. **Phase 1** — Power Query (`models/Phase1_*`) loads `raw/sales/*` → `Sales_Fact` → `derived/sales_fact.parquet`.
2. **Phase 2** — `models/Phase2_*` → customer/SaTy, criticality, action engine → `derived/phase2_*.csv`.
3. **Phase 3** — `models/Phase3_*` + BVP catalog → demand, stocking, PRD → `derived/phase3_*.csv`.

See `05_memory/projects/sales-analytics-pipeline.md`.

---

## §5 — Refresh protocol

1. New SAP export → `90_INBOX/` → file per §1 (keep ⚙ files at root).
2. Refresh Phase 1 Power Query → export `derived/sales_fact.parquet`.
3. Refresh Phase 2/3 pivots → summary CSVs to `derived/`.
4. Regenerate `14_dashboards/isze_data.json` from aggregates (not raw xlsx).
5. Update **Last refreshed** below + optional `15_gpt_safe/` monthly CSV.

| Dataset | Last refreshed | Rows (approx) | Owner |
|---------|----------------|---------------|-------|
| Sales_Fact (derived) | 2026-07-03 | 477,505 | Jerome |

---

## §6 — Dashboard JSON paths & the `dashboards` junction

**Local source:** `01_data/14_dashboards/isze_data.json`, `tender_data.json`
**Alias:** `01_data/dashboards/` is a **healthy NTFS junction → `14_dashboards/`** (verified 2026-07-16). It is **load-bearing** — `publish_tender.ps1`, `publish_live_tender_json.ps1`, and `sync_to_deploys.ps1` reference the `dashboards\` alias. Do **not** delete it. (The 2026-07-12 scraper health-check "I/O error on `dashboards`" was a sandbox mount artifact, not a real break.)
**Deploy-side compatibility** (GitHub Pages — not local edit paths): `../Data/dashboards/isze_data.json`, `../Data/dashboards/tender_data.json`

---

## §7 — Open cleanup items (need Jerome's call — not auto-resolved)

| Item | Question |
|------|----------|
| ~~GPS calculator canonical~~ | ✅ **Resolved 2026-07-16** — `_v9` is the build output and true canonical; CANONICAL.md corrected. No action. |
| ~~UIO v18→v19 + ITUK 23068~~ | ✅ **Resolved 2026-07-17** — `_CURRENT` is v19; code fallbacks are v19-only. **Keep ITUK UIO 23,068** for the PRISM capture lane (`verification_fixtures.yaml` / `facts_anchor.yaml` aligned). IML §1 / `iml_v7_*` may keep DVLA **22,389** as a separate lane — deliberate dual-anchor, not a pending bug. Root `v18` optional archive to `92_archive/` (not load-bearing). |
| ~~Stretch WIP `..._v2` locked~~ | ✅ **Resolved 2026-07-17** — Excel lock cleared; older IUK-UMI `v2` archived; newest remains `02_GPS/…_v3.xlsx`. (Note: IUK-only `v6`/`v7` may still sit at `01_data/` root — sort when convenient.) |

---

## §8 — Migration log

- **2026-07-16** — **Root de-clutter + INBOX rule (§0).** ~30 loose files re-filed from `01_data/` root into numbered folders; older duplicates → `92_archive/dedupe_2026-07-16/`; junk → `92_archive/junk_2026-07-16/`. Service PDFs → `03_PMS/service_schedules/`; Mainz conf → `09_meetings/European_Conference_2026_Mainz/`; stretch pilots → `02_GPS/` (newest per family); distributor studies → `08_Distributor/`; KPI/PL/budget → `11_planning/`. ITUK study newest (today) promoted to canonical. Root now holds only §3 wired files + docs. See `CHANGELOG.md` 2026-07-16.
- **2026-06-18** — Numbered `01_data` subfolders + resolver in `_shared/paths.py` + `prism/config.py`. Manifest reorganised by topic (§1) + wired-file watchlist (§3).
- **2026-05-15** — All 10 files from `new files/` filed (`migration-log.txt`).
