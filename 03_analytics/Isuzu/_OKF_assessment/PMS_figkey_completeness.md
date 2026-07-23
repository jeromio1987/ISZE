# PMS Fig-Key Completeness — Missing Parts (CY2025)

> **Historical / superseded (2026-06-15).** The 230 in-scope PNs from this analysis are included in `03_analytics/Isuzu/prism/data/pms_capture_supplement.csv` (339 PNs total with brake_rotor; built 2026-06-15, consumed by `build_bvp_p0_p1.py`). Do not re-add `pms_missing_pns_figkey.csv` as if still open.

**Method:** the full `parts_catalog_dimension.csv` (164,968 PNs) carries `fig_key` + `fig_key_label` + a PR00 `pms_category` — the authoritative classification. Capture only uses the 919-PN BVP dim + crossref + registry (`tag_pms_sales`). **Missing = catalog says PMS, sold CY2025, but not in the capture universe.** Every line carries PN · description · unit price · fig_key. Fix-list CSV: `pms_missing_pns_figkey.csv`.

## Headline

- **In-scope missing (the 13 current PMS categories): 230 PNs, €978,233** — **higher than the €880K keyword estimate**: the catalog catches air-filter elements, brake shoes and pressure plates my description scan missed. This is the complete fix-list for the current model.
- **Excluded 39 filter ASSEMBLIES (€81,886)** per your steer — the catalog tags them a filter but they're housings (€50–208/u). The **fig_key separates them**: `041-002`=element (keep) vs `041-001`=assembly (drop). DPD stays out too.
- **fig_key check is clean:** only 19 stragglers (€4,000) under the touched figures have a blank category — no hidden pockets *within* scope.
- **Scope gap (the bigger answer): 397 PNs / €1,758,593 are PMS-adjacent maintenance categories the model doesn't have at all** — led by **brake rotors** (discs that pair with the pads we're adding).

## In-scope missing — add these to the PMS universe

| Category | PNs | Qty | € | avg price |
|---|---:|---:|---:|---:|
| brake_pad | 13 | 6,178 | €424,767 | €69/u |
| oil_filter | 32 | 16,358 | €135,788 | €8/u |
| brake_shoe | 87 | 3,778 | €112,735 | €30/u |
| clutch_disc | 14 | 809 | €101,980 | €126/u |
| fuel_filter | 37 | 10,378 | €95,887 | €9/u |
| air_filter | 12 | 3,499 | €43,352 | €12/u |
| clutch_pressure_plate | 12 | 605 | €36,150 | €60/u |
| urea_filter | 5 | 1,383 | €14,085 | €10/u |
| clutch_booster | 8 | 31 | €8,517 | €275/u |
| clutch_kit | 6 | 56 | €4,529 | €81/u |
| release_bearing | 4 | 68 | €443 | €7/u |
| **TOTAL** | **230** | 43,143 | **€978,233** | |

### Biggest in-scope missing PNs (PN · description · price · fig_key)

| PN | Description | Unit € | Qty | € | fig_key (label) | cat |
|---|---|---:|---:|---:|---|---|
| `8975056801` | PAD KIT; CALIPER,DISC BRK,FRT | 71.36 | 4,293 | €306,344 | 302-017 (Brake pad) | brake_pad |
| `8982984040` | ELEMENT; OIL FILTER | 12.46 | 7,849 | €97,810 | 050-002 (Oil filter (element)) | oil_filter |
| `8976526220` | PAD KIT; CALIPER,DISC BRK,FRT | 60.28 | 1,558 | €93,919 | 302-017 (Brake pad) | brake_pad |
| `8975425390` | ELEMENT KIT; FUEL FILTER | 9.83 | 5,251 | €51,596 | 041-002 (Fuel filter (element)) | fuel_filter |
| `8983476230` | DISC; CLUTCH | 142.29 | 302 | €42,972 | 201-001 (Clutch disc) | clutch_disc |
| `8981475700` | ELEMENT; FUEL FILTER | 8.43 | 4,770 | €40,202 | 145-002 (Fuel filter) | fuel_filter |
| `8975435900` | DISC; CLUTCH | 155.27 | 240 | €37,264 | 201-001 (Clutch disc) | clutch_disc |
| `5876150531` | ELEMENT; OIL FILTER | 4.12 | 7,861 | €32,352 | 050-002 (Oil filter (element)) | oil_filter |
| `8983989321` | PLATE ASM; PRESSURE,CLU | 115.09 | 213 | €24,514 | 201-002 (Pressure plate / cover) | clutch_pressure_plate |
| `5876150021` | FILTER; ACL | 12.25 | 1,935 | €23,707 | 130-006 (Air filter) | air_filter |
| `1471702670` | SHOE; BRK,RR | 109.29 | 165 | €18,032 | 305-001 (Brake shoe / lining) | brake_shoe |
| `1471704851` | SHOE; BRK,RR | 75.79 | 216 | €16,371 | 305-001 (Brake shoe / lining) | brake_shoe |
| `5878316930` | SHOE KIT; BRAKE,RR | 205.65 | 75 | €15,424 | 305-218 (Brake shoe / lining) | brake_shoe |
| `8983753330` | DISC; CLUTCH | 113.05 | 124 | €14,018 | 201-001 (Clutch disc) | clutch_disc |
| `5876150041` | FILTER; ACL | 10.75 | 1,215 | €13,055 | 130-006 (Air filter) | air_filter |

## OUT-of-scope categories — decision needed (NOT added without your call)

These carry a catalog `pms_category` but are **not** in the current PMS model. Adding any means a new category + a service/wear factor in `pms_capture_assumptions.yaml` (and a FACTS re-sync).

| Category | PNs | Qty | € | avg price | PMS-relevant? |
|---|---:|---:|---:|---:|---|
| brake_rotor | 109 | 20,714 | €1,295,197 | €63/u | yes — pairs with brake pads |
| leaf_spring | 178 | 6,792 | €331,167 | €49/u | no — repair |
| shock_absorber | 71 | 5,045 | €117,471 | €23/u | maybe — wear |
| bushing | 11 | 8,397 | €11,793 | €1/u | no — repair |
| fan_belt | 14 | 170 | €1,868 | €11/u | yes — service belt |
| water_pump | 14 | 279 | €1,096 | €4/u | maybe — timing service |
| **TOTAL** | **397** | 41,397 | **€1,758,593** | | |

## Read / honesty

- **PN·desc·price·fig_key validated.** The catalog `pms_category` wrongly tags filter **assemblies** as filters; I drop them on description+price+fig_key (041-001 assembly vs 041-002 element). Kept lines are service-part priced (filters €4–20, pads ~€69, shoes ~€30, clutch discs ~€126); DPD stays out.
- **In-scope €1.06M supersedes the €880K keyword figure** — use the catalog `pms_category`, not description keywords, as the fix-list (CSV attached).
- **brake_rotor €1.3M is the headline scope question:** capturing pads but not the discs they're fitted with understates the brake service story. Recommend adding `brake_rotor` (+ deciding on fan_belt/water_pump) before re-running.
- Fix path unchanged: load `pms_missing_pns_figkey.csv` into the crossref/registry build with its `pms_category`, re-run `run_pipeline_and_verify.ps1` (capture, briefs, dashboard, FACTS anchor update together).

_Source: `parts_catalog_dimension.csv` + sales_fact via pipeline tagger. Regenerate: `python _OKF_assessment/_build/pms_figkey_completeness.py`._