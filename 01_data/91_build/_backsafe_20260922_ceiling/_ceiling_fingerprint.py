"""Read the ceiling table and print a per-market fingerprint.

  python _ceiling_fingerprint.py before | after

Writes .\_<label>.json with, per market: ceiling, captured, coverage,
uncaptured, over-target, uio_units, and a sha256 of the file.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
WALLET = ROOT / "01_data/00_derived/wallet_waterfall.csv"


def main() -> int:
    import pandas as pd

    label = sys.argv[1] if len(sys.argv) > 1 else "before"
    raw = WALLET.read_bytes()
    w = pd.read_csv(WALLET)

    markets = {}
    for year in sorted(w["year"].unique()):
        s = w[w["year"] == year]
        markets[str(year)] = {
            "ceiling_eur": round(float(s["theoretical_wallet_eur"].sum()), 2),
            "captured_eur": round(float(s["captured_total_eur"].sum()), 2),
            "coverage_pct": round(
                float(s["captured_total_eur"].sum()) / float(s["theoretical_wallet_eur"].sum()) * 100, 4
            ),
            "uncaptured_floored_eur": round(float(s["uncaptured_eur"].sum()), 2),
            "over_target_eur": round(float(s["over_target_eur"].sum()), 2),
            "rows": int(len(s)),
            "per_market": {
                str(r["distributor_code"]): {
                    "country": str(r["country"]),
                    "uio_units": int(r["uio_units"]),
                    "ceiling_eur": round(float(r["theoretical_wallet_eur"]), 2),
                    "captured_eur": round(float(r["captured_total_eur"]), 2),
                    "uncaptured_eur": round(float(r["uncaptured_eur"]), 2),
                    "over_target_eur": round(float(r["over_target_eur"]), 2),
                    "coverage_pct": round(float(r["gps_pct"]), 2),
                }
                for _, r in s.iterrows()
            },
        }

    net = markets["2025"]
    payload = {
        "label": label,
        "recorded_at": datetime.now().isoformat(timespec="seconds"),
        "file": str(WALLET),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "ceiling_2025_eur": net["ceiling_eur"],
        "coverage_2025_pct": net["coverage_pct"],
        "captured_2025_eur": net["captured_eur"],
        "years": markets,
    }
    # NOTE: deliberately NOT "_before.json" / "_after.json" - those names belong to the
    # backup manifest written by _take_backup.py.
    out = HERE / f"_ceiling_{label}.json"
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    tmp.replace(out)

    print(f"[{label}] sha256 {payload['sha256'][:16]}  ceiling CY2025 EUR {net['ceiling_eur']:,.2f}  "
          f"captured EUR {net['captured_eur']:,.2f}  coverage {net['coverage_pct']:.2f}%")
    for code, m in sorted(net["per_market"].items(), key=lambda kv: -kv[1]["ceiling_eur"]):
        print(f"    {code:9s} {m['uio_units']:>7,}  ceiling {m['ceiling_eur']:>14,.2f}  "
              f"billed {m['captured_eur']:>13,.2f}  cover {m['coverage_pct']:>6.1f}%")
    print(f"  -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
