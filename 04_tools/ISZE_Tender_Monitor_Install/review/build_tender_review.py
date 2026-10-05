"""Internal Monday tender review page (built 2026-10-01 on Jerome's go).

Reads, never writes:
  01_data/14_dashboards/tender_data.json             the live feed
  01_data/00_derived/tender_price_context.csv        parts families x rival-price coverage
  04_tools/ISZE_Tender_Monitor_Install/tender_outcomes.json   answers recorded so far

Writes, next to this script:
  ISZE_Tender_Review.html          self-contained, opens on double-click, no internet
  OPEN_ISZE_Tender_Review.cmd      CRLF launcher

The page answers four questions for one reviewer (Jerome):
  1. which tenders need a decision this week, and why those
  2. the parts business behind each one, and how much of it we can price against a rival
  3. what the feed does not know about each one
  4. what was answered before, and what happened to it

Answers typed on the page stay in the browser until "Download answers" is pressed. The
download is a CSV that `python tender_outcomes.py <file>` loads into the outcome store. This
script never writes into the store.

Selection is the same rule as the weekly distributor list (build_rm_digest.py), so the page
and the list never disagree: not Ignore, repair-and-maintenance or pickup/truck purchase,
deadline on or after the build date. Live tenders that fail only the product rule are shown
separately so nothing live is hidden.

Run:  python review\\build_tender_review.py [--date YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent
ROOT = TOOL.parents[1]
sys.path.insert(0, str(TOOL))

import build_rm_digest as digest  # noqa: E402  (shared selection, titles and twin matching)

FEED = ROOT / "01_data" / "14_dashboards" / "tender_data.json"
PRICE = ROOT / "01_data" / "00_derived" / "tender_price_context.csv"
STORE = TOOL / "tender_outcomes.json"
OUT = HERE / "ISZE_Tender_Review.html"
LAUNCHER = HERE / "OPEN_ISZE_Tender_Review.cmd"
TEMPLATE = HERE / "tender_review_template.html"

clean = digest.clean


def parse_date(v):
    return digest.parse_date(v)


def gaps(o: dict) -> list[str]:
    out = []
    if not o.get("deadline_date"):
        out.append("deadline")
    if o.get("value_amount") in (None, ""):
        out.append("value")
    if o.get("fleet_size") in (None, ""):
        out.append("fleet size")
    if not o.get("pms_demand_by_category"):
        out.append("parts demand")
    return out


def parts_reason(o: dict) -> str:
    """Plain-English reason the parts demand is missing, from the feed's own basis text."""
    if o.get("pms_demand_by_category"):
        return ""
    basis = clean(o.get("opportunity_basis"))
    seg = clean(o.get("product_segment"))
    if o.get("fleet_size") in (None, ""):
        return "The notice does not state how many vehicles are in the fleet."
    if seg not in digest.VEHICLE_SEGMENTS:
        label = clean(o.get("product_segment_label")) or seg
        return (f"The fleet is stated ({o.get('fleet_size')} vehicles) but the tender is classed "
                f"as “{label}”, and parts demand is only modelled for pickup and truck fleets.")
    if "no distributor mapping" in basis:
        return "No Isuzu distributor is mapped to this country, so there is no parts-spend figure to scale."
    if "no SPU row" in basis:
        return "This distributor has no parts-spend-per-vehicle figure on file."
    return (basis[:160] or "reason not recorded in the feed.")


