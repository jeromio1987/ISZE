# Approval summary: classification release 2026-10-04

**Status: waiting for your approval.** Nothing live has changed. The approved release 2026-10-02-chassis-frame stays in force until you approve this one.

- File: `01_data\00_derived\_releases\aim_pn_classification_release_2026-10-04.csv` (164,943 rows, sha256 `8aad884f...e18896`). It starts from the approved release 2026-10-02-chassis-frame (164,919 rows, sha256 `9bb86a9b...`), which is untouched.
- Name: 2026-10-04 is free in the register, so the date alone is the name. No suffix, no version number.
- Euro below = parts billed in the last 12 months (Sep 2025 to Aug 2026), all customers, from the billing table. Total parts billed in that window: EUR 35.2m.
- **Your brief's euro figures for cameras (EUR 125,967), DEF injectors (EUR 267,132) and EVRV (EUR 44k) are the release's own euro column, which runs Jan 2025 to Jun 2026.** In the Sep 2025 to Aug 2026 window the same parts are EUR 89,154, EUR 191,364 and EUR 31,856. I used Sep 2025 to Aug 2026 throughout, as in the earlier summaries.

## What changes: 421 parts (397 existing + 24 added), EUR 404,151 parts billed

The release has two ways of grouping a part: the **catalogue tree** (family > group > type) and the **AIM family** (what the AIM pages chart).

| # | What | Parts | EUR | Change |
|---|---|---:|---:|---|
| 1 | Billed parts missing from the release (High confidence) | 24 | 24,789 | added as new rows, both groupings, labels as in the proposal file |
| 2 | Engine gasket sets | 209 | 54,375 | AIM: Transmission > Bearings & Seals > Gasket -> Engine > Gasket & Sealing > Gasket |
| 3 | EVRV valves | 10 | 31,856 | AIM: Steering > Control & Sensors > Valve (7), blank (2), Emission Control > Catalyst (1) -> Intake Exhaust Emission > EGR > EGR Component |
| 4 | Antennas | 92 | 23,503 | AIM: Instrument Cluster (21), Unknown (16), blank (55) -> Electrical > Audio > Radio |
| 5 | Rear cameras, catalogue tree only | 81 | 78,132 | Engine parts > Other engine -> Electrical sensors > Other electrical |
| 6 | DEF dosing injectors | 5 | 191,496 | AIM: Fuel System > Fuel Control > Injector -> Intake Exhaust Emission > DEF System > **DEF Injector (new label)** |

**One reading for you to confirm.** 137,702 of the release's rows have no description of their own; it sits only in the Japanese parts-code file (`jp_codes_cache_20260920.csv`). I grouped parts by the release description, and where there is none by the Japanese-file description (the same way the 2 Oct body filing did). A part changes only if it carries the label you named as wrong (gasket sets: the Transmission label; antennas: Instrument Cluster, Unknown or blank; cameras: Other engine; EVRV: all, as you said "any other"). **111 of the 397 existing parts changed are found this way only (EUR 60 billed in total):** 2 gasket sets, 3 EVRV valves, 55 antennas, 51 camera parts. If you want release descriptions only, say so and I cut the release again without those 111.

**1. Missing billed parts: 24 added, EUR 24,789.** Labels exactly as in `next_release_proposal_missing_billed_2026-10-02.csv`. Biggest: service cab 7553266960 (EUR 14,812), front pad kit 5876102381 (EUR 5,109), generator 1812004173 (EUR 1,222), grille emblem 7552961740 (EUR 862). Not added: 15 Medium (EUR 9,948), 17 Low (EUR 1,688) and the unbilled 8974923852. All 24 were billed after Jun 2026, so the release's own euro column (window ends Jun 2026) shows 0.0 for them.

**2. Engine gasket sets: 209 parts, EUR 54,375 (86 of them billed).** 112 ENG OVERHAUL, 91 ENG HD OVERHAUL, 6 other spellings. The 17 GASKET SET; TRANS OVERHAUL sets and the 2 CARB sets stay on the Transmission label. The earlier "226" counted every GASKET SET on that label: 207 engine + 17 transmission + 2 carburettor. Catalogue tree unchanged.

**3. EVRV valves: 10 parts, EUR 31,856.** 7 carry the release description (5 of them billed); 3 more exist only in the Japanese file (2 with no AIM family, 1 on Catalyst; EUR 0). Catalogue tree unchanged.

**4. Antennas: 92 parts, EUR 23,503.** 82 plain antennas (ANTENNA, ANTENNA ASM, ROD; ANTENNA; EUR 23,053), 7 GPS antennas (EUR 357), 3 keyless entry antennas (EUR 93). All the euro sits on the 21 that were on Instrument Cluster. 1 antenna already on Radio stays. Catalogue tree unchanged.

**5. Rear cameras, catalogue tree only: 81 parts, EUR 78,132.** CAMERA ASM 36, COVER; CAMERA 32, CAMERA; SAFETY 7, CAMERA; REAR 6. The AIM family is left as it is. Your brief said 37 parts: that is every part with CAMERA in the release description (37, EUR 125,967 in the release column, EUR 89,154 in Sep 2025 to Aug 2026). 30 of them sat on Other engine and moved (EUR 78,073). Another 51 parts with the same descriptions, known only from the Japanese file, also sat on Other engine and moved with them (EUR 60 billed, one part 8972660550). That is why the count is 81 and not 37.

**6. DEF dosing injectors: 5 parts, EUR 191,496.** The 3 INJECTOR ASM; DEF DCM (EUR 191,364: 8983842670 EUR 135,958; 8982318983 EUR 55,112; 8977918600 EUR 293), CONNECTOR KIT; COOLANT,INJECTOR ASM DEF 8981694161 (EUR 56) and GASKET; INJECTOR ASM,DEF DCM 8980863330 (EUR 76). **New AIM label: Intake Exhaust Emission > DEF System > DEF Injector.** DEF System had DEF Pump, DEF Sensor and DEF Tank; this is the only new label in the release. Catalogue tree stays Injectors > Injector.

