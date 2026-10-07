# Memory — weekly backlog / IML warehouse read (WK41, 2026-10-07)

Working notes behind the WK41 backlog page. Internal. Not a KPI sheet.

## What the two source files are

**1. Natalie Vernimmen — "Backlog info file VP – update WK 41"** (Tue 6 Oct 2026, 13:47 local).
Attachment `BO info VP 06-10-2026.xlsx`. This is the **customer-side backlog**: what our
distributors have on order with ISZE and have not received.
- Sheet `DATA` — 2,022 usable lines. Columns: Sold-to n° / Customer / Sales Doc. /
  Customer Reference / Material / Material description / SaTy / Req.Dlv.Dt / Open Qty /
  Transit qty / ETA / Priority / Next ETA Supplier / Tentative future ETA ISZE /
  Confirmed Qty / MoT / Remark / Shipping Location.
- Sheet `ETD` — 1,812 rows, 932 part numbers, 296 PO refs. The IML supply view
  (PO REF / PART NUMBER / MoT / QTY / TTL BO QTY ISZE / PRIORITY / ETA / ETD / CONFIRMED QTY /
  ETA ISZE / TRANSIT REF).
- Sheet `ENQUIRY SHEET` — lookup sheet, header row 7.
- Sheet `PASTE DATA PO BACKLOG` — empty staging tab.
- "VP" = Vehicle Parts. Same mail pattern goes weekly to every distributor
  ("BO overview … (WK nn)"), e.g. ITUK, UTI, IMOTORS, Germany, Benelux, Ireland, EME.

**2. `01_data\ISZE_Order Status as of 2 October 2026_request to check.xlsx`** — the **IML
warehouse** side. One sheet `isze`, 2,102 lines. Columns: Order No (= the IML purchase order) /
Mode (S sea, A air) / PN / Supplied PN / Part Name / AcceptNo. / Item / Sub Item / Q'ty /
Procced / Expected Allocation date / Allocated / Picked / Packed / Invoice / Shipped / ETD /
INV.No. / Case No. / Status / Booking No. / HS Code2.

## The join, and its limit

- `ETD.PO REF` = `isze.Order No`. A real bridge. `po_ref|pn` matches **215 of 1,806** ETD keys.
- `DATA.Sales Doc.` is a **customer order number** (202852, 304722 …). It never equals the IML
  Order No (4510017xxx / 4610010xxx). Overlap: **0**.
- **There is no purchase-order → customer link on disk.** So a warehouse line cannot be
  attributed to a distributor without a new key. The page shows the two stacks side by side and
  never merges them.
- Parts that appear in **both**: 249. Those parts carry 3,823 pieces of in-scope customer backlog
  out of 14,739 — i.e. the two views are not the same problem.

## What the warehouse file actually says (as of 2 Oct 2026)

Status is the process state, not the delay state. The delay is in the **date columns**:

| Status | Lines | Pieces | Median days since Procced | Oldest |
|---|---|---|---|---|
| TO BE PICKED | 856 | 21,002 | 24 | 367 d |
| TO BE PACKED | 597 | 8,829 | 45 | 192 d |
| READY FOR SHIPMENT | 602 | 9,296 | 45 | 227 d |
| BACK ORDER | 47 | 4,824 | 17 | 94 d |
| **Total** | **2,102** | **43,951** | | |

- **1,090 lines (19,767 pieces) have been sitting more than 30 days.** 542 of them are
  "ready for shipment" and 490 "to be packed" — finished goods not moving out of the building.
- 58 lines are over 90 days; 4 are over 180 days.
- `Invoice` and `Shipped` are filled on **0** of 2,102 lines — this extract stops before dispatch,
  so it can never show what has actually left.
- Sea is 2,067 lines; Air 35.

## What the customer backlog says (as of 6 Oct 2026)

- 2,022 lines, 27 distributors, 15,986 pieces. **Scope used on the page: 21 distributors,
  1,846 lines, 14,739 pieces** (MIDI and Russia / Kazakhstan accounts left out).
