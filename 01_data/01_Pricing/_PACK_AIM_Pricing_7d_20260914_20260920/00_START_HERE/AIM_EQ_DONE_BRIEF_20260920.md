# AIM / EQ work done — 20 September 2026

Brief status for Jerome. Internal.

## Done today

1. **Fig-key vs AIM check** — figure key matches figure no + key no (clean). Found real identity errors (clutch as Brakes/Chassis, air cleaner as cleaning chemical). Patched those by euro.

2. **Critic review accepted and fixed on the live master**
   - **299** corrupt L3 cells (pandas dump) recovered from the residual patch
   - **169** identity rows: slave ≠ Pivot, disc/plate ≠ Kit, guide pin, coil spring, stabilizer bar, heater core, injection pipe, sensors, chillers; REBATE cleared from a physical path
   - New component leaves where the spine was forcing the wrong nearest label

3. **EQ overnight leftovers remapped where clean** — **111** PNs (~€18k): mounts, gears, head covers, rockers, etc.

4. **Leaves unlocked and applied** — **45** PNs (~€27k):
   - Transmission / Case / Case Cover  
   - Accident & Body / Wiper & Washer / Wiper Link  
   - Engine / Internal Rotating / Connecting Rod  
   - Electrical / Audio / Speaker | Microphone | Radio  
   - Fluids Chemicals / Coolant / Coolant  

5. **Left open on purpose**
   - EQ NEEDS_HUMAN is **not** “all missing leaf” — five-way system stays trusted; only translator/leaf gaps held
   - After unlock: **186 of 360** session NEEDS_HUMAN rows still blank/unknown (ambiguous fig/part, blank EQ evidence, or no clean rule yet)

6. **Not done** — catalogue reporting file not rebuilt (Other/review % still stale). No management pack ship. No commit.

## Live file

`01_data/00_derived/aim_master_v2.csv`  
Stamps: `figkey_aim_fix_20260920` · `critic_fix_20260920` · `eq_remap_20260920` · `leaf_unlock_20260920`

## Still-open list

`01_data/90_INBOX/_EQ_NEEDS_HUMAN_still_open_after_leaf_unlock_20260920.csv`

## How to talk about the trees (no “V2”)

- **Catalogue product tree** — Competitive / Repair / Accident / … / Other needing review  
- **AIM parts family** — Clutch, Brakes, Engine, … (three levels each)

## Management posture (from critic — still valid)

Approve bounded validation + pilot; do not treat every latest assignment as ready for unrestricted use. Component vs kit must stay explicit.
