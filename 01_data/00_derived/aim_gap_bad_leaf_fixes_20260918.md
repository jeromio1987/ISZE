# AIM gap bad-leaf fixes — 2026-09-18

Surgical corrections only. Bulk `gap_auto_20260918` apply kept. Proposal patch not merged. No HTML/Excel/cube rebuild.
SST tools marked `gap_auto_20260918_sst` were not touched.

Every new L1/L2/L3 was copied from an existing non-gap master triple (or Unknown).

## Fixed (mis-stamps)

| PN | Description | Old triple | New triple | Reason |
|---|---|---|---|---|
| `8978708710` | NOZZLE; HEADLAMP CLEANER | Fluids Chemicals > Cleaning Chemicals > Cleaner | Electrical > Lighting > Lamp | Headlamp cleaner nozzle is lighting hardware, not a cleaning chemical. Exemplar family: Electrical > Lighting > Lamp. Exemplar PN `1221332330`. Marker cleared=False. |
| `8978708720` | NOZZLE; HEADLAMP CLEANER | Fluids Chemicals > Cleaning Chemicals > Cleaner | Electrical > Lighting > Lamp | Same as sibling headlamp cleaner nozzle. Exemplar PN `1221332330`. Marker cleared=False. |
| `8980603820` | BOLT; EYE,ATF PIPE | Fluids Chemicals > Transmission Fluid > ATF | Chassis Frame > Mounting Hardware > Bolt | Eye bolt for ATF pipe is a fastener, not transmission fluid. Exemplar PN `108558700`. Marker cleared=False. |
| `1884055560` | BESCO BRAKE FLUID | Fluids Chemicals > Cleaning Chemicals > Cleaner | Fluids Chemicals > Lubricants > Lubricant | Brake fluid is a bottled fluid product. No brake-fluid L2/L3 exists in master vocab; Lubricants > Lubricant is the closest Fluids Chemicals leaf (not Cleaner, not ATF). Exemplar PN `550047337`. Marker cleared=False. |
| `7552816560` | BATTERY ASM; HIGH VOLTAGE | Electrical > Starting & Charging > Battery Cable | Unknown > Unknown > Unknown | HV battery pack was stamped Battery Cable (wrong). Electrical > Charging > HV Battery does not exist in master vocab; only Charging leaf is Alternator/Generator (also wrong). Revert to Unknown rather than invent a leaf or keep Battery Cable. Exemplar PN ``. Marker cleared=True. |
| `8974993681` | SENSOR; TIRE INFLATION | Electrical > Sensors & Switches > Radar Sensor | Electrical > Sensors & Switches > ABS Sensor Rotor | Tire inflation sensor is not radar. No TPMS leaf exists; ABS Sensor Rotor is the wheel-end sensor leaf under Sensors & Switches. Exemplar PN `8972382780`. Marker cleared=False. |
| `8980094180` | SENSOR; MAP | Electrical > Sensors > Speed Sensor | Intake Exhaust Emission > DPF/DPD > DPD Pressure Sensor | MAP is a pressure sensor, not a speed sensor. DPD Pressure Sensor is the only pressure-sensor L3 in non-gap vocab. Exemplar PN `7551850660`. Marker cleared=False. |

## Reverted (extra markers, wrong leaves)

These were among the 12 extra rows stamped with `gap_auto_20260918` but not on the high-confidence patch. Wrong leaves → Unknown + marker cleared.

| PN | Description | Old triple | New | Reason |
|---|---|---|---|---|
| `8944260371` | RUBBER; HELPER,RR SPR | Accident & Body > Panels > Bumper | Unknown > Unknown > Unknown | RUBBER; HELPER,RR SPR stamped Accident & Body > Panels > Bumper — wrong (spring helper rubber). |
| `8974039660` | COVER; HOLE,CONSOLE,RR | Accident & Body > Panels > Door | Unknown > Unknown > Unknown | COVER; HOLE,CONSOLE,RR stamped as Door panel — wrong leaf for console hole cover. |
| `8980062560` | PIN; GUIDE | Wheels Hub > Wheel Rim > (blank) | Unknown > Unknown > Unknown | PIN; GUIDE stamped Wheels Hub > Wheel Rim with blank L3 — incomplete/wrong. |
| `8980659861` | COVER; CONNECTOR BOX | Electrical > Switch Relay Fuse > Fuse | Unknown > Unknown > Unknown | COVER; CONNECTOR BOX stamped as Fuse — cover is not a fuse. |
| `8983565460` | COVER; FAN,RAD | Accident & Body > Panels > Bumper | Unknown > Unknown > Unknown | COVER; FAN,RAD stamped as Bumper — radiator fan cover, not bumper. |

## Extra markers left as-is (plausible leaf)

| PN | Description | Triple | Marker |
|---|---|---|---|
| `8972349091` | COVER; RR GATE | Accident & Body > Panels > Door | `gap_auto_20260918` |
| `8974720403` | COVER; SW | Electrical > Switch Relay Fuse > Switch | `gap_auto_20260918` |
| `8974724593` | COVER; SW | Electrical > Switch Relay Fuse > Switch | `gap_auto_20260918` |
| `8974775560` | COVER; HINGE | Accident & Body > Panels > Door | `gap_auto_20260918` |
| `8974775590` | COVER; HINGE | Accident & Body > Panels > Door | `gap_auto_20260918` |
| `8974779050` | COVER; HINGE | Accident & Body > Panels > Door | `gap_auto_20260918` |
| `8981810762` | COVER; RR GATE | Accident & Body > Panels > Door | `gap_auto_20260918` |

## Paths

- Master: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_master_v2.csv`
- Assign CSV: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_gap_auto_assign_20260918.csv`
- This note: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_gap_bad_leaf_fixes_20260918.md`
