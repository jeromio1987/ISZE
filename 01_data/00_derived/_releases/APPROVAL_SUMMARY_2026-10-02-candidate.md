# Approval summary: classification release 2026-10-02-candidate

**Status: waiting for your approval.** Nothing live has changed. The approved release 2026-10-02 stays in force until you approve this one.

- File: `01_data\00_derived\_releases\aim_pn_classification_release_2026-10-02-candidate.csv` (164,919 rows, sha256 `d17bb48d...c4c54e`)
- Why the "-candidate" name: 2026-10-02 is already taken by the release you approved this morning. The register has used one way to give a second release the same date: a suffix on the date (`2026-09-24-candidate`). I used the same form and did not add a version number.
- Euro below = parts billed in the last 12 months (Sep 2025 to Aug 2026), all customers, from the billing table. Total parts billed in that window: EUR 35.2m.

## What changes (300 parts, EUR 110,101 parts billed)

The release has two ways of grouping a part. One is the **catalogue tree** (family > group > type, e.g. Accident parts > Body parts > Panel). The other is the **AIM family** (the label the AIM pages chart, e.g. Accident & Body > Panels > Panel).

**1. The 42 parts from this morning's review: catalogue tree only, EUR 106,445.**

| Parts | From | To | EUR |
|---|---|---|---:|
| 32 intake throttles (THROTTLE ASM; INT) | Fuel system > Other fuel system | Air system > Air duct / intake | 43,703 |
| 2 ELEMENT KIT; PCV **(to check)** | Filters > Other filter | Injectors > Injection pump | 41,805 |
| 2 radiator skid plates (PLATE; SKID,RAD) **(to check)** | Body parts > Grille | Body parts > Step / guard | 13,889 |
| 1 guide pin 8980475290 (21 Sep value kept) | Brake parts > Brake pad | Hardware > Pin | 4,509 |
| 1 rear modulator 8982154541 | Air system > Other air system | Brake parts > ABS component | 2,539 |
| 3 king-pin pullers / driver (workshop tools) | Steering > Knuckle / arm | Special tools > Hand tools | 0 |
| 1 part 0001481480, no description (21 Sep value kept) | Review needed | Hardware > Spacer / retainer | 0 |

**2. Body parts that were not filed under body: EUR 3,656 on 256 parts.** These are the parts on the Israel back-order lists that the AIM pages did not count as body.
- **Roof panel 7552077720:** the AIM family was blank. It is now Accident & Body > Panels > Panel, together with the other 95 parts on the same figure key (660-001) that had no AIM family. EUR 0, because none of them was billed in the window. The 27 roof panels that already had the body label stay as they are.
- **Upper cowl panel 7475447681:** this part was not in the release at all. It is added as a body panel on both groupings (EUR 197). Also added: 7551939337, the only other billed cowl panel that was missing (EUR 172). The 13 cowl panels on the same figure key (605-030) that had no AIM family now get one (EUR 0). 8979363282 moves from Review needed to Body parts > Panel in the catalogue tree (EUR 97).
- **Front inner lid 7552895450:** this part was not in the release either. It is added as a body panel (EUR 585). There is no Japanese code or figure key on file for it, so its description comes from the back-order lists and the billing data. Its sibling 7552458070 moves from Review needed / Electrical (fuse) to body on both groupings (EUR 0).
- **Cab mounting members (MEMBER; CAB MTG RR):** 7552008820 (EUR 822), 8982268360 (EUR 1,072) and 8980107565 (EUR 712). They were filed as Unknown, Unknown and Chassis Frame > Bracket. Together with the other 139 parts on figure key 510-173 (EUR 0), they now go to Accident & Body > Panels > Panel. In the catalogue tree they were already Body parts > Body structure.
- Not added: 897 other part numbers of these four types that are not in the release. None of them was billed in the window.
- Full list of all 284 parts checked, with before, after and euro: `aim_pn_classification_release_2026-10-02-candidate.body_filing.csv`.

**3. Two parts filed wrongly in both files: catalogue tree only, EUR 0.**
- 5878305371 REPAIR KIT: moves from Air system to Steering > Knuckle / arm. It sits on the king-pin figure; all 128 other parts on that figure are king-pin parts.
- 9443730060 SPRING SEAT: moves from Body parts > Interior trim to Steering > Other steering. It sits on a drag-link figure, next to two drag-link spring seats.

## What stays the same

- Every other part, all 164,619 of them, is byte-for-byte the same as in the approved release. The PMS rules, the catalogue file `pr00_classification.csv` and the live pages are not touched.
- No new groups or types: still 27 groups and 177 types in the catalogue tree, and the AIM family uses only labels that already exist.
- **Safety check: passes.** All 18 checks pass. The 19th check, "is it approved", stays open until you decide. The match against the pinned 20 Sep catalogue copy is 99.97%; the 44 differences are all deliberate changes listed in the change log.
- **AIM pages (test copies in `02_dashboards\sales\_staged\`):** the share of units not classified in AIM does not change at two decimals: 1.97% billed / 2.65% sold to dealer (all distributors), 2.68% / 6.28% (Portugal). The only move is the Portugal comparison, period B: 6.52% -> 6.51%. By euro, the parts billed not classified in AIM go from EUR 1,308,332 to EUR 1,306,439 (3.72% to 3.71%). Three reasons the effect is small: most of the newly filed parts had no billing; the cab member 8980107565 was already counted under Chassis Frame; and the three added parts are not yet in the AIM master the pages are built from, so they will only show there after the master is refreshed.

## To check before or after approval

1. **2x ELEMENT KIT; PCV** (8981065790, 8980023462; EUR 41,805): reading this as the supply-pump control valve is my interpretation. It is not confirmed in the parts catalogue (EPC).
2. **2x PLATE; SKID,RAD** (8983941570, 8983941544; EUR 13,889): low confidence that this belongs under Step / guard.
3. **Cab mounting members on the AIM grouping:** Panels > Panel is the closest existing label. There is no body-structure label in AIM, and I did not invent one. The alternative is to keep them under Chassis Frame.

## Not changed, for a separate decision

- **King-pin rule for PMS:** it looks for the group "Suspension". The 534 king-pin parts sit in Steering > Knuckle / arm (EUR 147,302, 37 parts billed), so the rule matches 0 parts and no part carries a king-pin PMS category. The rule is in `03_analytics\Isuzu\prism\data\fig_key_taxonomy.yaml`. Reported only; not edited.
- **Siblings without a clear verdict, left as they are:** 12 other guide pins on 302-086 (Hardware > Pin, EUR 5,478); 9 ELEMENT KIT; PCV (Review needed, EUR 0); 10 MODULATOR; RR (Review needed, EUR 1,568); 28 skid-plate siblings on 603-012 (Review needed, EUR 5,574); 1 ADJ PLUG on drag-link figure 433-012 (Hardware > Cap / plug, EUR 0); 10 PANEL; COWL on 605-678 (no AIM family on 5 of them, EUR 521).
- **63 part numbers billed in the window are not in the release at all** (EUR 108,165). That is wider than this release and needs its own pass.