- Urgency mix is SaTy: SOR 1,488 / VOR 333 / RUSH 175 / PRD 25 / SVOR 1.
- Big lines: ITUK 8,625 pcs (628 lines), UMI 2,411, UTI 699, Ireland 627, I.M. Parts 585,
  iMotors 421. Ireland's oldest line is 453 days; ITUK's 1,625.
- Supply split: 1,349 lines ship from ISZJ, 672 from IMIT.
- Of 1,812 IML supply rows, **959 carry only the supplier's sea-freight estimate (WK42–WK46)**;
  a firm ETD exists on 163. Jerome expects a fresh ETD file at 16:00 on 7 Oct.

## Decisions taken on 2026-10-07 (do not re-litigate)

- The page leads with **lines, pieces and waiting time**, not euro. Jerome chose "no euro" for
  this view; a valuation is possible later from observed selling prices but was explicitly parked.
- Scope: all VP distributors **except MIDI and the Russia/Kazakhstan accounts**.
- The two files stay **separate tabs**, because the PO-to-customer bridge does not exist.
- Header click = sort, parts-family chip or bar click = filter. Both verified by clicking the
  built page inside the browser, not by reading the code.

## AIM coverage - the number that needs care

`aim_master_v2.csv` holds **165,001 distinct part numbers but only 24,915 carry a level-1 family.**
So "no AIM" on a page is almost always about the file, not about the order. Split it three ways
(lines, WK41):

| Family status | Customer backlog | IML warehouse |
|---|---|---|
| Has a parts family | 1,606 (87.0%) | 1,267 (60.3%) |
| In the classification file, no family assigned yet | 162 | 400 |
| Not in the classification file at all | 78 | 435 |

- The middle row is **our own housekeeping** - the part exists in the file, nobody assigned a family.
- The bottom row is mostly the **warehouse's** older repair and dealer-fit parts (injection pipes,
  oil cooler cores, valve springs). **None of the 353 unclassified warehouse part numbers appears
  anywhere in our billed history** (`sales_fact.parquet`), which is why they were never in the
  classification. The customer-side unclassified set is different: seat backs, antennas, tail-gate
  handles - a previous model generation.
- Matching must ignore leading zeros: the file stores some keys with them and some without.
  `pd.read_excel` **without** `dtype=str` strips leading zeros from both source files, because Excel
  stores those part numbers as numbers. Read every part-number column as text.

## The chart matrix - testing the whole space (eighth pass, 2026-10-07)

Four reports of blank charts, each on a different path, because each round tested one path. The
method was the problem. There is now a harness.

- `_qa_charts/matrix_probe.js` drives every tab and every `GROUP BY` option and reads each canvas
  from the live chart instance.
- `_qa_charts/server.py` is a local QA server with a `POST /save` so the page can hand the result
  back to disk (stock `http.server` cannot accept a POST).
- `_qa_charts/to_csv.py` writes `matrix.csv`. **Run 64 combinations: 64 PASS, 0 FAIL.**
- Test against a **frozen snapshot** (`_qa_charts/freeze.py` -> `frozen_now.html`), never the live
  file, because another worker is rebuilding it (see below).

### The mechanical cause of the fourth report - mine

`sizePanel()` called `resize()` on every chart each time a panel was shown. **`resize()` clears a
doughnut's arc geometry, and `update('none')` does not repaint it**, so the doughnut on the parts tab
was blank with 0 arcs on every dimension change. I introduced this in the sixth pass while fixing the
hidden-panel sizing. Now `sizePanel()` only resizes a canvas that is genuinely unsized, then calls a
full `update()`.

### Also fixed this pass

- **The parts tab never honoured its dimension** - its charts were hard-wired to AIM family and
  sea/air, so changing the dropdown did nothing visible there.
- **Charts no longer animate** (`animation:false`), so geometry exists the moment a chart is built.
- **Defensive layer**: grouping always recomputed from the full row set; an empty grouping falls back
  to the unfiltered one and says so; a doughnut has the same guard; and after each render every
  visible canvas is checked for drawn elements and repainted once if empty. Anything used is listed
  on screen in a "Fallbacks used during this render" strip, not hidden.

### Still not working - do not claim otherwise

