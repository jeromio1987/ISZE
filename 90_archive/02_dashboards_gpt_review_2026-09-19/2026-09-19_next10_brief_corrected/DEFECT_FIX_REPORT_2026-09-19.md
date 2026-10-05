# Defect-fix pass — 2026-09-19

**Folder:** `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected\`
**Scope of this pass:** the mechanical defects listed in the task brief, plus the verification badge. Nothing else.
**Backups:** every file edited in this pass has a sibling `.bak_pre_defectfix_20260919`. All six backups were verified byte-identical to the hashes in `FROZEN_BASE.md`.
**Live paths:** none touched. No mail, no publish, no version bump, no price change.

---

## 1. Files edited, and byte deltas

| # | File | before | after | delta |
|---|---|---:|---:|---:|
| 01 | `01_ISZE_Exec_Aftersales_Paper.html` | 281,142 | 281,314 | **+172** |
| 02 | `02_ISZE_Leakage_Cockpit.html` | 2,059,899 | 2,056,088 | **−3,811** |
| 03 | `03_Warranty_Commercial_Review.html` | 362,710 | 363,443 | **+733** |
| 04 | `04_ISZE_AIM_Classification_Paper.html` | 290,918 | 290,918 | **0** (equal-length string swap) |
| 07 | `07_ISZE_Pricing_Revision_AIM_Source.html` | 6,607,203 | 6,607,227 | **+24** |
| 10 | `10_Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html` | 63,027 | 63,221 | **+194** |

Files 05, 06, 08 and 09 were **not** edited: they carry no verification statement and no defect in the brief. (09 was not re-edited even after being listed; its only statement is the data-freshness warning at L349, which is already honest and dated.)

---

## 2. Every string changed, old → new

### F01 — `01_ISZE_Exec_Aftersales_Paper.html`

**2a. The raw placeholder (defect F01).**

```
old:  <tr><td>ITUK (UK truck)</td>…<td class="n">{ITUK_PCT:.1f}%</td>…
new:  <tr><td>ITUK (UK truck)</td>…<td class="n">45.6%</td>…
```

Evidence for **45.6%**, all from this file, no outside figure:
- L200 (page 3, same document): *"ITUK is green per truck and still sits at **45.6%** of its target spend"*.
- The column this value sits in is headed **"Billed vs target %"** (L359) — the same billed ÷ max-spend-ceiling measure L200 names for ITUK.
- L201 (page 3) ties ITUK to the same figure: *"ITUK €745 → **29.4%**"* is its sensitivity case, and L200's sentence belongs to that same 45.6% statement.
- The adjacent bar chart on the same page (L205) shows ITUK at `width:100.0%` with the caption *"€6.65M below target"*, and the embedded array `cBelowCeiling` (L780) carries ITUK = 6.65 as the group maximum — i.e. ITUK leads the below-ceiling euro pool, which is the sentence L200 makes about the 45.6% row.

**Stated plainly:** the replacement is the file's own printed value for the same metric on the same basis (45.6%). I did **not** recompute it, and I did **not** import a figure from outside this file. I deliberately did not substitute the sibling "Oil-filter total" column value (100% cap / 116% raw), which is a different measure on a different denominator and would have been wrong in this column.

**2b. Verification badge.** See §3.

### F02 — `02_ISZE_Leakage_Cockpit.html`

- **18 dead `"forward"` blocks removed** from the embedded `__LEAK__` object (each 7 lines: `"forward"`, `"year": 2030`, `"ceiling_2030_eur"`, `"vs_2024_pct"`, `"cum_ceiling_eur"`, `"modelled": true`, `}`), plus the trailing comma left on the preceding line. **−3,822 bytes from the payload, +11 from wording = −3,811 net.**
- `"the revenue bridge and forward ceiling model"` → `"the revenue bridge — the 2030 projection is not shown"` in `meta.source_methods`.
- Basis-strip Data status and the footer line: 143/0/0 · 2026-09-18 → **153/1/0 · 2026-09-19 13:00 UTC**.
- Both embedded `verification` blocks (L710 `meta`, L57636 `honesty`): `generated_at` 2026-09-18T20:22:00Z → **2026-09-19T13:00:24Z**, `pass` 143 → **153**, `warn` 0 → **1**.

### F03 — `03_Warranty_Commercial_Review.html`

- Section 7 note rewritten to describe the position basis and to say what was removed and why (+~470 bytes).
- Doughnut `c9`: three payer labels replaced by **two position categories** (`inside the stated limits` / `over the stated limits`), derived per operation from its own median age and median distance against the stated 36 months / 100,000 km.
- Table `t4`: column header `Who pays` → **`Position vs the limits`**; cell values from the payload's `who_pays` payer strings → the same two position categories.
- **No euro amount, claim count, period or row was changed.** `t4` still shows 16 rows and the same `€`, `Claims` and `Median km` values.

### F10 — `10_Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html`

- Scope sentence: *"it is value-parts **quantity** divided by value-parts plus contested-original **quantity** within the selected assortment. It is a mix measure inside the parts we sold."* → *"it is **Best Value Parts proxy euro** divided by value-parts plus contested-original **proxy euro** within the selected assortment, where each line's proxy euro is its reported quantity valued at the median CY2025 ISZE-to-distributor unit price for that part number. It is a **proxy-euro** mix measure inside the parts we sold — **not a quantity share**, not a share of expected service demand, and not a share of the market."*
- Basis-strip Data status: `143/0/0 on 2026-09-18` → **`153 pass / 1 warn / 0 fail · 2026-09-19 13:00 UTC`**.
- **No number changed.** 92.3% and every table value are untouched.

---

## 3. Task 3 (F02) — was `forward` reachable?

**Finding: genuinely unreachable dead payload. Removed.** Evidence, all read on the pre-edit bytes:

| Check | Result |
|---|---|
| `"forward"` as a property name | 18, all inside the `__LEAK__` object literal |
| `"ceiling_2030"` | only as the key itself; no read anywhere |
| `.forward` (dot access) | **0** |
| `["forward"]` / `['forward']` | **0** |
| `download` / `export` / `csv` / `blob` / `JSON.stringify` / `window.print` | **0** each |
| The ceiling the page actually renders | `modules.gps.ceiling` → the separate `ceiling` object, `ceiling_total_eur: 55253312` — **not** touched |

After the edit:
- `"forward"` occurrences: **0**. `ceiling_2030` occurrences: **0**.
- `ceiling_total_eur` still present: **55,253,312**.
- The located script block for `const __LEAK__ = {…}` evaluates in Node with **exit 0**: `EVAL_OK dbs=22 meta_keys=13`, `HAS_FORWARD=[]`, `VERIF={"generated_at":"2026-09-19T13:00:24Z","pass":153,"warn":1,"fail":0,"ok":true}`.
- `node --check` on the file's script block: **passes**.

The payload is **not literal JSON** — it is a JS object containing arrow functions (e.g. `"thinPeer": (n) => …`), which is why it cannot be checked with `json.loads`. It was validated by evaluating it in Node instead. This is a pre-existing property of the file, not something this pass introduced.

---

## 4. Task 5 — the verification badge

### 4.1 Inventory of every verification statement (post-edit)

| File | Line | Wording | Count / date printed |
|---|---|---|---|
| 01 | 106 | basis strip, `Data status` | 153 pass / 1 warn / 0 fail · 2026-09-19 13:00 UTC (data, not this HTML) |
| 01 | 137 | KPI sub-line ×2 | Data verification 153 pass / 1 warn / 0 fail · CY2026 = Jan–Jun YTD |
| 01 | 189–746 | 15 × `footer.pf` | data verification 153/1/0 · 2026-09-19 13:00 UTC |
| 01 | 603 | SWOT cell | 153 pass / 1 warn / 0 fail (data run 2026-09-19 13:00 UTC) |
| 01 | 709 | sources-page verdict | 153 pass / 1 warn / 0 fail, generated 2026-09-19 13:00 UTC; **no HTML test claimed** |
| 01 | 733 | Verify stamp card | Data verification 153 pass / 1 warn / 0 fail · generated **2026-09-19T13:00:24Z** |
| 02 | 309 | basis strip | 153 pass / 1 warn / 0 fail · 2026-09-19 13:00 UTC (data, not this HTML) |
| 02 | 365 | footer | data verification 153 passed / 1 warn / 0 failed, generated 2026-09-19 13:00 UTC; **this HTML was not part of that run** |
| 02 | 712, 57638 | two embedded payload blocks | generated_at 2026-09-19T13:00:24Z, pass 153, warn 1 |
| 02 | 60424 (runtime) | "Data checks" KPI tile | reads `v.pass` → **153 passed**, no failures |
| 02 | 60534 (runtime) | "Where the numbers come from" | Data checks dated 2026-09-19, showing 153 passed and 0 failed |
| 04 | 350 | basis strip | Data verification 153 pass / 1 warn / 0 fail · 2026-09-19 13:00 UTC |
| 07 | 109 | basis strip | Extract generated 2026-09-18; data verification 153 pass / 1 warn / 0 fail · 2026-09-19 13:00 UTC |
| 10 | 56 | basis strip | Extract generated 2026-09-15; data verification 153 pass / 1 warn / 0 fail · 2026-09-19 13:00 UTC |
| 03, 05, 06, 08, 09 | — | **no verification statement at all** | n/a |

Two entries are duplicated in the counts above on purpose: the F02 basis strip and footer both read through the same `honesty` payload object at runtime, and the counts listed for F02 include that object (L712, L57638) as separate occurrences.

Stale statements surviving in visible text: **NONE** (checked by regex for `143 pass`, `143/0/0`, `Pass 116`, `143 passed`, `verification 143`). The `116` / `143` figures that remain anywhere in the folder are unrelated numeric cells (e.g. `116% raw`, `€143.37`, `€6,143`).

### 4.2 What is on disk

I searched the workspace for a record at **143 pass** and at **116**:

- **The live report supersedes 143.** `01_data\00_derived\_verification_report.json` — mtime 2026-09-19 15:01:38 local, `generated_at` **2026-09-19T13:00:24Z**, `summary` **{"pass":153,"warn":1,"fail":0,"ok":true}**, 154 checks. The single non-pass is `uio_year.historical_gaps` (warn): *"DENMARK 2012", "DENMARK 2013" unfilled*.
- **No _verification_report.json anywhere on disk carries 143.** The report copies present are: the live one (153/1/0), `01_data\90_INBOX\PPT_GPT_commercial_pack_2026-09-19\10_calc_support\` (same run, identical bytes), the stale `02_dashboards\Data\00_derived\` copy (2026-08-18, 108 pass) and a worktree copy (2026-07-29).
- **The 143 figure exists only in narrative documents**, all of which were written yesterday and now describe a superseded run: `FACTS.md`, `00_docs\PMS_INTERVAL_FIX_SCOPE.md`, `00_docs\PMS_UREA_INTERVAL_FIX_20260919.md` ("143 pass, 0 warn, 0 fail"), `00_docs\agent\STATE_PACKET.md`, `01_data\00_derived\_data_integrity_open_issues.md`, and several `08_gpt\` context copies. The most recent of them (`PMS_UREA_INTERVAL_FIX_20260919.md`) is explicit that the 143-check run belongs to the **urea-interval fix** and that **the leakage README's ITUK AdBlue figures, the exec paper and the hub were left untouched** by it. So the 143 stamp was never the exec paper's own run.
- **The 116 record does exist on disk**, but as a *description of an old report*, not as a report: `01_data\90_INBOX\_tmp_bpr_aim_prism_ids.json` carries `"verification_report": {"source_files": ["01_data/00_derived/_verification_report.json", …], "pass": 116, "warn": 0, "fail": 0, "generated_at": "2026-08-25T17:19:54Z"}` with a note that the report file mtime is 2026-07-09. **No `_verification_report.json` at 116 exists on disk.** `01_data\00_derived\metrics_snapshot.json` also still carries `verify.pass = 116` with `verify.generated = 2026-09-17T05:47:43Z`.

### 4.3 Data verification, HTML test, or both — decided per file

| File | What it claims | Option applied | Why |
|---|---|---|---|
| 01 | Data verification only, after the edit | **(b), partly (a)** | The data claim genuinely supersedes to 153/1/0 · 2026-09-19 13:00 UTC. The old promise of an HTML test *"recorded in the same block below"* was removed because no HTML test was ever recorded there — the block carried the stale 116 data stamp. The 116 stamp was replaced with the current data record. **No HTML test is claimed anywhere.** |
| 02 | Data verification only, explicitly *"this HTML was not part of that run"* | **(a)** | The wording already separates the two. Only the count and date moved, in the basis strip, the footer and both payload blocks. |
| 04 | Data verification only | **(a)** | Same. |
| 07 | Data verification only | **(a)** | Same. |
| 10 | Data verification only | **(a)** | Same. |
| 03, 05, 06, 08, 09 | Nothing | **(c)** | No verification claim exists. Left alone. |
| 03 (basis strip) | *"Claim files published 2026-09-18, currency correction applied same day"* | **(c)** | Already honest and correctly dated; it cites no count. Left alone. |
| 09 (L349) | *"File last updated 2026-05-22 — verify underlying data freshness before sharing externally"* | **(c)** | Dated and self-qualifying. Left alone. |

**No count was printed that I did not read from a file.** The 153 / 1 / 0 and `2026-09-19T13:00:24Z` all come from the live report read in this pass. **No HTML test was asserted** for any file — the suites in this folder are `node --check` / id / render checks I ran, but I did not paste them into the pages.

---

## 5. Verification run on this pass

- **Inline JavaScript parses.** `node --check` on every `<script>` block of every edited file: **0 failures.** 01: 2/2; 02: 1/1; 03: 3/3; 04: 2/2; 07: 2/2 (the third block is the `application/json` payload, parsed separately as JSON); 10: **no script blocks at all** — the file is pure markup, so there is nothing to parse.
- **Payload integrity after the F02 surgery.** The `__LEAK__` object evaluates in Node with exit 0; `dbs=22`; no `forward` key survives; the live ceiling (`55253312`) survives.
- **Element ids and label references.** Static markup: 27 / 24 / 25 / 16 / 33 / 0 ids respectively; **0 duplicates** in every file. Every `getElementById` target resolves. The three apparent gaps are pre-existing dynamic patterns, not breakage: `getElementById("mod-" + m.id)`, `getElementById('sec' + sec)`, and `getElementById('cb-…')` whose static ids are written unquoted by the markup. `c9` (canvas) and `t4` (table) both still exist in the markup and both still render.
- **Rendering.** Screenshots **taken: 18, read: 18**. Reader: this agent, image Read at full resolution, one at a time. Every screenshot is a viewport or a region of a **changed** file. Five intermediate full-page renders that I did not read were deleted rather than left on disk, so taken and read are the same number.

### What I actually saw, one at a time

- `defectfix_01b_league.png` / `defectfix_01d_p6_runtime.png` — page 6 "Distributor league — three separate columns". The ITUK row reads `249 · Green · **45.6%** · 100% cap · 97.3%`, sitting between Ireland 124.2% and Belgium 86.0%. No brace, no `:.1f`. The runtime DOM read of `#p6` returns the same 12 rows with `45.6%` in the third column.
- `defectfix_01c_sources.png` / `defectfix_01e_p16_runtime.png` — page 16 sources and verify stamp. Reads *"Data verification is green: 153 pass / 1 warn / 0 fail, generated 2026-09-19 13:00 UTC … A warning is a named, unfilled hole … uio_year.historical_gaps (DENMARK 2012 and 2013 left unfilled). No HTML test has been run for this corrected copy — none is claimed."* The Verify-stamp card below reads `153 pass / 1 warn / 0 fail · generated 2026-09-19T13:00:24Z`. All 15 page footers read `153/1/0 · 2026-09-19 13:00 UTC`.
- `defectfix_03c_sec7_runtime.png` — section 7 renders live. The doughnut paints with two segments and the legend `inside the stated limits` / `over the stated limits`; Chart.js reports labels `["inside the stated limits","over the stated limits"]` with data `[2133193.4, 1546429.03]`. The table below has headers `Operation · € · Claims · Median km · **Position vs the limits**`, 16 rows, first row `PUMP, UREA FLUID · €780,371 · 589 · 20,900 · inside the stated limits`. No payer label is visible, and the file contains no `Who pays` / `who actually pays` string.
- `defectfix_02c_honesty_runtime.png` — the cockpit's "What this does not claim" section renders: the KPI tile reads **"Data checks 153 passed / no failures"**, and the footer reads *"… data verification 153 passed / 1 warn / 0 failed, generated 2026-09-19 13:00 UTC; this HTML was not part of that run"*. The rest of the page (market picker, charts, family selectors) paints normally — no half-built panel.
- `defectfix_10c_scope_callout.png` — the F10 scope callout renders in one block; first sentence reads *"it is Best Value Parts proxy euro divided by value-parts plus contested-original proxy euro within the selected assortment … It is a proxy-euro mix measure inside the parts we sold — not a quantity share …"*. The basis strip above it reads `… data verification 153 pass / 1 warn / 0 fail · 2026-09-19 13:00 UTC`.
- `defectfix_04b_basis.png`, `defectfix_07b_basis.png` — the two basis strips, legible, reading `Data verification 153 pass / 1 warn / 0 fail · 2026-09-19 13:00 UTC` and `Extract generated 2026-09-18; data verification 153 pass / 1 warn / 0 fail · 2026-09-19 13:00 UTC`.
- `defectfix_01_exec.png`, `defectfix_02_leakage.png`, `defectfix_03_warranty.png`, `defectfix_04_aimclass.png`, `defectfix_07_pricingrev.png`, `defectfix_10_dealer.png` — first viewport of each changed file; hero, KPIs and charts paint, no blank page.
- Runtime console: **0 page errors** on 01, 02, 03, 04, 07 and 10.
- Two `#fragment`-only renders came back as blank white images (`defectfix_02b_honesty.png`, `defectfix_03b_sec7.png`). These are a headless screenshot-of-fragment artefact, not page failures; the same regions render correctly in the Playwright element shots above, which is why those two files were replaced by the `*_runtime` versions.
