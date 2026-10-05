# Billed parts missing from the classification release: proposal for the next release

**Status: proposal only.** No release file, RELEASES.json, pr00 or gate was changed. Values go into a release only after your approval.

File with every part, both groupings, evidence and open question:
`01_data\00_derived\_releases\next_release_proposal_missing_billed_2026-10-02.csv`
Builder (re-runs the count and checks every label already exists): `01_data\91_build\build_next_release_proposal_missing_billed_20261002.py`

## How the list was made

- Billed = sales_fact, billing date 1 Sep 2025 to 31 Aug 2026, net sales value (same window as the approval summary).
- Part numbers are compared after putting back leading zeros (the billing table writes 0583306120 as 583306120). Without that, 364 parts look missing.
- Against the approved release 2026-10-02: **63 parts, EUR 108,165** (matches the approval summary). The candidate release already adds 3 of them (7475447681, 7551939337, 7552895450; EUR 954), so **60 remain, EUR 107,210**.
- Taken out, because they are not parts (4 lines, EUR 70,786): Service fee outside Europe (EUR 35,200), Service fee within Europe (EUR 35,000), Cost Demurrage (transport cost, EUR 360), Compensations Sale E-Credits (credit line, EUR 226). No lubricant or Shell part is in the list.
- **Left to classify: 56 parts, EUR 36,425.** None of them is in the newer release file `2026-10-02-chassis-frame` either.

## Result by confidence

Confidence is the lower of the two groupings (catalogue tree and AIM family). Only labels that already exist in the release are used.

| Confidence | Parts | EUR billed |
|---|---:|---:|
| High | 24 | 24,789 |
| Medium | 15 | 9,948 |
| Low | 17 | 1,688 |
| **Total** | **56** | **36,425** |

- **High:** the parts on the same figure key and with the same description already carry one label. Biggest: service cab 7553266960 (EUR 14,812, Body parts > Other body / Cab Assembly), front pad kit 5876102381 (EUR 5,109, Brake pad / Brake Pad Kit).
- **Medium:** the catalogue side is clear, but the AIM label follows a sibling convention that looks doubtful, or the AIM master says something else. Biggest: the two multi displays (EUR 6,144: Meter / gauge; AIM Instrument Cluster, where the AIM master says Audio > Radio).

## Low confidence (17 parts, EUR 1,688)

| Part | Description | EUR | Proposed catalogue tree | Proposed AIM family | Why low |
|---|---|---:|---|---|---|
| 7552647041 | SEALER | 702 | Consumables > Sealant / adhesive | Engine > Gasket & Sealing > Oil Seal | no sibling on its figure key; label read from the word only |
| 7552647031 | SEALER | 502 | Consumables > Sealant / adhesive | Engine > Gasket & Sealing > Oil Seal | same |
| 8972718920 | BLOCK; JUNCTION | 262 | Electrical sensors > Relay / solenoid / fuse | Electrical > Switch Relay Fuse > Fuse | its 2 siblings (no description) sit on Handle / lock; "fuse block" is my reading |
| 7552056260 | PLATE | 57 | Hardware > Bracket / stay | Chassis Frame > Mounting Hardware > Plate | no sibling; the 2 other PLATE parts are still Review needed |
| 7552710020 | SCREW KIT | 29 | Exhaust > Aftertreatment | Intake Exhaust Emission > DEF System > DEF Pump | AIM label is a guess from the figure |
| 7552614230 | PIPE; SENSOR | 21 | Electrical sensors > Sensor | Intake Exhaust Emission > EGR > EGR Component | AIM taken from the figure, siblings are blank |
| 7552614250 | HOSE; VAC,VSV | 20 | Air system > Air hose / pipe | Intake Exhaust Emission > EGR > EGR Component | same |
| 8973269420 | WASHER; THRUST,INPUT SHAFT | 14 | Hardware > Washer | Transmission > Geartrain > Gear | no sibling; AIM from the figure |
| 7552125540 | VALVE | 11 | Electrical sensors > Other electrical | Electrical > Charging > Battery Accessory | no sibling; "battery valve" is my reading |
| 8980528100 | PIPE; OIL,JET | 9 | Engine parts > Other engine | Engine > Internal Rotating > Engine Internal | its one sibling sits on Oil / lubricant, which would count an engine part with lubricants; not followed |
| 1331560180, -190, -200, -210, -220, -230 | SHIM (6 sizes) | 52 | Hardware > Spacer / retainer | Transmission > Geartrain > Gear | catalogue clear; AIM blank on all siblings, taken from the figure |
| 8980376041 | INHIBITOR | 8 | Transmission parts > Other transmission | Transmission > Case > Case Cover | what the part is, is not clear; AIM from the AIM master |

## Questions for you (wider than these 56 parts)

These are sibling labels that look wrong. I followed them so the new parts match their siblings. I did not propose changing them.
1. **EVRV valves** (8 parts, EUR 44k billed on the 7 already in the release): AIM says Steering > Control & Sensors > Valve; they are engine vacuum valves on the EGR figure.
2. **Engine gasket sets** (226 parts): AIM says Transmission > Bearings & Seals > Gasket.
3. **DEF dosing injectors** (EUR 267k on the 3 in the release): filed as fuel injectors on both groupings.
4. **Rear cameras**: catalogue tree says Engine parts > Other engine.
5. **Antennas**: AIM Instrument Cluster (14) or Audio > Radio (1).
6. Also missing and not billed: 8974923852 (newest number of the chassis harness 8974923851). Add it with the same values?
