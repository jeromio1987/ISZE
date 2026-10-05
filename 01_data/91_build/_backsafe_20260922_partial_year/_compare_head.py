"""Compare HEAD-committed vs current working files, read-only."""
from __future__ import annotations

import csv
import io
import subprocess
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")


def git_show(rel: str) -> str:
    return subprocess.run(
        ["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True, check=True
    ).stdout.decode("utf-8-sig")


def load_text(txt: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(txt)))


def load_file(p: Path) -> list[dict]:
    return list(csv.DictReader(p.open(encoding="utf-8-sig", newline="")))


for rel in (
    "01_data/00_derived/network_percentile.csv",
    "01_data/00_derived/aim_gps_matrix.csv",
    "01_data/00_derived/gps_spu_by_distributor.csv",
):
    head = load_text(git_show(rel))
    cur = load_file(ROOT / rel)
    print("=" * 90)
    print(rel)
    print(f"  committed rows={len(head)}  current rows={len(cur)}")
    hk = {(r["year"], r["distributor_code"]) for r in head}
    ck = {(r["year"], r["distributor_code"]) for r in cur}
    print(f"  only in committed: {sorted(hk - ck)}")
    print(f"  only in current:   {sorted(ck - hk)}")

    if "metric" in (head[0] if head else {}):
        for lbl, rows in (("committed", head), ("current", cur)):
            per: dict[tuple[str, str], int] = {}
            for r in rows:
                per[(r["metric"], r["year"])] = per.get((r["metric"], r["year"]), 0) + 1
            print(f"  {lbl}: {dict(sorted(per.items()))}")
        # UNMAPPED rows
        for lbl, rows in (("committed", head), ("current", cur)):
            un = [r for r in rows if r["distributor_code"] == "UNMAPPED"]
            print(f"  {lbl} UNMAPPED rows: {len(un)}")
            for r in un:
                print("     ", r)

# percentile before/after for the named markets
print("=" * 90)
print("gps_spu percentile by market/year, committed vs current")
head = load_text(git_show("01_data/00_derived/network_percentile.csv"))
cur = load_file(ROOT / "01_data/00_derived/network_percentile.csv")


def pct(rows, code, metric="gps_spu"):
    out = {}
    for r in rows:
        if r["distributor_code"] == code and r["metric"] == metric:
            out[r["year"]] = r["percentile_rank"]
    return out


for code in ("IUK", "HUNGARY", "GREECE", "ROMANIA", "UNMAPPED"):
    print(f"  {code:10} committed={pct(head, code)}")
    print(f"  {'':10} current  ={pct(cur, code)}")
