"""Append one EQ-HIT scrape from id/family/text triples JSON via playbook helper."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

AP = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_append_eqhit_playbook.py")


def main() -> None:
    pn = sys.argv[1]
    cat = sys.argv[2]
    triples_path = Path(sys.argv[3])
    total = int(sys.argv[4]) if len(sys.argv) > 4 else None
    raw = json.loads(triples_path.read_text(encoding="utf-8"))
    by: dict[str, list] = {}
    if isinstance(raw, dict) and "byFamily" in raw:
        scrape = raw
        scrape["pn"] = pn
        if total is not None:
            scrape["total"] = total
    else:
        for row in raw:
            if len(row) == 2:
                cid, text = row
                fam = "UNKNOWN"
            else:
                cid, fam, text = row[0], row[1], row[2]
            by.setdefault(fam, []).append({"id": cid, "text": text})
        n = sum(len(v) for v in by.values())
        scrape = {
            "pn": pn,
            "total": total if total is not None else n,
            "found": n > 0,
            "editions": n,
            "families": list(by),
            "byFamily": by,
        }
    if scrape.get("total") == 0 or scrape.get("found") is False:
        scrape = {"pn": pn, "total": 0, "found": False}
    outj = triples_path.with_suffix(".scrape.json")
    outj.write_text(json.dumps(scrape, ensure_ascii=False), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("ap", AP)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    added, uniq = m.append_only(m.rows_from_scrape(scrape, cat))
    print(f"pn={pn} cat={cat} editions={scrape.get('editions', 0)} total={scrape.get('total')} added={added} unique_pns={uniq}")


if __name__ == "__main__":
    main()
