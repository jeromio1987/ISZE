"""Shape probe (reviewer tool).

Prints only structural information (key names and types) about the frozen
case-data blob, never the commercial values themselves. Used to write the
acceptance fixtures without copying restricted figures into test files.
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FROZEN = ROOT / "reference" / "ISZE_AIM_Pricing_Decisions_v03_FROZEN.html"


def load_blob(path: Path) -> dict:
    html = io.open(path, encoding="utf-8", errors="ignore").read()
    m = re.search(r'<script id="case-data" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        raise SystemExit("no case-data block")
    return json.loads(m.group(1))


def t(v) -> str:
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, (int, float)):
        return "num"
    if v is None:
        return "null"
    if isinstance(v, str):
        return "str" if v.strip() else "str(blank)"
    if isinstance(v, list):
        return "list[%d]" % len(v)
    if isinstance(v, dict):
        return "obj{%s}" % ",".join(sorted(v.keys())[:12])
    return type(v).__name__


def main() -> int:
    d = load_blob(FROZEN)
    print("top:", sorted(d.keys()))
    print("cases:", [c.get("id") for c in d.get("cases", [])])
    print("meta keys:", sorted((d.get("meta") or {}).keys()))
    print("costBases:")
    for b in (d.get("meta") or {}).get("costBases", []):
        print("   ", {k: t(v) for k, v in b.items()})
    print("objectives:", json.dumps((d.get("meta") or {}).get("objectives"))[:400])
    print("defaultForwardBasis:", t((d.get("meta") or {}).get("defaultForwardBasis")))
    print("candidateScreen:", len(d.get("candidateScreen") or []))
    if d.get("candidateScreen"):
        print("candidate0 keys:", {k: t(v) for k, v in d["candidateScreen"][0].items()})
    c0 = d["cases"][0]
    print("case0 keys:", sorted(c0.keys()))
    print("case0 baselineDefined:", {k: t(v) for k, v in (c0.get("baselineDefined") or {}).items()})
    for c in d["cases"]:
        print("case", c["id"], "pn type", t(c.get("pn")), "alts:")
        for a in c.get("alternatives") or []:
            print("    ", a.get("alternative_id"), "kind=", a.get("kind"), "scope=", a.get("scope"),
                  "delta=", a.get("price_delta_pct"), "vol=", a.get("volume_assumption"),
                  "vol_label=", a.get("volume_label"), "support=", a.get("support_eur"),
                  "basis=", a.get("cost_basis_for_offer"), "pack=", a.get("pack_size_units"))
    print("verifiedCosts:", len(d.get("verifiedCosts") or []))
    for r in (d.get("verifiedCosts") or [])[:20]:
        print("    pn=", r.get("part_number"), "bases=", sorted((r.get("cost_bases") or {}).keys()),
              "restricted=", r.get("restricted"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
