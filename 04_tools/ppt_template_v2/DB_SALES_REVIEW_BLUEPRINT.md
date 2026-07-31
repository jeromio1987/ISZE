# ISZE Distributor Sales Review — Blueprint

Built from the Portugal / I-Motors deck (`build_portugal_gps_target_deck.py`), 28-29 July 2026;
extended after the IUK deck, 29-30 July 2026. Those two went through ~15 and ~4 rounds of
correction respectively before they were meeting-ready — this document exists so the next DB
doesn't repeat the same rounds. Follow it in order; each section names the mistake it prevents.

> **The build is now parameterised — do not copy a script per DB.**
> `C:\Users\jerom\Desktop\claude\ISZE\04_tools\db_sales_review\` holds the multi-DB toolchain:
> `db_profiles.yaml` (every per-DB constant, already filled in for IUK, PORTUGAL, ISD, IBX,
> PETROS, IRELAND), then `preflight.py --db X` → `build_parts_analysis.py --db X` →
> `build_deck.py --db X` → `qa_contact_sheet.py --pptx ...`.
> `preflight.py` replaces the whole of section 1 below with one call; sections 1, 5 and the
> per-DB watch lists are encoded in the profile and printed by it. Read this document for the
> **structure and the tone rules** — those are the parts no script can hold.

---

## 1. Data sources — gather in this order, verify each before trusting it

| Need | Primary source | Fallback | Trap to check |
|---|---|---|---|
| Fleet / UIO base | A real registration file if the DB has one (Portugal: `01_data\Matriculas Isuzu SAP.xlsx`) | `06_uio\_CURRENT\ISUZU_UIO_Overview_2026.xlsx` (V19) | V19's 2026+ forecast is broken (flat 3%/yr decay vs real 10-12% survival curves) — fine for historical years, not for forward projection. See `project_uio_v20.md`. |
| GPS % | `01_data\00_derived\gps_master.csv` | — | **Check the `rate` column before quoting.** It may be a single flat rate (e.g. €250/unit) applied to every vehicle class including trucks, which understates the true target wallet and inflates GPS%. Rebuild with per-segment rates (`prism\data\gps_model_targets.csv`: N35=€296, N75+=€739, F-series=€887, LCV=€250) before presenting. Portugal: flat method said 74.0%, segmented said 63.3% — an 11pp gap. |
| PMS capture | `01_data\00_derived\pms_capture_by_db_year.csv`, filter `line_type=='total'` | — | Has 3 `line_type` rows per category (genuine/bvp/total) — sum all three and you triple-count. Also: **UIO/fleet-size input is frozen identical across every reported year** for every distributor — there is no real multi-year PMS trend in this file, only the actual/numerator side moves. Don't chart a "PMS capture over time" line from it. |
| PMS service intervals | `prism\data\pms_capture_assumptions.yaml` + `prism\modules\pms_capture_config.py` | Web search for the category, but treat results as low-confidence (see below) | Only oil/fuel filter (20,000km, lcv bucket) is CONFIRMED. Air filter (40,000km) is a derived PROVISIONAL ratio. Urea/blower have no OEM-sourced interval — a web search on "AdBlue filter interval" returns wildly inconsistent results (9,000km to 100,000km depending on brand) from non-authoritative sources; don't present any of those as fact. |
| H1/Q-period parts sales | Current CY file (e.g. `01_data\00_derived\cy2026_q1.csv` + the latest tagged billing extract) vs prior-year CY file | — | **Join on `Material`, never `Material Number`** — the columns are swapped in these raw exports (`Material Number` holds free-text description). PN descriptions live in that swapped `Material Number` column — useful once you know the trap. |
| Category classification | `01_data\00_derived\parts_catalog_dimension.csv`, field `pr00_group`, join on `Material` = `part_number` | — | — |
| BVP alternative check | `01_data\00_derived\genuine_bvp_crossref.csv` | — | Coverage is incomplete — a real BVP alternative can exist in the catalog without appearing here. If the user/product team says one exists, trust them over an empty crossref result; label it "per ISZE product knowledge," not as a data finding. |
| **Official reconciliation** | Accounting / PowerBI (ask the user for a screenshot or access) | — | **Always do this check.** This session's own derived H1 sales figure was ~9% off the official PowerBI "Sales amount" — different basis (GPS-signed/filtered vs raw). When the user provides accounting figures, those win, full stop — don't keep the derived number "for comparison." |
| IDS / dealer network | Check `09_meetings\<DB>_IDS_<year>\` first | — | A full dealer-map + fiches pack may already exist from a parallel session — check before building a new one. |

---

## 2. Deck structure (17-slide template, adjust count per DB's actual findings)

1. Cover
2. Agenda
3. Q period Sales Review — actual vs budget, actual vs prior year, by month. **Use official/accounting figures if the user supplies them, not a self-derived cut.**
4. Parts Performance — category-level H1/period movers, waterfall or bar chart, both up and down
5+. One slide per material problem category (each ~-15% or worse) — see tone rules below for exact structure
   - One slide for "New Business" — PNs with zero sales in prior years, cross-checked they don't just have a timing/backdated-invoice artifact, and cross-checked against warranty claims before calling them "new" wins
6. GPS Capture — one line, the clean number, nothing else (see tone rules)
7. PMS Coverage — filter categories with real km intervals labeled, wear-item categories with confidence caveats
8. Fleet trend (multi-year chart, real registrations if available)
9. FY target build-up — **two separate tables, same €-level (both ISZE-net or both dealer-level, never mixed)**: (a) Market Potential = units × rate by segment, (b) Actual + Stretch = target. Never present these as one flat list of percentages that look like they should sum — they don't, and it will get challenged.
10. Growth / Price / Incentive — lead with the DB's own organic growth as credit, state the price move plainly, disclose incentive status honestly (pending/approved/none), don't defend the math unless asked
11. SPA — status/process cards, correct actual workflow, DB-attributed not person-attributed
12. R&M (or equivalent commercial-programme topic) — discussion QUESTIONS, not a status statement
13. Data request (if applicable) — card layout, lead with what's in it for them
14. IDS / dealer network summary (if a pack exists)
15. Next steps — pull every open item stated elsewhere in the deck into one list
16. Closing

### Locked FY2027 lenses

- The customer-facing target is **Sales-to-Dealer** from Dashboard columns P:U:
  `FY2026 Sales-to-Dealer × (1 + fleet movement) × 1.05 × 1.018`.
  If FY2026 Sales-to-Dealer is unavailable, use FY2026 ISZE billing divided by 0.65
  and label the base as a working estimate. ISZE-to-distributor billing remains an
  internal reconciliation measure, not the headline target.
- Growth tables require **prior-period sales above zero** and exclude credit notes
  and warranty/campaign heuristics. Prior-zero/current-positive parts move to a
  **New Business validation** slide; they are not described as incremental growth
  until new model, supersession, timing and campaign explanations are checked.
- Fleet charts show **2019–2026 only**. The 2026 point is labelled as a working
  year-end estimate. UK LCV CY2026 is fixed at **44,926 units**, about **6% below**
  2025, and the title must state decline rather than imply continued growth.

---

## 3. Tone rules — every one of these was a correction in the Portugal round. Apply from the start.

- **Never name an internal colleague on a slide**, and never reference an internal person's uncertainty ("X asked what this means"). If a term needs defining, just define it.
- **Never show internal QA/correction process on a slide** — no "old number vs corrected number" tables, no "PRISM master (flat) vs segment-priced" comparisons. State only the final, correct number. The correction trail stays in chat/memory.
- **Formal, neutral titles for anything declining** — "Brake Parts Performance — H1 2026 vs H1 2025," not "-33%, and it's not a value-tier switch." Save the editorial framing for the takeaway bullets, not the headline.
- **Frame declines as open questions, grounded in what's realistic** — distributors essentially never source competitively at DB level, so lead with price/service questions, not "did you switch suppliers." Ask, don't assert a cause.
- **If a genuine part is declining, ask whether a BVP alternative exists and is growing** — that's the real diagnostic question (value-tier switch vs real loss), not a rhetorical one.
- **State a positive fact once.** Don't reinforce "your growth is good" twice on the same slide — it reads as buttering up, not as analysis.
- **Price increases: state them plainly, don't apologize, don't over-explain.** Lead with the DB's own organic growth as genuine credit before mentioning price. If challenged on "why doesn't the math add up," the two-table structure in section 2.9 is the answer — but don't pre-empt the question by cramming the defense onto the slide itself.
- **Incentive status: say it's pending if it's pending.** Silence reads worse than an honest "not yet approved."
- **Numbers only from an authoritative source, always cited to a full path** in your own working notes (not on the slide itself — customer slides don't carry file paths, only the internal build log/memory does).

---

## 4. Technical build process

- Template library: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ppt_template_v2\` — `isze_deck_builder.py` (layout primitives: `build_cover`, `build_content`, `build_two_col`, `txt`, `bullet_list`, `add_picture_fit`) and `isze_chart_theme.py` (brand-consistent `bar_chart`, `waterfall`, `trend_line`, `donut_share` — matplotlib, no default Office styling).
- Two extra local helpers worth copying from `build_portugal_gps_target_deck.py`: `styled_table()` (red-header/alternating-row Excel-style table via `add_table`) and `card()`/`badge()`/`rounded_rect()` (numbered card layout for discussion-style slides — SPA, R&M).
- **Do not build a Python script per DB any more.** Use `04_tools\db_sales_review\build_deck.py --db X`.
  The two hand-rolled predecessors are `build_portugal_gps_target_deck.py` (still in this folder, kept
  because it built a deck that shipped) and the IUK pair, which have been removed now that the generic
  tool reproduces them to the euro.
- **Mandatory visual QA before ever sending a deck**: `python qa_contact_sheet.py --pptx <path>`.
  It exports every slide via PowerPoint COM, writes the PDF alongside, and stitches the slides into
  3×2 contact sheets — 18 slides become 3 images. Look at all of them.
  On the IUK run the sheets immediately caught an agenda overflowing behind the footer logo, a BVP
  paragraph repeated verbatim on two consecutive slides, and a mis-cased title; on Ireland, a footnote
  overlapping a table on the mixed-segment target slide. None of those were visible from reading the
  build script. Don't skip it because the script "looks right."
  The underlying COM pattern, if you ever need it directly:
  ```powershell
  $ppt = New-Object -ComObject PowerPoint.Application
  $pres = $ppt.Presentations.Open($path, $true, $true, $false)
  $pres.SaveAs($outDir, 17)   # 17 = JPG, 32 = PDF
  $pres.Close(); $ppt.Quit()
  ```
  Needs `dangerouslyDisableSandbox: true` on the Bash/PowerShell call or Office COM won't open the file.
- Export both `.pptx` (editable) and `.pdf` (universal viewing) — `qa_contact_sheet.py` does both.
- **The generated deck is a draft, not a finished deck.** Computed narrative bullets are correct but
  flat and the templated questions are generic. Read it once on the contact sheets and sharpen the
  wording for the specific relationship before it goes out.
- `recalc.py` (the standard xlsx-skill formula recalculator) doesn't work in this Windows sandbox — `AF_UNIX` isn't available. Use Excel COM instead (`$excel.CalculateFullRebuild()`) for any workbook with formulas, then verify with a `data_only=True` openpyxl read that no cell starts with `#`.
- For an accompanying Excel workbook: raw PN-level sheet with `ws.auto_filter.ref` (dropdown filtering on every column) rather than a fragile PivotTable or dynamic-array formula — `FILTER`/`UNIQUE`/`SORT`/`XLOOKUP` are not reliably supported in this environment's recalculation path.

