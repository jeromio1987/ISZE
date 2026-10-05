"""Independent audit of the two pricing deliverables.

Run by the parent after the builder reported done, so the "verified" claim is
checked rather than inherited: self-containment of the HTML, coverage of the
receipts against the current file, and the workbook's own tie-out.

Run: python 02_dashboards/pricing/_build/audit_pricing_deliverables.py
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ISZE / "02_dashboards" / "pricing" / "ISZE_Pricing_Revision_AIM_Source.html"
XLSX = ISZE / "01_data" / "01_Pricing" / "Pricing_Revision_AIM_Source_Analysis.xlsx"

fails: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{'  — ' + detail if detail else ''}")
    if not ok:
        fails.append(label)


print("=" * 78)
print("HTML — self-containment")
print("=" * 78)
src = HTML.read_text(encoding="utf-8")
check("file exists", HTML.exists(), f"{HTML.stat().st_size/1024:,.0f} KB")
ext = re.findall(r'(?:src|href)\s*=\s*["\'](https?://[^"\']+)', src)
check("no external http(s) dependency", len(ext) == 0, f"{len(ext)} found {ext[:4]}")
check("no file:// links", src.count("file://") == 0)
# The minified UMD bundle names itself "chartjs" internally (_chartjs listeners,
# $chartjs) and assigns the export as Chart=. It ships no source map. Assert on
# those internals plus the absence of any CDN host, not on the source filename.
inlined = ("cdn.jsdelivr" not in src and "cdnjs" not in src and "unpkg" not in src
           and "_chartjs" in src and "Chart=" in src)
check("Chart.js inlined, not CDN", inlined,
      f'_chartjs={"chartjs" in src}, export={"Chart=" in src}')
check("no sourceMappingURL left in the bundle",
      "sourceMappingURL" not in src)
check("data embedded as JSON", 'type="application/json"' in src)
check("no NaN literal in payload", not re.search(r':\s*NaN\b|"NaN"', src))
check("four canvas elements", src.count("<canvas") == 4, f"{src.count('<canvas')}")
check("uses the Chart constructor", "new Chart(" in src)
payload = re.search(r'<script type="application/json" id="payload">([\s\S]*?)</script>', src)
if payload:
    d = json.loads(payload.group(1))
    t = d["totals"]
    check("payload total matches published step", abs(t["step"] - 1652140.71) < 0.05,
          f'€{t["step"]:,.2f}')
    check("payload total matches published %", abs(t["pct"] - 5.9616) < 0.001,
          f'{t["pct"]:.4f}%')
    check("pool + groups present",
          all(k in d for k in ("pool", "groups", "customers", "db_rows")))
    check("22 distributors pooled", len(d["pool"]["db"]) == 22, f'{len(d["pool"]["db"])}')

print()
print("=" * 78)
print("Receipts cover the current files")
print("=" * 78)
for art in (HTML, XLSX):
    st = art.stat()
    rp = art.with_name(art.stem + ".SHIP_RECEIPT.json")
    if not rp.exists():
        check(f"receipt for {art.name}", False, "missing")
        continue
    rec = json.loads(rp.read_text(encoding="utf-8"))
    cover = rec["artifact_mtime_ms"] >= int(st.st_mtime * 1000) - 2000
    bad = [c["id"] for c in rec["checks"] if not c["ok"]]
    check(f"receipt ok and covers mtime ({art.name})", rec["ok"] and cover and not bad,
          f'ok={rec["ok"]} covered={cover} fails={bad or "none"}')
    # the launcher for this HTML is named OPEN_Pricing_Revision_AIM_Source.cmd, so
    # matching on the artifact's own stem fails; match on the target filename inside
    cands = sorted(art.parent.glob("OPEN_*.cmd"))
    hits = [c for c in cands
            if art.name in c.read_text(encoding="ascii", errors="replace")]
    ok_cmd = len(hits) == 1
    crlf = ok_cmd and b"\r\n" in hits[0].read_bytes()
    check(f"launcher beside {art.name}", ok_cmd and crlf,
          f'{hits[0].name if hits else "none"} crlf={crlf}')

print()
print("=" * 78)
print("Workbook — structure and last-known tie-out")
print("=" * 78)
try:
    import openpyxl
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    want = ["Read me", "DB summary", "DB x AIM L1", "DB x AIM L2", "DB x AIM L3",
            "TH-JP source", "Source x AIM L1", "Customer", "Top movers", "PN data",
            "Checks"]
    check("11 expected sheets", wb.sheetnames == want,
          f"{len(wb.sheetnames)} sheets")
    ws = wb["PN data"]
    check("PN data rows match the in-scope count", ws.max_row - 4 == 48653,
          f"{ws.max_row - 4:,} rows")
    wb.close()
except Exception as e:  # noqa: BLE001
    check("workbook opens", False, str(e)[:120])

print()
print("=" * 78)
print("FAILED CHECKS" if fails else "ALL CHECKS PASSED")
if fails:
    for f in fails:
        print("  -", f)
print("=" * 78)