## What stays the same

- Every other row, all 164,522 of them, is byte-for-byte the same as in the approved release. Checked on the raw file lines, not only on the values.
- The PCV element kits (8981065790, 8980023462), the radiator skid plates (8983941570, 8983941544), the rear modulator 8982154541 and the 35 other parts with those three descriptions are untouched.
- Catalogue tree: no new groups or types, still 27 groups and 177 types. AIM family: 269 label combinations (was 268); the one new one is DEF Injector.
- Not touched: `pr00_classification.csv`, `parts_catalog_dimension.*`, `fig_key_taxonomy.yaml`, the live pages, the AIM master, the gate and its rules. File hashes before and after were compared (69 files, 0 changed). `RELEASES.json` has one new entry (2026-10-04, PENDING_APPROVAL); the five earlier entries are identical to git.

## Safety check

- **Passes.** 18 checks pass, 0 fail. The 19th, "is it approved", stays open until you decide. Report: `aim_pn_classification_release_2026-10-04.gate.json`.
- The match against the pinned 20 Sep catalogue copy is 99.92% (approved release: 99.97%). The 81 extra differences are exactly the 81 camera parts.
- The new label did not trip anything: the safety check has no test on AIM labels (it checks the catalogue tree only). In the build I added my own test that the only AIM label combination not already in the approved release is DEF Injector; it holds.
- Independent re-read of the written files: 29 checks, all pass (all seven points present, nothing else differs, register / meta / gate hashes equal the file). Script: `01_data\91_build\_release_20261004_diff.py`.

## AIM pages (test copies in `02_dashboards\sales\_staged\`, built today from the approved release and from this release on the same inputs)

All four pages build and pass their own checks (17 / 48 / 25 / 61, 0 fail). Share of units not classified in AIM:

| Page | Approved | This release |
|---|---|---|
| Deep Dive Portugal, billed | 2.68% | 2.65% |
| Deep Dive Portugal, sold to dealer | 6.28% | 6.27% |
| Deep Dive all distributors, billed / sold | 1.97% / 2.65% | unchanged |
| Comparison Portugal, period A / B | 6.28% / 6.51% | 6.25% / 6.51% |
| Comparison all distributors, period A / B | 4.12% / 2.12% | 4.11% / 2.11% |

- By euro nothing moves: parts billed and not classified in AIM stay EUR 1,306,439 (3.71%), because the 73 parts that gain an AIM family (55 blank antennas, 16 Unknown antennas, 2 blank EVRV valves) were not billed. By count they fall from 144,039 to 143,966. The page tree gains the DEF Injector type (236 -> 237 types).
- **20 of the 24 added parts (EUR 9,771) are not in the AIM master the pages are built from.** They show on the pages only after the master is refreshed; I did not touch the master. The other 4 (EUR 15,019) are in the master already. For 2 of those the proposal label differs from the master and wins on the pages: 7475007370 (Seat Back, master says Seat Cushion) and 7552923220 (Panels > Bumper, master says Bumpers > Bumper Assembly).
- Side effects of the test copies, all new files: the page input export `01_data\00_derived\AIM_Master_PN_Categories_Figkey_release_2026-10-04.{csv,xlsx,release.json}` + an OPEN cmd, and 8 `VERIFY_*_staged` files in `04_tools\aim_db_dlr_deep_dive\`. Delete or keep as you like.

## To look at before approval

1. **GPS antennas (7 changed, EUR 357):** 8972651462 (was Instrument Cluster, EUR 152), 8983963532 (Instrument Cluster, EUR 51), 8983963542 (Instrument Cluster, EUR 154), 8983963531 and 8983963541 (Unknown), 8983963550 and 8983963551 (blank, Japanese file). All now Radio.
2. **Keyless entry antennas (3 changed, EUR 93):** 8983947820 (Instrument Cluster, EUR 93), 8980763321 (Unknown), 8981905250 (blank, Japanese file). Now Radio. **2 left on their own label Electrical > Switch Relay Fuse > Switch:** 8980763330 and 8981335712 (EUR 39). I read that as an existing, better label; say if they should go to Radio too.
3. **AEBS camera-aiming targets, not moved:** 5884032481 (TARGET;AEBS,CAMERA AIMING, Other engine, EUR 10,511, the biggest camera-related item) and 5884032930 (Review needed, EUR 0). A target board is not a camera.
4. **Other camera parts, not moved:** 7552325071 CAMERA; DRIVER MONITORING SYSTEM (Engine parts > Engine ring, EUR 172; clearly a camera, but not on Other engine), 2 HARNESS; CAMERA (EUR 398, already Harness / cable), BRACKET ASM; CAMERA and CABLE; CAMERA (EUR 0).
5. **Antenna accessories not on your list, not changed:** POLE; ANTENNA (3 parts, EUR 29: Instrument Cluster, Unknown, blank), ANTENNA; DOOR L (1, blank), plus bolts, nuts, screws, cables and sheets.

## Not changed, for a separate decision

- **5,978 more engine gasket sets have no AIM family at all** (EUR 586 billed, 3 parts). They were not on the Transmission label, so they are outside your decision. Same label on request.
- **DEF injectors:** 7552973320 is a fourth injector assembly (EUR 849 billed). It sits in the Medium list, so it was not added. Three Japanese-file parts `INJECTOR ASM; D...` (8982318980, 8982318981, 8982318982, EUR 0, no AIM family) look like the same family; not changed.
- **Master refresh** for the 20 added parts that are not in the AIM master (above).
