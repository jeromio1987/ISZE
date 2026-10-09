# Pricing revision

Open this folder when you want the price-list work and the AIM classification table.

## Open first

1. Double-click `OPEN_Pricing_revision.cmd`  
   Opens the live pack from 14–20 September (base-price compare, FX view, stack simulation, AIM-by-source, classification). Start inside that pack at `00_START_HERE`.
2. Or double-click the shortcut **AIM pricing pack 14–20 Sep** — same folder.
3. Day-to-day new / superseded PN into SAP: double-click `OPEN_PriceCalc_AIM.cmd`  
   Opens the AIM-aligned PriceCalc (Config matched to live `config.yaml`). Rules: `PRICECALC_AIM_OPS.md`. One open ask: `PRICECALC_AIM_VOICE_ASK.md`.

Live pack:

`C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920`

## In this folder

| File | Use |
|---|---|
| `OPEN_PriceCalc_AIM.cmd` | Opens AIM-aligned PriceCalc (FOB → SAP). Not a substitute for the revision pack. |
| `PRICECALC_AIM_OPS.md` | How to use PriceCalc if you skip to AIM-led margins |
| `PRICECALC_AIM_VOICE_ASK.md` | Spec Q1 — can ISZE set new-PN margin by AIM category? |
| `AIM_Master_PN_Categories_Figkey_20260921.csv` | Power BI (BVDV) — flat AIM + figure-key table |
| `AIM_Master_PN_Categories_Figkey_20260921.xlsx` | Same table for browsing (double-click `OPEN_AIM_Master_PN_Categories_Figkey_20260921.cmd`) |
| `ISZE_AIM_Management_20_Slides_2026-09-21.pptx` | AIM management slides |
| `ISZE_Pricing_Simulation_Spec_Basis.xlsx` | The full pricing simulation: 47,618 part lines, the base-price step re-cut by captured-demand position and by price against the independent aftermarket. Double-click `OPEN_ISZE_Pricing_Simulation_Spec_Basis.cmd` |

The simulation workbook is the complete one. It is a copy of the master, which stays in the live pack at
`C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\03_Simulation_stack\ISZE_Pricing_Simulation_Spec_Basis.xlsx`.
It models the base-price step that is already published (5.9616% weighted, EUR 1,652,141) and proposes no price change. The companion that shows what the revision does to each market's margin is `ISZE_Pricing_Stack_Simulation_2026-09-19.xlsx` in that same `03_Simulation_stack` folder, opened by `OPEN_Pricing_Stack_Simulation.cmd`.

In the CSV/Excel amount column `l12m_billed_eur`: billed sales from 1 January 2025 to 30 June 2026 (eighteen months), EUR 52,414,407.82 in total. The `l12m` in the name is an old label — it does not mean twelve months.

## Archive

Older backups of the AIM table sit in `_archive\`. Do not use those for Power BI.
