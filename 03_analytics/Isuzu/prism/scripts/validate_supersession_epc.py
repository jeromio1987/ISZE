#!/usr/bin/env python3
"""
EPC validation harness for the supersession map (P1 task 1.2).

Validates `01_data/00_derived/pn_supersession_map.csv` (IE40 `newest_pn` mapping,
925 PN / EUR2.48M, currently `epc_validated: false`) against an EPC supersession
export once one lands in 90_INBOX.

What it does, row by row, **only when an EPC export is present**:
  - load the current map (old_pn -> current_pn)
  - load an EPC export of old->new supersession pairs (CSV or XLSX)
  - for each mapped PN decide:
      MATCH      EPC confirms old_pn -> current_pn (possibly via a chain)
      MISMATCH   EPC maps old_pn to a DIFFERENT current PN
      NOT_FOUND  EPC has no supersession entry for old_pn (map may be over-resolved)
  - writes a per-row verdict CSV + a summary JSON, and prints the summary.

`--epc` is optional. If omitted, this script searches 90_INBOX and common names.
If nothing is found it writes `pn_supersession_epc_validation.meta.json` with
`status: BLOCKED_NO_EPC_EXPORT` and **never** emits MATCH.

Optional IE40 `newest_pn` integrity is labelled `INTERNAL_IE40_CHECK` — that is
**not** EPC-validated.

This harness is READ-ONLY: it never rewrites pn_supersession_map.csv or its meta.
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

from config import DERIVED_DIR, INBOX_DIR, ISZE_ROOT  # noqa: E402

MAP_CSV = DERIVED_DIR / "pn_supersession_map.csv"
OUT_CSV = DERIVED_DIR / "pn_supersession_epc_validation.csv"
OUT_META = DERIVED_DIR / "pn_supersession_epc_validation.meta.json"
IE40_PARQUET = DERIVED_DIR / "pricing_pr00_ie40.parquet"

COMMON_EPC_NAMES = (
    "epc_supersession_export.xlsx",
    "epc_supersession_export.csv",
    "epc_supersession.xlsx",
    "epc_supersession.csv",
    "EPC_supersession_export.xlsx",
    "Isuzu_EPC_supersession.xlsx",
)

COMMON_EPC_GLOBS = (
    "*epc*supersession*.xlsx",
    "*epc*supersession*.csv",
    "*supersession*epc*.xlsx",
    "*supersession*epc*.csv",
    "*EPC*supersession*.xlsx",
    "*EPC*supersession*.csv",
)


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


def _pn_keys(v: object) -> list[str]:
    n = _norm_pn(v)
    if not n:
        return []
    stripped = n.lstrip("0") or "0"
    keys = [n, stripped]
    if stripped.isdigit() and len(stripped) <= 10:
        keys.append(stripped.zfill(10))
    return list(dict.fromkeys(keys))


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


def search_dirs() -> list[Path]:
    dirs = [
        Path(INBOX_DIR),
        ISZE_ROOT / "01_data" / "90_INBOX",
        ISZE_ROOT / "01_data" / "_INBOX",
        DERIVED_DIR,
        PRISM_ROOT / "data",
        Path.cwd(),
    ]
    out: list[Path] = []
    seen: set[Path] = set()
    for d in dirs:
        try:
            resolved = d.resolve()
        except OSError:
            continue
        if resolved in seen or not d.is_dir():
            continue
        seen.add(resolved)
        out.append(d)
    return out


def discover_epc_export(explicit: Path | None = None) -> tuple[Path | None, list[str]]:
    """Return (path or None, search log). Never invents a MATCH source."""
    searched: list[str] = []
    inbox = ISZE_ROOT / "01_data" / "90_INBOX"
    if explicit is not None:
        searched.append(str(explicit))
        if explicit.is_file():
            return explicit, searched
        return None, searched

    if not inbox.is_dir():
        searched.append(f"{inbox} (directory missing)")

    for d in search_dirs():
        for name in COMMON_EPC_NAMES:
            p = d / name
            searched.append(str(p))
            if p.is_file():
                return p, searched
        for pat in COMMON_EPC_GLOBS:
            hits = sorted(d.glob(pat))
            searched.append(f"{d}/{pat}")
            files = [h for h in hits if h.is_file()]
            if files:
                return files[-1], searched
    return None, searched


def ie40_integrity_check(map_df: pd.DataFrame, parquet_path: Path | None = None) -> dict:
    """Compare map current_pn to IE40 newest_pn. NOT an EPC validation."""
    path = parquet_path or IE40_PARQUET
    result: dict = {
        "status": "INTERNAL_IE40_CHECK",
        "epc_validated": False,
        "note": "IE40 newest_pn integrity only — not EPC-validated. Never treat as MATCH.",
        "ie40_source": str(path) if path else None,
        "rows_compared": 0,
        "newest_pn_agrees": 0,
        "newest_pn_differs": 0,
        "not_in_ie40": 0,
    }
    if path is None or not Path(path).is_file():
        result["note"] = "IE40 parquet missing — INTERNAL_IE40_CHECK skipped."
        return result

    pr = pd.read_parquet(path, columns=["part_number", "newest_pn"])
    newest: dict[str, str] = {}
    for _, r in pr.iterrows():
        new = _norm_pn(r.get("newest_pn"))
        if not new:
            continue
        for key in _pn_keys(r.get("part_number")):
            newest.setdefault(key, new)

    agrees = differs = missing = 0
    for _, r in map_df.iterrows():
        old = _norm_pn(r.get("old_pn"))
        current = _norm_pn(r.get("current_pn"))
        ie40 = None
        for key in _pn_keys(old):
            if key in newest:
                ie40 = newest[key]
                break
        if ie40 is None:
            missing += 1
            continue
        ie40_keys = set(_pn_keys(ie40))
        cur_keys = set(_pn_keys(current))
        if ie40_keys & cur_keys:
            agrees += 1
        else:
            differs += 1

    result["rows_compared"] = agrees + differs + missing
    result["newest_pn_agrees"] = agrees
    result["newest_pn_differs"] = differs
    result["not_in_ie40"] = missing
    return result


def _write_meta(payload: dict) -> None:
    OUT_META.parent.mkdir(parents=True, exist_ok=True)
    OUT_META.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_blocked_meta(
    *,
    map_pn_count: int,
    searched: list[str],
    ie40_check: dict | None,
) -> dict:
    summary = {
        "validated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "BLOCKED_NO_EPC_EXPORT",
        "epc_validated": False,
        "epc_source": None,
        "map_pn_count": map_pn_count,
        "match": 0,
        "mismatch": 0,
        "not_found": 0,
        "match_rate": 0.0,
        "note": (
            "No EPC supersession export in --epc or 90_INBOX. "
            "MATCH is never inferred from IE40 newest_pn. "
            "Snap-on EPC basket JSON has edition/family, not fig-key pairs."
        ),
        "searched": searched[:80],
    }
    if ie40_check is not None:
        summary["internal_ie40_check"] = ie40_check
    _write_meta(summary)
    return summary


def validate_against_epc(
    map_df: pd.DataFrame,
    epc_next: dict[str, str],
    epc_path: Path,
    *,
    ie40_check: dict | None = None,
) -> dict:
    rows: list[dict] = []
    n_match = n_mismatch = n_not_found = 0
    for _, r in map_df.iterrows():
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
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    summary = {
        "validated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "EPC_VALIDATED",
        "epc_validated": True,
        "epc_source": str(epc_path),
        "map_pn_count": len(map_df),
        "match": n_match,
        "mismatch": n_mismatch,
        "not_found": n_not_found,
        "match_rate": round(n_match / len(map_df), 4) if len(map_df) else 0.0,
    }
    if ie40_check is not None:
        summary["internal_ie40_check"] = ie40_check
    _write_meta(summary)
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--epc",
        default=None,
        help="Path to EPC supersession export (CSV/XLSX). Optional — searches 90_INBOX if omitted.",
    )
    ap.add_argument("--map", default=str(MAP_CSV), help="Path to pn_supersession_map.csv")
    ap.add_argument("--old-col", default=None, help="EPC column for the old/superseded PN")
    ap.add_argument("--new-col", default=None, help="EPC column for the new/current PN")
    ap.add_argument(
        "--skip-ie40-check",
        action="store_true",
        help="Skip the INTERNAL_IE40_CHECK newest_pn integrity pass",
    )
    args = ap.parse_args()

    map_path = Path(args.map)
    if not map_path.exists():
        print(f"Missing supersession map: {map_path}", file=sys.stderr)
        return 1

    m = pd.read_csv(map_path, dtype=str)
    ie40_check = None if args.skip_ie40_check else ie40_integrity_check(m)

    explicit = Path(args.epc) if args.epc else None
    epc_path, searched = discover_epc_export(explicit)
    if epc_path is None:
        summary = write_blocked_meta(
            map_pn_count=len(m),
            searched=searched,
            ie40_check=ie40_check,
        )
        print("EPC validation BLOCKED_NO_EPC_EXPORT — no export in --epc or 90_INBOX.")
        print("  MATCH is not inferred. IE40 newest_pn check is INTERNAL_IE40_CHECK only.")
        print(f"  summary    {OUT_META}")
        if ie40_check:
            print(
                f"  INTERNAL_IE40_CHECK agrees={ie40_check.get('newest_pn_agrees')} "
                f"differs={ie40_check.get('newest_pn_differs')} "
                f"missing={ie40_check.get('not_in_ie40')}"
            )
        print(f"  searched   {len(searched)} paths")
        return 0

    epc_next = _load_epc(epc_path, args.old_col, args.new_col)
    print(f"EPC export: {len(epc_next):,} old->new pairs from {epc_path.name}")
    summary = validate_against_epc(m, epc_next, epc_path, ie40_check=ie40_check)

    print(f"\nValidation summary ({len(m):,} mapped PNs):")
    print(f"  MATCH      {summary['match']:,}")
    print(f"  MISMATCH   {summary['mismatch']:,}")
    print(f"  NOT_FOUND  {summary['not_found']:,}")
    print(f"  match rate {summary['match_rate']:.1%}")
    print(f"  report     {OUT_CSV}")
    print(f"  summary    {OUT_META}")
    if summary["mismatch"]:
        print("\nTop mismatches (EPC says a different terminal PN):")
        out = pd.read_csv(OUT_CSV, dtype=str)
        mism = out[out["verdict"] == "MISMATCH"].head(10)
        for _, r in mism.iterrows():
            print(f"  {r['old_pn']}: map={r['map_current_pn']} epc={r['epc_terminal_pn']} ({r['old_description']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
