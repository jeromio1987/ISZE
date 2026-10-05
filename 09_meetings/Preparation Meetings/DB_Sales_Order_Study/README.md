# DB Sales & Order Study — network pipeline (resumable)

**Hub folder:** `09_meetings/Preparation Meetings/DB_Sales_Order_Study/`  
**Deep template (current):** `../Imotors_UMI_Sales_Study/_build_v4_customer_packs.py`

## Status (2026-07-26)

| Phase | State |
|-------|--------|
| Shallow all-DB packs | **Complete** (22 DBs) → `packs/*.json` |
| Customer deep **V4** | **Complete** — all 22 DBs → [`deep_v4/`](deep_v4/) |

## Customer deep deliverables (V4)

FY2024 vs FY2025 (Apr–Mar), PN depth + channel-shift, shared single-customer packs.

| Location | Contents |
|----------|----------|
| [`deep_v4/`](deep_v4/) | All 22 HTML + Excel + JSON |
| Highlight copies | `../Imotors_UMI_Sales_Study/ISZE_Imotors_Deep_Study_V4.*` · `ISZE_UMI_Deep_Study_V4.*` |

Rebuild:

```powershell
python "$env:ISZE_ROOT\09_meetings\Preparation Meetings\Imotors_UMI_Sales_Study\_build_v4_customer_packs.py"
```

Rules: `../Imotors_UMI_Sales_Study/CUSTOMER_PACK_RULES.md`

## Way of working

1. Confirm PBI access → `SALES DATA VP NEW` (SALES + ORDER).
2. Green `_verification_report.json` before KPIs.
3. Hierarchy: network → customer → SaTy → source/category → PN depth + GPS/PMS.
4. FY = Apr–Mar; only **complete** FYs in deep packs.
5. Total PMS primary; UMI pack never emits UTI; external language on shared decks.
6. Chart-first HTML (Chart.js inlined, no CDN) + Excel pre-delivery check.
