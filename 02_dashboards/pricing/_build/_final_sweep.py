"""Final sweep: every superseded pricing figure, on published pages and builders, with file+line."""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")

SUPERSEDED = {
    "+1.7393% whole priced book": re.compile(r"1[.,]7393"),
    "+5.7076% Japan": re.compile(r"5[.,]7076"),
    "-2.4751% Thailand": re.compile(r"2[.,]4751\s*%|[-−]\s*2[.,]4751"),
    "+7% base revision (fabricated)": re.compile(r"7\s*%\s*(?:base\s*)?revision", re.I),
}
SETTLED = {
    "+1.8001% / +1.80% whole book": re.compile(r"1[.,]800[01]\s*%|\+1\.80%"),
    "+5.7369% / +5.74% Japan": re.compile(r"5[.,]7369|\+5\.74%"),
    "-2.4513% / -2.45% Thailand": re.compile(r"2[.,]4513|[-−]2[.,]45%"),
}

TARGETS = [
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source.html",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.html",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source_L3PN_20260918.html",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_FX_20261001.html",
    "02_dashboards/pricing/PRICING_STACK_APPLIED_2026-09-19.html",
    "02_dashboards/pricing/ISZE_Price_BP_Weighted_Compare.html",
    "02_dashboards/pricing/ISZE_Pricing_Policy_Paper.html",
    "02_dashboards/pricing/_build/build_pricing_revision_dashboard.py",
    "02_dashboards/pricing/_build/build_pricing_revision_prototype_alldb.py",
    "02_dashboards/pricing/_build/build_pricing_fx_overlay_20261001.py",
    "02_dashboards/pricing/_build/build_price_bp_weighted_compare.py",
]

total_bad = 0
for rel in TARGETS:
    p = ROOT / rel
    if not p.is_file():
        print(f"{rel}\n   NOT ON DISK\n")
        continue
    raw = p.read_text(encoding="utf-8", errors="replace")
    lines = raw.split("\n")
    in_payload = False
    bad, good = [], []
    for i, ln in enumerate(lines, 1):
        if re.search(r'<script[^>]*type="application/json"', ln):
            in_payload = True
        if in_payload:
            if "</script>" in ln:
                in_payload = False
            continue
        for name, rx in SUPERSEDED.items():
            for m in rx.finditer(ln):
                a = max(0, m.start() - 110)
                b = min(len(ln), m.end() + 110)
                bad.append((i, name, ln[a:b].strip()))
        for name, rx in SETTLED.items():
            if rx.search(ln):
                good.append((i, name))
    total_bad += len(bad)
    print(f"{rel}")
    for i, name, ctx in bad:
        print(f"   SUPERSEDED  L{i}  {name}")
        print(f"               ...{ctx}...")
    seen = sorted(set(n for _, n in good))
    if seen:
        print(f"   settled figures present: {', '.join(seen)}")
    if not bad and not seen:
        print("   no superseded figure, no settled headline (nothing to correct)")
    print()

print(f"TOTAL SUPERSEDED HITS: {total_bad}")
