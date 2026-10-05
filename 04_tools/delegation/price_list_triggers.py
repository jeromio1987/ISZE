# -*- coding: utf-8 -*-
"""
Task cards 5.3 + 5.5 + 5.6 — automatic triggers from the price list.

Compares the current price list (01_data/00_derived/pricing_pr00_ie40.parquet) with the
last snapshot this script saw, and queues a price check for:
  new_part      part number not in the previous snapshot            -> any tier
  superseded    part whose newest number changed (old -> new pair)   -> any tier; observations carry over
  price_change  list price changed (a revision)                      -> tier A + B only (before/after pair)
Every trigger is appended to 04_tools/delegation/trigger_log.csv (5.6) and to the fetch queue
04_tools/delegation/state/trigger_queue.csv. No fetching happens here.

First run with no snapshot: pass --baseline <file> to diff against an older list, e.g.
  python 04_tools/delegation/price_list_triggers.py --baseline 01_data/00_derived/pricing_pr00_ie40_2025.parquet
Otherwise the first run only stores the snapshot.

5.4 ("don't lose the deal" intake) plugs into the same log once the intake form (3.1) exists:
use log_triggers([...], "dlod_case").
"""
import argparse
import csv
from datetime import datetime
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STATE = HERE / "state"
SNAP = STATE / "price_list_snapshot.parquet"
LOG = HERE / "trigger_log.csv"
QUEUE = STATE / "trigger_queue.csv"
CURRENT = ROOT / "01_data/00_derived/pricing_pr00_ie40.parquet"
MAX_NEW_PARTS = 2000
SERVE_WINDOW_DAYS = {"new_part": 14, "superseded": 14, "price_change": 30, "dlod_case": 2}


def load_list(path):
    d = pd.read_parquet(path)
    if "part_number" in d.columns:                       # current IE40 format
        d = d.assign(part_no=d["part_number"].astype(str).str.zfill(10),
                     newest=d["newest_pn"].astype(str).str.zfill(10),
                     price=d["sp_eur"])
    elif "Material" in d.columns:                        # yearly archive format
        d = d.assign(part_no=d["Material"].astype("Int64").astype(str).str.zfill(10),
                     newest=None, price=d["Price_EUR"])
    else:
        raise SystemExit(f"unknown price-list layout: {path}")
    return d[["part_no", "newest", "price"]].drop_duplicates("part_no", keep="last")


def tiers():
    f = STATE / "refresh_tiers.csv"
    return dict(pd.read_csv(f, dtype=str).values) if f.exists() else {}


def log_triggers(rows, now=None):
    now = now or datetime.now().isoformat(timespec="seconds")
    new = not LOG.exists()
    STATE.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", newline="", encoding="utf-8") as fh, open(QUEUE, "a", newline="", encoding="utf-8") as qh:
        w, q = csv.writer(fh), csv.writer(qh)
        if new:
            w.writerow(["time", "type", "part_no", "related_part_no", "tier", "detail", "serve_by_days", "served_at"])
        if QUEUE.stat().st_size == 0:
            q.writerow(["time", "type", "part_no", "tier"])
        for r in rows:
            w.writerow([now, r["type"], r["part_no"], r.get("related", ""), r.get("tier", ""), r.get("detail", ""),
                        SERVE_WINDOW_DAYS.get(r["type"], 14), ""])
            q.writerow([now, r["type"], r["part_no"], r.get("tier", "")])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", help="older price-list parquet to diff against (first run)")
    ap.add_argument("--dry-run", action="store_true", help="print counts, write nothing")
    ap.add_argument("--force-snapshot", action="store_true", help="store current list as baseline, no triggers")
    a = ap.parse_args()

    cur = load_list(CURRENT)
    if a.force_snapshot:
        STATE.mkdir(parents=True, exist_ok=True)
        cur.to_parquet(SNAP, index=False)
        print(f"re-baselined: {len(cur):,} rows stored, no triggers")
        return
    if a.baseline:
        old = load_list(ROOT / a.baseline)
    elif SNAP.exists():
        old = pd.read_parquet(SNAP)
    else:
        if not a.dry_run:
            STATE.mkdir(parents=True, exist_ok=True)
            cur.to_parquet(SNAP, index=False)
        print(f"no snapshot yet — stored {len(cur):,} rows as baseline, no triggers")
        return

    t = tiers()
    m = cur.merge(old, on="part_no", how="left", suffixes=("", "_old"), indicator=True)
    rows = []
    for _, r in m[m["_merge"] == "left_only"].iterrows():
        if r["price"] and r["price"] > 0:
            rows.append({"type": "new_part", "part_no": r["part_no"], "tier": t.get(r["part_no"], "")})
    both = m[m["_merge"] == "both"]
    sup = both[both["newest_old"].notna() & (both["newest"] != both["newest_old"])]
    for _, r in sup.iterrows():
        rows.append({"type": "superseded", "part_no": r["newest"], "related": r["part_no"],
                     "tier": t.get(r["part_no"], ""), "detail": f"{r['newest_old']} -> {r['newest']}"})
    chg = both[(both["price"] > 0) & (both["price_old"] > 0) & ((both["price"] - both["price_old"]).abs() > 0.005)]
    for _, r in chg.iterrows():
        tier = t.get(r["part_no"], "")
        if tier in ("A", "B"):
            rows.append({"type": "price_change", "part_no": r["part_no"], "tier": tier,
                         "detail": f"{r['price_old']:.2f} -> {r['price']:.2f}"})

    counts = pd.Series([r["type"] for r in rows]).value_counts().to_dict() if rows else {}
    print(f"current {len(cur):,} vs previous {len(old):,}: triggers {counts or 'none'} "
          f"(price changes outside tiers A/B not queued: {len(chg) - counts.get('price_change', 0):,})")
    if a.dry_run:
        return
    # Guard: a flood of "new" parts means the file layout/scope changed, not 20k new parts.
    if counts.get("new_part", 0) > MAX_NEW_PARTS:
        raise SystemExit(f"REFUSED — {counts['new_part']:,} new parts > {MAX_NEW_PARTS:,}: looks like a scope/layout "
                         "change, not real new numbers. Check the file, then rerun with --force-snapshot to re-baseline.")
    if rows:
        log_triggers(rows)
    cur.to_parquet(SNAP, index=False)


if __name__ == "__main__":
    main()
