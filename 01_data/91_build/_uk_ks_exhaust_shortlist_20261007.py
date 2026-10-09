# -*- coding: utf-8 -*-
"""Build ~15 Isuzu exhaust-class PN shortlist for KS exact_oem harvest."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "01_data" / "90_INBOX" / "_uk_ks_exhaust_harvest_20261007"
OUT.mkdir(parents=True, exist_ok=True)

KEEP = re.compile(
    r"MUFFLER|SILENCER\s*ASM|SILENCER\s*;\s*EXH|TAIL\s*PIPE|TAILPIPE|"
    r"EXHAUST\s*PIPE|PIPE\s*;\s*EXH|EXH\s*;\s*PIPE|EXHAUST\s*MUFFLER|"
    r"EXHAUST\s*SILENCER",
    re.I,
)
REJECT = re.compile(
    r"BRACKET|BRKT|NUT|BOLT|WASHER|STUD|GASKET|PROTECTOR|HEAT|"
    r"MAT\s*;?\s*SILENCER|MAT\s*ASM|CAB\s*(FLOOR|BACK)|DPD|SENSOR|CLAMP|"
    r"RING;\s*SEAL|COLLAR|MANIFOLD|MANIF\b|BRAKE\s*UNIT|EXHAUST\s*BRAKE|"
    r"CAMSHAFT|VALVE|TEMPERATURE|HANGER|RUBBER|MOUNT|INSULATOR|COVER|FLEX",
    re.I,
)
ELIGIBLE = {
    "8983682091",
    "8970622940",
    "8974995480",
    "8975546610",
    "8976739570",
    "8981394280",
    "8981402650",
    "8981596930",
    "8981941190",
    "8982399830",
    "8982705240",
    "8982831940",
    "8983214130",
}

hits: dict[str, dict] = {}


def add(pn, desc, eur, src: str) -> None:
    pn = str(pn or "").strip()
    if not pn or pn in ELIGIBLE:
        return
    d = str(desc or "").strip()
    if not KEEP.search(d) or REJECT.search(d):
        return
    try:
        eur_f = float(eur) if eur not in (None, "", "nan", "None") else 0.0
        if eur_f != eur_f:  # NaN
            eur_f = 0.0
    except (TypeError, ValueError):
        eur_f = 0.0
    prev = hits.get(pn)
    if prev is None:
        hits[pn] = {"desc": d[:120], "eur": eur_f, "sources": {src}}
        return
    prev["eur"] = max(prev["eur"], eur_f)
    prev["sources"].add(src)
    if len(d) > len(prev["desc"]):
        prev["desc"] = d[:120]


def _priority(desc: str) -> int:
    """Prefer muffler/silencer/tail pipe wording over generic PIPE; EXH."""
    d = desc.upper()
    if "MUFFLER" in d or "SILENCER" in d:
        return 0
    if "TAIL" in d:
        return 1
    return 2


def main() -> None:
    bb = pd.read_csv(
        ROOT / "01_data/00_derived/revision_book_b_review_pack_2026-09-22.csv",
        dtype=str,
        low_memory=False,
    )
    for _, r in bb.iterrows():
        eur = r.get("l12m_eur") or r.get("bill_eur") or r.get("forecast_weight_eur") or 0
        add(r["pn"], r["description"], eur, "book_b")

    up = pd.read_csv(
        ROOT / "01_data/00_derived/unpriced_no_price_one_side_list.csv",
        dtype=str,
        low_memory=False,
    )
    pn_c, desc_c = up.columns[0], up.columns[1]
    for _, r in up.iterrows():
        eur = 0.0
        for c in up.columns:
            if "eur" in c.lower():
                try:
                    eur = max(eur, float(r[c] or 0))
                except (TypeError, ValueError):
                    pass
        add(r[pn_c], r[desc_c], eur, "unpriced")

    lo = pd.read_csv(
        ROOT
        / "01_data/00_derived/_releases/next_release_proposal_live_order_unclassified_2026-10-07.csv",
        dtype=str,
        low_memory=False,
    )
    for _, r in lo.iterrows():
        desc = r.get("description_if_any") or r.get("description") or ""
        eur = r.get("eur_all") or r.get("open_eur") or 0
        add(r["pn"], desc, eur, "live_order")

    eq = pd.read_csv(
        ROOT / "01_data/00_derived/_eq_hit_results_20261007.csv",
        dtype=str,
        low_memory=False,
    )
    for _, r in eq.iterrows():
        desc = r.get("eq_part_name") or r.get("description_if_any") or ""
        add(r["pn"], desc, 0, "eq_hit")

    epc = pd.read_csv(
        ROOT / "01_data/00_derived/epc_catalogue_heavy_20260919.csv",
        dtype=str,
        low_memory=False,
    )
    for _, r in epc.iterrows():
        add(r["part_number"], r["part_name"], 0, "epc_heavy")

    # Prior KS relevance card for silencer — re-probe for OE-on-card
    add("8983656821", "EXHAUST SILENCER ASSEMBLY", 0.0, "ledger_ks_catonly")

    ranked = sorted(
        hits.items(),
        key=lambda x: (_priority(x[1]["desc"]), -x[1]["eur"], x[0]),
    )
    print("total_candidates", len(ranked))
    for pn, v in ranked[:40]:
        srcs = ",".join(sorted(v["sources"]))
        print(f"{pn}\t{v['eur']:.2f}\t{v['desc']}\t{srcs}")

    short: list[tuple[str, dict]] = []
    seen: set[str] = set()
    # Force prior silencer hit first
    if "8983656821" in hits:
        short.append(("8983656821", hits["8983656821"]))
        seen.add("8983656821")
    for pn, v in ranked:
        if pn in seen:
            continue
        short.append((pn, v))
        seen.add(pn)
        if len(short) >= 15:
            break

    print("\n=== SHORTLIST ===")
    rows = []
    for i, (pn, v) in enumerate(short, 1):
        print(i, pn, v["eur"], v["desc"])
        rows.append(
            {
                "rank": i,
                "part_number": pn,
                "description": v["desc"],
                "eur_proxy": v["eur"],
                "sources": ";".join(sorted(v["sources"])),
            }
        )
    out_csv = OUT / "shortlist_exhaust_20261007.csv"
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print("wrote", out_csv)


if __name__ == "__main__":
    main()