def load_price() -> dict[str, dict[str, dict]]:
    out: dict[str, dict[str, dict]] = collections.defaultdict(dict)
    if not PRICE.exists():
        return out
    with PRICE.open(encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            out[r["opportunity_id"]][r["pms_category"]] = r
    return out


def demand_rows(o: dict, price: dict) -> list[dict]:
    rows = []
    for item in o.get("pms_demand_by_category") or []:
        p = price.get(o["opportunity_id"], {}).get(item.get("pms_category"), {})
        rows.append({
            "family": item.get("category_label"),
            "qty": item.get("expected_qty"),
            "eur": item.get("addressable_eur"),
            "asp": item.get("avg_sp_eur"),
            "our_parts": int(p["our_parts_in_category"]) if p.get("our_parts_in_category") else None,
            "rival_parts": int(p["parts_with_rival_price"]) if p.get("parts_with_rival_price") else None,
            "coverage": float(p["coverage_pct"]) if p.get("coverage_pct") not in (None, "") else None,
            "rival_min": float(p["rival_min_eur"]) if p.get("rival_min_eur") else None,
            "rival_max": float(p["rival_max_eur"]) if p.get("rival_max_eur") else None,
        })
    return rows


def slim(o: dict, boiler: set, price: dict, twins: dict, store: dict, listed: set) -> dict:
    oid = o["opportunity_id"]
    conf = o.get("ids_match_confidence")
    return {
        "id": oid,
        "twin": twins.get(oid),
        "title": digest.display_title(o, boiler),
        "buyer": clean(o.get("buyer")),
        "country": clean(o.get("country")),
        "distributor": clean(o.get("ids_distributor_label")) if o.get("distributor_code") else "",
        "dealer": clean(o.get("ids_dealer_name")) if conf is not None and float(conf) >= digest.HIGH_CONFIDENCE else "",
        "dealer_city": clean(o.get("ids_dealer_city")),
        "deadline": str(parse_date(o.get("deadline_date")) or ""),
        "value": o.get("value_amount"),
        "currency": clean(o.get("currency")),
        "fleet": o.get("fleet_size"),
        "kind": "Repair and maintenance" if digest.is_rm(o) else "Vehicle purchase",
        "segment": clean(o.get("product_segment_label")) or clean(o.get("product_segment")),
        "decision": clean(o.get("decision")),
        "fleet_brand": clean(o.get("fleet_brand")),
        "fleet_brand_label": clean(o.get("fleet_brand_label")),
        "score": o.get("opportunity_score"),
        "fit": o.get("fit_score"), "win": o.get("win_score"), "econ": o.get("econ_score"),
        "drivers": [clean(x) for x in (o.get("score_drivers") or [])][:8],
        "scope": clean(o.get("aftersales_summary")),
        "owner": clean(o.get("owner_suggested")),
        "next": clean(o.get("next_action_suggested")),
        "evidence": clean(o.get("evidence_label")),
        "sources": [clean(s) for s in (o.get("sources") or [])],
        "url": clean(o.get("url")),
        "gaps": gaps(o),
        "parts": demand_rows(o, price),
        "parts_reason": parts_reason(o),
        "listed": oid in listed,
        "answer": (store.get(oid) or {}),
        "doc_check": doc_check(o),
    }


def doc_check(o: dict) -> dict:
    """What tender_doc_reader.py found in the tender documents (empty if not checked)."""
    c = o.get("fleet_doc_check") or {}
    if not c:
        return {}
    return {
        "verdict": c.get("verdict"),
        "label": clean(c.get("label")),
        "reason": clean(c.get("reason")),
        "read": c.get("documents_read"),
        "listed": c.get("documents_listed"),
        "brands": c.get("brands_in_list") or {},
        "evidence": [{"file": clean(e.get("file")), "where": clean(e.get("where")),
                      "snippet": clean(e.get("snippet"))[:260]} for e in (c.get("evidence") or [])[:3]],
        "folders": [str(ROOT / Path(x)) for x in (c.get("notice_dirs") or [])],
        "checked": str(c.get("checked_at") or "")[:10],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="build date YYYY-MM-DD (default today)")
    args = ap.parse_args(argv)
    run_date = parse_date(args.date) or dt.date.today()

    feed = json.loads(FEED.read_text(encoding="utf-8"))
    O, N, meta = feed["opportunities"], feed["notices"], feed["meta"]
    store = (json.loads(STORE.read_text(encoding="utf-8")) if STORE.exists() else {}).get("outcomes", {})
    price = load_price()

    dated, undated, stats = digest.select_rows(feed, run_date)
    # 2026-10-01: a tender to service an existing fleet whose brand the notice does not
    # name is not a pursue/pass decision yet. It goes to its own list: read the vehicle
    # list in the tender documents first. (Fleet-brand gate, isze_core_v3.)
    brand_check = [o for o in dated if str(o.get("fleet_brand") or "").startswith("unknown")]
    dated = [o for o in dated if not str(o.get("fleet_brand") or "").startswith("unknown")]
    stats["brand_unknown_check_first"] = len(brand_check)
    twins = digest.find_twins(dated)
    listed = {o["opportunity_id"] for o in dated}

    def live(o):
        d = parse_date(o.get("deadline_date"))
        return d is not None and d >= run_date

    other_live = [o for o in O if live(o) and clean(o.get("decision")) in digest.DECISIONS
                  and not digest.in_scope(o)]
    sized = [o for o in O if o.get("pms_demand_by_category")]
    answered = [o for o in O if o["opportunity_id"] in store]

    boiler = digest.boilerplate_headings(O)
    data = {
        "built": run_date.isoformat(),
        "feed_generated_at": meta.get("generated_at"),
        "queue": [slim(o, boiler, price, twins, store, listed) for o in dated],
        "brand_check": [slim(o, boiler, price, {}, store, listed)
                        for o in sorted(brand_check, key=lambda o: str(o.get("deadline_date") or "9999"))],
        "other_live": [slim(o, boiler, price, {}, store, listed) for o in other_live],
        "undated": [slim(o, boiler, price, {}, store, listed) for o in undated],
        "sized": [slim(o, boiler, price, {}, store, listed) for o in sized],
        "answered": [slim(o, boiler, price, {}, store, listed) for o in answered],
        "store_orphans": sorted(set(store) - {o["opportunity_id"] for o in O}),
        "book": {
            "opportunities": len(O),
            "notices": len(N),
            "notices_fleet_stated": sum(1 for n in N if n.get("fleet_size") not in (None, "", 0)
                                        or n.get("FleetSize") not in (None, "", 0)),
            "opps_deadline": sum(1 for o in O if o.get("deadline_date")),
            "opps_value": sum(1 for o in O if o.get("value_amount") not in (None, "")),
            "opps_fleet": sum(1 for o in O if o.get("fleet_size") not in (None, "")),
            "opps_sized": len(sized),
            "store_recorded": len(store),
            "selection": stats,
            "twin_pairs": len(twins) // 2,
        },
        "outcomes_summary": meta.get("outcomes_summary") or {},
    }
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*@@DATA@@*/null", blob)
    OUT.write_text(html, encoding="utf-8", newline="\n")
    with LAUNCHER.open("wb") as fh:
        fh.write(b'@echo off\r\nstart "" "%~dp0ISZE_Tender_Review.html"\r\n')

    print(f"built {OUT} ({OUT.stat().st_size:,} bytes)")
    print(f"queue rows {len(data['queue'])} | twin pairs {len(twins)//2} | other live {len(other_live)} | "
          f"undated {len(undated)} | sized {len(sized)} | answers on file {len(store)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