Clicking a bar narrows the table on the **delay** and **backlog** tabs, and Clear restores it. It does
**not** narrow the table on the **parts**, **who-is-waiting** and **waiting-over-30-days** tabs,
because those three tables are built from tables computed in the payload (`D.dparts`, `D.per_part`,
`D.wait`) rather than from the filtered rows. Next thing to fix.

### The concurrent writer - read this before touching this page again

**Another worker is writing this page and its builder at the same time as this agent.**

- 18:48: `01_data/00_derived/aim_master_v2.csv` rewritten by a process named `pre_forward_repair_oct4`.
  Warehouse family coverage moved **60.3% -> 71.6%**, backlog **87.0% -> 90.1%**.
- 19:11-19:16: `_build_backlog_iml_wk41.py` was edited by something other than this agent (new wording
  about clicking a distributor bar) and it rebuilt the page at 19:12 and 19:16.
- Consequence on the page: the Definitions **heading** still says "Why the warehouse reads 60% and the
  backlog 87%" while its own body reads 71.6% and 90.1%. That inconsistency is real and unresolved.
- Before editing, check the mtime of the builder and the page. Freeze a snapshot before testing.

## Regrouping, the waiting view and the build stamp (seventh pass, 2026-10-07)

Three merged asks. None of them changed a figure.

**1. The dropdown now re-groups the charts, not just the drill dimension.** Until this pass the two
breakdown charts on the warehouse and customer backlog tabs stayed fixed (band x status, distributor)
while the dropdown only changed what a click filtered on. Now the first chart shows the selected
dimension and the second shows the longest wait in it, both retitled to name the grouping. The label
changed from "Go deeper by" to **"Group by"** on all panels because the old wording understated it.

**2. New tab, "Waiting over 30 days"** - the answer to his actual ask, "parts waiting for 30 days and
I want to know what kind of parts and for which customers":
- Part A: the 1,090 over-30-day lines cut by the **noun in the description** (48 groups). Biggest:
  element 5,479 pcs / 5 lines, gasket 3,659 / 110, "other" 3,501 / 290, stud 826, bolt 748, sensor 558.
  Each group carries lines, part numbers, pieces, median, longest wait, orders, 5 examples.
- Part B: the **part-number link** to customers, labelled as a link and not a traced order. Gasket
  group: 110 lines, 9 distributors. 14 of the 48 noun groups have no customer order carrying those part
  numbers - printed as such, not filled in.
- Grouping options: kind of part (in words), AIM family, Catalogue category, Sub-family.

**3. Build stamp.** Generated in the builder from a hash of the key content figures, written to a fixed
corner badge and the footer, so it cannot drift from the file. This build: `2026-10-07 18:19 build 15c72e7dff`.

**On the second report (stale filter):** the dimension-change handler already cleared the filter in the
builder before that report, and the blank state could not be reproduced on this build. Most likely he was
looking at an earlier file - which is exactly why the stamp now exists. Recorded in the receipt as such
rather than claimed as fixed.

**A defect of my own:** the new waiting block was first inserted *after* the `renderAll()` call, so it
never ran and the tabs after it did not render either. Moved inside the render pass. Caught because the
build stamp and the coverage block were silently empty - a symptom worth remembering: when the tail of
the page is blank, look for code placed after the render call.

## Blank charts when a tab is clicked - the real bug (sixth pass, 2026-10-07)

Jerome reported the delay tab's two charts blank with a 0..1 axis. **Root cause: a chart built while
its panel is `display:none` gets a zero-size canvas, so Chart.js falls back to a 0..1 scale and draws
nothing. Showing the panel later does not resize the chart.** Only `p-delay` is visible at load, so
only its charts were ever right.

Measured on a plain load then clicking each tab: **10 of the 12 charts on the page were blank** -
`ch-waim` (yMax 15 against data 6795), `ch-mode` (canvas 0x0), `ch-ov` (13 vs 131), `ch-uti1` (no bars),
`ch-uti2` (no points), `ch-fill` (16 vs 4), `ch-cust` (20 vs 8625), `ch-custage` (20 vs 1625),
`ch-bofam` (15 vs 2011). The delay tab was fine even before the fix, which is why the report and the
screenshot of *that* tab are slightly confusing - the blank state he photographed is reachable by
switching tabs and coming back, which is exactly what the dimension change did.

