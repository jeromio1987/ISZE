#!/usr/bin/env python3
"""Build risk_cockpit.json for ISZE_Risk_Cockpit.html + Master Dashboard tiles."""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    AIM_GPS_MATRIX_CSV,
    AUTODOC_SCRAPER_DIR,
    DASHBOARDS_DIR,
    DASHBOARDS_JSON_DIR,
    DERIVED_DIR,
)

REPORT_JSON = DERIVED_DIR / "_verification_report.json"

VIZ_DIR = DASHBOARDS_JSON_DIR / "viz"
OUT_JSON = VIZ_DIR / "risk_cockpit.json"
OUT_JS = DASHBOARDS_DIR / "sales" / "risk_cockpit.data.js"

WALLET_CSV = DERIVED_DIR / "wallet_waterfall.csv"
DEFECTION_CSV = DERIVED_DIR / "defection_alerts.csv"
SUBSTITUTION_CSV = DERIVED_DIR / "substitution_timeline.csv"
PMS_OPP_CSV = DERIVED_DIR / "pms_opportunity_matrix.csv"
NETWORK_PCT_CSV = DERIVED_DIR / "network_percentile.csv"
TENDER_JSON = DASHBOARDS_JSON_DIR / "tender_data.json"
AUTODOC_CSV = AUTODOC_SCRAPER_DIR / "autodoc_results.csv"
KS_CSV = AUTODOC_SCRAPER_DIR / "ks_results.csv"

GBP_TO_EUR = 1.17
BOGUS_GBP_CEILING = 3.05

QUADRANT_COLORS = {
    "defend": "#3D6B4F",
    "grow_capture": "#CC0E1E",
    "fix_pricing": "#E65100",
    "strategic_watch": "#7A8FA6",
    "protect": "#B8956B",
}


def _require_verify_ok(force: bool) -> None:
    if force:
        print("WARNING: --force skips verification gate", flush=True)
        return
    if not REPORT_JSON.exists():
        raise SystemExit(f"Missing {REPORT_JSON} — run verify first or pass --force")
    summary = json.loads(REPORT_JSON.read_text(encoding="utf-8")).get("summary", {})
    if not summary.get("ok"):
        raise SystemExit("Verification not green — fix pipeline or pass --force")


def _wallet_network(year: int) -> dict:
    df = pd.read_csv(WALLET_CSV)
    sub = df[df["year"] == year].copy()
    if sub.empty:
        raise SystemExit(f"No wallet_waterfall rows for year {year}")
    wallet = float(sub["theoretical_wallet_eur"].sum())
    genuine = float(sub["captured_genuine_eur"].sum())
    bvp = float(sub["captured_bvp_eur"].sum())
    uncaptured = float(sub["addressable_uncaptured_eur"].sum())
    gps_pct = round(genuine / wallet * 100, 1) if wallet else 0.0
    return {
        "year": year,
        "theoretical_wallet_eur": round(wallet, 0),
        "captured_genuine_eur": round(genuine, 0),
        "captured_bvp_eur": round(bvp, 0),
        "addressable_uncaptured_eur": round(uncaptured, 0),
        "gps_pct": gps_pct,
        "waterfall": [
            {"label": "Theoretical wallet", "value": round(wallet, 0), "type": "total"},
            {"label": "Captured genuine", "value": round(-genuine, 0), "type": "decrease"},
            {"label": "Captured BVP", "value": round(-bvp, 0), "type": "decrease"},
            {"label": "Addressable gap", "value": round(uncaptured, 0), "type": "remainder"},
        ],
        "top_gaps": [
            {
                "distributor_code": str(r["distributor_code"]),
                "country": str(r["country"]),
                "addressable_uncaptured_eur": round(float(r["addressable_uncaptured_eur"]), 0),
                "gps_pct": round(float(r["gps_pct"]), 1),
            }
            for _, r in sub.sort_values("addressable_uncaptured_eur", ascending=False).head(8).iterrows()
        ],
    }


