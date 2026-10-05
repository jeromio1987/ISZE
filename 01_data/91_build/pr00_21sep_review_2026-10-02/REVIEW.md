# pr00 21 Sep vs 20 Sep: which side is right, part by part

Review of the 1,661 part numbers where the live `pr00_classification.csv` (the 21 Sep state, restored 2 Oct) differs from the approved release 2026-10-02 (= the pinned 20 Sep pr00, plus one deliberate fix). Read-only: nothing in pr00, the release, `RELEASES.json` or the gate was touched. This is input for the next release; nothing is applied.

Per-part file: `01_data/91_build/pr00_21sep_review_2026-10-02/pr00_21sep_review_per_part.csv` (1,661 rows; both sides, verdict, proposed value, confidence, evidence, L12M EUR).

## Headline

**The 20 Sep side is right on 1,619 of 1,661 parts (EUR 2,323,697.32 of L12M billing).** The 21 Sep side is right on 2 parts; on 40 parts neither side is right and a third value is proposed.

The brief reads the before/after columns the wrong way round. In `settle_from_release_2026-10-02.changes.csv`, `before` is the 21 Sep live value and `after` is the 20 Sep / release value. So on 21 Sep the air filters went **into** A/C, bumper bars went **into** leaf spring, wiper blades went **to** Review needed, and king pins went **to** Hardware > Pin. Those are the regressions, not the fixes. The retest memo says the same about the air filters and bumper bars (sections 3c and 4).

**Why it is one-sided.** The 21 Sep values are not new classification work. On 1,645 of the 1,661 parts, the 21 Sep value is exactly the value in the pre-17 Sep pr00 (`pr00_classification.csv.bak_pre_eq_20260917`; the 23 Jul commit `ff93f562` gives the same 1,645 matches). In other words, the 21 Sep file undid the 17 to 18 Sep classification passes. Those passes were rule-based and partly checked against the Isuzu EPC (`00_docs/CLASSIFICATION_FULL_AUDIT_20260917.md` section 8 and the EQ-hit table). Where each 20 Sep value came from, worked out by stepping through the dated pr00 backups:

| 20 Sep value first appears | Parts | L12M EUR |
|---|---:|---:|
| eq_doubt_18sep | 45 | 605,399.99 |
| eq_pass_17sep | 1,264 | 1,271,607.00 |
| leaf_add_or_later_18-20sep | 13 | 146,477.68 |
| pad_supersession_17sep | 337 | 404,055.95 |
| release_only | 2 | 2,602.15 |

(eq_pass_17sep = ACL air cleaner, king pin, drag link, ball joint, bumper bar and window regulator rules. pad_supersession_17sep = the 19:50 to 22:22 change on 17 Sep, i.e. pad supersession plus the residual pass-2 heads: wiper, gate/transfer/throttle ASM, tensioner, pad kit, LLC. eq_doubt_18sep = `_patch_eq_doubt_pass_20260918.py`. leaf_add = `_leaf_add_battery_tools_20260918.py`. release_only = 8980913940, fixed in the 2 Oct release, and 0001481480, which only exists in the 21 Sep file.)

**Undone classification.** 387 parts sit on `Miscellaneous > Review needed` in the 21 Sep file but carry a named leaf on 20 Sep (EUR 1,145,941.54). The brief's figure of 301 does not reproduce; 387 is the count in the changes file. Only one part goes the other way: 0001481480 has a named leaf on 21 Sep and Review needed in the release.

**The "questionable swaps" in the brief are 20 Sep corrections.** Every one of them is right on the 20 Sep side:
- **Pin -> Knuckle / arm (367):** all are king-pin parts (KING PIN SET/KIT, covers, shims, thrust bearings, bushings). Exception: 3 workshop tools.
- **Washer -> Knuckle / arm (136):** thrust washers for the king pin.
- **Linkage / lever -> Other steering (200):** drag links and drag-link ball joints. The EPC files them under 4-33 STEERING LINKAGE.
- **Voltage regulator -> Door (107):** these are `REGULATOR ASM; DOOR` parts, i.e. window regulators. The EPC files them under 6-31 FRONT DOOR GLASS AND REGULATOR. They are not alternator parts.

## Totals per verdict

