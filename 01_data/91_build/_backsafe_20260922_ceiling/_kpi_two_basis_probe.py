"""Ask the rebuilt KPI dashboard what ceiling basis each market row is on.

Reads the embedded payload out of the built HTML (not the builder's variables) and
prints the network ceiling, plus per market the ceiling it carries, the fleet beside
it, and the implied per-truck figure - so the two-basis problem is visible or absent
from the artifact rather than from the source.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
KPI = ROOT / "02_dashboards/sales/ISZE_KPI_Dashboard.html"
WALLET = ROOT / "01_data/00_derived/wallet_waterfall.csv"
GPS = ROOT / "01_data/00_derived/gps_spu_by_distributor.csv"


def main() -> int:
    import pandas as pd

    t = KPI.read_text(encoding="utf-8")
    print("network ceiling in the HTML:", re.findall(r'"ceiling":([0-9.]+)', t)[:3])
    print("network ceilingCap in the HTML:", re.findall(r'"ceilingCap":([0-9.]+)', t)[:3])
    print("network ceilingBvp in the HTML:", re.findall(r'"ceilingBvp":([0-9.]+)', t)[:3])
    print("network cover text 56.6 :", "56.6" in t, "| 55.7 :", "55.7" in t)
    print("floored gap printed as 23,843,103:", "23843103" in t.replace(",", ""),
          "| 23,950,221:", "23950221" in t.replace(",", ""))

    w = pd.read_csv(WALLET)
    g = pd.read_csv(GPS)
    w25 = w[w.year == 2025].set_index("distributor_code")
    g25 = g[g.year == 2025].set_index("distributor_code")

    print("\nmarket   wallet_ceiling  gps_maxSpend   uio(wallet)  uio(gps)   "
          "spu from wallet   spu from gps")
    for code in sorted(w25.index):
        wc = float(w25.loc[code, "theoretical_wallet_eur"])
        wu = float(w25.loc[code, "uio_units"])
        gm = float(g25.loc[code, "max_spend_eur"]) if code in g25.index and pd.notna(
            g25.loc[code, "max_spend_eur"]) else float("nan")
        gu = float(g25.loc[code, "uio_units"]) if code in g25.index else float("nan")
        flag = ""
        if gm == gm and abs(gm - wc) > 0.005:
            flag = "  <-- the two files disagree"
        print(f"{code:9s} {wc:>14,.2f} {gm:>14,.2f} {wu:>12,.0f} {gu:>10,.0f} "
              f"{wc/wu:>15,.2f} {gm/gu:>15,.2f}{flag}")

    print("\nWhich of the two a rebuilt KPI row uses, per the builder:")
    print("  ceiling      <- wallet_waterfall.csv   (network hero)")
    print("  ceilingCap   <- wallet_waterfall.csv")
    print("  maxSpend     <- gps_spu_by_distributor.csv (per market, builder line ~392)")
    print("  uio/cvUio    <- wallet_waterfall.csv overlay (builder line ~438-450)")
    print("\nSo every market whose two files disagree still shows one basis in its")
    print("ceiling and another in its fleet. Nothing in this pass resolved that;")
    print("it needs a data-owner decision which basis is the KPI layer's.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