def _defection_summary() -> dict:
    df = pd.read_csv(DEFECTION_CSV)
    active = df[(df["alert"] == True) & (df["level"] == "distributor")].copy()  # noqa: E712
    by_db = (
        active.groupby("distributor_code")
        .size()
        .reset_index(name="alert_count")
        .sort_values("alert_count", ascending=False)
    )
    top = []
    for _, r in by_db.head(10).iterrows():
        code = str(r["distributor_code"])
        cats = active[active["distributor_code"] == code]["pms_category"].tolist()[:4]
        top.append(
            {
                "distributor_code": code,
                "alert_count": int(r["alert_count"]),
                "categories": cats,
            }
        )
    return {
        "active_distributor_alerts": int(len(active)),
        "distributors_flagged": int(by_db.shape[0]),
        "top": top,
    }


def _substitution_families(year: int, top_n: int = 8) -> list[dict]:
    df = pd.read_csv(SUBSTITUTION_CSV)
    sub = df[df["year"] == year].copy()
    if sub.empty:
        return []
    fam = (
        sub.groupby("product_family")
        .agg(
            genuine_share=("genuine_unit_share", "mean"),
            bvp_units=("bvp_units", "sum"),
            genuine_units=("genuine_units", "sum"),
        )
        .reset_index()
    )
    fam = fam[fam["bvp_units"] > 0].sort_values("genuine_share").head(top_n)
    series: dict[str, list] = {}
    for fam_name in fam["product_family"].unique():
        chunk = df[(df["product_family"] == fam_name) & (df["year"].isin([year - 2, year - 1, year]))]
        by_year = chunk.groupby("year")["genuine_unit_share"].mean()
        series[str(fam_name)] = [
            {"year": int(y), "genuine_share_pct": round(float(by_year.get(y, 0)) * 100, 1)}
            for y in sorted(by_year.index)
        ]
    return [
        {
            "family": str(r["product_family"]),
            "genuine_share_pct": round(float(r["genuine_share"]) * 100, 1),
            "bvp_units": int(r["bvp_units"]),
            "series": series.get(str(r["product_family"]), []),
        }
        for _, r in fam.iterrows()
    ]


def _aim_gps_motion(latest_year: int) -> dict:
    df = pd.read_csv(AIM_GPS_MATRIX_CSV)
    prev = latest_year - 1
    cur = df[df["year"] == latest_year].copy()
    prior = df[df["year"] == prev][["distributor_code", "gps_spu_eur", "aim_high_risk_pct"]]
    merged = cur.merge(prior, on="distributor_code", how="left", suffixes=("", "_prev"))
    points = []
    for _, r in merged.iterrows():
        if pd.isna(r.get("gps_spu_eur")) or float(r.get("uio_units") or 0) <= 0:
            continue
        points.append(
            {
                "distributor_code": str(r["distributor_code"]),
                "region": str(r.get("region", "")),
                "quadrant": str(r.get("quadrant", "")),
                "quadrant_label": str(r.get("quadrant_label", "")),
                "gps_spu_eur": round(float(r["gps_spu_eur"]), 1),
                "aim_high_risk_pct": round(float(r["aim_high_risk_pct"]) * 100, 2)
                if float(r["aim_high_risk_pct"]) <= 1
                else round(float(r["aim_high_risk_pct"]), 2),
                "gps_spu_prev": round(float(r["gps_spu_eur_prev"]), 1)
                if pd.notna(r.get("gps_spu_eur_prev"))
                else None,
                "aim_prev": round(float(r["aim_high_risk_pct_prev"]) * 100, 2)
                if pd.notna(r.get("aim_high_risk_pct_prev")) and float(r["aim_high_risk_pct_prev"]) <= 1
                else (
                    round(float(r["aim_high_risk_pct_prev"]), 2)
                    if pd.notna(r.get("aim_high_risk_pct_prev"))
                    else None
                ),
                "color": QUADRANT_COLORS.get(str(r.get("quadrant", "")), "#7A8FA6"),
            }
        )
    counts = cur["quadrant"].value_counts().to_dict()
    return {"year": latest_year, "quadrant_counts": counts, "points": points}


