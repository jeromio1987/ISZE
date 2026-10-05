"""The exec paper's printed per-market table: are the six markets showing the rebuilt cover?

Reads the table rows out of the built HTML and prints them, so the numbers on the page can
be compared with the ceiling file rather than trusted from the builder's log.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PAPER = ROOT / "02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html"
WALLET = ROOT / "01_data/00_derived/wallet_waterfall.csv"

SIX = ["PORTUGAL", "IRELAND", "GERMANY", "BELGIUM", "MALTA", "CYPRUS"]


def main() -> int:
    t = PAPER.read_text(encoding="utf-8")
    w = pd.read_csv(WALLET)
    w25 = w[w.year == 2025].set_index("distributor_code")

    print("per-market rows found in the paper (label | uio | ceiling | cover):")
    rows = re.findall(r"<tr><td>([^<]{2,30})</td>(.{0,400}?)</tr>", t, flags=re.S)
    seen = 0
    for label, rest in rows:
        cells = re.findall(r'class="n">([^<]*)<', rest)
        if len(cells) >= 3:
            seen += 1
            print(f"  {label:22s} {' | '.join(c.strip() for c in cells[:4])}")
    print(f"  ({seen} rows)")

    print("\nwhat the ceiling file says for the six:")
    for code in SIX:
        r = w25.loc[code]
        print(f"  {code:9s} uio {int(r.uio_units):>7,}  ceiling {float(r.theoretical_wallet_eur):>12,.0f}  "
              f"cover {float(r.gps_pct):>6.1f}%")

    print("\nstale markers still in the paper:")
    for needle in ("56.0%", "124.2%", "40.3%", "55.25M", "55.7%"):
        n = t.count(needle)
        if n:
            print(f"  {needle}: {n}")
            for m in list(re.finditer(re.escape(needle), t))[:2]:
                s, e = max(0, m.start() - 130), min(len(t), m.end() + 60)
                print("      ...", " ".join(t[s:e].split()), "...")
    print("\nheading / thesis numbers:")
    for needle in ("54.38M", "56.6%", "41%", "70.4", "138.7"):
        print(f"  {needle}: present={needle in t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