**Fix:** `show()` now calls `sizePanel(t)` (`resize()` then `update('none')`) for the panel being
switched to; `renderAll()` ends with `sizeVisiblePanel()` so a dropdown or filter redraw also
re-measures; `draw()` keeps the forced synchronous `update('none')` the click geometry needs.

After the fix, every tab on a plain load plus click: delay 20000 / 25000 / 900 (6/6 and 4/4 bars),
parts 7000 (16/16) plus 2/2 doughnut arcs at full radius, who 140 (14/14), recur 100 (39/39) plus a
39-point line at yMax 250, fill 5 (17/17), backlog 9000 / 1800 / 2500 (21/21, 21/21, 16/16).

**Second bug found and fixed on the same path:** switching the "Go deeper by" dimension kept the old
filter value, which is meaningless in the new dimension (a waiting-time band is not a process status),
so the chart filtered to nothing. The dropdown change now clears the filter.

**Why the earlier QA missed it: I opened each tab with a `#hash` URL**, which makes the panel visible
at load, so the charts were built at full size. Jerome loads plain and clicks. Screenshots from now on
must be taken after clicking the tab, never via a fragment.

## Clickable charts and drills (fifth pass, 2026-10-07)

Jerome: *"why can't I click on this make a dropdown on how to go deeper customer or AIM classification?
that's how you create something ok?"* Standard set: every chart clickable, each with a go-deeper-by dropdown.

- Clickable: warehouse waiting-time stacked bar, status bars, over-30-days bar, parts-family bar,
  air-against-sea doughnut, and on the backlog tab the distributor bar, oldest-order bar and family bar.
- Dropdowns are per panel and offer only what that tab has. Warehouse: AIM family, Catalogue category,
  Process status, Sea or air, Waiting-time band, Part. Backlog: Distributor, AIM family,
  Catalogue category, Order type, Age band, Ships from, Parts family group.
- **No Distributor in the warehouse dropdown**, with the reason printed under it. A chart that offered
  it would print a dimension that does not exist.
- Two implementation traps, both now fixed and worth remembering:
  1. **Chart.js 4.4.1 `getElementsAtEventForMode` returns nothing for a real click here**, even when
     the element reports `inRange: true`. Do not use the built-in `onClick`. The page resolves clicks
     itself from the bar and arc geometry.
  2. **A `responsive: true` chart has no bar geometry until the next animation frame**, so a click
     right after a re-render misses. `draw()` forces `update('none')`.
- Verified by real DOM clicks over localhost: 31-60 days bar -> 919 lines / 18,531 pieces = the bar's own
  height; TO BE PACKED segment in that bar -> same; dropdown switched to Process status -> 8,829 pieces
  = the source total for that status; Clear filter -> back to 2,102 / 43,951.

## Scope addition folded in (fourth pass, 2026-10-07)

Two vocabularies, shown side by side on every table that shows a family. Labels as agreed:
**AIM family** (resolved from `aim_l1`, falling back to `aim_l1_fixed`) and **Catalogue category**
(`cat_l1`). Where a line has neither, the AIM column carries `in AIM, no family yet` /
`not in the AIM file` and the catalogue cell stays blank.

Verified coverage, matching the approved figures:

| Denominator | AIM family | Catalogue category |
|---|---|---|
| IML warehouse, 2,102 lines | 1,267 = 60.3% | 1,658 = 78.9% |
| Customer backlog, 1,846 lines in scope | 1,606 = 87.0% | 1,720 = 93.2% |

- Warehouse split: 400 lines in the classification file with no family, and `cat_l1` is filled on
  **all 400**. The other 435 are absent from every list, so both columns stay blank.
- Backlog split: 162 no-family and 78 absent.
- Why 60% vs 87%: `aim_master_v2.csv` holds 165,001 part numbers and only 24,915 carry a family,
  because the family is filled from the parts we bill. The difference between the two files is
  **which parts are in them** - the warehouse list is slow, older and one-off parts; the backlog is
  what is on order now.