def _pms_bubbles(year: int, top_n: int = 20) -> list[dict]:
    df = pd.read_csv(PMS_OPP_CSV)
    sub = df[(df["year"] == year) & (df["revenue_gap_eur"] > 0)].copy()
    sub = sub.sort_values("revenue_gap_eur", ascending=False).head(top_n)
    return [
        {
            "distributor_code": str(r["distributor_code"]),
            "category": str(r["pms_category"]),
            "capture_pct": round(float(r["capture_rate_total"]) * 100, 1),
            "revenue_gap_eur": round(float(r["revenue_gap_eur"]), 0),
            "tam_eur": round(float(r["tam_eur"]), 0),
            "region": str(r.get("region", "")),
        }
        for _, r in sub.iterrows()
    ]


def _null_nan(obj):
    if isinstance(obj, dict):
        return {k: _null_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_null_nan(v) for v in obj]
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj


def _finite_or_none(x) -> float | None:
    if x is None or pd.isna(x):
        return None
    return float(x)


def _gbp_to_eur(gbp: float | None) -> float | None:
    if gbp is None or pd.isna(gbp) or gbp <= BOGUS_GBP_CEILING:
        return None
    return round(float(gbp) * GBP_TO_EUR, 2)


def _mask_pn(pn: str) -> str:
    s = str(pn).strip()
    return f"…{s[-4:]}" if len(s) >= 4 else s


def _competitive_fusion(top_n: int = 18) -> dict:
    if not AUTODOC_CSV.exists() or not KS_CSV.exists():
        return {"available": False, "reason": "scraper CSV missing", "items": []}
    ad = pd.read_csv(AUTODOC_CSV)
    ks = pd.read_csv(KS_CSV)
    merged = ad.merge(
        ks[
            [
                "PN",
                "KS_AM_MinPrice_GBP",
                "KS_GEN_MinPrice_GBP",
                "Status",
            ]
        ],
        on="PN",
        how="left",
        suffixes=("_ad", "_ks"),
    )
    merged["Rev_CY2025_EUR"] = pd.to_numeric(merged["Rev_CY2025_EUR"], errors="coerce").fillna(0)
    merged["PR00_EUR"] = pd.to_numeric(merged["PR00_EUR"], errors="coerce")
    merged["autodoc_eur"] = merged["Autodoc_MinPrice_GBP"].apply(_gbp_to_eur)
    merged["ks_am_eur"] = merged["KS_AM_MinPrice_GBP"].apply(_gbp_to_eur)
    merged["ks_gen_eur"] = merged["KS_GEN_MinPrice_GBP"].apply(_gbp_to_eur)
    merged = merged[merged["Rev_CY2025_EUR"] > 0].copy()
    merged = merged.sort_values("Rev_CY2025_EUR", ascending=False).head(top_n * 2)
    items: list[dict] = []
    for _, r in merged.iterrows():
        pr00 = _finite_or_none(r["PR00_EUR"])
        ad_e = _finite_or_none(r["autodoc_eur"])
        ks_a = _finite_or_none(r["ks_am_eur"])
        ks_g = _finite_or_none(r["ks_gen_eur"])
        if pr00 is None:
            continue
        market = [x for x in (ad_e, ks_a, ks_g) if x is not None]
        if not market:
            continue
        min_market = min(market)
        items.append(
            {
                "pn_mask": _mask_pn(r["PN"]),
                "description": str(r.get("Description", ""))[:40],
                "aim_class": str(r.get("Class", "")),
                "rev_cy2025_eur": round(float(r["Rev_CY2025_EUR"]), 0),
                "pr00_eur": round(pr00, 2),
                "autodoc_eur": round(ad_e, 2) if ad_e is not None else None,
                "ks_am_eur": round(ks_a, 2) if ks_a is not None else None,
                "ks_gen_eur": round(ks_g, 2) if ks_g is not None else None,
                "min_market_eur": round(min_market, 2),
                "iam_discount_pct": round((1 - min_market / pr00) * 100, 1) if pr00 > 0 else None,
            }
        )
        if len(items) >= top_n:
            break
    ad_scraped = str(ad["Scraped_At"].iloc[0]) if len(ad) else ""
    ks_scraped = str(ks["Scraped_At"].iloc[0]) if len(ks) else ""
    stale = None
    try:
        from datetime import date
        ad_dt = pd.to_datetime(ad_scraped, errors="coerce")
        if pd.notna(ad_dt):
            stale = (date.today() - ad_dt.date()).days
    except Exception:
        pass
    return {
        "available": len(items) > 0,
        "autodoc_scraped_at": ad_scraped,
        "ks_scraped_at": ks_scraped,
        "scrape_stale_days": stale,
        "gbp_eur": GBP_TO_EUR,
        "bogus_filter_gbp": BOGUS_GBP_CEILING,
        "items": items,
    }