L12M = `net_sales_value` from `01_data/00_derived/sales_fact.parquet`, billing dates 2025-09-01 to 2026-08-31 (the last 12 full months in the parquet, which ends 2026-08-31). All sold-to customers, all lines. Raw XLSX was not read. Part numbers are matched on the 10-digit zero-padded key.

| Verdict | Parts | Parts with L12M billing | L12M EUR |
|---|---:|---:|---:|
| keep 20 Sep | 1,619 | 260 | 2,323,697.32 |
| keep 21 Sep | 2 | 1 | 4,508.94 |
| neither | 40 | 13 | 101,936.51 |
| **Total** | **1,661** | **274** | **2,430,142.77** |

## Pattern table (21 Sep -> 20 Sep, group > leaf)

| # | 21 Sep value -> 20 Sep value | Parts | L12M EUR | Verdict | Examples (highest billing first) |
|---:|---|---:|---:|---|---|
| 1 | Hardware > Pin -> Steering > Knuckle / arm | 367 | 146,478.20 | split (keep 20 Sep 364, neither 3) | 5878324001 KING PIN KIT; 5878323991 KING PIN KIT; 5878324011 KING PIN KIT |
| 2 | Hydraulic / mechanical > Linkage / lever -> Steering > Other steering | 200 | 117,600.51 | keep 20 Sep | 8980256421 LINK; DRAG; 8980067942 LINK; DRAG; 1443803030 LINK; DRAG |
| 3 | Suspension > Leaf / suspension spring -> Body parts > Bumper | 151 | 101,796.62 | keep 20 Sep | 8983621213 BAR; FRT BUMPER; 8975471071 BAR; FRT BUMPER; 8982294320 BAR; FRT BUMPER |
| 4 | Hardware > Washer -> Steering > Knuckle / arm | 136 | 0.00 | keep 20 Sep | 1431710020 WASHER; THRUST,KING PIN; 1431710030 WASHER; THRUST,KING PIN; 1431710040 WASHER; THRUST,KING PIN |
| 5 | Air conditioning > Other A/C -> Filters > Air filter | 118 | 714,435.49 | keep 20 Sep | 8974995480 FILTER; ACL; 1876101132 FILTER; ACL; 8981772710 FILTER; ACL |
| 6 | Miscellaneous > Review needed -> Body parts > Wiper | 116 | 105,864.72 | keep 20 Sep | 8980537880 BLADE; WIPER; 8975568060 BLADE; WIPER; 8980537900 BLADE; WIPER |
| 7 | Starter / alternator > Voltage regulator -> Body parts > Door | 107 | 10,229.03 | keep 20 Sep | 8980098112 REGULATOR ASM; DOOR; 8980098102 REGULATOR ASM; DOOR; 8978681133 REGULATOR ASM; DOOR |
| 8 | Hydraulic / mechanical > Linkage / lever -> Suspension > Other suspension | 70 | 82,825.76 | keep 20 Sep | 8980058750 JOINT ASM; BALL,LWR CONT ARM; 8971424521 JOINT ASM; BALL,LWR CONT ARM; 8980058270 JOINT ASM; BALL,UPR CONT ARM |
| 9 | Miscellaneous > Review needed -> Body parts > Other body | 59 | 156,768.91 | keep 20 Sep | 8983860446 GATE ASM; RR; 8972432530 GATE ASM; RR; 8975536860 BODY ASM; REAR |
| 10 | Miscellaneous > Review needed -> Transmission parts > Other transmission | 56 | 80,941.44 | keep 20 Sep | 7552283740 TRANSFER ASM; 7552283750 TRANSFER ASM; 7551846320 TRANSFER ASM |
| 11 | Miscellaneous > Review needed -> Fuel system > Other fuel system | 35 | 202,857.38 | split (neither 32, keep 20 Sep 3) | 8984890180 RAIL; COMMON; 8983300400 RAIL;COMMON; 8982473951 THROTTLE ASM; INT |
| 12 | Miscellaneous > Review needed -> Belts > Tensioner / idler | 35 | 70,212.66 | keep 20 Sep | 8983786752 TENSIONER; AUTO; 8983786751 TENSIONER; AUTO; 8975074361 TENSIONER; AUTO |
| 13 | Air system > Other air system -> Body parts > Bumper | 34 | 3,654.64 | keep 20 Sep | 8981396950 GUIDE; AIR,FRT BUMPER; 8981396940 GUIDE; AIR,FRT BUMPER; 8980454500 GUIDE; AIR,FRT BUMPER |
| 14 | Miscellaneous > Review needed -> Brake parts > Brake pad | 27 | 682.16 | keep 20 Sep | 5872211390 PAD KIT; CALIPER,RR; 8970392691 PAD KIT; CALIPER,RR; 8976890770 PAD KIT; CALIPER,RR |
| 15 | Hardware > Bolt -> Steering > Knuckle / arm | 22 | 508.75 | keep 20 Sep | 8971419452 BOLT; KEY,KING PIN; 1431160110 BOLT; KEY,KING PIN; 1431160090 BOLT; KEY,KING PIN |
| 16 | Miscellaneous > Review needed -> Cooling > Other cooling | 12 | 3,089.13 | keep 20 Sep | 1884055410 LLC;4L TYPE AS; 1884053350 LLC;4L TYPE E; 1884053385 LLC;2L TYPE E |
| 17 | Body parts > Step / guard -> Steering > Other steering | 11 | 0.00 | keep 20 Sep | 1443650070 GUARD; MUD,DRAG LINK; 1443650100 GUARD; MUD,DRAG LINK; 1443650101 GUARD; MUD,DRAG LINK |
| 18 | Hardware > Pin -> Steering > Other steering | 7 | 1,243.87 | keep 20 Sep | 0811230250 PIN; SPLIT,DRAG LINK; 8980980240 PIN; SPLIT,DRAG LINK; 8973497660 PIN; SPLIT,DRAG LINK |
| 19 | Air system > Other air system -> Filters > Air filter | 7 | 95,814.79 | keep 20 Sep | 5876100201 ELEMENT; AIR CLEANER; 5876102500 ELEMENT; AIR CLEANER; 8982290480 ELEMENT ASM; AIR CLEANER |
| 20 | Gaskets / seals > Other gasket / seal -> Steering > Knuckle / arm | 7 | 102.30 | keep 20 Sep | 1423192070 GASKET; KING PIN COVER; 8983084270 GASKET; KING PIN COVER; 1431390670 GASKET; KING PIN COVER |
| 21 | Air system > Other air system -> Steering > Other steering | 5 | 108.45 | keep 20 Sep | 1855740400 REPAIR KIT; DRAG LINK; 1855740360 REPAIR KIT; DRAG LINK; 1855740370 REPAIR KIT; DRAG LINK |
| 22 | Miscellaneous > Review needed -> Special tools > Jack | 5 | 2,912.54 | keep 20 Sep | 8982692090 JACK ASM; 8982692080 JACK ASM; 8972177881 JACK ASM |
| 23 | Hardware > Spring -> Steering > Other steering | 5 | 0.00 | keep 20 Sep | 1095804090 SPRING; COIL,DRAG LINK; 1095804100 SPRING; COIL,DRAG LINK; 8943609430 SPRING; COIL,DRAG LINK |
| 24 | Miscellaneous > Review needed -> Body parts > Handle / lock | 4 | 23,629.10 | keep 20 Sep | 7551893811 KEY; BLANK; 7551893782 KEY; BLANK; 8983380850 KEY; BLANK |
| 25 | Miscellaneous > Review needed -> Brake parts > Other brake | 4 | 43,039.50 | keep 20 Sep | 8983487480 CHAMBER; POWER; 1476010870 EXPANDER; 8980435960 CHAMBER; POWER |
| 26 | Gaskets / seals > Oil seal / seal -> Steering > Knuckle / arm | 4 | 212.68 | keep 20 Sep | 1096256480 SEAL; OIL,KING PIN; 1096256510 SEAL; KING PIN; 1431390400 SEAL; KING PIN |
| 27 | Exhaust > Aftertreatment -> Body parts > Bumper | 4 | 33.39 | keep 20 Sep | 8980829750 SCREW; FRT BUMPER; 8941528330 SCREW; RR BUMPER; 8943189800 SCREW; BUMPER TO BRKT |
| 28 | Miscellaneous > Review needed -> Exhaust > Aftertreatment | 3 | 156,540.95 | keep 20 Sep | 8972746690 TANK ASM; DEF; 8974996342 CONVERTER; 8983353097 TANK ASM; DEF |
| 29 | Miscellaneous > Review needed -> Special tools > Hand tools | 3 | 1,741.56 | keep 20 Sep | 5884028630 DRIVER TOOL SET; 5884028560 SRS LOAD TOOL; 5852200240 SETTING TOOL |
| 30 | Exhaust > Aftertreatment -> Steering > Other steering | 3 | 0.00 | keep 20 Sep | 8942491810 SCREW; ADJ,DRAG LINK; 8942558080 SCREW; ADJ,DRAG LINK; 9443750250 SCREW; ADJ,DRAG LINK |
| 31 | Body parts > Interior trim -> Steering > Other steering | 3 | 0.00 | keep 20 Sep | 1443730060 SEAT; SPR,DRAG LINK; 9443716050 SEAT; BALL,DRAG LINK; 9443730020 SEAT; SPR,DRAG LINK |
| 32 | Miscellaneous > Review needed -> Transmission parts > Differential / axle | 2 | 15,230.89 | keep 20 Sep | 8981476781 BOOT KIT; OUTSIDE,FRT DRIVE SH; 8975289790 BOOT KIT; OUTSIDE,FRT DRIVE SH |
| 33 | Miscellaneous > Review needed -> Transmission parts > Gear set / gear | 2 | 7,864.95 | keep 20 Sep | 8972413111 RING; INSIDE,3RD & 2ND; 8972413071 RING; OUTSIDE,3RD & 2ND |
| 34 | Lighting > Lens / reflector -> Body parts > Bumper | 2 | 0.00 | keep 20 Sep | 1712900530 PLATE; RR BUMPER,REFLECTOR; 1712900660 PLATE; RR BUMPER,REFLECTOR |
| 35 | Gaskets / seals > Oil seal / seal -> Body parts > Bumper | 2 | 0.00 | keep 20 Sep | 8980071490 SEAL; BUMPER; 8980071491 SEAL; BUMPER |
| 36 | Consumables > Oil / lubricant -> Special tools > Jack | 2 | 259.01 | keep 20 Sep | 8975562380 4TON OIL JACK; 9855110348 OIL JACK;MAIN BODY,MH-7 |
| 37 | Cooling > Cooler / intercooler -> Body parts > Bumper | 2 | 0.00 | keep 20 Sep | 8943888330 GRILLE; OIL COOLER,FRT BUMPER; 8943888331 GRILLE; OIL COOLER,FRT BUMPER |
| 38 | Miscellaneous > Review needed -> Filters > Other filter | 2 | 41,805.42 | neither | 8981065790 ELEMENT KIT; PCV; 8980023462 ELEMENT KIT; PCV |
| 39 | Miscellaneous > Review needed -> Filters > Fuel filter | 2 | 0.00 | keep 20 Sep | 8941214310 ELEMENT KIT;FUE; 8944068980 ELEMENT KIT;F/F |
| 40 | Miscellaneous > Review needed -> Electrical sensors > Other electrical | 2 | 20,850.57 | keep 20 Sep | 8976598981 COVER; RADAR; 8976598991 COVER; RADAR |
| 41 | Miscellaneous > Review needed -> Body parts > Trim / molding | 2 | 11,821.16 | keep 20 Sep | 8980973800 EMBLEM; CAB FRT; 8980419130 MARK; ISUZU |
| 42 | Miscellaneous > Review needed -> Body parts > Grille | 2 | 13,889.01 | neither | 8983941570 PLATE; SKID,RAD; 8983941544 PLATE; SKID,RAD |
| 43 | Miscellaneous > Review needed -> Battery > 12V battery | 2 | 8,764.94 | keep 20 Sep | 7552430370 BATTERY; 8976634340 BATTERY |
| 44 | Miscellaneous > Review needed -> Body parts > Interior trim | 2 | 13,967.61 | keep 20 Sep | 8974716802 BOX; GLOVE,INST PNL; 8974786091 BOX; GLOVE,INST PNL |
| 45 | Miscellaneous > Review needed -> Air conditioning > Heater core / heater | 1 | 3,026.85 | keep 20 Sep | 8980485080 CORE |
| 46 | Miscellaneous > Review needed -> Air system > Air duct / intake | 1 | 4,122.93 | keep 20 Sep | 8983097971 HOSE; CONN |
| 47 | Hardware > Spacer / retainer -> Miscellaneous > Review needed | 1 | 0.00 | keep 21 Sep | 0001481480 (no desc) |
| 48 | Hardware > Pin -> Brake parts > Brake pad | 1 | 4,508.94 | keep 21 Sep | 8980475290 PIN; GUIDE |
| 49 | Belts > Timing belt -> Belts > Tensioner / idler | 1 | 0.00 | keep 20 Sep | 9113196130 TENSIONER; TIMING BELT |
| 50 | Hardware > Spacer / retainer -> Steering > Other steering | 1 | 0.00 | keep 20 Sep | 1443790080 SPACER; DRAG LINK |
| 51 | Miscellaneous > Review needed -> Body parts > Bumper | 1 | 4,141.34 | keep 20 Sep | 8980458132 PROTECTOR; UNDER |
| 52 | Miscellaneous > Review needed -> Belts > Pulley | 1 | 3,906.20 | keep 20 Sep | 8981302040 PULLEY ASM; IDLER,CMPR |
| 53 | Miscellaneous > Review needed -> Battery > High-voltage battery | 1 | 132,799.63 | keep 20 Sep | 7552816560 BATTERY ASM; HIGH VOLTAGE |
| 54 | Miscellaneous > Review needed -> Air system > Other air system | 1 | 2,539.10 | neither | 8982154541 MODULATOR; RR |
| 55 | Miscellaneous > Review needed -> Engine parts > Valve / valvetrain | 1 | 5,433.19 | keep 20 Sep | 8982482610 ADJUSTER; VLV LASH |
| 56 | Miscellaneous > Review needed -> Injectors > Injection pump | 1 | 3,806.20 | keep 20 Sep | 8973133620 ADVANCER ASM; STARTING,GOV |
| 57 | Miscellaneous > Review needed -> Filters > Oil filter | 1 | 0.00 | keep 20 Sep | 8970215690 ELEMENT KIT; OI |
| 58 | Miscellaneous > Review needed -> Suspension > Stabilizer | 1 | 3,691.50 | keep 20 Sep | 8980672390 BAR ASM; STAB,RR SUSP |
| 59 | Transmission parts > Differential / axle -> Suspension > Bushing / mount | 1 | 4,388.80 | keep 20 Sep | 8970895560 BUSHING; STAB BAR TO RR AXLE |

