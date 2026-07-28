# Customer deep-study packs — V4

## Open now — V4 (all distributors)

**Period:** FY2024 (Apr 2024–Mar 2025) vs FY2025 (Apr 2025–Mar 2026) — both complete (billing through 2026-03-31).

| Hub | Path |
|-----|------|
| All 22 HTML/Excel/JSON | [`V4/`](V4/) · also [`../DB_Sales_Order_Study/deep_v4/`](../DB_Sales_Order_Study/deep_v4/) |
| **I Motors** | [`ISZE_Imotors_Deep_Study_V4.html`](ISZE_Imotors_Deep_Study_V4.html) · [`.xlsx`](ISZE_Imotors_Deep_Study_V4.xlsx) |
| **UMI** | [`ISZE_UMI_Deep_Study_V4.html`](ISZE_UMI_Deep_Study_V4.html) · [`.xlsx`](ISZE_UMI_Deep_Study_V4.xlsx) |

Rebuild:

```powershell
python "$env:ISZE_ROOT\09_meetings\Preparation Meetings\Imotors_UMI_Sales_Study\_build_v4_customer_packs.py"
```

Rules: [`CUSTOMER_PACK_RULES.md`](CUSTOMER_PACK_RULES.md)

### V4 vs V3.1

- **All 22 customers** (not only I Motors + UMI)
- **Part-number depth:** vanished / new / continuing qty droppers + channel-shift test (customer-local vs network-wide vs shift)
- Figures refreshed from current `sales_fact` + canonical `pms_capture_by_db_year` (`model_bucket`)
- Same Mode A rules: one network YoY benchmark, GPS now-vs-past only, PMS never silent-cap, no “PR00” wording

## Earlier

| Version | Role |
|---------|------|
| V3.1 | I Motors + UMI only — superseded by V4 |
| V3 | First separate packs |
| V2 | Dual compare — internal only |
