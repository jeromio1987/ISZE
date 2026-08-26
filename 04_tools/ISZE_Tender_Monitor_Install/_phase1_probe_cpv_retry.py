"""Phase 1 throwaway: retry TED probes that rate-limited; sample titles; hierarchical check."""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

TED_URL = "https://api.ted.europa.eu/v3/notices/search"

CURRENT_CPV = [
    "34131000", "34113000", "34136000", "34130000", "34136200",
    "50110000", "50112000", "50116000", "50111000",
]
TED_COUNTRIES = [
    "GBR", "IRL", "POL", "PRT", "GRC", "ISR",
    "DEU", "FRA", "ESP", "ITA", "NLD", "BEL",
    "DNK", "SWE", "NOR", "FIN", "ROU", "HUN",
    "CZE", "SVK", "BGR", "HRV", "AUT", "LVA",
    "LTU", "EST", "SVN",
]

RETRY_ALONE = [
    "50100000", "50111100", "50111110", "50112200", "50113000",
    "50114000", "50117000", "50118000", "50118100", "50118200",
    "34300000", "34320000", "34330000", "66114000",
]
RETRY_COUNTRIES = ["MLT", "CYP", "ISL"]
PRIORITY_ADD = [
    "34136100", "34113200", "50111100", "50111110", "50113200",
    "50112200", "34320000", "66114000", "34134000", "34139000",
    "50100000", "50118200", "34144700", "34144900", "34300000",
    "34134100", "34134200", "50112100",
]


def since() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=70)).strftime("%Y%m%d")


def countries_q(codes=None) -> str:
    codes = codes or TED_COUNTRIES
    return " OR ".join(f"CY={c}" for c in codes)


def cpv_q(codes) -> str:
    return " OR ".join(f"PC={c}" for c in codes)


def call(session, query, fields=None, limit=1, retries=4):
    payload = {
        "query": query,
        "fields": fields or ["ND"],
        "limit": limit,
        "paginationMode": "ITERATION",
        "scope": "ACTIVE",
    }
    last = None
    for attempt in range(retries):
        try:
            r = session.post(TED_URL, json=payload, timeout=60)
            if r.status_code == 429 or not r.content:
                time.sleep(1.5 * (attempt + 1))
                last = {"status": r.status_code, "total": None, "error": f"empty/429 attempt {attempt+1}", "raw": (r.text or "")[:120]}
                continue
            if r.headers.get("Content-Type", "").startswith("application/json") is False and not r.text.strip().startswith("{"):
                time.sleep(1.5 * (attempt + 1))
                last = {"status": r.status_code, "total": None, "error": "non-json", "raw": r.text[:120]}
                continue
            body = r.json()
            return {
                "status": r.status_code,
                "total": body.get("totalNoticeCount"),
                "error": None if r.ok else str(body)[:200],
                "notices": body.get("notices") or [],
                "timedOut": body.get("timedOut"),
            }
        except Exception as exc:
            time.sleep(1.5 * (attempt + 1))
            last = {"status": None, "total": None, "error": str(exc), "notices": []}
    return last or {"status": None, "total": None, "error": "failed", "notices": []}


