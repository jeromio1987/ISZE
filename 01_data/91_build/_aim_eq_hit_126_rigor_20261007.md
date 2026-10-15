# EQ-HIT 126 rigor — 2026-10-07

## Verdict

PARTIAL — 116 of 126 are apply-ready under description + EQ figure evidence; 10 fail commercial/family checks (keyword-order traps in the overnight suggester); 0 inconclusive. ZKK does not prove family here.

**Permission bar:** `PARTIAL`  
**Apply aim_master?** No.

## Counts

| Piece | Rows |
|---|---:|
| Proposal (figure dig + family) | 126 |
| Rigor PASS (apply-ready under desc+EQ) | **116** |
| Fail | 10 |
| Inconclusive | 0 |

Session was **603/603 HIT**, zero misses. Of those HITs:

| Dig depth | Rows | What they still need |
|---|---:|---|
| Figure + part + family suggestion (this proposal) | 126 | Rigor above — only PASS is apply-ready |
| Figure + part, no family map | 40 | Map figure text to a family (rules missed them) |
| Vehicle/catalog only, no figure name | 397 | **Figure dig** (open the figure, capture fig name + part name) |
| Status HIT only | 40 | **Full figure dig** |

So **477** of 603 HITs still need figure dig and/or a family map before they can join a proven proposal. That is the pile behind the 126.

## What we checked

| Check | Result |
|---|---|
| Description + EQ figure/part vs proposed family | Independent truth rules on united text; hard traps for governor/valve springs→Suspension, fuel pipes→Filters, A/C→generic pipe |
| PN length / charset | 0 length fails |
| Price (master list euro) | 0 priced; 0 absurdity fails |
| ZKK / HKK | See honesty — **not** used as family proof |

## Honesty — price / ZKK

Price: 0 of 126 have a list euro on master; 0 absurdity fails. ZKK filled on 87/126; only 0 sit on a ≥80% pure master-family ZKK code (n≥20) — and those majorities speak master AIM labels (Engine, Brakes, …), not this overnight Powertrain/Chassis tree, so ZKK cannot approve these suggestions. HKK filled on 87/126; 5 on a strong pure code. PN length fails: 0. Family proof for this file is description text + EQ figure/part name, not ZKK.

## Systematic weak paths (fail rate ≥25% on buckets of 3+)

| Proposed path | n | fails | rate |
|---|---:|---:|---:|
| Filters > Fuel filtration > Fuel filter | 5 | 3 | 60% |
| Powertrain > Pipes / hoses > Pipe / hose | 12 | 5 | 42% |

## Example fails

| PN | Description | EQ figure | Proposed | Truth from text |
|---|---|---|---|---|
| `0952348320` | CLIP; OIL PIPE | 8-75 - CONDENSER | Powertrain > Pipes / hoses > Pipe / hose | Comfort > HVAC > Heater / A/C |
| `1154142950` | PIPE; FUEL,FUEL | 0-42B - FUEL PUMP AND PIPE | Filters > Fuel filtration > Fuel filter | Powertrain > Pipes / hoses > Pipe / hose |
| `1154168700` | PIPE; FUEL,FEED | 0-42 - FUEL PUMP AND PIPE | Filters > Fuel filtration > Fuel filter | Powertrain > Pipes / hoses > Pipe / hose |
| `1157232600` | SPRING | 0-81 - GOVERNOR; INJECTION PUMP | Chassis > Suspension > Suspension parts | Powertrain > Fuel system > Fuel system parts |
| `7551874070` | HOSE; FLEX,A/C | 8-52 - PIPING; AIR CONDITIONING | Powertrain > Pipes / hoses > Pipe / hose | Comfort > HVAC > Heater / A/C |
| `7551938790` | HOSE; FLEX,A/C | 8-52 - PIPING; AIR CONDITIONING | Powertrain > Pipes / hoses > Pipe / hose | Comfort > HVAC > Heater / A/C |
| `7551938800` | HOSE; FLEX,A/C | 8-52 - PIPING; AIR CONDITIONING | Powertrain > Pipes / hoses > Pipe / hose | Comfort > HVAC > Heater / A/C |
| `7552614900` | HOSE ASM; DEF DCM | 1-46 - DEF TANK AND PIPING | Powertrain > Pipes / hoses > Pipe / hose | Powertrain > Exhaust / aftertreatment > Exhaust parts |

## Files

- Proven subset: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_releases\next_release_proposal_eq_hit_live_order_PROVEN_2026-10-07.csv`
- Fails / inconclusive: `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_eq_hit_126_rigor_fails_20261007.csv`
- JSON: `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_eq_hit_126_rigor_20261007.json`
- This note: `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_eq_hit_126_rigor_20261007.md`

## What was not done

aim_master was not written. No dated release apply. ZKK is not claimed as family proof.
