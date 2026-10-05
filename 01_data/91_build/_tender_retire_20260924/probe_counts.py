"""Probe: what countable facts does each of the three tender readers produce?

Run with ``--phase before`` (the state as found) or ``--phase after`` (the
repointed state). Nothing is written; the readers are called, not duplicated.

Reader 1  scripts/export_tender_pipeline.py   -> its own _load()
Reader 2  scripts/sync_evidence_derived.py    -> the CSV it copies into evidence-app
Reader 3  evidence-app sources/prism/tender_pipeline.sql -> DuckDB reading that CSV
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
EVIDENCE_CSV = PRISM / "evidence-app" / "data" / "derived" / "tender_pipeline.csv"
EVIDENCE_FEED_CSV = PRISM / "evidence-app" / "data" / "derived" / "tender_feed.csv"
OLD_TABLE = ROOT / "01_data" / "00_derived" / "tender_pipeline.csv"
FEED = ROOT / "01_data" / "14_dashboards" / "tender_data.json"

sys.path.insert(0, str(PRISM))


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _counts(df) -> dict:
    act = df["actionable"]
    if act.dtype != bool:
        act = act.astype(str).str.lower().isin(["true", "1"])
    rm = df["rm_contract"]
    rm = rm if rm.dtype == bool else rm.astype(str).str.lower().isin(["true", "1"])
    return {"rows": int(len(df)), "actionable": int(act.sum()), "rm_contract": int(rm.sum())}


def reader1(phase: str) -> dict:
    """scripts/export_tender_pipeline.py, as its own module calls it.

    Before the repoint its ``_load()`` returned a frame read from the flattened
    CSV; after, it returns ``(frame, feed meta)`` from the live feed.
    """
    mod = _load_module("_probe_export", PRISM / "scripts" / "export_tender_pipeline.py")
    loaded = mod._load()
    df = loaded[0] if isinstance(loaded, tuple) else loaded
    return _counts(df)


def reader2(phase: str) -> dict:
    """scripts/sync_evidence_derived.py: the tender file it puts in evidence-app.

    Before: it copies tender_pipeline.csv. After: it writes tender_feed.csv.
    Either way we read the file it produced, which is the thing the reader owns.
    """
    target = EVIDENCE_FEED_CSV if phase == "after" else EVIDENCE_CSV
    if not target.is_file():
        return {"error": f"missing {target}"}
    import pandas as pd

    return _counts(pd.read_csv(target))


def reader3(phase: str) -> dict:
    """The evidence-app tender page: DuckDB over the source SQL file's path."""
    import duckdb
    import re

    sql = (PRISM / "evidence-app" / "sources" / "prism" / "tender_pipeline.sql").read_text(
        encoding="utf-8")
    m = re.search(r"read_csv_auto\('([^']+)'\)", sql)
    if not m:
        return {"error": "no read_csv_auto in tender_pipeline.sql"}
    rel = m.group(1)
    path = PRISM / "evidence-app" / rel
    if not path.is_file():
        return {"error": f"missing {path}"}
    con = duckdb.connect()
    con.execute(f"create view t as select * from read_csv_auto('{path.as_posix()}')")
    row = con.execute(
        "select count(*), sum(case when actionable then 1 else 0 end),"
        " sum(case when rm_contract then 1 else 0 end) from t"
    ).fetchone()
    return {"rows": int(row[0]), "actionable": int(row[1]), "rm_contract": int(row[2]),
            "sql_path": rel}


def feed_counts() -> dict:
    mod = _load_module("_probe_feed", PRISM / "modules" / "tender_feed.py")
    df, meta = mod.load_feed()
    out = _counts(df)
    out["generated_at"] = meta.get("generated_at")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=("before", "after"), required=True)
    args = ap.parse_args()

    print(f"PHASE: {args.phase}")
    print(f"  old table on disk : {OLD_TABLE.is_file()} "
          f"({OLD_TABLE.stat().st_size if OLD_TABLE.is_file() else '-'} bytes)")
    print(f"  live feed         : {FEED.is_file()}")
    print()
    for label, fn in (("reader1 export_tender_pipeline", reader1),
                      ("reader2 sync_evidence_derived ", reader2),
                      ("reader3 evidence-app DuckDB    ", reader3)):
        try:
            print(f"  {label}: {json.dumps(fn(args.phase))}")
        except Exception as exc:  # a broken reader must be visible, not swallowed
            print(f"  {label}: ERROR {type(exc).__name__}: {exc}")
    print()
    print(f"  live feed (truth) : {json.dumps(feed_counts())}")


if __name__ == "__main__":
    main()