## Parts where the 20 Sep side is not taken

| Part | Description | 21 Sep | 20 Sep | Proposed | Confidence | L12M EUR |
|---|---|---|---|---|---|---:|
| 0001481480 | (none) | Hardware > Spacer / retainer | Miscellaneous > Review needed | Hardware > Spacer / retainer (keep 21 Sep) | low | 0.00 |
| 1852380010 | DRIVER; NEEDLE,KING PIN | Hardware > Pin | Steering > Knuckle / arm | Special tools > Hand tools (neither) | medium | 0.00 |
| 2 parts (e.g. 8981065790, 8980023462) | ELEMENT KIT; PCV | Miscellaneous > Review needed | Filters > Other filter | Injectors > Injection pump (neither) | medium | 41,805.42 |
| 8982154541 | MODULATOR; RR | Miscellaneous > Review needed | Air system > Other air system | Brake parts > ABS component (neither) | medium | 2,539.10 |
| 8980475290 | PIN; GUIDE | Hardware > Pin | Brake parts > Brake pad | Hardware > Pin (keep 21 Sep) | medium | 4,508.94 |
| 2 parts (e.g. 8983941570, 8983941544) | PLATE; SKID,RAD | Miscellaneous > Review needed | Body parts > Grille | Body parts > Step / guard (neither) | low | 13,889.01 |
| 2 parts (e.g. 1852100090, 9852101510) | PULLER ASM; KING PIN | Hardware > Pin | Steering > Knuckle / arm | Special tools > Hand tools (neither) | medium | 0.00 |
| 32 parts (e.g. 8982473951, 8982473952, 8979455224) | THROTTLE ASM; INT | Miscellaneous > Review needed | Fuel system > Other fuel system | Air system > Air duct / intake (neither) | medium | 43,702.98 |

