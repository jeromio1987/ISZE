#!/usr/bin/env python3
from pathlib import Path
import shutil

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_fixed")
GPT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\08_gpt\html_dashboard_review_next10_2026-09-19")

extra = """

## Visual QA notes (2026-09-19)

- Screenshots: 10 taken, 10 image-read under `_qa/*_viewport.png`. Suite receipt: `SUITE.SHIP_RECEIPT.json`.
- Exec / Leakage / Dealer / Pricing Policy / 5pct / AIM case: first viewport paints with basis strip; no blank shells.
- Pricing Revision AIM Source: charts and KPIs paint; bar chart continues below fold (expected).
- Warranty: KPI cards paint; ten-line bar charts start on first viewport and continue below fold.
- AIM Classification: hero paints; lower card body text is tight at fold (pre-existing density, not blank).
- Competitiveness: fixed preload key alias (`../Data/...` vs `Data/...`) so file:// loads. KPIs now paint.
  Autodoc Class C table still shows bad scrap mins (€2.34) / 0% ratios — scrap data quality, not this language pass.

## Builders touched (for next rebuild)

- `02_dashboards/_build/build_exec_aftersales_paper.py` — rebuilt live, then basis strip polished onto copy/live
- `02_dashboards/_build/build_warranty_commercial.py` — rebuilt + basis strip
- `02_dashboards/_build/leakage/labels.mjs` — title/nav wording (full node rebuild deferred)
- `03_analytics/Isuzu/prism/scripts/build_dealer_sellout_aim_gps.py` — HTML strings patched (full data rebuild deferred this pass)
"""

log = OUT / "FIX_LOG.md"
t = log.read_text(encoding="utf-8")
if "Visual QA notes" not in t:
    log.write_text(t.rstrip() + extra, encoding="utf-8")

idx = OUT / "INDEX.md"
it = idx.read_text(encoding="utf-8")
block = """

## Live originals (overwritten)

Same content also at:

1. `C:\\Users\\jerom\\Desktop\\claude\\ISZE\\02_dashboards\\sales\\ISZE_Exec_Aftersales_Paper.html`
2. `C:\\Users\\jerom\\Desktop\\claude\\ISZE\\02_dashboards\\sales\\ISZE_Leakage_Cockpit.html`
3. `C:\\Users\\jerom\\Desktop\\claude\\ISZE\\02_dashboards\\sales\\Warranty_Commercial_Review.html`
4. `C:\\Users\\jerom\\Desktop\\claude\\ISZE\\02_dashboards\\sales\\ISZE_AIM_Classification_Paper.html`
5. `C:\\Users\\jerom\\Desktop\\claude\\ISZE\\02_dashboards\\sales\\ISZE_AIM_vs_Price_Class_Case.html`
6. `C:\\Users\\jerom\\Desktop\\claude\\ISZE\\02_dashboards\\pricing\\ISZE_Pricing_Policy_Paper_REV3.html`
7. `C:\\Users\\jerom\\Desktop\\claude\\ISZE\\02_dashboards\\pricing\\ISZE_Pricing_Revision_AIM_Source.html`
8. `C:\\Users\\jerom\\Desktop\\claude\\ISZE\\02_dashboards\\pricing\\ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html`
9. `C:\\Users\\jerom\\Desktop\\claude\\ISZE\\02_dashboards\\sales\\ISZE_Competitiveness_Dashboard.html`
10. `C:\\Users\\jerom\\Desktop\\claude\\ISZE\\02_dashboards\\sales\\Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html`

Open fixed map: double-click `0N_OPEN_*.cmd` in this folder.
"""
if "Live originals" not in it:
    idx.write_text(it.rstrip() + block, encoding="utf-8")

shutil.copy2(log, GPT / "FIX_LOG.md")
shutil.copy2(idx, GPT / "FIXED_INDEX.md")
print("docs updated")
