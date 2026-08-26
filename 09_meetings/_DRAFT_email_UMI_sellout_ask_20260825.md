# Draft — UMI sell-out / PartSales ask

**To:** UMI parts contact (keep separate from UTI 1799 — UMI is sold_to **1797**)  
**From:** Jerome / ISZE  
**Subject:** UMI parts sell-out data request (PN × month qty) — FY2027 analytics  
**Status:** DRAFT — not sent  
**Date drafted:** 2026-08-25  

---

Hi,

For our network aftersales analytics we already receive monthly **UTI** PartSales (1799). We need the same visibility for **UMI** (1797) — please do **not** blend the two entities.

Could you please send (Excel is fine):

1. **Parts sold to dealers / network** for **calendar 2025** (full year) and **2026 YTD** through the latest closed month  
2. Grain: **part number × month × quantity** (EUR optional — qty is enough)  
3. If you have an automated job like UTI’s `UTIPartSales`, the monthly attachment on the 1st is ideal going forward  

We will file it under our dealer sell-out registry and use it only for internal GPS/PMS capture and replenishment work — not for public disclosure of line-level dealer data.

Happy to jump on a short call if the extract layout needs aligning.

Thanks,  
Jerome

---

**Filing note (after reply):** drop attachment in `01_data/90_INBOX/` → `12_raw/dealer_sales/UMI/` → register in `_registry.yaml` → normalize long CSV → run `build_dealer_sellout_aim_gps.py`.
