"""Phase 1 throwaway: TED CPV volume + CYP/MLT/ISL probes. Report only — do not wire in."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone

import requests

TED_URL = "https://api.ted.europa.eu/v3/notices/search"

CURRENT_CPV = [
    "34131000",  # Pick-ups
    "34113000",  # 4WD vehicles
    "34136000",  # Vans
    "34130000",  # Goods-transport motor vehicles
    "34136200",  # Panel vans
    "50110000",  # R&M motor vehicles
    "50112000",  # Repair of cars
    "50116000",  # Repair of vehicle parts
    "50111000",  # Fleet management + repair
]

TED_COUNTRIES = [
    "GBR", "IRL", "POL", "PRT", "GRC", "ISR",
    "DEU", "FRA", "ESP", "ITA", "NLD", "BEL",
    "DNK", "SWE", "NOR", "FIN", "ROU", "HUN",
    "CZE", "SVK", "BGR", "HRV", "AUT", "LVA",
    "LTU", "EST", "SVN",
]

# Candidates NOT in CURRENT_CPV — LCV / pickup-adjacent / R&M / fleet / leasing+service
CANDIDATE_CPV = [
    ("34136100", "Light vans", "LCV core sibling of 34136000/34136200"),
    ("34113200", "Off-road vehicles", "Pickup / utility 4x4 adjacent to 34113000"),
    ("34113300", "All-terrain vehicles", "Utility / ATV fleet adjacent"),
    ("34113100", "Jeeps", "4x4 passenger-utility adjacent"),
    ("34134000", "Flatbed and tipper trucks", "Chassis-cab / dropside municipal fleet"),
    ("34134100", "Flatbed trucks", "Dropside / platform goods vehicles"),
    ("34134200", "Tipper trucks", "Tipper goods vehicles"),
    ("34137000", "Second-hand goods vehicles", "Used LCV / pickup purchases"),
    ("34139000", "Chassis", "Chassis-cab builds (D-Max / N-Series path)"),
    ("34144700", "Utility vehicles", "Utility / municipal light fleet label"),
    ("34144900", "Electric vehicles", "EV fleet purchase (often mixed LCV)"),
    ("50100000", "Repair/maint. of vehicles & related equip. (parent)", "Parent of 5011xxxx — broader R&M net"),
    ("50111100", "Vehicle-fleet management services", "Fleet mgmt without forcing repair CPV"),
    ("50111110", "Vehicle-fleet-support services", "Fleet support / managed services"),
    ("50112100", "Car repair services", "Repair child under 50112000"),
    ("50112200", "Car maintenance services", "Maintenance contracts"),
    ("50113000", "Repair and maintenance of buses", "Adjacent heavy R&M (noise risk)"),
    ("50113200", "Truck repair services", "Truck R&M — fleet workshop contracts"),
    ("50114000", "Repair and maintenance of specialised vehicles", "Specialised fleet workshop"),
    ("50117000", "Vehicle conversion and reconditioning", "Conversion / reconditioning / bodywork"),
    ("50118000", "Automobile emergency road services", "Breakdown / roadside (fleet servicing edge)"),
    ("50118100", "Breakdown and recovery services for cars", "Recovery — fleet servicing edge"),
    ("50118200", "Breakdown and recovery for commercial vehicles", "Commercial recovery — closer to LCV fleet"),
    ("34300000", "Parts and accessories for vehicles and engines", "Parts supply (fleet servicing)"),
    ("34320000", "Mechanical spare parts for motor vehicles", "Mechanical parts supply"),
    ("34330000", "Spare parts for goods / special vehicles / buses", "Goods-vehicle parts"),
    ("66114000", "Financial leasing services", "Fleet leasing (often + servicing in title)"),
]


def pd_from(days: int = 70) -> str:
    d = datetime.now(timezone.utc) - timedelta(days=days)
    return d.strftime("%Y%m%d")


def country_block(codes: list[str]) -> str:
    return " OR ".join(f"CY={c}" for c in codes)


def cpv_block(codes: list[str]) -> str:
    return " OR ".join(f"PC={c}" for c in codes)


def ted_count(session: requests.Session, query: str) -> dict:
    payload = {
        "query": query,
        "fields": ["ND"],
        "limit": 1,
        "paginationMode": "ITERATION",
        "scope": "ACTIVE",
    }
    try:
        r = session.post(TED_URL, json=payload, timeout=45)
        body = r.json() if r.content else {}
        total = body.get("totalNoticeCount")
        if total is None:
            total = body.get("total")
        if total is None and isinstance(body.get("notices"), list):
            # fallback: some responses only paginate
            total = len(body["notices"])
        return {
            "status": r.status_code,
            "total": total,
            "error": None if r.ok else (body.get("message") or r.text[:200]),
            "keys": sorted(body.keys()) if isinstance(body, dict) else [],
        }
    except Exception as exc:
        return {"status": None, "total": None, "error": str(exc), "keys": []}


def main() -> None:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "ISZE-TenderPhase1/0.1 (coverage probe)",
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    since = pd_from(70)
    base_countries = country_block(TED_COUNTRIES)
    out: dict = {
        "probed_at": datetime.now(timezone.utc).isoformat(),
        "window": f"PD>={since} (~70d)",
        "baseline_cpv": CURRENT_CPV,
        "baseline_countries_n": len(TED_COUNTRIES),
        "results": {},
    }

    print(f"Window PD>={since}")

    # Baseline
    q_base = f"({cpv_block(CURRENT_CPV)}) AND ({base_countries}) AND PD>={since}"
    base = ted_count(session, q_base)
    out["results"]["baseline_current_9_cpv"] = {"query": q_base, **base}
    print(f"BASELINE current 9 CPV × 27 countries: {base}")

    # Each candidate alone (same countries)
    cand_rows = []
    for code, label, why in CANDIDATE_CPV:
        q = f"PC={code} AND ({base_countries}) AND PD>={since}"
        res = ted_count(session, q)
        row = {"code": code, "label": label, "why": why, "query": q, **res}
        cand_rows.append(row)
        print(f"  {code} {label}: status={res['status']} total={res['total']} err={res['error']}")
    out["results"]["candidates_alone"] = cand_rows

    # Country probes with CURRENT CPV only
    country_probes = {}
    for code in ("CYP", "MLT", "ISL"):
        q = f"({cpv_block(CURRENT_CPV)}) AND CY={code} AND PD>={since}"
        res = ted_count(session, q)
        country_probes[code] = {"query": q, **res}
        print(f"COUNTRY {code} × current CPV: {res}")

        # Any notices at all for country (no CPV) — volume context
        q_any = f"CY={code} AND PD>={since}"
        res_any = ted_count(session, q_any)
        country_probes[f"{code}_any"] = {"query": q_any, **res_any}
        print(f"COUNTRY {code} ANY CPV: {res_any}")

    out["results"]["country_probes"] = country_probes

    # Confirm CYP/MLT omitted: baseline + CYP+MLT
    plus = TED_COUNTRIES + ["CYP", "MLT"]
    q_plus = f"({cpv_block(CURRENT_CPV)}) AND ({country_block(plus)}) AND PD>={since}"
    res_plus = ted_count(session, q_plus)
    out["results"]["baseline_plus_cyp_mlt"] = {"query": q_plus, **res_plus}
    print(f"BASELINE + CYP + MLT: {res_plus}")

    # Incremental: each high-priority add vs baseline (single CPV OR current)
    priority_add = [
        "34136100", "34113200", "50111100", "50111110", "50113200",
        "50112200", "34320000", "66114000", "34134000", "34139000",
        "50100000", "50118200",
    ]
    increments = []
    for code in priority_add:
        codes = CURRENT_CPV + [code]
        q = f"({cpv_block(codes)}) AND ({base_countries}) AND PD>={since}"
        res = ted_count(session, q)
        delta = None
        if res.get("total") is not None and base.get("total") is not None:
            delta = res["total"] - base["total"]
        increments.append({"add": code, "total": res.get("total"), "delta_vs_baseline": delta, **{k: res[k] for k in ("status", "error")}})
        print(f"  ADD {code}: total={res.get('total')} delta={delta}")
    out["results"]["priority_increments"] = increments

    path = __file__.replace("_phase1_probe_cpv_countries.py", "_phase1_probe_cpv_countries_results.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
    sys.exit(0)
