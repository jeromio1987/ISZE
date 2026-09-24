"""Tier analysis part 7 -- the honesty checks.

1. Do the two named trap rows land in Tier A under the 'description agrees with
   figure key' rule? If they do, the rule is not safe.
2. Hand-check 15 Tier A rows against the description text.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np, re

pd.set_option("display.width", 320); pd.set_option("display.max_columns", 80)
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"
qt = pd.read_csv(OUT / "queue_tiered.csv", dtype=str, encoding="utf-8-sig")
for c in ("pr00_eur", "list_eur"):
    qt[c] = pd.to_numeric(qt[c], errors="coerce")
qt["tierA"] = qt["tierA"] == "True"

log = []
def say(*a):
    line = " ".join(str(v) for v in a); print(line); log.append(line)

say("=" * 78)
say("1. THE TWO DOCUMENTED TRAP ROWS")
tr = qt[qt["desc_norm"].str.contains("TRANSMISSION ASM; MANUAL", na=False)]
say(f"  rows with that description: {len(tr)}")
for _, r in tr.iterrows():
    say(f"    {r['pn']} fk={r['fk']} d_l1={r['d_l1']} fk_l1={r['fk_l1']} "
        f"d_n={r['d_n']} tierA={r['tierA']} list={r['list_eur']:,.2f} pr00={r['pr00_eur']:,.2f}")
say("")
hd = qt[qt["desc_norm"].str.contains("HEAD ASM; CYL", na=False)]
say(f"  rows with HEAD ASM; CYL: {len(hd)}")
for _, r in hd.iterrows():
    say(f"    {r['pn']} fk={r['fk']} d_l1={r['d_l1']} fk_l1={r['fk_l1']} "
        f"d_n={r['d_n']} tierA={r['tierA']} list={r['list_eur']:,.2f} pr00={r['pr00_eur']:,.2f}")

say("")
say("=" * 78)
say("2. 'SUSPECT FAMILY' SCAN INSIDE TIER A")
say("   families that cannot plausibly carry a four-figure list price in a")
say("   parts price file; anything Tier A that lands here is a rule failure.")
suspect = {"Literature Marketing", "Logistics Packaging", "Tools Equipment"}
sq = qt[qt["tierA"] & qt["d_l1"].isin(suspect)]
say(f"  Tier A rows assigned to a suspect family: {len(sq)}, PR00 EUR {sq['pr00_eur'].sum():,.2f}")
for _, r in sq.sort_values("pr00_eur", ascending=False).iterrows():
    say(f"    {r['pn']}  {str(r['desc_norm'])[:40]:40s} -> {r['d_l1']}  "
        f"list={r['list_eur']:,.2f} pr00={r['pr00_eur']:,.2f} fk={r['fk']}")

say("")
say("   high-value Tier A rows on ANY family (top 30 by PR00 EUR): do they read right?")
ta = qt[qt["tierA"]].sort_values("pr00_eur", ascending=False)
for _, r in ta.head(30).iterrows():
    say(f"    {r['pn']}  {str(r['desc_norm'])[:38]:38s} -> {str(r['d_l1'])[:22]:22s} "
        f"fk={r['fk']:9s} d_n={r['d_n']:>4s} list={r['list_eur']:10,.2f} pr00={r['pr00_eur']:10,.2f}")

say("")
say("=" * 78)
say("3. HOW MUCH OF TIER A IS CARRIED BY A HANDFUL OF DESCRIPTIONS")
ds = ta.groupby("d_l1").agg(rows=("pn", "size"), eur=("pr00_eur", "sum")).sort_values("eur", ascending=False)
for k, r in ds.iterrows():
    say(f"    {k:26s} rows={int(r['rows']):4d} EUR={r['eur']:12,.2f}")

(OUT / "run_log7.txt").write_text("\n".join(log), encoding="utf-8")
print("\nDONE7")
