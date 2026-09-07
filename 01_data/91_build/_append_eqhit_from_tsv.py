"""Append EQ-HIT fitment from id\\tfamily\\ttext TSV. APPEND-ONLY via playbook helper."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

AP = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_append_eqhit_playbook.py")


def scrape_from_tsv(pn: str, tsv_text: str, total: int | None = None) -> dict:
    by: dict[str, list] = {}
    for line in tsv_text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) == 2:
            cid, text = parts
            fam = "UNKNOWN"
        elif len(parts) >= 3:
            cid, fam, text = parts[0], parts[1], "\t".join(parts[2:])
        else:
            continue
        by.setdefault(fam, []).append({"id": cid, "text": text})
    n = sum(len(v) for v in by.values())
    return {
        "pn": pn,
        "total": total if total is not None else n,
        "found": n > 0,
        "editions": n,
        "families": list(by),
        "byFamily": by,
    }


def main() -> None:
    pn = sys.argv[1]
    cat = sys.argv[2]
    tsv_path = Path(sys.argv[3])
    total = int(sys.argv[4]) if len(sys.argv) > 4 else None
    scrape = scrape_from_tsv(pn, tsv_path.read_text(encoding="utf-8-sig"), total)
    out_json = tsv_path.with_suffix(".json")
    out_json.write_text(json.dumps(scrape, ensure_ascii=False), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("ap", AP)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    added, uniq = m.append_only(m.rows_from_scrape(scrape, cat))
    print(f"pn={pn} editions={scrape['editions']} total={scrape['total']} added={added} unique_pns={uniq}")


if __name__ == "__main__":
    main()
