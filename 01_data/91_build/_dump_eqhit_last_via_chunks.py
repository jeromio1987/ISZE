"""Dump window.__eqDump / chunks written by browser into a JSON file, then append."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
AP = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_append_eqhit_playbook.py")


def append_scrape(path: Path, category: str) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("ap", AP)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    rows = m.rows_from_scrape(data, category)
    added, uniq = m.append_only(rows)
    print(f"pn={data.get('pn')} editions={data.get('editions')} added={added} unique_pns={uniq}")


if __name__ == "__main__":
    # argv: out_json category [chunk_file...]
    out = Path(sys.argv[1])
    cat = sys.argv[2]
    if len(sys.argv) > 3:
        parts = [Path(p).read_text(encoding="utf-8") for p in sys.argv[3:]]
        out.write_text("".join(parts), encoding="utf-8")
    append_scrape(out, cat)
