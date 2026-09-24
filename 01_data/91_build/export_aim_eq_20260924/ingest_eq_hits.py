"""Ingest the EQ-Hit lookup results for the IE40 price extract into the AIM master.

Input  : the JSON the paste script downloads (eq_hits_export_20260924.json)
Output : aim_master_v2.csv filled for the parts the EPC settles, plus a review list
         for the parts it does not.

How a family is decided
  1. The EPC lookup returns a figure key for the part (its home page in the catalogue).
  2. The master already holds a full AIM path for many figure keys. Build a map
     figure key -> full AIM path, using ONLY rows whose family is known, and only
     where those rows agree on exactly one path and there are at least 3 of them.
     A figure key that disagrees with itself is dropped rather than guessed at.
  3. A part is classified only if its EPC figure key is in that map.
  4. Anything else goes to the review list, named with its reason.

Safety
  - Backup of the master before any write.
  - Only fills rows whose current aim_l1 is empty, 'Unknown' or 'Unknown Review'.
  - Stamps every row it touches with aim_source = 'eq_hit_20260924'.
  - Verifies after writing: row count unchanged, no other row's aim columns moved.

Usage
  python ingest_eq_hits.py --hits <path to eq_hits_export_20260924.json>
  python ingest_eq_hits.py --hits <path> --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
MASTER = DER / "aim_master_v2.csv"
STAMP = "eq_hit_20260924"
UNKNOWN = {"", "unknown", "unknown review"}
OUT_DIR = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"


def nkey(v) -> str:
    return str(v).strip().upper().lstrip("0")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_figkey_map(master: pd.DataFrame) -> dict[str, str]:
    """figure key -> one full AIM path, only where the master agrees with itself."""
    ok = master["aim_l1"].fillna("").str.strip()
    fk = master["fig_key"].fillna("").astype(str).str.strip()
    known = master[(fk != "") & ok.ne("") & ~ok.str.lower().isin(UNKNOWN)].copy()
    known["path"] = (
        known["aim_l1"].fillna("") + ">" + known["aim_l2"].fillna("") + ">" + known["aim_l3"].fillna("")
    )
    g = known.groupby(fk)["path"].agg(n="nunique", sz="size")
    good = g[(g["n"] == 1) & (g["sz"] >= 3)]
    first = known[known["fig_key"].fillna("").astype(str).str.strip().isin(good.index)]
    first = first.drop_duplicates("fig_key").set_index("fig_key")["path"]
    return {k: v for k, v in first.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hits", required=True, help="path to the eq_hits JSON the browser downloaded")
    ap.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    args = ap.parse_args()

    hits_path = Path(args.hits)
    hits = json.loads(hits_path.read_text(encoding="utf-8"))
    print(f"hits read: {len(hits)} from {hits_path}")

    h = pd.DataFrame(hits)
    if h.empty or "pn" not in h.columns:
        raise SystemExit("the hits file carries no 'pn' column — nothing to do")
    h["k"] = h["pn"].map(nkey)
    h = h.drop_duplicates("k", keep="first")
    print("status mix:", h.get("eq_status", pd.Series(dtype=str)).value_counts().to_dict())

    master = pd.read_csv(MASTER, dtype=str, low_memory=False)
    before_rows = len(master)
    fk_map = build_figkey_map(master)
    print(f"figure keys with one agreed AIM path on the master: {len(fk_map):,}")

    master["k"] = master["part_number"].map(nkey)
    idx = master.drop_duplicates("k").set_index("k")

    decided, review = [], []
    for r in h.itertuples(index=False):
        k = getattr(r, "k")
        status = str(getattr(r, "eq_status", "") or "")
        fk = str(getattr(r, "eq_fig_key", "") or "").strip()
        row = idx.loc[k] if k in idx.index else None
        current = str(row["aim_l1"]).strip() if row is not None else None

        if row is not None and current is not None and current.lower() not in UNKNOWN:
            review.append((k, "already has a family on the master", status, fk))
            continue
        if status != "FOUND":
            review.append((k, f"EPC did not return the part ({status or 'no status'})", status, fk))
            continue
        if not fk:
            review.append((k, "EPC returned the part but no figure key", status, fk))
            continue
        path = fk_map.get(fk)
        if not path:
            review.append((k, f"figure key {fk} has no single agreed AIM path on the master", status, fk))
            continue
        decided.append((k, fk, *path.split(">")))

    print(f"can be classified from the EPC figure key : {len(decided)}")
    print(f"go to review                              : {len(review)}")

    review_df = pd.DataFrame(review, columns=["pn", "reason", "eq_status", "eq_fig_key"])
    review_df.to_csv(OUT_DIR / "eq_hits_review_20260924.csv", index=False, encoding="utf-8-sig")
    if not review:
        print("no review rows")
    else:
        print("top review reasons:")
        print(review_df["reason"].value_counts().head(10).to_string())

    if args.dry_run:
        print("\nDRY RUN — master not written, pair not rebuilt.")
        return

    if not decided:
        print("\nnothing decidable — master not written.")
        return

    stamp = datetime.now().strftime("%H%M%S")
    backup = MASTER.with_name(f"aim_master_v2.csv.bak_pre_eq_hits_{STAMP}_{stamp}")
    shutil.copy2(MASTER, backup)
    print(f"\nbackup: {backup}")

    by_k = {d[0]: d for d in decided}

    touched = 0
    for i, r in master.iterrows():
        k = r["k"]
        if k not in by_k:
            continue
        cur = str(r["aim_l1"]).strip() if pd.notna(r["aim_l1"]) else ""
        if cur != "" and cur.lower() not in UNKNOWN:
            continue
        _, fk, l1, l2, l3 = by_k[k]
        master.at[i, "aim_l1"] = l1
        master.at[i, "aim_l2"] = l2
        master.at[i, "aim_l3"] = l3
        master.at[i, "aim_source"] = STAMP
        touched += 1

    master.drop(columns=["k"]).to_csv(MASTER, index=False, encoding="utf-8")
    print(f"rows filled: {touched}")

    after = pd.read_csv(MASTER, dtype=str, low_memory=False)
    assert len(after) == before_rows, f"row count moved {before_rows} -> {len(after)}"
    b = pd.read_csv(backup, dtype=str, low_memory=False)
    b["k"] = b["part_number"].map(nkey)
    a = after.copy()
    a["k"] = a["part_number"].map(nkey)
    bs = b.set_index("k")[["aim_l1", "aim_l2", "aim_l3"]]
    asx = a.set_index("k")[["aim_l1", "aim_l2", "aim_l3"]]
    common = bs.index.intersection(asx.index)
    moved = (bs.loc[common].fillna("") != asx.loc[common].fillna("")).any(axis=1).sum()
    stamped = (a["aim_source"].fillna("") == STAMP).sum()
    print(f"verification: row count {len(after)} (unchanged), pre-existing rows whose aim moved: {moved}, rows carrying stamp: {stamped}")
    print(f"before sha256 {sha(backup)}")
    print(f"after  sha256 {sha(MASTER)}")
    print("\nnow rebuild the dated pair:  python 01_data/91_build/export_aim_pn_categories_figkey_xlsx.py")


if __name__ == "__main__":
    main()
