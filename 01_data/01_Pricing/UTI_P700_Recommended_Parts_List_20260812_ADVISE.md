# UTI P700 recommended parts list — advise

**internal notes · 2026-08-12T11:49:59Z · UTI ≠ UMI · Shell out · RG21 not mixed**

## Deliverables

| File | Role |
|------|------|
| `UTI_P700_Recommended_Parts_List_20260812.xlsx` | Excel: Advise · Recommended · Volume_context · Family_priority · Catalogue_all_VL27 |
| `UTI_P700_Recommended_Parts_List_20260812.csv` | Recommended sheet only (CSV) |
| `uti_p700_recommended_parts_list_20260812.csv` | Same CSV under derived |

## Counts

- **Recommended unique PN:** 1885
- **Catalogue_all VL27 unique PN:** 4282
- **Recommended ∩ ITUK APL:** 1109
- **Priority split:** {"P3_other_recommended": 1021, "P0_first_stock": 533, "P1_wear": 167, "P2_body": 164}
- **Source roles (exploded):** {"VL27_Belgium_recommended": 1369, "ITUK_P700_initial_PRD": 458, "accessories_list": 52, "body_P700_sample": 20}

## How “recommended” was chosen

1. **VL27 Belgium — Recommended Class** (not All Parts)  
2. **ITUK P700 initial PRD** (first-stock)  
3. **Accessories** 2026 list + ITUK feedback (FCA/EXW EUR where printed)  
4. **Body P700** sample rows only (not old N75 column)  

VL27 **All Parts** stays on `Catalogue_all_VL27` with `list_flag=catalogue_all` unless the PN is also on Recommended.

## Volume

- **800** CY2025 → **1000** CY2026 units → scale **1.25** on network demand index / Book B seed €  
- **No per-PN qty** invented

## Can continue without detail

- PN universe from APL  
- Family prioritisation (P0/P1/P2/P3 qualitative)  
- Book B growth hook **1.25** on UTI P700 seed € once ambition % is set  
- ITUK APL overlap crosswalk  

## Still need (ask Jerome)

1. Model mix (3.5t / 6.5t / 7.5t / 13.5t) or rough %  
2. Gearbox mix (ISIM DCT vs manual) if known  
3. Market for 800/1000 (Israel UTI only?)  
4. Preferred price basis (FCA accessory vs PR00)  
5. Ambition % for Book B  
