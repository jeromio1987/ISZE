# AIM PBI file — deep QA verdict (2026-10-11)

## Bottom line

The Oct-7 file Bart would load is **better than the 21 Sep file he still has**.
It is **not** free of every old misfile. I would still send it for PBI, with eyes open on the leftovers below.

## What I checked

- File hashes vs the approved release register (2026-10-07)
- Excel vs CSV (same rows / same AIM path + figure key)
- Full Sep-21 vs Oct-7 compare (fills, losses, path changes)
- Known remaps: engine gasket sets, EVRV, antennas, DEF injectors
- Export vs governed classification (`aim_l1/2/3_fixed`)
- Export vs master `aim_l1_fixed` (first pass false alarm fixed)
- Independent sales-fact euro coverage
- Strict conflict scan on all 31,216 blank→AIM fills
- Top sales-euro path changes + random samples

Reports on disk:
- `01_data/91_build/_aim_pbi_export_deep_qa_20261011.md`
- `01_data/91_build/_aim_pbi_export_deep_qa_pass2_20261011.md`

## Better than 21 Sep

| Check | Sep-21 | Oct-7 |
|---|---:|---:|
| PNs with an AIM family | 24,470 | 55,895 |
| Blank → AIM fills | — | +31,216 |
| AIM lost | — | **0** |
| Engine gasket sets under Transmission | 207 | **0** (now Engine) |
| EVRV under Steering | 7 | **0** (now Intake/EGR) |
| DEF injector under Fuel (main billed ones) | yes | moved to DEF System |
| Antennas | many Unknown / Instrument Cluster | mostly Electrical > Audio > Radio |
| Sales euro with AIM family | 97.71% | 97.84% |

xlsx fingerprint = csv. Approved hash matches.

## Old dirt still in the file (not introduced by Oct-7)

These were already wrong on 21 Sep:

1. **Cylinder-head gasket under Transmission** — 79 PNs, about **€45k** on the export l12m field. Same class of error as before; 2 eng-head gasket *sets* were fixed Engine-side.
2. **Transmission ASM filed under Literature / Manuals** — 38 PNs, about **€273k** sales. Same set as Sep-21.

So PBI will still show those wrong until a later clean-up. Oct-7 does not make them worse.

## Small new mistakes found (low euro)

Among 31,216 new fills, a strict keyword scan found **10** clear conflicts, **€127** sales on the worst one:

- `8973586990` PIPE ASM; WATER,TURBOCHARGER RETURN → Fuel > Sedimenter (should be cooling / turbo water)
- `5873113800` turbocharger kit → Brake caliper repair kit (€0 billed)

A few water-pipe *brackets* landed under Chassis Frame brackets (soft).

One soft fill: `8983419590` PLATE; BRAKE → Transmission case (€34).

## High-euro remaps that look right

DEF injectors (~€290k), EVRV valves, Shell oils that were wrongly under Wheel Rim, cab assemblies, engine mounts from Unknown, antennas to Radio.

## Can you be 100% sure?

No. Nobody can swear a 165k-row parts tree has zero wrong leaves.
What I can swear from this pass:

1. The file attached for Bart is the approved Oct-7 cut (hash locked).
2. Excel and CSV match.
3. It is materially better than 21 Sep on the remaps you care about.
4. It does not drop AIM families that Sep-21 already had.
5. Known old misfiles (cyl-head gasket, transmission ASM→literature) are still there.
6. A handful of small new fill errors exist; they are tiny in euro vs the fixes.

**Recommendation:** send the draft. Do not wait for a perfect catalogue. Park cyl-head gasket + transmission-ASM literature as the next clean-up if Bart asks why those still look odd in PBI.
