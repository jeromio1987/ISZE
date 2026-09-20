# DB Sales Review — multi-distributor toolchain

Parameterised build for the distributor sales-review pack (deck + parts workbook).
Replaces the copy-a-script-per-DB approach: Portugal and IUK were each built by hand,
this folder is the generalisation of both.

Method, deck structure and — importantly — the **tone rules** live in
`..\ppt_template_v2\DB_SALES_REVIEW_BLUEPRINT.md`. Read that first. This folder only
implements it.

---

## Run order

```bash
python preflight.py --db ISD
```

Resolves every field in the DB's profile against the live files and prints one report:
payer match, window completeness against canonical FY billing, credit memos, GPS (both
conventions), PMS vs network, UIO, FY2027 target, IDS, warranty, the official quarter,
and the DB's own watch list. Exits 1 on a blocking problem. **This one call is the whole
of the discovery work** — do not go hunting through source files by hand.

```bash
python build_parts_analysis.py --db ISD
```

Writes `09_meetings\<DB>_Sales_Review_2026\ISZE_<DB>_<window>_Parts_Analysis.xlsx`
(14 sheets) plus `_summary.json`.

```bash
python build_deck.py --db ISD
python qa_contact_sheet.py --pptx "..\..\09_meetings\ISD_Sales_Review_2026\ISZE_ISD_Sales_Review_FY2027.pptx"
```

**Full pack (shared + deep dive)** — preferred for Hungary / IBX / UMI and next DBs:

```bash
python build_full_deck.py --db IBX
```

See blueprint §7. Lands `ISZE_<DB>_Sales_Review_FY2027.pptx` plus `_shared_only.pptx`.

The shared-only deck lands in its `09_meetings\<DB>_Sales_Review_2026\` folder. The QA step exports the PDF and stitches the slides into
3×2 contact sheets — read those instead of opening 18 separate images. The mandatory
visual QA pass in the blueprint is satisfied by looking at the sheets.

---

## Adding a distributor

Copy a block in `db_profiles.yaml` and fill it in. Every field is documented at the top
of that file. `preflight.py` tells you which ones do not resolve.

The one field you cannot derive is `pbi:` — the official Power BI quarter. Request
the screenshot and type the figures in. **Do not invent the sales-review slide from the SAP
extract**: it is short by a DB-specific amount (IUK ran at 35% of the official cut while
Portugal ran at 94%). Missing or partial `pbi:` skips that slide; the rest of the deck still builds.

Build-enabled profiles: `IUK`, `ISD`, `IBX`, `PETROS`, `IRELAND`, `UMI`, `NORWAY`,
`SWEDEN`, `HUNGARY`, `FINLAND`, `ROMANIA`, `DENMARK`, `ICELAND`, `CYPRUS`, `MALTA`.
`PORTUGAL` remains registered but is excluded from the standard build list.

---

## What the tools do automatically

- **Credit memos** (`BillT` G2 / `SaTy` CR) are signed negative. They carry a *positive*
  Net value in the raw exports, so an unsigned read turns a rebate credit into a gain.
  They are then excluded from the mover lists as a commercial adjustment.
- **Movers** are cut on **commercial** gross parts lines for **CY H1 (Jan–Jun, Q1+Q2)** vs
  prior-year H1 — warranty/campaign PNs excluded — rolled up to ITC family (Newest P/N) as
  well as raw PN, joined on `Material` (the column *labelled* `Material Number` holds the
  description — the headers are swapped in these exports). CY2026 H1 = `cy2026_q1.csv`
  (Jan–Mar) + `q1fy2027_billing_tagged.csv` (Apr–Jun).
- **Warranty exclusion (all DBs):** ERP has no warranty doc type. Movers drop PNs that appear
  on `warranty_raw_grain.csv` claim lines for that DB (assess-month window with a 3-month lag
  before the prior H1) plus a PN/description text heuristic (PM sensor / warranty / campaign /
  recall). shared takeaways label the chart **commercial / ex-warranty**. Limitation: all
  billing of a claim-matched PN is dropped, not only the claim units.
- **Growth is incremental only:** prior-period sales must be above zero. Prior-zero /
  current-positive lines are quarantined on the New Business slide for validation as a new
  model, supersession, timing item or campaign.
- **FY2027 target uses the Sales-to-Dealer lens:** Dashboard columns P:U, with the locked
  fleet movement, 5% price adjustment and 1.8% additional growth. Missing FY2026
  Sales-to-Dealer KPI is clearly imputed from FY2026 ISZE billing divided by 0.65.
- **Fleet charts stop at 2026.** The 2026 point is a working year-end estimate. UK LCV is
  locked at 44,926 units (about -6%); near-term estimates use the corrected survival basis.
- **Decline slides** are generated for the top declining categories, with per-category
  question sets from the bank in `build_deck.py`. Each movers / decline / growth slide
  names the **largest-EUR PN drivers** (increase and decrease). Optional `vehicle_model`
  is joined from BVP/PMS application tables when the PN is in that basket — not a full
  EPC; browser catalogue is not required for the PN-EUR story.
- The genuine-vs-BVP read is stated once on the first decline slide only.
- **Slides degrade rather than lie.** No IDS data → no dealer slide (ISD and Ireland have
  none). No Sales-to-Dealer figure → the data-request slide changes its framing. GPS over
  100% → the amount-based variant, no percentage quoted anywhere (Ireland).
- **PMS is shown against the network**, never as a bare capture rate. All markets sit on
  the same expected-quantity model, which normalises away the interval assumptions — the
  only defensible way to put these numbers in front of a distributor.

## What still needs you

The deck is a meeting-ready **draft**, not a finished deck. Computed narrative bullets are
correct but flat; the templated questions are sensible but generic. Read it once on the
contact sheets and sharpen the wording for the specific relationship. The watch list
printed at the end of `build_deck.py` is not optional reading.
