"""Read-only: what does each remaining candidate page read, and is that source AIM-master-derived?"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
FILES = [
    "03_analytics/Isuzu/prism/scripts/build_dealer_sellout_aim_gps.py",
    "03_analytics/Isuzu/prism/scripts/build_risk_cockpit_viz.py",
    "03_analytics/Isuzu/prism/scripts/build_isze_dashboard_json.py",
    "02_dashboards/sales/_build/build_pms_capture_by_family.py",
    "02_dashboards/sales/_build/build_pms_family_evolution_v2.py",
    "02_dashboards/sales/_build/lost_sales_model/build_lost_sales_model_html.py",
    "02_dashboards/_build/build_kpi_dashboard.py",
]
pat = re.compile(r"""["'(]([A-Za-z0-9_\-]+\.(?:csv|parquet|json))["')]""")
for rel in FILES:
    p = ROOT / rel
    if not p.is_file():
        print("==", rel, "MISSING")
        continue
    s = p.read_text(encoding="utf-8", errors="replace")
    names = sorted(set(pat.findall(s)))
    aim = [n for n in names if "aim" in n.lower()]
    outs = sorted(set(re.findall(r"(?:to_csv|to_parquet|write_text)\([^,\n)]*([A-Za-z0-9_\-]+\.(?:csv|parquet|json|js))", s)))
    print("==", rel)
    print("   AIM-ish inputs:", ", ".join(aim) or "(none)")
    print("   writes:", ", ".join(outs) or "(none)")
    print("   master?", "aim_master_v2" in s, "| classification?", "aim_pn_classification" in s)
