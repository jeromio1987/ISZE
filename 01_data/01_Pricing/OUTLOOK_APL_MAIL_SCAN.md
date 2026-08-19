# APL hunt — ITUK vs UTI P700

**RG21 = D-Max 2.2L.**  
**Source this pass:** files already under `01_data/90_INBOX/` (Outlook COM hung; disk inventory used). No part numbers invented.

---

## 1) ITUK APL / Recommended parts list (Suzuki)

**Found — yes.**

| Item | Path |
|------|------|
| Suzuki zip **`20260714_1037.zip`** | `01_data/90_INBOX/APL_ITUK_202607/2026-07-23_20260714_1037.zip` (+ `…_ITUK_20260714_1037.zip`) |
| Same zip earlier pull | `01_data/90_INBOX/suzuki_pms_mail_pull/20260723_035639_20260714_1037.zip` |
| Unpacked | `suzuki_pms_mail_pull/zip_20260714_1037/20260714_1037/` → **10 × `.xls`** (IDs like `90119_12231_…`, `91010_…` … `91769_…`) |

Also in `APL_ITUK_202607` (useful for ITUK / VR05 / RG21):

- `2026-02-05_ITUK_APL_VR05_Israel.zip` / `…_ISZE.zip`
- `2026-05-12_ITUK_VK05_UK_B_Gr.zip`
- **RG21 (= 2.2L) recommended lists:**  
  - `2026-05-07_ITUK_RL_for_RG21_Norway_20251028.xlsx` (~4440 data rows, sheet `RL`)  
  - `2026-07-01_ITUK_RL_for_RG21_Greece.xlsx` (same shape)

Screenshot mail (Suzuki → Natalie, 23 Jul 2026, APL VR05 D-Gr) matches the **`20260714_1037.zip`** already filed.

Folder: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\APL_ITUK_202607` (**33** files)

---

## 2) UTI P700 APL

**Found — yes (mixed bag; not empty).**  
Folder: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\APL_UTI_P700` (**26** files)

### Clearly P700 / UTI-relevant

| File | Role (from name) |
|------|------------------|
| `2026-02-05_UTI_P700_RHD_P700_N-series_accessories_part_no_2026_price_list.xlsx` | P700 N-series accessories PN + 2026 price list |
| `2026-07-20_…_RHD_P700_N-series_accessories_…_ITUK_Feedback.xlsx` | Same family + ITUK feedback |
| `2026-05-20_UTI_P700_All_Parts_and_Recommended_Items_list_for_New_Project_VL27_Belgium_.xlsx` | Recommended items — new project VL27 BE |
| `2026-05-28_UTI_P700_For_N-series.xlsx` / `…_For_F-series.xlsx` | N / F series lists |
| `2026-07-15_UTI_P700_body_parts_p-700.xlsx` | P700 body parts |
| `2026-07-31_UTI_P700_ITUK_P700_initial_PRD.xlsx` | ITUK P700 initial PRD |
| `2026-07-13_UTI_P700_VK05_UK_D_Gr.zip` | VK05 UK D-Gr pack |
| `2026-05-12_UTI_P700_VK05_UK_B_Gr.zip` | VK05 UK B-Gr (same size as ITUK VK05 B-Gr — likely shared pack) |

### Caution — may be ITUK APL copies renamed into UTI folder

- `2026-07-23_UTI_P700_20260714_1037.zip` — **same Suzuki ITUK APL zip** (do not call this “UTI P700 APL” without opening; it is the ITUK recommended-parts pull)

---

## 3) Outlook live scan

COM Restrict/brute **hung** this session (Outlook lock).  
Evidence above is from **on-disk INBOX pulls**, not a fresh mailbox walk.

---

## Next (when you want)

1. ~~Parse ITUK `20260714_1037` × `.xls` + RG21 RL sheets into a clean PN table~~ → done 2026-08-12 (`apl_pn_list_*_20260812.csv`).  
2. ~~Parse UTI P700 accessories + VL27 + body + PRD~~ → done (N/F series skipped: no PN column).  
3. Keep Shell out; use `apl_pn_list_book_b_seeds_20260812.csv` for **forecast-weighted ambition** Book B join.

See map in `01_data/01_Pricing/PLAN_FORECAST_WEIGHTED_AMBITION.md` § Real PN lists from APL packs.
