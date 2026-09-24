"""Read-only: list the data files each of the three stale pages reads."""
import re
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
FILES = [
    "02_dashboards/_build/build_pms_family_compare.py",
    "02_dashboards/sales/_build/build_pms_tonnage_evolution.py",
    "02_dashboards/sales/_build/build_db_dlr_replenishment_cy2025.py",
    "02_dashboards/_build/aftermarket_bi_data.py",
    "02_dashboards/_build/tier_a_dashboard_common.py",
]
pat = re.compile(r"""["'(]([A-Za-z0-9_\-]+\.(?:csv|parquet|json))["')]""")
for rel in FILES:
    p = ROOT / rel
    s = p.read_text(encoding="utf-8", errors="replace")
    names = sorted(set(pat.findall(s)))
    print("==", rel)
    print("   ", ", ".join(names) or "(none)")
