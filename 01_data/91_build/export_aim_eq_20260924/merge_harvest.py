"""Merge the harvested EQ lookup batches into one results file.

Reads every harvest_*.tsv (part number, status, figure name) plus the queue,
and writes eq_results.jsonl — the file classify.py reads.

Run:  python 01_data/91_build/export_aim_eq_20260924/merge_harvest.py
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\export_aim_eq_20260924")


def main() -> None:
    seen: dict[str, dict] = {}
    files = sorted(OUT.glob("harvest_*.tsv"))
    for f in files:
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.rstrip("\n")
            if not line.strip():
                continue
            bits = line.split("\t")
            pn = bits[0].strip().upper()
            if not pn:
                continue
            status = bits[1].strip() if len(bits) > 1 else ""
            fig = bits[2].strip() if len(bits) > 2 else ""
            # BLANK marks a part the EPC finds but does not name; keep the status
            # so it still gets a figure-key path if one exists.
            if status == "BLANK":
                status = "FOUND"
            # A later FOUND beats an earlier ERROR for the same part.
            prev = seen.get(pn)
            if prev and prev.get("eq_status") == "FOUND" and status != "FOUND":
                continue
            seen[pn] = {"pn": pn, "eq_status": status, "eq_fig_name": fig}

    order: list[str] = []
    q = OUT / "queue.json"
    if q.exists():
        order = [str(x).strip().upper() for x in json.loads(q.read_text(encoding="utf-8"))]

    rows = [seen[p] for p in order if p in seen]
    rows += [v for k, v in seen.items() if k not in set(order)]

    with (OUT / "eq_results.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    found = sum(1 for r in rows if r["eq_status"] == "FOUND")
    nf = sum(1 for r in rows if r["eq_status"] == "NOT_FOUND")
    err = sum(1 for r in rows if r["eq_status"] == "ERROR")
    print(f"files={len(files)} rows={len(rows)} found={found} not_found={nf} error={err}")


if __name__ == "__main__":
    main()
