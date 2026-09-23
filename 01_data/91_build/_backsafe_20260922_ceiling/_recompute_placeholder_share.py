"""Recompute the flat-placeholder disclosure from the LIVE ceiling table.

The convention: some markets' target spend sits on one flat EUR 250-per-truck
placeholder (an LCV-basis assumption), and the share of the ceiling carried by
those markets is disclosed wherever the ceiling is quoted.

This script does NOT copy a percentage. It re-derives it, market by market, from
whatever wallet_waterfall.csv currently holds, and prints the headroom either
side of the tolerance so a market sitting near EUR 250 is visible rather than
silently in or out.

Usage:  python _recompute_placeholder_share.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
WALLET = ROOT / "01_data/00_derived/wallet_waterfall.csv"
HERE = Path(__file__).resolve().parent

PLACEHOLDER = 250.0
TOL = 0.01  # the builders use <= 0.01 on the per-truck rate


def block(year: int) -> dict:
    w = pd.read_csv(WALLET)
    s = w[w["year"] == year].copy()
    s["spu"] = s["theoretical_wallet_eur"] / s["uio_units"].replace(0, pd.NA)
    ceiling = float(s["theoretical_wallet_eur"].sum())
    flat = s[(s["spu"] - PLACEHOLDER).abs() <= TOL]
    flat_eur = float(flat["theoretical_wallet_eur"].sum())
    near = s[(s["spu"] - PLACEHOLDER).abs() <= 5.0]
    return {
        "year": year,
        "ceiling_eur": round(ceiling, 2),
        "flat_markets": sorted(flat["distributor_code"].tolist()),
        "flat_market_count": int(len(flat)),
        "flat_eur": round(flat_eur, 2),
        "flat_share_pct": round(flat_eur / ceiling * 100, 4) if ceiling else None,
        "flat_share_pct_1dp": round(flat_eur / ceiling * 100, 1) if ceiling else None,
        "near_250_within_5eur": {
            str(r["distributor_code"]): round(float(r["spu"]), 4)
            for _, r in near.sort_values("spu").iterrows()
        },
    }


def main() -> int:
    out = {}
    for y in (2023, 2024, 2025):
        b = block(y)
        out[str(y)] = b
        print(f"CY{y}: ceiling EUR {b['ceiling_eur']:,.2f}")
        print(f"  markets at exactly EUR {PLACEHOLDER:.0f}/truck: {b['flat_market_count']} "
              f"-> {', '.join(b['flat_markets'])}")
        print(f"  placeholder euro: EUR {b['flat_eur']:,.2f}   (unchanged by the ceiling move)")
        print(f"  share of ceiling: {b['flat_share_pct']:.4f}%  -> printed as {b['flat_share_pct_1dp']}%")
        print(f"  markets within EUR 5/truck of {PLACEHOLDER:.0f} (tolerance check):")
        for code, spu in b["near_250_within_5eur"].items():
            print(f"      {code:9s} {spu:>10,.4f}")
        print()

    tmp = HERE / "_placeholder_share.json.tmp"
    tmp.write_text(json.dumps(out, indent=1), encoding="utf-8")
    tmp.replace(HERE / "_placeholder_share.json")
    print(f"-> {HERE / '_placeholder_share.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