Reasons, in short:
- **0001481480:** it is not in the 20 Sep file. The release has no classification for it, and there is no description in any source. The one sibling on its figure key 249-041 is `Spacer / retainer`, so the 21 Sep value stands (low confidence). Zero billing.
- **8980475290 `PIN; GUIDE`:** this is the known fault in retest memo section 4 ("guide pin in brake pads"), and the brake-pad value is the 20 Sep one. All its `PIN; GUIDE` siblings on 302-086 sit on Hardware > Pin in both files, so the 21 Sep value is the consistent one. A later option is to move the whole 302-086 key to Brake parts > Other brake.
- **`THROTTLE ASM; INT` (32):** this is the intake throttle, which meters air, not fuel. The AIM label is Air Intake > Air Duct. 20 Sep (Fuel system) is better than Review needed but is still wrong.
- **`ELEMENT KIT; PCV` (2):** the figure key 028-318 and the AIM label (Injection Pump > Element) point to the supply-pump control valve, not a crankcase-ventilation filter. Proposed: Injectors > Injection pump. This is my reading of the PCV abbreviation and is not EPC-confirmed.
- **`MODULATOR; RR` (1):** a rear brake modulator on brake figure 320-107. Proposed: Brake parts > ABS component (not EPC-confirmed).
- **`PULLER ASM; KING PIN` (2), `DRIVER; NEEDLE,KING PIN` (1):** these are workshop tools. Proposed: Special tools > Hand tools.
- **`PLATE; SKID,RAD` (2):** a radiator skid plate is an underbody guard, not a grille. Proposed: Step / guard (low confidence).

