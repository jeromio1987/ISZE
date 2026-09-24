"""Inspect exactly what the payload carries for the band labels and the settled evidence rows.

Answers:
  * does `weightEvidence.settled` carry one row per band, or several?
  * does each row's `label` equal the band's `label` in `D.bands`, or differ?
  * where exactly does the INTERIM string live?
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HTML = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales"
            r"\ISZE_PMS_Family_Evolution_v2.html")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass


def main() -> int:
    h = HTML.read_text(encoding="utf-8")
    d = json.loads(re.search(r'<script id="pmfe2-data" type="application/json">(.*?)</script>',
                             h, re.S).group(1))
    print("=" * 100)
    print("D.bands (the label the evidence table renders today)")
    print("=" * 100)
    for b in d["bands"]:
        print(f"  {b['key']:22s} label {b['label']!r}")
    print()
    print("=" * 100)
    print("D.weightEvidence.settled (the rows, with their own labels)")
    print("=" * 100)
    for s in d["weightEvidence"]["settled"]:
        print(f"  band {s['band']:22s} series {str(s['series']):6s} "
              f"confidence {s['confidence']:8s} label {s['label']!r}")
    print()
    print("=" * 100)
    print("D.seriesEvidence")
    print("=" * 100)
    for k, v in d["seriesEvidence"].items():
        if isinstance(v, dict):
            print(f"  {k}: label {v.get('label')!r} series {v.get('series')}")
        else:
            print(f"  {k}: {v}")
    print()
    print("=" * 100)
    print("EVERY occurrence of the INTERIM string in the payload")
    print("=" * 100)
    text = json.dumps(d)
    for m in re.finditer(r".{70}INTERIM.{60}", text):
        print(f"  ...{m.group(0)}...")
    print(f"  total occurrences: {text.count('INTERIM')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
