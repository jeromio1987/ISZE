# -*- coding: utf-8 -*-
"""Agent C1 (U26) - add the Eucon-11 / 112-without-Eucon split to status.json.

The 123 numbers = 112 in NEEDS_CROSSREF_112_PNS_20261007.csv (no Eucon cross-reference)
+ 11 that already have one (they corroborate Spareto). Read from the MAIN clone.
Idempotent: safe to run after _c1_from_pass.py.
"""
import csv, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAIN = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
NEEDS = MAIN / "01_data" / "90_INBOX" / "NEEDS_CROSSREF_112_PNS_20261007.csv"

st = json.loads((HERE / "status.json").read_text(encoding="utf-8"))
per = {}
with (HERE / "spareto_crossref_per_part.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        per[r["part_no"].strip()] = r["page_result"].startswith("rows")

need = {r["isuzu_part_number"].strip() for r in csv.DictReader(NEEDS.open(encoding="utf-8", newline=""))}
need.discard("")
eucon11 = sorted(set(per) - need)

def split(pns):
    return {"queried": len(pns),
            "with_rows": sum(1 for p in pns if per.get(p)),
            "no_match": sum(1 for p in pns if p in per and not per[p])}

st["eucon_11"] = split(eucon11)
st["without_eucon_112"] = split(sorted(need))
st["eucon_11_pns"] = eucon11
(HERE / "status.json").write_text(json.dumps(st, indent=2), encoding="utf-8")
print(json.dumps({"eucon_11": st["eucon_11"], "without_eucon_112": st["without_eucon_112"]}, indent=2))