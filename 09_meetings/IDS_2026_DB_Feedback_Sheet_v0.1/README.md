# Isuzu Dealer Standards 2026 — dealer feedback sheet (v0.1)

A working document for distributors to use with their dealers after the 2026 IDS
evaluation. It turns the evaluation result into something a dealer can read in
two minutes and act on the same day.

This is a **draft for review (v0.1)** — not yet a released pack.

---

## What is in the folder

| Layer | What it is | Use it for |
|---|---|---|
| **A — Executive summary** | One printed page per dealer: total score, band, position against the country average, top 3 strengths, top 3 gaps | Open the review. Hand it to the dealer principal. |
| **B — Dealer workshop pack** | The executive summary plus the section scorecard A–E and a Kaizen action table | The working session with the dealer. |
| **C — Distributor rollup** | Network cover for the whole market: average, band distribution, sections ranked weakest first, full dealer list | Your own planning: where to spend visit time. |
| **D — Commitments** | The block the dealer fills in and returns | Follow-up. All returned files can be merged into one list. |

### Files

```
France/
  IDS_2026_Dealer_Feedback_France_I_B_R_CONCEPT_SARL_v0.1_exec_summary.html    A — prints to one page
  IDS_2026_Dealer_Feedback_France_I_B_R_CONCEPT_SARL_v0.1_workshop_pack.html   B — prints to two pages
  IDS_2026_Dealer_Feedback_France_I_B_R_CONCEPT_SARL_v0.1.xlsx                 A + B + D + country data
  IDS_2026_DB_Rollup_France_v0.1.html                                          C — network cover + dealer list
  IDS_2026_DB_Rollup_France_v0.1.xlsx                                          C — network data + consolidation sheet
_template/
  IDS_2026_Dealer_Feedback_BLANK_TEMPLATE_v0.1_exec_summary.html               blank, to fill by hand
  IDS_2026_Dealer_Feedback_BLANK_TEMPLATE_v0.1_workshop_pack.html              blank, to fill by hand
  IDS_2026_Dealer_Feedback_BLANK_TEMPLATE_v0.1.xlsx                            blank workbook
```

The France files are a **worked example** on real 2026 evaluation data, so the
layout can be judged on real numbers rather than dummy text.

---

## How a distributor uses it

1. **Prepare.** Open the rollup (layer C) and look at the sections ranked
   weakest first. That is where the network as a whole loses points.
2. **Print the one-pager.** Open the executive summary in a browser and print it,
   or save it as PDF. It is designed to fill exactly one A4 page.
3. **Run the review.** Work through the section scorecard, then agree **3 to 5
   Kaizen actions**. The largest scored gaps are already pre-filled; reword them
   so the dealer recognises the action as its own. Every action needs an owner
   (role), a target date and the proof you will accept as done.
4. **Close the loop.** The dealer keeps the Commitments sheet. When the file
   comes back, the commitments of every dealer can be merged into a single list
   for the whole network.

### Working in Excel

The workbook has six sheets:

| Sheet | Content |
|---|---|
| Read me | The same instructions, inside the file |
| Dealer fiche | The printable one-pager |
| Sections A-E | Section scores against the country average |
| Kaizen actions | 3 to 5 actions, with owner / target date / proof |
| Commitments | The block the dealer returns |
| Master data | The full country table, ready for filters and pivots |

Yellow cells are for you and the dealer to fill in. Everything else comes from
the evaluation.

---

## How the numbers are built

| Figure | Where it comes from |
|---|---|
| Total score, section scores, checklist items | 2026 IDS evaluation result report for the country |
| Maximum score | 280 points across sections A–E (A 46, B 80, C 80, D 47, E 27) |
| Country average, section averages | Calculated from the dealers in that country — see the note below |
| Rank | Position among **all** evaluated dealers in the country, highest score first |
| Top 3 strengths | The heaviest checklist items scored in full |
| Top 3 gaps | The checklist items losing the most points |

**Bands:** Good 80% and above · Medium 60% to under 80% · Needs improvement
below 60%. The band is printed together with the scale on every sheet, so the
result can always be traced back.

### Note on the average — please read before challenging a benchmark

> For **France** and **Spain**, dealers marked red in the 2026 ranking
> (evaluation not completed) are excluded **from the average calculation only**.
> They remain part of the network, they stay in the dealer list, and they keep
> their own feedback sheet. For **Italy** and **Switzerland**, every dealer is
> included in the average. Markets without a defined exclusion list include every
> dealer.

Every sheet states the number of dealers behind its own average, for example
*"64 of 84 dealers in average"* for France. This matters: including the
20 not-completed French files would move the France average from **79.8%** to
**62.1%** and would make every dealer look far better than it is.

### Fields shown as N.A.

Where the 2026 evaluation data does not contain a value, the sheet shows
**N.A.** and is left empty on purpose. Nothing is estimated or filled in by
assumption.

---

## Rebuilding the sheets

Generator: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ids_dealer_ranking\build_db_feedback_sheet.py`

```powershell
# one dealer plus the network rollup
python build_db_feedback_sheet.py build --country France --dealer "I.B.R. CONCEPT SARL" --rollup

# every dealer in a market
python build_db_feedback_sheet.py build --country Italy --all-dealers --rollup

# the blank template
python build_db_feedback_sheet.py template

# merge the Commitments sheets of returned workbooks into one list
python build_db_feedback_sheet.py consolidate --in-dir <folder with returned files>
```
