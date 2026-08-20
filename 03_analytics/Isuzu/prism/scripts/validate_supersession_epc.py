#!/usr/bin/env python3
"""
EPC validation harness for the supersession map (P1 task 1.2).

Validates `01_data/00_derived/pn_supersession_map.csv` (IE40 `newest_pn` mapping,
925 PN / EUR2.48M, currently `epc_validated: false`) against an EPC supersession
export once Jerome provides EPC access.

What it does, row by row:
  - load the current map (old_pn -> current_pn)
  - load an EPC export of old->new supersession pairs (CSV or XLSX)
  - for each mapped PN decide:
      MATCH      EPC confirms old_pn -> current_pn (possibly via a chain)
      MISMATCH   EPC maps old_pn to a DIFFERENT current PN
      NOT_FOUND  EPC has no supersession entry for old_pn (map may be over-resolved)
  - writes a per-row verdict CSV + a summary JSON, and prints the summary.

Usage (after EPC export lands in 90_INBOX or a named path):
    python scripts/validate_supersession_epc.py --epc "01_data/90_INBOX/epc_supersession_export.xlsx"

Column detection: auto-detects old/new PN columns by name; override with
--old-col / --new-col when the export uses different headers. Chain exports
("8974...>7552...>7552...") are parsed too.

This harness is READ-ONLY: it never rewrites pn_supersession_map.csv or its meta.
It writes only the validation report + summary.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DERIVED_DIR  # noqa: E402

MAP_CSV = DERIVED_DIR / "pn_supersession_map.csv"
OUT_CSV = DERIVED_DIR / "pn_supersession_epc_validation.csv"
OUT_META = DERIVED_DIR / "pn_supersession_epc_validation.meta.json"


def _norm_pn(v: object) -> str:
    """Normalise a part number to a comparable string (strip spaces, leading zeros kept)."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    s = str(v).strip()
    if s.lower() in ("nan", "none", ""):
        return ""
    # Excel often floats PNs; restore an integer form without losing significance
    try:
        if "." in s and s.replace(".", "", 1).isdigit():
            f = float(s)
            if f.is_integer():
                return str(int(f))
    except ValueError:
        pass
    return s


def _detect_pn_columns(df: pd.DataFrame, old_col: str | None, new_col: str | None) -> tuple[str, str]:
    if old_col and new_col:
        return old_col, new_col
    cols = [str(c) for c in df.columns]
    old_pat = re.compile(r"(old|from|supersed|former|legacy|part[ _-]?no|part[ _-]?number)", re.I)
    new_pat = re.compile(r"(new|to|replac|current|latest|superseded[ _-]?by)", re.I)
    if old_col is None:
        for c in cols:
            if old_pat.search(c):
                old_col = c
                break
    if new_col is None:
        for c in cols:
            if new_pat.search(c):
                new_col = c
                break
    if old_col is None or new_col is None:
        raise ValueError(
            f"Could not auto-detect PN columns in EPC export {list(cols)}. "
            "Pass --old-col and --new-col explicitly."
        )
    return old_col, new_col


def _follow_chain(epc_next: dict[str, str], start: str, max_hops: int = 12) -> str:
    """Resolve a supersession chain to its terminal PN, guarding against cycles."""
    cur = start
    seen: set[str] = set()
    for _ in range(max_hops):
        if cur in seen:
            break
        seen.add(cur)
        nxt = epc_next.get(cur)
        if not nxt or nxt == cur:
            break
        cur = nxt
    return cur


def _load_epc(path: Path, old_col: str | None, new_col: str | None) -> dict[str, str]:
    if path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path, dtype=str)
    else:
        df = pd.read_csv(path, dtype=str)
    old_c, new_c = _detect_pn_columns(df, old_col, new_col)
    epc_next: dict[str, str] = {}
    for _, row in df.iterrows():
        o = _norm_pn(row[old_c])
        n = _norm_pn(row[new_c])
        if not o:
            continue
        # A "chain" value like "7552A>7552B>7552C" — take the last hop.
        if ">" in n:
            parts = [p for p in re.split(r"[>\s/]+", n) if p]
            n = parts[-1] if parts else ""
        if n and n != o:
            epc_next[o] = n
    return epc_next


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--epc", required=True, help="Path to EPC supersession export (CSV/XLSX)")
    ap.add_argument("--map", default=str(MAP_CSV), help="Path to pn_supersession_map.csv")
    ap.add_argument("--old-col", default=None, help="EPC column for the old/superseded PN")
    ap.add_argument("--new-col", default=None, help="EPC column for the new/current PN")
    args = ap.parse_args()

    map_path = Path(args.map)
    epc_path = Path(args.epc)
    if not map_path.exists():
        print(f"Missing supersession map: {map_path}", file=sys.stderr)
        return 1
    if not epc_path.exists():
        print(f"Missing EPC export: {epc_path}", file=sys.stderr)
        return 1

    m = pd.read_csv(map_path, dtype=str)
    epc_next = _load_epc(epc_path, args.old_col, args.new_col)
    print(f"EPC export: {len(epc_next):,} old->new pairs from {epc_path.name}")

    rows: list[dict] = []
    n_match = n_mismatch = n_not_found = 0
    for _, r in m.iterrows():
        old = _norm_pn(r["old_pn"])
        current = _norm_pn(r["current_pn"])
        if old in epc_next:
            epc_terminal = _follow_chain(epc_next, old)
            if epc_terminal == current:
                verdict = "MATCH"
                n_match += 1
            else:
                verdict = "MISMATCH"
                n_mismatch += 1
        else:
            epc_terminal = ""
            verdict = "NOT_FOUND"
            n_not_found += 1
        rows.append(
            {
                "old_pn": old,
                "map_current_pn": current,
                "epc_terminal_pn": epc_terminal,
                "verdict": verdict,
                "billed_on_old_pn_eur": r.get("billed_on_old_pn_eur", ""),
                "old_description": r.get("old_description", ""),
            }
        )

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)

    summary = {
        "validated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "epc_source": str(epc_path),
        "map_pn_count": len(m),
        "match": n_match,
        "mismatch": n_mismatch,
        "not_found": n_not_found,
        "match_rate": round(n_match / len(m), 4) if len(m) else 0.0,
    }
    OUT_META.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\nValidation summary ({len(m):,} mapped PNs):")
    print(f"  MATCH      {n_match:,}")
    print(f"  MISMATCH   {n_mismatch:,}")
    print(f"  NOT_FOUND  {n_not_found:,}")
    print(f"  match rate {summary['match_rate']:.1%}")
    print(f"  report     {OUT_CSV}")
    print(f"  summary    {OUT_META}")
    if n_mismatch:
        print("\nTop mismatches (EPC says a different terminal PN):")
        mism = out[out["verdict"] == "MISMATCH"].head(10)
        for _, r in mism.iterrows():
            print(f"  {r['old_pn']}: map={r['map_current_pn']} epc={r['epc_terminal_pn']} ({r['old_description']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