## How much each kind of evidence counted

- **Description:** decisive on nearly every pattern. Each pattern is driven by a single description head (FILTER; ACL, KING PIN, LINK; DRAG, REGULATOR ASM; DOOR, BAR; FRT BUMPER, BLADE; WIPER ...).
- **`parts_catalog_dimension.csv` figure-key label:** not independent evidence. On 1,509 of the 1,661 parts it equals the 21 Sep leaf, because it is built from the same pr00 tree. The exception is the 130-0xx air-cleaner keys, which 21 Sep's own figure-key work relabelled `Air filter`.
- **AIM label in the approved release:** present on 353 of 1,661 parts. Where present, it agrees with the 20 Sep leaf, except on the five "neither" groups above and the guide pin.
- **Siblings on the same figure key (unchanged parts):** often weak. Many keys have 0 or 1 unchanged sibling, or siblings that are themselves on Review needed. They decided the guide pin and 0001481480.

## Seen in passing, outside the 1,661 (not reviewed, not applied)

Some unchanged siblings sit on the same wrong leaf in both files and are worth a look in the next release: 5878305371 on king-pin key 410-004 (Air system > Other air system), the other `PIN; GUIDE` parts on 302-086, the remaining `ELEMENT KIT; PCV` and `MODULATOR; RR` parts on 028-318 and 320-107 (Review needed), and single siblings on drag-link keys 433-012 / 410-076. The king-pin service category in `fig_key_taxonomy.yaml` matches group `Suspension` (audit section 3.1), so it still will not fire on Steering > Knuckle / arm. That needs its own decision.

## Method

Scripts are in the session scratchpad (p2 to p9), not in the repo. Inputs, all read-only: the changes CSV; `pr00_classification.csv` (live, sha256 f1e48191...); `_releases/pr00_classification_reference_20260920.csv`; `_releases/aim_pn_classification_release_2026-10-02.csv` (description, AIM label, catalogue tree, figure key); `parts_catalog_dimension.csv`; the four dated `pr00_classification.csv.bak_pre_*` backups and git `ff93f562` / `5d6b98b3`; `sales_fact.parquet`. Checks: the changes file's `before` equals live pr00 on every cell (0 mismatches); the dimension rows mirror the pr00 rows (0 mismatches); the release catalogue equals the 20 Sep reference on 1,659 of 1,661 (the other 2 are 8980913940 and 0001481480).