def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "ISZE-TenderPhase1/0.1b",
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    pd = since()
    cy = countries_q()
    out = {"probed_at": datetime.now(timezone.utc).isoformat(), "window": f"PD>={pd}", "results": {}}

    base_q = f"({cpv_q(CURRENT_CPV)}) AND ({cy}) AND PD>={pd}"
    base = call(session, base_q)
    out["results"]["baseline"] = {"query": base_q, **{k: base[k] for k in ("status", "total", "error", "timedOut")}}
    print("BASELINE", base["total"])
    time.sleep(0.8)

    alone = {}
    for code in RETRY_ALONE:
        q = f"PC={code} AND ({cy}) AND PD>={pd}"
        res = call(session, q)
        alone[code] = {"total": res["total"], "status": res["status"], "error": res["error"]}
        print(f"ALONE {code}: {res['total']}")
        time.sleep(0.7)
    out["results"]["retry_alone"] = alone

    countries = {}
    for code in RETRY_COUNTRIES:
        q = f"({cpv_q(CURRENT_CPV)}) AND CY={code} AND PD>={pd}"
        res = call(session, q, fields=["ND", "TI", "PC", "CY"], limit=5)
        titles = []
        for n in res.get("notices") or []:
            titles.append({"ND": n.get("ND"), "TI": n.get("TI"), "PC": n.get("PC"), "CY": n.get("CY")})
        countries[code] = {"total": res["total"], "status": res["status"], "samples": titles, "error": res["error"]}
        print(f"COUNTRY {code}: {res['total']} samples={len(titles)}")
        time.sleep(0.7)

        q_any = f"CY={code} AND PD>={pd}"
        res_any = call(session, q_any)
        countries[f"{code}_any"] = {"total": res_any["total"], "status": res_any["status"], "error": res_any["error"]}
        print(f"COUNTRY {code} ANY: {res_any['total']}")
        time.sleep(0.7)
    out["results"]["countries"] = countries

    # CYP+MLT together vs baseline
    plus = TED_COUNTRIES + ["CYP", "MLT"]
    q_plus = f"({cpv_q(CURRENT_CPV)}) AND ({countries_q(plus)}) AND PD>={pd}"
    res_plus = call(session, q_plus)
    out["results"]["baseline_plus_cyp_mlt"] = {
        "total": res_plus["total"],
        "delta": (res_plus["total"] - base["total"]) if res_plus["total"] is not None and base["total"] is not None else None,
        "status": res_plus["status"],
        "error": res_plus["error"],
    }
    print("PLUS CYP+MLT", res_plus["total"], "delta", out["results"]["baseline_plus_cyp_mlt"]["delta"])
    time.sleep(0.7)

    # Also ISL alone add
    plus_isl = TED_COUNTRIES + ["ISL"]
    q_isl = f"({cpv_q(CURRENT_CPV)}) AND ({countries_q(plus_isl)}) AND PD>={pd}"
    res_isl = call(session, q_isl)
    out["results"]["baseline_plus_isl"] = {
        "total": res_isl["total"],
        "delta": (res_isl["total"] - base["total"]) if res_isl["total"] is not None and base["total"] is not None else None,
    }
    print("PLUS ISL", res_isl["total"], "delta", out["results"]["baseline_plus_isl"]["delta"])
    time.sleep(0.7)

    increments = []
    for code in PRIORITY_ADD:
        codes = CURRENT_CPV + [code]
        q = f"({cpv_q(codes)}) AND ({cy}) AND PD>={pd}"
        res = call(session, q)
        delta = None
        if res.get("total") is not None and base.get("total") is not None:
            delta = res["total"] - base["total"]
        increments.append({"add": code, "total": res.get("total"), "delta": delta, "status": res.get("status"), "error": res.get("error")})
        print(f"ADD {code}: total={res.get('total')} delta={delta}")
        time.sleep(0.7)
    out["results"]["increments"] = increments

    # Sample titles for high-noise candidates
    samples = {}
    for code in ["34144700", "34144900", "50100000", "66114000", "34300000", "50111100"]:
        q = f"PC={code} AND ({cy}) AND PD>={pd}"
        res = call(session, q, fields=["ND", "TI", "PC"], limit=5)
        samples[code] = {
            "total": res.get("total"),
            "titles": [n.get("TI") for n in (res.get("notices") or [])],
            "error": res.get("error"),
        }
        print(f"SAMPLE {code}: n={res.get('total')}")
        time.sleep(0.7)
    out["results"]["samples"] = samples

    path = __file__.replace("_phase1_probe_cpv_retry.py", "_phase1_probe_cpv_retry_results.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("Wrote", path)


if __name__ == "__main__":
    main()
    sys.exit(0)