---

## 5. Known data gotchas (condensed — full detail in `project_uio_v20.md` and `project_pms_model.md` memory)

All of these are handled by `04_tools\db_sales_review\common.py` and flagged by `preflight.py`.
They are listed here because they will bite again in any hand-rolled analysis.

- **Credit memos carry a POSITIVE `Net value`.** `BillT` G2 / `SaTy` CR rows are economically
  negative but stored positive in `cy2025_raw.csv` / `cy2026_q1.csv` / the raw extracts; only
  `q1fy2027_billing_tagged.csv` signs them, in `net_value_gps_signed`. Unsigned, IUK's EUR 95,000
  rebate credit turned a -9.8% quarter into a reported -4.5%. **This is network-wide, not an IUK
  quirk** — Q1 2026 alone carries credits for ITUK (142K), UMI (113K), IUK (96K), RSA (47K), ISD
  (30K), IBX (25K), Sverige (24K), Portugal (20K), Ireland (0.7K). Sign them, then keep them out
  of the mover lists as a commercial adjustment.
  ⚠ The July 2026 Portugal deck reported H1 2026 at EUR 935,636 with its EUR 20,000 rebate counted
  as a positive — the correct figure is EUR 40,000 lower. Fix before that deck is reused.
- **A quarter's SAP extract can be badly short, by a DB-specific amount.** `Q1FY2027.XLSX` holds
  35% of the official Power BI figure for IUK but 94% for Portugal. Never publish a current-quarter
  number without the Power BI cut; if it isn't available, move the PN-level window back to the last
  complete calendar quarter instead. Prove completeness by summing Apr-Mar from the CY files against
  `gps_master.csv`'s `bill_FY2026` — expect 0 to +5% (GPS exclusions), not more.
