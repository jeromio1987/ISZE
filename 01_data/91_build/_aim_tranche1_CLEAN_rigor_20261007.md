# CLEAN tranche-1 rigor — FAIL

**No — conditional apply permission is not earned for the full 38,213.** The CLEAN file still maps cylinder-head gaskets to Transmission, which is the same class of error Shard A already held back on gasket sets. That is a systematic family error, not a thin tail.

Checked **38,213** rows **per part number**. Pass **30,653**, fail **406**, inconclusive **7,154**. Safe-to-apply count if you only keep rows that passed this gate: **30,653** (still a proposal, not a release).

Nothing was written to aim_master. No release CSV was cut.

## What we actually checked

| Check | Grain | Result |
|---|---|---|
| Description fit (proposal + master + Japan code file) | per PN | **31,016** rows have part text; noun/hard rules scored against propose L1 |
| PN length / prefix outliers | per PN | no material length fails; prefix majority rarely pure enough to decide |
| Price (master `eur`) | per PN | no absurd list-price fails on this set |
| ZKK / HKK vs known AIM families | per PN where code is family-pure | ZKK almost useless as a family signal (1 code ≥80% pure at n≥20); HKK 23 codes usable; cannot define what each part is from ZKK alone |
| Teaching bugs | path × propose, plus description hard patterns | gasket-set / trans-asm / air-valve holds **absent** from CLEAN; **cylinder-head gasket → Transmission still present (328)** |

## The mechanism of the FAIL

Shard A held `Repair parts > Gaskets / seals > Gasket set` → Transmission (6,550 rows). CLEAN correctly dropped that path.

It did **not** drop `Repair parts > Gaskets / seals > Cylinder head gasket` → Transmission (**328** rows). Japan descriptions on the described subset say things like `GASKET; CYL HD` — engine cylinder-head gaskets — while the proposal still names them Transmission. That contradicts the same teaching you locked on 2026-10-04 (engine gasket language belongs under Engine > Gasket & Sealing, not Transmission).

Of the 406 fails, **328** are that path (teaching-bug flag). Most of those also trip the description hard rule. The other ~80 fails are thinner description/stem conflicts, not another whole wrong family.

## Did we define what each part is from description / ZKK / HKK?

**Description — mostly yes on the 31,016 with text.** Join worked once Japan PNs were padded to 10 characters (earlier Shard A only filled ~287 because it looked up the wrong column). That is how the cylinder-head gasket leak was visible.

**ZKK / HKK — no, not as a family definition.** Codes are filled on ~31,000 CLEAN rows, but ZKK is a Japan catalogue attribute that mixes hundreds of part types under one code. It cannot approve or reject AIM families for this proposal. HKK is slightly more usable on a few dozen codes only. Commodity codes here are coverage, not proof.

**7,154 rows** have no description and no strong ZKK/HKK majority signal → marked **inconclusive**, not pass.

## Teaching-bug re-verify

- Gasket set → Transmission: **0** (held)
- Transmission assembly → Literature: **0** (held)
- Air valve → Steering: **0** (held)
- Cylinder head gasket → Transmission: **328** (still in CLEAN — this is why permission fails)

## Apply permission

**Verdict: FAIL.** Flag: `NOT_EARNED`.

If you later want a narrower proposal, hold the cylinder-head gasket path (and review the residual ~80 description conflicts), then the pass set is about **30,653**. That subset is written as a proposal-only SAFE file below — still not applied.

## Files

- Summary JSON: `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_tranche1_CLEAN_rigor_20261007.json`
- Fail / inconclusive rows: `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_tranche1_CLEAN_rigor_fails_20261007.csv`
- SAFE proposal (pass only): `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_tranche1_CLEAN_rigor_SAFE_20261007.csv`
- Checker script: `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_tranche1_CLEAN_rigor_20261007.py`