- The 435: all genuine ten-digit Isuzu part numbers; none billed in any month Jan 2023 - Aug 2026.
  Leading-six-digits overlap measured here at **292 of 345 against billed parts** and 332 of 345
  against the classification master. The brief says 339 of 345, which I could not reproduce, so the
  page states the overlap without a count. Needs a check on the denominator.
- The 163: measured 23 real family names in the old backup file (29 distinct `aim_l1` values, 6 of
  which are catalogue names). 163 did not reproduce at name level. Page wording is as instructed on
  this point, so a reader outside should not treat 163 as settled.

## The delay answer (third pass, 2026-10-07)

- **1,090 lines over 30 days, holding 19,767 pieces.** Median wait across the whole file is 31 days;
  the longest single line is 367 days (order 4610029452, a cartridge kit, processed 30 Sept 2025,
  still only picked).
- **1,032 of those 1,090 are to be packed or ready for shipment.** Only 58 are BACK ORDER. Across the
  whole file only 47 lines are true back orders (4,824 pieces). So the big queue is finished goods
  not leaving, not orders waiting on Japan. Read it as work in progress: IML packs to clear the
  backlog, which is what the pack queue is.
- **The bridge does not exist, and this is now proven, not assumed.** Every reference in the 16
  per-distributor WK41 files was tested against IML's 140 order numbers: 391 Sales Doc. values, 0
  matches; 391 Customer Reference values, 0 matches. The number ranges are different systems
  (customer 3xxxxx / ST0000xxxx; IML 4510017xxx / 4610013xxx). So the customer behind a delayed
  line cannot be named from any file we hold. The who-is-waiting tab is a part-number overlap
  (146 of 781 delayed part numbers also sit on an open order, 269 lines, 2,380 pieces, 14
  distributors) and is labelled as a warning, not a traced document.
- **The recurrence proof (the cleanest supply evidence).** UTI, 39 weekly lists WK2-WK40 2026:
  116 parts, 9 of them on the list 20 or more weeks, 50 on 10 or more. The same part ordered again
  and again and never arriving is a supply weakness, not a slow warehouse. The list peaked at 58
  lines in WK23 and the median age fell from 40 days (WK2) to 27 (WK40), so UTI is recovering.
- **Fill rate against the FY26-27 targets: 12 of 20 distributors are below their own target.**
  Worst gaps from the targets file: WAE (Hungary) now 73.6% vs 82% target, Petros (Greece) 60% vs
  80%, IBX 81.8% vs 90%, Imotors (Portugal) 83.6% vs 87%, IUK 92.5% vs 95%. Network standard is 95%,
  floor 92%. Latest reported month is printed beside every value because several are stale (ISD Jan
  25, UMI Feb 25, UTI May 26).

## What is missing (the asks)

1. **Destination customer or sold-to on the IML warehouse extract.** One column. This is the whole
   answer and nothing else closes it. IML knows it; the warehouse document does not carry it.
2. Actual dispatch date per line, so "ready for shipment" can be told apart from "forgotten".
3. Actual arrival date per line - the only way to measure time underway. Not in SAP, so not in PBI.
4. Fill rate and back-order lines for the distributors that do not report (UMI, Germany, Benelux,
   Denmark, Cyprus, Greece).

## Corrections made in the third pass

- Fill-rate table had value and month swapped; fixed and re-verified on the rendered table.
- The network total row was being read as a distributor; removed.
- The verdict sentence wrongly implied IML packs to fix a back-order problem. It now says plainly
  that the packing queue is the work in progress and the back-order tail is the part waiting on Japan.
- The customer backlog tabs were kept as their own tab rather than dropped.

## Open asks

1. An **ETD file** with a firm ETD per line (promised 7 Oct 16:00).
2. A **PO → customer / distributor** column on the warehouse extract. Without it, "which customer
   is delayed" can only be answered from the customer side.
3. IML to confirm whether `Expected Allocation date` means anything (it is blank on all 2,102 rows).