- `Material` / `Material Number` columns are swapped in raw SAP exports — join on `Material`.
- PMS capture file's fleet-size denominator is frozen across years, network-wide, not just for one DB.
- **Never present a bare PMS capture rate.** Show it against the rest of the network on the same
  expected-quantity model — that normalises away the interval assumptions. IUK's 1.9% fuel-filter
  capture is indefensible as an absolute and solid as "1.9% against 16.4% network".
- GPS master file may use a flat, non-segmented rate — always cross-check. Pick ONE convention and
  hold it across the whole deck: the FY27 Extended Target tab's segmented rates, not `gps_master`'s
  flat rate. IUK reads 46% flat vs 57% segmented; mixing them is the fastest way to get challenged.
- **Some DBs read over 100% GPS** (Ireland 122%, Finland, Iceland, and Belgium/Norway close behind).
  That means the denominator is wrong, not that capture is complete. Do not quote a percentage —
  discuss the amount, or agree the per-unit rate first.
- **IBX bills for BE/NL/PL/LUX but its max spend uses the BELGIUM UIO rows only** — its GPS is
  overstated by construction. Say so, or widen the denominator.
- **Greece's billing sits under payer 66, labelled 'RSA'** in `gps_billing_fy_ALLCUSTOMERS.csv`,
  while the warranty file uses 'RSA' for Norway. Joining those two on the name merges Greece into
  Norway. Live bug at source.
