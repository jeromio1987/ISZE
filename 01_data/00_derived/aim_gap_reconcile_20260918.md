# AIM gap reconcile — 2026-09-18

**Verdict:** Yes — `aim_master_v2.csv` was updated. **2,480** part numbers carry marker `gap_auto_20260918` on `aim_changed` (and a `…|gap_auto_20260918` suffix on `aim_source`). The applying run’s own high-confidence list is **2,468 PNs / EUR 5.19M** billed in the revision cube. The extra **12** stamped rows are not on that high list and look like accidental cover/pin leftovers.

---

## Did the master get updated?

**Yes.** Marker is live on disk.

| Measure | Count / € |
|---|---|
| Master rows with `aim_changed=gap_auto_20260918` | **2,480** |
| Of which also in `aim_gap_high_conf_patch_20260918.csv` | **2,468** (exact triple match) |
| Extra stamped, not in high patch | **12** (mostly COVER / one PIN; one empty L3) |
| High-confidence billed € (revision cube, patch CSV) | **EUR 5,189,911** |
| Master `l12m_billed_eur` / `eur` sum on all 2,480 markers | **EUR 5,714,421** (different € field than the revision cube; rebate/transport/Shell lines often show €0 on master) |

Git cannot measure a line diff: `01_data/00_derived/aim_master_v2.csv` is **untracked** (`??`). No restore from git was attempted. No corruption check failed in a way that forced a restore.

---

## Conflict between the two runs (one paragraph)

Two agents finished minutes apart with different jobs. The earlier one (~06:17, proposal-only) left a **3,194-row high** proposal at EUR **6.02M** in `aim_gap_master_patch_proposal_20260918.csv` and claimed a `…_SUMMARY.md` under `00_derived` — that SUMMARY file is **not on disk**. The later-finishing apply run (~06:20) **overwrote** `aim_gap_auto_assign_20260918.csv` with its own 5,620-row full gap file (**2,468 high / 1,862 medium / 446 low / 844 none**), wrote `aim_gap_high_conf_patch_20260918.csv`, wrote the INBOX summary that says the master was updated, and **did** stamp the master. So the shared filename `aim_gap_auto_assign_20260918.csv` now belongs to the **apply** agent, not the proposal agent. The two high sets only overlap on **2,113** PNs, and among those overlap rows the L1/L2/L3 triples **disagree on 1,347** — same parts, different leaves (e.g. charge-air cooler as Intake/Turbo vs Cooling/Radiator; HV battery as “Battery Cable”; ball joint as Steering Drag Link vs Suspension). They are not two views of one agreed patch.

---

## Which CSV is current?

| File | Role | Winner? |
|---|---|---|
| `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_gap_auto_assign_20260918.csv` | Full gap assign (5,620 rows). Method/confidence columns; **does not say “applied” in-file** — apply is proven by master marker + high patch. | **Current** (apply agent, mtime ~06:20) |
| `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_gap_high_conf_patch_20260918.csv` | Mirror of the 2,468 high rows written to master | Current apply mirror |
| `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_gap_master_patch_proposal_20260918.csv` | Proposal-only 3,194 high; **not** what landed in master | Kept as the other agent’s artefact |
| `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\aim_gap_auto_assign_20260918_summary.md` | Apply agent’s narrative | Current narrative |
| `01_data/00_derived/aim_gap_auto_assign_20260918_SUMMARY.md` | Claimed by proposal agent | **Missing** |

