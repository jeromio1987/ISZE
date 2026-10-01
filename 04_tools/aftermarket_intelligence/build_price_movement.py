# -*- coding: utf-8 -*-
"""Price movement — what changed since we last looked.

WHY THIS IS THE POINT OF THE WHOLE PARTS PROGRAMME
--------------------------------------------------
A single price tells you very little. The same price a week later tells you whether you
are drifting out of the market. The parts side has now been read 1,093 times across 133
part numbers, and until this report nothing ever compared two readings: only 1 of 24 web
pages had been seen twice (measured 2026-09-25).

The first real movement was caught by accident — Amayama moved 8974995480 from 54.25 to
56.42 USD in six days, and only because an old test happened to assert the older figure.
This makes that automatic.

WHAT IT COMPARES
----------------
Every pair of observations for the SAME part number, SAME source, SAME price type,
on DIFFERENT dates. Part numbers and sources only: never across price types (a trade
price and a retail price are not the same thing), and never across currencies without
saying so.

Output:
  state/price_movement.csv      one row per (part, source, price_type) pair
  state/PRICE_MOVEMENT.md       the readable version

Run:  python 04_tools/aftermarket_intelligence/build_price_movement.py
      python 04_tools/aftermarket_intelligence/build_price_movement.py --min-pct 2
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "01_data" / "00_derived" / "price_observations.parquet"
OUT = ROOT / "04_tools" / "aftermarket_intelligence" / "state" / "price_movement.csv"
REPORT = ROOT / "04_tools" / "aftermarket_intelligence" / "state" / "PRICE_MOVEMENT.md"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-pct", type=float, default=0.0,
                    help="only report moves at least this large (percent change)")
    a = ap.parse_args()

    if not LEDGER.exists():
        print(f"REFUSED — no ledger at {LEDGER}")
        return 1

    d = pd.read_parquet(LEDGER)
    d = d[d["price"].notna()].copy()
    d["observed_at"] = d["observed_at"].astype(str)
    d["part_no"] = d["part_no"].astype(str)

    print(f"priced observations : {len(d):,}")
    print(f"part numbers        : {d['part_no'].nunique():,}")
    print(f"dates present       : {sorted(d['observed_at'].unique())}")

    # only a real series: same part, same source, same price type, different dates
    key = ["part_no", "source", "price_type", "currency"]
    g = d.groupby(key)
    sizes = g.size()
    multi = sizes[sizes > 1]
    print(f"\nkeys with more than one observation: {len(multi):,}")

    if multi.empty:
        print("\nNo part has been observed twice at the same source and price type yet.")
        print("The report will populate as soon as the runner visits the same part again.")
        REPORT.write_text(
            "# Price movement\n\n"
            f"Built {datetime.now(timezone.utc).isoformat(timespec='seconds')}.\n\n"
            "**No movement can be reported yet.** Every part number has been observed "
            "once per source. A movement needs the same part at the same source on two "
            "different dates, and the parts runner has only had one pass.\n\n"
            "The first real movement in this programme was found by accident — Amayama "
            "moved 8974995480 from 54.25 to 56.42 USD between 18 and 24 September 2026, "
            "caught only because an old test asserted the earlier figure. Run the parts "
            "runner again and this report will show it automatically.\n",
            encoding="utf-8")
        print(f"wrote {REPORT.name}")
        return 0

    rows = []
    for k, grp in g:
        if len(grp) < 2:
            continue
        grp = grp.sort_values("observed_at")
        first, last = grp.iloc[0], grp.iloc[-1]
        if first["observed_at"] == last["observed_at"]:
            continue
        if not first["price"] or first["price"] <= 0:
            continue
        pct = 100 * (last["price"] / first["price"] - 1)
        rows.append({
            "part_no": k[0],
            "source": k[1],
            "price_type": k[2],
            "currency": k[3],
            "first_date": first["observed_at"],
            "first_price": float(first["price"]),
            "last_date": last["observed_at"],
            "last_price": float(last["price"]),
            "change_abs": round(float(last["price"]) - float(first["price"]), 4),
            "change_pct": round(float(pct), 2),
            "n_observations": int(len(grp)),
            "description": (first.get("description") or "")[:90],
            "source_url": first.get("source_url"),
        })

    if a.min_pct:
        rows = [r for r in rows if abs(r["change_pct"]) >= a.min_pct]

    out = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*74}")
    if out.empty:
        print("no pair of observations with a different date and price")
        return 0

    out = out.reindex(out["change_pct"].abs().sort_values(ascending=False).index)
    out.to_csv(OUT, index=False)

    print(f"movements found : {len(out)}")
    print(f"{'part_no':<12} {'source':<20} {'type':<18} {'from':>9} {'to':>9} {'chg':>8}")
    print("-" * 82)
    for _, r in out.head(25).iterrows():
        print(f"{r['part_no']:<12} {str(r['source'])[:19]:<20} {str(r['price_type'])[:17]:<18} "
              f"{r['first_price']:>9.2f} {r['last_price']:>9.2f} {r['change_pct']:>+7.1f}%")

    up = out[out["change_pct"] > 0]
    down = out[out["change_pct"] < 0]
    lines = [
        "# Price movement\n",
        f"Built {datetime.now(timezone.utc).isoformat(timespec='seconds')} by "
        "`build_price_movement.py`.\n",
        f"- pairs compared: **{len(out)}**",
        f"- moved up: **{len(up)}**  ·  down: **{len(down)}**\n",
        "Only the same part number, source, price type and currency are compared. A trade "
        "price and a retail price are never put in the same series, and no currency is "
        "converted to make a pair.\n",
        "| part | source | type | from | to | change |",
        "|---|---|---|---:|---:|---:|",
    ]
    for _, r in out.head(40).iterrows():
        lines.append(
            f"| `{r['part_no']}` | {r['source']} | {r['price_type']} | "
            f"{r['first_price']:.2f} {r['currency']} ({r['first_date']}) | "
            f"{r['last_price']:.2f} {r['currency']} ({r['last_date']}) | "
            f"**{r['change_pct']:+.1f}%** |")
    lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"\nwrote {OUT.name} and {REPORT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