- **Not every DB has IDS 2026 data** — Germany and Ireland have none. Drop the slide rather than
  substitute something.
- N35 Grafter (3.5t) trucks get mispriced at the N75+ rate unless manually split out — check the real
  tonnage mix from registration data if available, not just the V19 "LD" bucket total.
- Self-derived sales figures can diverge materially from official accounting/PowerBI — always
  reconcile if the user can provide the official cut.

---

## 6. What's Portugal-specific vs. transferable

**Transferable as-is:** deck structure, tone rules, build tooling, QA process, the data-source checklist and its traps.

**Needs re-deriving per DB:** every number. In particular, check early whether the DB has a Matriculas-equivalent (real registration data) — Portugal did; not every market will. Without it, fall back to V19 history (pre-2026, which is sound) and flag the forward projection as V20-pending rather than presenting V19's broken 2026+ forecast.

**Per-DB judgement the tool cannot make for you**, over and above the watch lists in `db_profiles.yaml`:

| DB | The thing that will decide the meeting |
|---|---|
| IUK | Q1 FY27 is +13% on budget but the whole beat is April; May and June are both under. Orders ran at 56% of shipments. Brakes -54% and filters -65% — and BVP fell too (EUR 263K → 132K), so the volume left the tent altogether rather than moving to the value tier. |
| PORTUGAL | Has real registration data — use it for the fleet chart. Fix the rebate-sign error in the shipped deck before reusing it. |
| ISD | Mapping says LCV-only, UIO says mixed. No IDS data, no FY26 Sales-to-Dealer. Q1 CY26 is up ~34%, so this is a good-news meeting — do not manufacture a problem slide. |
| IBX | The GPS number is overstated by construction (BE/NL/PL/LUX billing over a Belgium-only denominator). Lead with that honestly or the whole target discussion is contestable. |
| PETROS | Q1 CY26 down ~41%. That is the meeting. Get the Power BI cut before presenting anything. |
| IRELAND | GPS reads over 100%. No percentage anywhere in the deck — amounts only, and offer to agree the per-unit rate. |
