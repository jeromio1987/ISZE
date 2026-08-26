"""Throwaway analysis for Phase 0 — field completeness + coverage map. No functional changes."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\tender_data.json")

# ISZE markets from isze_core + known extras named in v4 prompt pack
ISZE_CODES = {
    "GBR", "IRL", "POL", "PRT", "GRC", "ISR",
    "DEU", "FRA", "ESP", "ITA", "NLD", "BEL",
    "DNK", "SWE", "NOR", "FIN", "ROU", "HUN",
    "CZE", "SVK", "BGR", "HRV", "AUT", "LVA",
    "LTU", "EST", "SVN",
}
# Named in Phase 1 coverage gaps / dark-markets doc but NOT in TED filter
EXTRA_ISZE = {"CYP", "MLT", "ISL", "KAZ"}  # Cyprus, Malta, Iceland, Kazakhstan

CODE_TO_NAME = {
    "AUT": "Austria", "BEL": "Belgium", "BGR": "Bulgaria", "CYP": "Cyprus",
    "CZE": "Czechia", "DEU": "Germany", "DNK": "Denmark", "ESP": "Spain",
    "EST": "Estonia", "FIN": "Finland", "FRA": "France", "GBR": "United Kingdom",
    "GRC": "Greece", "HRV": "Croatia", "HUN": "Hungary", "IRL": "Ireland",
    "ISR": "Israel", "ISL": "Iceland", "ITA": "Italy", "KAZ": "Kazakhstan",
    "LTU": "Lithuania", "LVA": "Latvia", "MLT": "Malta", "NLD": "Netherlands",
    "NOR": "Norway", "POL": "Poland", "PRT": "Portugal", "ROU": "Romania",
    "SVK": "Slovakia", "SVN": "Slovenia", "SWE": "Sweden",
}


def is_empty(v) -> bool:
    if v is None:
        return True
    if isinstance(v, str) and v.strip() in ("", "—", "-", "n/a", "N/A"):
        return True
    if isinstance(v, (list, dict)) and len(v) == 0:
        return True
    if v == 0 and False:  # keep 0 as populated for scores; fleet 0 handled separately
        return True
    return False


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    notices = data["notices"]
    opps = data["opportunities"]
    meta = data.get("meta", {})
    n = len(notices)
    assert n > 0

    # Field completeness across notices
    all_keys = sorted({k for row in notices for k in row.keys()})
    completeness = []
    for k in all_keys:
        populated = 0
        for row in notices:
            v = row.get(k)
            # FleetSize / fleet_size: treat 0 as empty (extractor default)
            if k in ("FleetSize", "fleet_size"):
                if v not in (None, "", 0, "0"):
                    populated += 1
            elif k in ("Est. Value", "value_amount"):
                if v not in (None, "", 0, "0", 0.0):
                    populated += 1
            elif not is_empty(v):
                populated += 1
        pct = 100.0 * populated / n
        completeness.append({
            "field": k,
            "populated": populated,
            "empty": n - populated,
            "pct_populated": round(pct, 1),
            "pct_empty": round(100.0 - pct, 1),
        })
    completeness.sort(key=lambda x: x["pct_empty"], reverse=True)

    # Coverage by country
    by_country = Counter()
    sources_by_country = defaultdict(Counter)
    action_by_country = Counter()
    for o in opps:
        code = (o.get("country_code") or "").upper() or "UNK"
        # normalize GB -> GBR
        if code in ("GB", "UK"):
            code = "GBR"
        by_country[code] += 1
        for s in o.get("sources") or [o.get("Source")]:
            if s:
                sources_by_country[code][s] += 1
        dec = (o.get("decision") or "").lower()
        if dec in ("attack", "selective"):
            action_by_country[code] += 1

    # Also count notices (raw) by country for source attribution
    notice_country = Counter()
    notice_source = Counter()
    for row in notices:
        code = (row.get("Country Code") or "").upper()
        if code in ("GB", "UK"):
            code = "GBR"
        notice_country[code] += 1
        notice_source[row.get("Source", "?")] += 1

    markets_with = sorted(set(by_country) | set(notice_country) - {"", "UNK"})
    zero_markets = sorted((ISZE_CODES | EXTRA_ISZE) - set(by_country.keys()) - set(notice_country.keys()))

    report = {
        "generated_from": str(DATA),
        "meta_generated_at": meta.get("generated_at"),
        "notice_count": n,
        "opportunity_count": len(opps),
        "field_completeness": completeness,
        "notice_source_counts": dict(notice_source.most_common()),
        "markets_returning": [
            {
                "code": c,
                "name": CODE_TO_NAME.get(c, c),
                "opportunities": by_country.get(c, 0),
                "notices": notice_country.get(c, 0),
                "action_tier": action_by_country.get(c, 0),
                "sources": dict(sources_by_country.get(c, {})),
            }
            for c in sorted(markets_with, key=lambda x: (-by_country.get(x, 0), x))
        ],
        "zero_notice_isze_markets": [
            {"code": c, "name": CODE_TO_NAME.get(c, c), "in_ted_filter": c in ISZE_CODES}
            for c in zero_markets
        ],
        "ted_filter_missing_named_markets": sorted(EXTRA_ISZE - ISZE_CODES),
    }
    out = ROOT / "_audit_analyze_v3_results.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"notices={n} opps={len(opps)} markets={len(markets_with)} zero={len(zero_markets)}")
    print("Top empty fields:")
    for row in completeness[:12]:
        print(f"  {row['field']}: {row['pct_empty']}% empty")
    print("Zero markets:", [z["code"] for z in report["zero_notice_isze_markets"]])
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