Master path: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_master_v2.csv`

---

## Sample quality (10 top billed real parts)

Checked against non-gap master vocabulary (same L1, L1+L2, and full triple elsewhere).

| PN | Desc (short) | Assigned | Vocab? |
|---|---|---|---|
| 7552816560 | BATTERY ASM; HIGH VOLTAGE | Electrical > Starting & Charging > Battery Cable | L1 only — **L2/L3 invented / wrong leaf** (HV battery ≠ battery cable) |
| 8975340131 | COOLER; CHARGE AIR | Cooling > Radiator > Radiator Assembly | Triple OK in vocab (proposal agent wanted Intake/Turbo) |
| 8974993681 | SENSOR; TIRE INFLATION | Electrical > Sensors & Switches > Radar Sensor | Triple exists — **wrong leaf** (tire ≠ radar) |
| 8978480280 | SENSOR; DEF DCM EXH NOX | Intake Exhaust Emission > Sensors > NOx Sensor | Triple OK |
| 8983929650 | SHAFT ASM; FRT DRIVE | Driveline Axle > Axle Shaft > Drive Shaft | Triple OK |
| 8980256421 | LINK; DRAG | Steering > Linkage > Drag Link | Triple OK |
| 8980058750 | JOINT ASM; BALL,LWR CONT ARM | Suspension > Suspension Arm > Ball Joint | Triple OK |
| 8983300400 | RAIL;COMMON | Fuel System > Fuel Rail > Common Rail | Triple OK |
| 8978752451 | HARNESS; CHAS | Electrical > Harness & Connectors > Connector | Triple OK (leaf a bit coarse) |
| 8980094180 | SENSOR; MAP | Electrical > Sensors > Speed Sensor | **L2 not in prior vocab; MAP ≠ speed** |

Across all 2,480 markers: **0** unknown L1; **56** L1+L2 pairs not seen elsewhere; **64** full triples not seen elsewhere (often `Review needed`); **2** empty L3. **No Friction** leftover; brakes use **Pads & Shoes** where present (1 hit; 271 non-gap already use that L2). **No UTI/UMI distributor nonsense** — one false alarm was the letters `UTI` inside the word **CAUTION**.

---

## Logistics / Shell / wrong stamps

**Logistics Packaging (2):** `0000REBATE` and `0TRANSPORT` only → Packaging > Label. Not stamped onto ordinary hardware. OK as commercial non-parts, though L3 “Label” is odd (proposal used “Non-part”).

**Shell `05500*` oils (7):** all under Fluids Chemicals > Lubricants > Lubricant. Correct family; master € often 0 while revision cube still carries the billed €.

**Wrongly stamped onto real parts (review these):**

- `8978708710` / `8978708720` — **NOZZLE; HEADLAMP CLEANER** → Fluids Chemicals > Cleaning Chemicals > Cleaner (hardware, not fluid)
- `8980603820` — **BOLT; EYE,ATF PIPE** → Transmission Fluid > ATF (bolt, not fluid)
- `1884055560` — **BESCO BRAKE FLUID** → Cleaning Chemicals > **Cleaner** (wrong leaf)

**Extra 12** not in the high patch but marked anyway include obvious garbage leaves (e.g. COVER; FAN,RAD and RUBBER; HELPER as Bumper; PIN; GUIDE with blank L3).

---

## Keep vs review

**Keep** the apply as the working master state for the **2,468** high-confidence rows that match the patch file — do not roll back the whole stamp without a deliberate restore plan (file is untracked, so restore means an older local copy, not `git checkout`).

**Review before trusting pricing / AIM reporting:**

1. Hardware misfiled under Fluids Chemicals (nozzles, ATF bolt; brake fluid as Cleaner).
2. Leaf nonsense with high € (HV battery → Battery Cable; tire sensor → Radar; MAP → Speed Sensor).
3. The **12** extra markers not on the high patch — clear or reclassify.
4. Do **not** merge the proposal agent’s extra **1,081** PNs or its disagreeing triples without a new adjudicated pass — the two runs conflict on method and leaves.

Medium/low in the current auto-assign CSV were **not** meant to update the master; leave them proposal-only until you say otherwise.

---

## Absolute paths

- Reconcile note (this file): `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_gap_reconcile_20260918.md`
- Master: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_master_v2.csv`
- Current full assign CSV: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_gap_auto_assign_20260918.csv`
- Applied high patch: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_gap_high_conf_patch_20260918.csv`
- Proposal-only (other agent): `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_gap_master_patch_proposal_20260918.csv`
- Apply summary: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\aim_gap_auto_assign_20260918_summary.md`
