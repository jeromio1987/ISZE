# AIM + pricing pack (14â€“20 Sep 2026)

**Folder:** `01_data/01_Pricing/_PACK_AIM_Pricing_7d_20260914_20260920/`  
**Method:** Windows shortcuts (`.lnk`) to the live files â€” originals stay where they are.  
**Manifest:** `MANIFEST.csv` in this folder.

Open this folder: double-click `OPEN_PACK.cmd` (next to this file).

---

## Way forward â€” after you arrange the missing base prices

Headline today (rows priced on both sides): **weighted increase +5.9616%**, step **â‚¬1,652,141**. That holds until the BP gaps are filled and the compare is rebuilt.

### Your step

1. Fill **old** and/or **new** base price (JPY) for genuine gaps.  
   List: `00_START_HERE` â†’ `BP_missing_for_price_simulation_20260920.xlsx`  
   Filter out lubricants / rebate admin via `unpriced_reason` â€” they should not block PR00 work.
2. Drop the updated PRICE CD / simulation file into `01_data/01_Pricing/_raw/` (same place as todayâ€™s `PRICE_CD_20260910.xlsx` / `pricing_simulation_2026_5pct.xlsx`).

### Then rebuild (in this order)

| # | What | Builder / open |
|---|------|----------------|
| 1 | BP weighted compare (source of truth) | `07_Builders` â†’ `build_price_bp_weighted_compare.py` â†’ refreshes `01_BP_impact` CSVs |
| 2 | BP impact view + coverage | `01_BP_impact` â†’ `OPEN_ISZE_Price_BP_Weighted_Compare.cmd` |
| 3 | FOB / FX pack (Suzuki 178.5) | `02_FOB_FX` â†’ rebuild via `build_pricing_fx_overlay_20261001.py` |
| 4 | Stack simulation | `03_Simulation_stack` â†’ `build_pricing_stack_simulation_20260919.py` (ask before changing the dated filename) |
| 5 | AIM Ã— source cube + Excel | `04_AIM_x_revision` â†’ `build_pricing_aim_source_cube.py` + analysis xlsx builder |
| 6 | AIM residual (parallel â€” not blocked by BP) | See below |

### AIM residual (can run while BP is still open)

| Track | Size (approx.) | Action |
|-------|----------------|--------|
| Strong description alone | 64 PNs / â‚¬128k | Short review â†’ apply or hold |
| Clean dimension leaves | ~â‚¬280k of the weak pile | Sample top euros â†’ batch apply if clean |
| EQ blanks / conflicts | 744 PNs / â‚¬254k | Snap-on / EQ session (already queued) |
| Soft / noisy long tail | rest of ~â‚¬627k | Do **not** auto-apply |

Do not invent BP for lubricants. Do not ship shared HTML/mail until you say **rebuild** or **ship** on that file.

---

## Folder map

| Folder | Contents |
|--------|----------|
| `00_START_HERE` | This INDEX, BP missing list, AIM status overview, EQ briefs |
| `01_BP_impact` | Weighted BP compare HTML, PN CSV + meta, unpriced + BP-missing lists |
| `02_FOB_FX` | AIM FX / FOB workbook + HTML (178.5) |
| `03_Simulation_stack` | Stack simulation workbook + applied write-up |
| `04_AIM_x_revision` | AIM Ã— TH/JP source analysis Excel + HTML + cube |
| `05_AIM_classification` | 4-signal / applied / residual / EQ / master + classification CSV |
| `06_Policy_decks` | Policy paper, framework, family/market workbooks, management deck |
| `07_Builders` | Main rebuild scripts used this week |

---

## Where things stand (snapshot)

- Missing BP (in-scope unique PN): **599** / â‚¬2.40M union â€” old-only 369, new-only 85, both 145.  
- AIM on revision book: ~**97%** of billed â‚¬ has an L1; open commercial residual still material (EQ + weak/strong-desc).  
- Pack assembled: 2026-09-20. Re-run:  
  `powershell -NoProfile -File 01_data\91_build\assemble_aim_pricing_7d_pack_20260920.ps1`
---

**Duplicates (2026-09-20):** each numbered folder now holds a **full copy** of every listed file **and** a `.lnk` shortcut to the live original. Open the copy in-folder, or the shortcut to jump to the source path.