def _tender_horizon(horizon_days: int = 90, top_n: int = 30) -> dict:
    if not TENDER_JSON.exists():
        return {"available": False, "reason": "tender_data.json missing", "items": []}
    raw = json.loads(TENDER_JSON.read_text(encoding="utf-8"))
    meta = raw.get("meta", {})
    opps = raw.get("opportunities", [])
    items: list[dict] = []
    for o in opps:
        decision = str(o.get("decision", ""))
        if decision not in ("Attack", "Selective"):
            continue
        days = o.get("days_to_deadline")
        if days is None:
            continue
        if int(days) < -14 or int(days) > horizon_days:
            continue
        title = str(o.get("title", ""))
        if len(title) > 72:
            title = title[:69] + "…"
        items.append(
            {
                "title": title,
                "country": str(o.get("country", "")),
                "deadline_date": str(o.get("deadline_date", "")),
                "days_to_deadline": int(days),
                "opportunity_score": int(o.get("opportunity_score", 0) or 0),
                "decision": decision,
                "lifecycle": str(o.get("lifecycle", "")),
            }
        )
    items.sort(key=lambda x: (-x["opportunity_score"], x["days_to_deadline"]))
    items = items[:top_n]
    gen = meta.get("generated_at", "")[:10]
    stale_days = None
    if gen:
        try:
            gen_dt = datetime.strptime(gen, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            stale_days = (datetime.now(timezone.utc) - gen_dt).days
        except ValueError:
            pass
    stats = meta.get("stats", {})
    return {
        "available": len(items) > 0,
        "generated_at": gen,
        "stale_days": stale_days,
        "stats": {
            "opportunities": stats.get("opportunities"),
            "attack": stats.get("attack"),
            "selective": stats.get("selective"),
            "due_14d": stats.get("due_14d"),
        },
        "horizon_days": horizon_days,
        "items": items,
    }


def _network_bump(latest_year: int, top_n: int = 12) -> dict:
    df = pd.read_csv(NETWORK_PCT_CSV)
    metrics = [
        ("gps_spu", "GPS €/UIO"),
        ("total_capture", "PMS capture %"),
        ("genuine_capture", "Genuine capture %"),
        ("aim_risk", "AIM safety (inverted)"),
    ]
    years = sorted(df["year"].unique())
    years = [y for y in years if y <= latest_year][-3:]
    # Score distributors on latest year average percentile
    latest = df[df["year"] == latest_year]
    pivot = latest.pivot_table(
        index="distributor_code", columns="metric", values="percentile_rank", aggfunc="first"
    )
    pivot["avg_pct"] = pivot.mean(axis=1, skipna=True)
    top_dbs = pivot.sort_values("avg_pct", ascending=False).head(top_n).index.tolist()
    series: list[dict] = []
    for metric_id, metric_label in metrics:
        lines = []
        for db in top_dbs:
            pts = []
            for y in years:
                row = df[(df["distributor_code"] == db) & (df["year"] == y) & (df["metric"] == metric_id)]
                if row.empty:
                    continue
                pct = float(row.iloc[0]["percentile_rank"])
                if pd.isna(pct):
                    continue
                if metric_id == "aim_risk":
                    pct = 100.0 - pct
                rank = int(round(100 - pct)) + 1
                pts.append({"year": int(y), "percentile": round(pct, 1), "rank": rank})
            if pts:
                lines.append({"distributor_code": db, "points": pts})
        series.append({"metric_id": metric_id, "label": metric_label, "lines": lines})
    return {"years": [int(y) for y in years], "top_distributors": top_dbs, "metrics": series}


def build_payload(force: bool = False) -> dict:
    _require_verify_ok(force)
    year = int(pd.read_csv(WALLET_CSV)["year"].max())
    wallet = _wallet_network(year)
    defection = _defection_summary()
    substitution = _substitution_families(year)
    aim_gps = _aim_gps_motion(year)
    pms_bubbles = _pms_bubbles(year)
    competitive = _competitive_fusion()
    tender = _tender_horizon()
    network_bump = _network_bump(year)

    verify_ok = False
    if REPORT_JSON.exists():
        verify_ok = bool(json.loads(REPORT_JSON.read_text(encoding="utf-8")).get("summary", {}).get("ok"))

    sources = [
                "wallet_waterfall.csv",
                "defection_alerts.csv",
                "substitution_timeline.csv",
                "aim_gps_matrix.csv",
                "pms_opportunity_matrix.csv",
                "network_percentile.csv",
                "autodoc_results.csv",
                "ks_results.csv",
                "tender_data.json",
            ]

    return {
        "_meta": {
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "year": year,
            "verification_ok": verify_ok,
            "sources": sources,
        },
        "headline": {
            "addressable_gap_eur": wallet["addressable_uncaptured_eur"],
            "network_gps_pct": wallet["gps_pct"],
            "active_defection_alerts": defection["active_distributor_alerts"],
            "substitution_families_at_risk": len(substitution),
            "grow_capture_count": int(aim_gps["quadrant_counts"].get("grow_capture", 0)),
            "defend_count": int(aim_gps["quadrant_counts"].get("defend", 0)),
            "competitive_pn_tracked": len(competitive.get("items", [])),
            "tender_pipeline_90d": len(tender.get("items", [])),
            "tender_stale_days": tender.get("stale_days"),
        },
        "wallet": wallet,
        "defection": defection,
        "substitution": substitution,
        "aim_gps": aim_gps,
        "pms_opportunity": pms_bubbles,
        "competitive_fusion": competitive,
        "tender_horizon": tender,
        "network_bump": network_bump,
    }


def write_payload(payload: dict) -> None:
    """Write the JSON and embedded-JS variants from one serialization."""
    serialized = json.dumps(_null_nan(payload), ensure_ascii=False, indent=2, allow_nan=False)
    VIZ_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(serialized, encoding="utf-8")
    OUT_JS.parent.mkdir(parents=True, exist_ok=True)
    OUT_JS.write_text(
        "/* Generated by build_risk_cockpit_viz.py — do not edit */\n"
        "window.__RISK_COCKPIT_DATA__ = "
        + serialized
        + ";\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build risk_cockpit.json for static HTML")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    payload = build_payload(force=args.force)
    write_payload(payload)
    h = payload["headline"]
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_JS}")
    print(
        f"  {payload['_meta']['year']}: gap €{h['addressable_gap_eur']:,.0f} | "
        f"GPS {h['network_gps_pct']}% | defection alerts {h['active_defection_alerts']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
