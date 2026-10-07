"""Connect the first two real feeds to the INTERNAL build (U29 task C).

Writes `payload/real_feeds.local.json`, a small block that records the two real feeds in
the shape the product already reads:

  tender_data.notices   the live weekly tender feed (`01_data/14_dashboards/tender_data.json`),
                        reduced to the fields `src/data/tender_investigation.js` snapshots.
  prism_measures        accepted PRISM-shaped measures at the level each was measured
                        (national ITUK and Portugal, CY2025), built only from
                        `01_data/00_derived/`. No national total is split to a dealer.

It never invents a value, never infers a delivery basis, and never writes the feed itself.
Nothing here goes into the SYNTHETIC artifact: the synthetic build keeps its own fixtures.

Run from anywhere.  Read-only on both sources.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
COMPONENT = HERE.parent
ISZE = COMPONENT.parents[1]  # ...\ISZE
DERIVED = ISZE / "01_data" / "00_derived"
TENDER = ISZE / "01_data" / "14_dashboards" / "tender_data.json"
OUT = COMPONENT / "payload" / "real_feeds.local.json"

# The two markets this pilot prices. Never another distributor.
MARKETS = {"ITUK": "Isuzu Truck UK", "PORTUGAL": "Portugal (I-Motors)"}
YEAR = 2025


def _name(v):
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _date(v):
    """The feed writes ISO dates or nothing. Never guess a date."""
    s = _name(v)
    if not s:
        return None
    return s[:10] if len(s) >= 10 and s[4] == "-" else s


def build_notices() -> dict:
    if not TENDER.exists():
        return {"present": False, "reason": "the weekly tender feed file is not on disk",
                "notices": []}
    doc = json.loads(TENDER.read_text(encoding="utf-8"))
    raw = doc.get("notices") or []
    out = []
    seen = set()
    for n in raw:
        code = _name(n.get("distributor_code"))
        if code not in MARKETS:
            continue
        oid = _name(n.get("opportunity_id"))
        if not oid or oid in seen:
            continue
        seen.add(oid)
        out.append({
            "opportunity_id": oid,
            "title": _name(n.get("Title")),
            "buyer": _name(n.get("Buyer")),
            "country": _name(n.get("Country")),
            "deadline_date": _date(n.get("Deadline Date")),
            "published_latest": _date(n.get("Published Date")),
            "lifecycle": _name(n.get("Lifecycle")),
            "notice_type": _name(n.get("Notice Type")),
            "value_amount": (None if n.get("value_amount") in (None, "")
                             else float(n["value_amount"])),
            "currency": _name(n.get("Currency")),
            "source": _name(n.get("Source")) or "tender_feed",
            "url": _name(n.get("URL")),
            "distributor_code": code,
            "aftersales_tags": n.get("aftersales_tags") or [],
            "parts_signal": bool(n.get("parts_signal")),
            "decision": _name(n.get("decision")),
        })
    return {
        "present": True,
        "generated_at": (doc.get("meta") or {}).get("generated_at"),
        "source_file": str(TENDER),
        "source_stats": (doc.get("meta") or {}).get("stats"),
        "rule": ("notices whose distributor_code is ITUK or PORTUGAL only; the deadline is "
                 "the notice's own; an expired or cancelled notice is never a current "
                 "deadline; a notice value is never Isuzu parts revenue"),
        "notices": out,
    }


def build_prism_measures() -> dict:
    """Accepted measures at the LEVEL each was measured. National stays national."""
    src = DERIVED / "gps_spu_by_distributor.csv"
    pms = DERIVED / "gps_spu_pms.csv"
    measures = []
    if src.exists():
        g = pd.read_csv(src)
        g = g[(g["year"] == YEAR) & (g["distributor_code"].isin(MARKETS))]
        for _, r in g.iterrows():
            code = r["distributor_code"]
            uio_src = _name(r.get("uio_source")) or "01_data/00_derived/gps_spu_by_distributor.csv"
            measures.append({
                "id": f"PRISM-UIO-{code}-{YEAR}",
                "kind": "trucks_in_service",
                "value": (None if pd.isna(r["uio_units"]) else float(r["uio_units"])),
                "unit": "vehicles",
                "source": uio_src,
                "period": f"CY{YEAR}",
                "year": YEAR,
                "population": "national",
                "accepted_basis": "ituk_dvla_2026" if code == "ITUK" else "v18_actual",
                "denominator_version": "uio_v1",
                "market": code,
                "note": "national fleet; never divided to a dealer",
            })
            measures.append({
                "id": f"PRISM-SPEND-{code}-{YEAR}",
                "kind": "measured_spend",
                "value": (None if pd.isna(r["total_sales_eur"]) else float(r["total_sales_eur"])),
                "unit": "EUR",
                "source": "01_data/00_derived/gps_spu_by_distributor.csv",
                "period": f"CY{YEAR}",
                "year": YEAR,
                "population": "national",
                "accepted_basis": "billed_eur_v2",
                "denominator_version": "spend_v2",
                "market": code,
                "note": "billed parts value on the GPS basis; national",
            })
            if not pd.isna(r.get("spend_per_unit_eur")):
                measures.append({
                    "id": f"PRISM-SPU-{code}-{YEAR}",
                    "kind": "spend_per_truck",
                    "value": float(r["spend_per_unit_eur"]),
                    "unit": "EUR/vehicle",
                    "source": "01_data/00_derived/gps_spu_by_distributor.csv",
                    "period": f"CY{YEAR}",
                    "year": YEAR,
                    "population": "national",
                    "accepted_basis": "billed_eur_v2 / uio_v1",
                    "denominator_version": "spu_v2",
                    "market": code,
                    "note": "national average; not a dealer rate",
                })
    families = []
    if pms.exists():
        p = pd.read_csv(pms)
        p = p[(p["year"] == YEAR) & (p["distributor_code"].isin(MARKETS))
              & (p["line_type"] == "all")]
        for _, r in p.iterrows():
            families.append({
                "distributor_code": r["distributor_code"],
                "pms_category": r["pms_category"],
                "net_sales_eur": float(r["net_sales_eur"]),
                "uio_units": None if pd.isna(r["uio_units"]) else float(r["uio_units"]),
                "spu_eur": None if pd.isna(r["spu_eur"]) else float(r["spu_eur"]),
            })
    return {
        "present": bool(measures),
        "year": YEAR,
        "source_files": ["01_data/00_derived/gps_spu_by_distributor.csv",
                         "01_data/00_derived/gps_spu_pms.csv"],
        "rule": ("each measure stays at the level it was measured at; a national total is "
                 "never allocated to a dealer; the fleet forecast beyond 2025 is excluded"),
        "measures": measures,
        "family_detail_national": families,
    }


def main() -> int:
    notices = build_notices()
    prism = build_prism_measures()
    block = {
        "_note": ("Real feeds for the INTERNAL build only (U29 task C). Tender notices are "
                  "read from the weekly feed; PRISM measures are read from derived files at "
                  "their measured level. The SYNTHETIC artifact never carries this block."),
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "markets": MARKETS,
        "tender_data": {"notices": notices["notices"]},
        "prism_measures": prism["measures"],
        "provenance": {
            "tender": {k: v for k, v in notices.items() if k != "notices"},
            "prism": {k: v for k, v in prism.items() if k != "measures"},
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(block, indent=2, ensure_ascii=False), encoding="utf-8")
    by = {}
    for n in notices["notices"]:
        by[n["distributor_code"]] = by.get(n["distributor_code"], 0) + 1
    print(f"wrote {OUT}")
    print(f"  tender notices (ITUK/PORTUGAL): {len(notices['notices'])}  by market: {by}")
    print(f"  prism measures: {len(prism['measures'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

