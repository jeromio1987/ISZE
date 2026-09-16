#!/usr/bin/env python3
"""Israel LCV (UMI) Section E coverage + network average snapshot."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
sys.path.insert(0, str(ROOT / "04_tools" / "ids_dealer_ranking"))

from ids_paths import IDS_RESULT_REPORTS_DIR  # noqa: E402
from ids_report_extract import build_dashboard_payload  # noqa: E402

OUT = Path(__file__).resolve().parent


def pct(v):
    return None if v is None else round(float(v) * 100, 1)


def main() -> int:
    print("Building dashboard payload…", flush=True)
    full = build_dashboard_payload(IDS_RESULT_REPORTS_DIR)
    network = full.get("network") or {}
    dealers = full.get("dealers") or []

    umi = [d for d in dealers if d.get("country") == "Israel LCV"]
    uklcv = [d for d in dealers if d.get("country") == "UK LCV"]

    def section_e_stats(rows, label):
        e_none = []
        e_zero = []
        e_scored = []
        for d in rows:
            sec = (d.get("sections") or {}).get("E") or {}
            score = sec.get("score")
            spct = sec.get("pct")
            rec = {
                "name": d.get("name"),
                "total_pct": pct(d.get("total_pct")),
                "e_score": score,
                "e_pct": pct(spct),
                "excluded_from_average": bool(d.get("excluded_from_average")),
            }
            if score is None and spct is None:
                e_none.append(rec)
            elif (score or 0) == 0 or (spct or 0) == 0:
                e_zero.append(rec)
            else:
                e_scored.append(rec)
        return {
            "label": label,
            "n_dealers": len(rows),
            "e_blank": e_none,
            "e_zero": e_zero,
            "e_scored_n": len(e_scored),
            "e_blank_n": len(e_none),
            "e_zero_n": len(e_zero),
            "e_scored_avg_pct": round(mean([r["e_pct"] for r in e_scored if r["e_pct"] is not None]), 1)
            if e_scored
            else None,
            "e_scored_names_sample": [r["name"] for r in e_scored[:8]],
        }

    by_country_e = defaultdict(lambda: {"n": 0, "blank": 0, "zero": 0, "scored": 0})
    for d in dealers:
        c = d.get("country") or "?"
        by_country_e[c]["n"] += 1
        sec = (d.get("sections") or {}).get("E") or {}
        score = sec.get("score")
        spct = sec.get("pct")
        if score is None and spct is None:
            by_country_e[c]["blank"] += 1
        elif (score or 0) == 0 or (spct or 0) == 0:
            by_country_e[c]["zero"] += 1
        else:
            by_country_e[c]["scored"] += 1

    profiles = full.get("country_profiles") or {}
    country_avgs = {
        c: {
            "n": p.get("n_dealers"),
            "excluded": p.get("excluded_from_average_count"),
            "avg_pct": pct(p.get("avg_pct") or p.get("total_pct")),
            "sections_pct": {k: pct(v) for k, v in (p.get("sections_pct") or {}).items()},
        }
        for c, p in profiles.items()
    }

    out = {
        "network": {
            "n": network.get("n_dealers"),
            "avg_pct": pct(network.get("avg_pct") or network.get("total_pct")),
            "sections_pct": {k: pct(v) for k, v in (network.get("sections_pct") or {}).items()},
        },
        "israel_lcv": section_e_stats(umi, "Israel LCV (UMI)"),
        "uk_lcv": section_e_stats(uklcv, "UK LCV (IUK)"),
        "section_e_by_country": dict(sorted(by_country_e.items())),
        "country_avgs": country_avgs,
        "countries": full.get("countries"),
    }
    (OUT / "ids_umi_section_e.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({k: out[k] for k in ("network", "israel_lcv", "uk_lcv")}, indent=2))
    print("Wrote", OUT / "ids_umi_section_e.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
