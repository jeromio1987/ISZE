# Isuzu Universe programme — run-book

Written 2026-09-23 so the programme survives if Jerome is unavailable for a month. Plain English, absolute paths. Nothing here was invented — every command below was actually run during this write-up (build.py and build2.py both completed cleanly; see section 6).

---

## 1. White paper, edition 1 — the PDF

**What it produces:** `C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\ISUZU_UNIVERSE_WHITE_PAPER_FINAL_2026-09-23.pdf` (33 pages).

**Where the build lives:** `C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\_build_final\`
- `build.py` — assembles the HTML, renders it to PDF twice (first pass to find page numbers, second pass with the contents page filled in), then rasterises every page to PNG for a visual check and scans the text for banned internal terms.
- `charts.py` — draws every chart as inline SVG, reading numbers live from the CSV/JSON sources listed in section 3 below. No numbers are hard-coded in the paper itself; the `assert` lines near the top of build.py (pad values, billed total, dealer counts) exist so the build fails loudly if the source data has drifted.

**Exact command:**
```
cd "C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\_build_final"
python build.py
```

**Dependencies:**
- Python 3 with `fitz` (PyMuPDF) installed.
- Google Chrome at `C:\Program Files\Google\Chrome\Application\chrome.exe` (headless, network blocked via a dead proxy so it cannot phone home).
- Nothing else — no internet access needed, no API keys.

**How to check the output is right:**
- Console prints `pages 33 chapters {...}` — confirms page count and that every chapter heading was found by the second pass (if a chapter is missing from that dict, the contents page will show a blank page number for it).
- Console then prints a `banned '...'` line per internal codename/term (campaign, AIM, PRISM, DLOD, IDS, .csv, .json, .py, GPS, BVP, IML, ITUK, IUK, etc.) with a hit count. **All must read 0.** A nonzero count means an internal term leaked into client-facing text — do not ship the PDF as-is.
- Rasterised pages land in `C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\_build_final\_qa\` (one PNG per page, deleted and regenerated on every run) — open a few to eyeball layout.

**What breaks most often:**
- A source CSV/JSON changes shape or a row disappears → the `assert` statements at the top of build.py fail immediately, before any HTML is written. That is the intended failure mode — do not remove the asserts to force a build.
- Chrome path changes (reinstall, version update) → `CHROME` constant in build.py needs updating.
- A new internal codename creeps into prose → shows up as a nonzero banned-term count; find it with the printed example snippet and reword.

---

## 2. White paper, edition 2 — the PDF

**What it produces:** `C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\ISUZU_UNIVERSE_WHITE_PAPER_FINAL_v2_2026-09-23.pdf` (31 pages). Same underlying data and charts as edition 1, restructured as a build-up argument (4 parts, 9 chapters) rather than 7 flat chapters.

**Where the build lives:** same folder, `build2.py`. It reuses `charts.py` and literally imports the CSS block out of `build.py` (`open(...).read().split('CSS = """', 1)[1]...`), so **build.py must exist and be importable for build2.py to run** — they are not independent.

**Exact command:**
```
cd "C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\_build_final"
python build2.py
```

**Dependencies:** identical to build.py (PyMuPDF, Chrome at the same path).

**How to check the output is right:**
- Console prints `pages 31 found 14 [...]` — 14 is the count of parts+chapters+reference section located in the rendered PDF; compare against the 4 parts / 9 chapters / 1 reference section defined in the script (14 total) — if the printed count is lower, a heading failed to match and the TOC page number for it will be blank.
- Unlike build.py, build2.py's banned-term scan is defined but was silently not reached in this run (the script's `__main__` block calls it after `print("done", ...)`) — worth a visual spot-check of a couted page for internal terms in Chrome/Acrobat until confirmed.
- QA screenshots: `C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\_build_final\_qa2\`.

**What breaks most often:** same causes as build.py, plus: if build.py's CSS block format ever changes (the `CSS = """..."""` triple-quote marker), build2.py's CSS-import trick breaks with a Python exception on that line.

---

## 3. Source files both builds depend on

Read directly from `charts.py` (`DERIVED` and `TENDERS` constants) — this is the exact list, nothing more:

`C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\`:
- `pms_genuine_bvp_vs_price_2024_2025.csv`
- `pms_campaign_suspect_by_db_2024_2025.csv`
- `pms_campaign_suspect_by_family_2024_2025.csv`
- `pms_campaign_suspect_by_db_family_2024_2025.csv`
- `ids_dealer_network_cleaned_2026-09-20.csv`
- `gps_spu_by_distributor.csv`
- `pms_price_volume_response_2024_2025.csv`
- `pms_capture_by_db_year.csv`
- `dealer_sellout_gps_2025.csv`
- `dealer_sellout_long_*.csv` (all files matching this pattern, read dynamically to work out which distributors sent sales-to-dealer data)

`C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\tender_data.json` (4.6 MB, last modified 2026-09-22) — the public-tender feed.

If any of these files move, get renamed, or are deleted, both builds fail at the `load()`/`open()` call with a plain `FileNotFoundError` naming the missing file.

---

## 4. Universe Success Framework — static page

`C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\UNIVERSE_SUCCESS_FRAMEWORK_2026-09-23.html` (24.7 KB, last modified 2026-09-23).

**What it is:** a single self-contained HTML file — no build step, no external data, no dependencies. Open it by double-click in any browser.

**How to check it is right:** open it and read it; there is nothing to regenerate. If content needs to change, it is a direct hand-edit of that HTML file.

**What breaks:** nothing, unless the file itself is edited and something is copy-pasted wrong. There is no generator to fail.

---

## 5. Isuzu Dealer Standards (IDS) compare tools

**Deployed dashboards a browser opens directly (no build needed to view):**
`C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ids\IDS_2026_dealer_compare.html` and per-country variants (`IDS_2026_dealer_compare_<Country>.html`) in the same folder and under `IDS_all_dashboards_2026-08-19\02_country\`. `OPEN_*.cmd` files sit next to most of them for double-click launch.

**Generator (do not run — see caution below):**
`C:\Users\jerom\Desktop\claude\ISZE\04_tools\ids_dealer_ranking\build_ids_dashboard.py`
- Reads country `.xls` result reports from a results-report folder (`IDS_RESULT_REPORTS_DIR`, defined in `ids_paths.py`).
- Writes the combined dashboard HTML to its own output path, then **mirrors a copy into `02_dashboards\ids\IDS_2026_dealer_compare.html`** — i.e. running it overwrites the live per-country dashboard files.
- Depends on sibling modules in the same folder: `ids_dashboard_qa.py` (validates the payload and prints a QA report), `ids_dealer_geo.py` (attaches geocoding and sanity-checks clustering), `ids_report_extract.py` (parses the `.xls` reports into the dashboard's JSON payload), `ids_paths.py` (central path constants).
- Flags exist for `--skip-qa` (bypass QA failures — emergency only) and `--no-mirror` (build without overwriting the live copy).

**Caution, per the brief:** this generator overwrites country dashboard files. **It was not run during this exercise.** A deputy should not run it either without understanding what feeds `IDS_RESULT_REPORTS_DIR` and confirming with Jerome, since a bad or partial `.xls` drop would silently republish a wrong dealer-standards dashboard to `02_dashboards\ids\`.

**Related tools in the same folder** (`04_tools\ids_dealer_ranking\`, ~119 files): country-specific ranking builders (`build_b1_ranking.py`, `build_midi_fr_ranking.py`, `build_country_ranking.py`, `build_ituk_ranking.py`), Kaizen study builders (`build_ids_kaizen_full_study.py`, `build_ids_kaizen_belgium.py`), a QA/logic checker (`ids_logic_check.py`, `ids_report_qa.py`, `ids_dashboard_qa.py`), email drafters (`draft_ids_country_pack_emails.py`), and a large set of one-off `_` prefixed scratch/inspection scripts. These were not individually inventoried or run — the folder is large and most scripts are single-use or country-specific patches rather than part of a repeatable pipeline. A deputy needing one of them should search by filename for the country/task in question and read the script's own docstring before running it.

---

## 6. Parts Atlas / Network Atlas prototypes

`C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\02_Atlas\`:
- `README.md` — states this folder is "where the project started: one view of the network and the parts business," that HTML atlases open by double-click, and that shortcuts point at the live IDS dealer compare and a parts-atlas handoff folder (originals live elsewhere).
- `AIM_Parts_Atlas_v2.0.html`, `IDS_2026_atlas0.1.html`, `ISUZU_Network_Atlas_v0_2.html` — static prototype HTML files, open by double-click, no build step evident in the folder.
- `Parts atlas handoff 2.1.lnk`, `IDS dealer comparison.lnk` — Windows shortcuts to files elsewhere (likely the live dashboard and a handoff folder); if these shortcuts break (target moved), relink by asking Jerome where the current handoff/live copies live.
- `IDS_NETWORK_ATLAS_CONCEPT_2026-09-20.md`, `IDS_ATLAS_PLATFORM_AND_ACCESS_PLAN_2026-09-20.md`, `ISUZU_Atlas_v0_2_Review_and_Handoff.md`, `IDS_ATLAS_DATA_INVENTORY_2026-09-20.md` / `.csv` — concept, access-plan, review/handoff and data-inventory documents. Read these before touching the prototypes; they are design notes, not runnable code.

No generator scripts were found in this folder — these are prototypes to open and read, not to rebuild.

---

## 7. Build confirmation (run once each, as instructed)

```
cd "C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\_build_final"
python build.py
python build2.py
```

**Result: both completed cleanly, no errors.**
- `build.py` → `pages 33 chapters {1: 4, 2: 9, 3: 13, 4: 18, 5: 22, 6: 26, 7: 29, 'ref': 33}`; all 20 banned-term checks returned 0 hits.
- `build2.py` → `pages 31 found 14 [...]` (all 4 parts + 9 chapters + reference section located).

Both PDFs were overwritten with re-rendered (functionally identical) output, as expected — this is not a change to the deliverables, just a confirmation the pipeline still runs end to end.

---

## First day for a deputy

1. Read this file, then open both PDFs and `UNIVERSE_SUCCESS_FRAMEWORK_2026-09-23.html` to see what "correct" looks like.
2. Confirm Python 3 + PyMuPDF (`pip show pymupdf`) and Chrome at `C:\Program Files\Google\Chrome\Application\chrome.exe` are present on the machine you're using.
3. Run `python build.py` then `python build2.py` from `_build_final\` exactly as in section 7. Confirm the console output matches the shape in section 7 (page counts, all banned-term counts at 0) before touching anything else.
4. Do **not** run `04_tools\ids_dealer_ranking\build_ids_dashboard.py` or any other `04_tools\ids_dealer_ranking\build_*` script without first understanding what data folder it reads from and confirming with Jerome — several of these overwrite live per-country dashboard files in `02_dashboards\ids\`.
5. Never open `01_data\raw\sales\*.XLSX` directly.
6. If a build fails on an `assert` in build.py, that means a source number moved — do not silently increase or remove the assert; find out why the number changed first.

---

## What a deputy cannot do today without Jerome

- **Judgement on which distributor/sales data is trustworthy.** The white papers state explicitly (section on price response, section on target-spend ceiling) that some inputs are thin, modelled, or based on a flat assumption rather than measured data. Which sources are solid enough to quote and which are not was not documented anywhere outside Jerome's own read of the business — a deputy has no written rule for this.
- **`IDS_RESULT_REPORTS_DIR` provenance.** Where the country `.xls` result reports that feed `build_ids_dashboard.py` actually come from, how often they're refreshed, and who supplies them was not established in this exercise. Running the generator without knowing this risks publishing a stale or wrong dashboard.
- **Access/credentials.** No credentials, logins, or access paths for any upstream system (SAP extracts, the tender feed's source, whatever populates the `.xls` result reports) were reviewed or are recorded here. A deputy would need these handed over separately.
- **Undocumented scope calls.** Which of the ~119 files in `04_tools\ids_dealer_ranking\` are still "live" pipeline versus abandoned one-off patches is not written down anywhere; the naming (many `_`-prefixed scratch scripts) suggests heavy ad-hoc history that only Jerome can currently distinguish.
- **Content judgement calls in the papers themselves** — e.g. which findings are safe to present externally, which numbers are still provisional, what "still open" items (participation scoring, competition-law review, named ownership of the answer function) have actually moved since 23 September — are Jerome's calls, not something the build tooling can tell a deputy.
- **The Atlas prototypes' current status** — whether `AIM_Parts_Atlas_v2.0.html` / `ISUZU_Network_Atlas_v0_2.html` are the versions currently being shown to anyone, or superseded, is not stated in the folder; the `.lnk` shortcuts imply a "live" version exists elsewhere but do not say where.
