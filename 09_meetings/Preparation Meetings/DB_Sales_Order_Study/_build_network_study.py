# -*- coding: utf-8 -*-
"""
Resumable all-DB Sales/Order hierarchy study.

Usage:
  python _build_network_study.py --resume
  python _build_network_study.py --only IUK,ITUK
  python _build_network_study.py --from-db UTI
  python _build_network_study.py --rebuild-hub
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow.dataset as ds

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PACKS = OUT / "packs"
STATE = OUT / "study_state.json"
PARQUET = ROOT / "01_data" / "00_derived" / "sales_fact.parquet"
SAP_MAP = ROOT / "03_analytics" / "Isuzu" / "prism" / "data" / "sap_sold_to_mapping.csv"
GPS = ROOT / "01_data" / "00_derived" / "gps_spu_by_distributor.csv"
PMS = ROOT / "03_analytics" / "Isuzu" / "prism" / "evidence-app" / "data" / "derived" / "pms_summary_by_db.csv"
PMS_CAP = ROOT / "03_analytics" / "Isuzu" / "prism" / "evidence-app" / "data" / "derived" / "pms_capture_by_db_year.csv"
MIX = ROOT / "03_analytics" / "Isuzu" / "prism" / "evidence-app" / "data" / "derived" / "db_parts_mix_classification.csv"
MASTER = ROOT / "03_analytics" / "Isuzu" / "prism" / "data" / "distributor_master_mapping.csv"
SEED = ROOT / "09_meetings" / "Preparation Meetings" / "Imotors_UMI_Sales_Study" / "study_data.json"

FYS = [2024, 2025]
SEED_CODES = {"PORTUGAL", "UMI"}


def _money(x) -> float:
    return round(float(x or 0), 2)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state() -> dict:
    return json.loads(STATE.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    state["updated"] = now_iso()
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def load_sales() -> pd.DataFrame:
    sap = pd.read_csv(SAP_MAP).rename(columns={"sap_sold_to_pt": "sold_to_sap"})
    sap["sold_to_sap"] = pd.to_numeric(sap["sold_to_sap"], errors="coerce")
    keep = [
        "billing_date",
        "sold_to_sap",
        "part_number",
        "description",
        "billed_qty",
        "net_sales_value",
        "saty",
        "year",
        "fig_key",
    ]
    df = ds.dataset(PARQUET).to_table(columns=keep).to_pandas()
    df["billing_date"] = pd.to_datetime(df["billing_date"])
    df["month"] = df["billing_date"].dt.month
    df["year"] = df["billing_date"].dt.year
    df["fiscal_year"] = df.apply(
        lambda r: int(r["year"]) if int(r["month"]) >= 4 else int(r["year"]) - 1, axis=1
    )
    df["sold_to_sap"] = pd.to_numeric(df["sold_to_sap"], errors="coerce")
    df = df.merge(sap[["sold_to_sap", "distributor_code"]], on="sold_to_sap", how="left")
    df["part_number"] = df["part_number"].astype(str).str.strip()
    df["description"] = df["description"].fillna("").astype(str)
    df["saty"] = df["saty"].fillna("(blank)").astype(str)
    df["fig_key"] = df["fig_key"].fillna("(none)").astype(str)
    return df


def label_for(code: str, master: pd.DataFrame) -> str:
    hit = master.loc[master["distributor_code"] == code]
    if len(hit):
        le = str(hit.iloc[0].get("legal_entity") or code)
        country = str(hit.iloc[0].get("country") or "")
        return f"{le} ({country})" if country else le
    return code


def build_db(df: pd.DataFrame, code: str, master: pd.DataFrame) -> dict:
    g = df[df["distributor_code"] == code].copy()
    sap_codes = sorted(
        {
            int(x)
            for x in df.loc[df["distributor_code"] == code, "sold_to_sap"].dropna().unique().tolist()
        }
    )
    fy_totals = {}
    for fy, sub in g.groupby("fiscal_year"):
        fy_totals[str(int(fy))] = {
            "sales_eur": _money(sub["net_sales_value"].sum()),
            "qty": _money(sub["billed_qty"].sum()),
            "lines": int(len(sub)),
            "distinct_pn": int(sub["part_number"].nunique()),
            "months": int(sub["billing_date"].dt.to_period("M").nunique()),
            "date_min": str(sub["billing_date"].min().date()) if len(sub) else None,
            "date_max": str(sub["billing_date"].max().date()) if len(sub) else None,
        }

    sub = g[g["fiscal_year"].isin(FYS)].copy()
    sub["ym"] = sub["billing_date"].dt.to_period("M").astype(str)
    monthly = (
        sub.groupby(["fiscal_year", "ym"], as_index=False)
        .agg(sales_eur=("net_sales_value", "sum"), qty=("billed_qty", "sum"), lines=("part_number", "size"))
        .sort_values("ym")
    )
    monthly_rows = [
        {
            "fiscal_year": int(r.fiscal_year),
            "ym": r.ym,
            "sales_eur": _money(r.sales_eur),
            "qty": _money(r.qty),
            "lines": int(r.lines),
        }
        for r in monthly.itertuples()
    ]

    by_saty = []
    saty = (
        sub.groupby(["fiscal_year", "saty"], as_index=False)
        .agg(sales_eur=("net_sales_value", "sum"), qty=("billed_qty", "sum"), lines=("part_number", "size"))
        .sort_values(["fiscal_year", "sales_eur"], ascending=[True, False])
    )
    for fy, chunk in saty.groupby("fiscal_year"):
        tot = float(chunk["sales_eur"].sum()) or 1.0
        for r in chunk.itertuples():
            by_saty.append(
                {
                    "fiscal_year": int(fy),
                    "saty": r.saty,
                    "sales_eur": _money(r.sales_eur),
                    "share_pct": round(100 * float(r.sales_eur) / tot, 2),
                    "qty": _money(r.qty),
                    "lines": int(r.lines),
                }
            )

    desc = (
        sub.groupby("part_number")["description"]
        .agg(lambda s: s.value_counts().index[0] if len(s) else "")
        .to_dict()
    )
    top_pn = []
    pn = (
        sub.groupby(["fiscal_year", "part_number"], as_index=False)
        .agg(sales_eur=("net_sales_value", "sum"), qty=("billed_qty", "sum"), lines=("part_number", "size"))
        .sort_values(["fiscal_year", "sales_eur"], ascending=[True, False])
    )
    for fy, chunk in pn.groupby("fiscal_year"):
        tot = float(chunk["sales_eur"].sum()) or 1.0
        for i, r in enumerate(chunk.head(40).itertuples(), 1):
            top_pn.append(
                {
                    "fiscal_year": int(fy),
                    "rank": i,
                    "part_number": r.part_number,
                    "description": str(desc.get(r.part_number, ""))[:80],
                    "sales_eur": _money(r.sales_eur),
                    "share_pct": round(100 * float(r.sales_eur) / tot, 2),
                    "qty": _money(r.qty),
                    "lines": int(r.lines),
                }
            )

    a = g[g["fiscal_year"] == 2024].groupby("part_number")["net_sales_value"].sum()
    b = g[g["fiscal_year"] == 2025].groupby("part_number")["net_sales_value"].sum()
    both = pd.DataFrame({"fy_a": a, "fy_b": b}).fillna(0.0)
    both["delta"] = both["fy_b"] - both["fy_a"]
    desc_all = (
        g.groupby("part_number")["description"]
        .agg(lambda s: s.value_counts().index[0] if len(s) else "")
        .to_dict()
    )

    def pack_movers(series: pd.Series) -> list:
        out = []
        for pn_code, delta in series.items():
            out.append(
                {
                    "part_number": pn_code,
                    "description": str(desc_all.get(pn_code, ""))[:80],
                    "fy_a_eur": _money(both.loc[pn_code, "fy_a"]),
                    "fy_b_eur": _money(both.loc[pn_code, "fy_b"]),
                    "delta_eur": _money(delta),
                }
            )
        return out

    def concentration(fy: int) -> dict:
        s = g[g["fiscal_year"] == fy]
        by = s.groupby("part_number")["net_sales_value"].sum().sort_values(ascending=False)
        tot = float(by.sum()) or 1.0
        cum = by.cumsum() / tot
        return {
            "fiscal_year": fy,
            "top10_share_pct": round(100 * float(by.head(10).sum()) / tot, 2),
            "top25_share_pct": round(100 * float(by.head(25).sum()) / tot, 2),
            "top50_share_pct": round(100 * float(by.head(50).sum()) / tot, 2),
            "pn_for_80pct": int((cum <= 0.80).sum() + 1) if len(by) else 0,
            "distinct_pn": int(by.shape[0]),
        }

    # enrich GPS/PMS/mix
    gps_rows = []
    if GPS.exists():
        gps = pd.read_csv(GPS)
        for _, r in gps[(gps["distributor_code"] == code) & (gps["year"].isin([2024, 2025, 2026]))].iterrows():
            gps_rows.append(
                {
                    "year": int(r["year"]),
                    "sales_eur": _money(r["total_sales_eur"]),
                    "uio": float(r["uio_units"]) if pd.notna(r["uio_units"]) else None,
                    "spu": _money(r.get("spend_per_unit_eur") or 0),
                    "gps_capture_vs_max": None
                    if pd.isna(r.get("gps_capture_vs_max"))
                    else round(float(r["gps_capture_vs_max"]), 4),
                    "traffic_light": r.get("traffic_light"),
                }
            )
    pms_summary = []
    if PMS.exists():
        pms = pd.read_csv(PMS)
        for _, r in pms[(pms["distributor_code"] == code) & (pms["year"] == 2025)].iterrows():
            pms_summary.append(
                {
                    "year": 2025,
                    "capture_rate_total_wtd": round(float(r["capture_rate_total_wtd"]), 4),
                    "capture_rate_genuine_wtd": round(float(r["capture_rate_genuine_wtd"]), 4),
                    "revenue_gap_eur": _money(r["revenue_gap_eur_sum"]),
                    "oil_filter_capture": round(float(r["oil_filter_capture"]), 4),
                    "top_gap_categories": r["top_gap_categories"],
                }
            )
    pms_cats = []
    if PMS_CAP.exists():
        cap = pd.read_csv(PMS_CAP)
        for _, r in cap[
            (cap["distributor_code"] == code) & (cap["year"] == 2025) & (cap["line_type"] == "total")
        ].iterrows():
            pms_cats.append(
                {
                    "category": r["pms_category"],
                    "capture_rate": round(float(r["capture_rate"]), 4),
                    "revenue_gap_eur": _money(r["revenue_gap_eur"]),
                    "actual_rev_eur": _money(r["actual_rev_eur"]),
                }
            )
    mix_rows = []
    if MIX.exists():
        mix = pd.read_csv(MIX)
        for _, r in mix[(mix["distributor_code"] == code) & (mix["year"].isin([2024, 2025]))].iterrows():
            mix_rows.append(
                {
                    "year": int(r["year"]),
                    "total_eur": _money(r["total_eur"]),
                    "bvp_pct": round(100 * float(r["bvp_pct"]), 2),
                    "genuine_only_pct": round(100 * float(r["genuine_only_pct"]), 2),
                }
            )

    fy24 = fy_totals.get("2024", {}).get("sales_eur", 0) or 0
    fy25 = fy_totals.get("2025", {}).get("sales_eur", 0) or 0
    yoy = round(100 * (fy25 - fy24) / fy24, 1) if fy24 else None

    payload = {
        "key": code,
        "label": label_for(code, master),
        "distributor_code": code,
        "sap_sold_to": sap_codes,
        "billing_span": {
            "min": str(g["billing_date"].min().date()) if len(g) else None,
            "max": str(g["billing_date"].max().date()) if len(g) else None,
            "rows": int(len(g)),
        },
        "fy_totals": fy_totals,
        "fy_yoy_pct": yoy,
        "monthly": monthly_rows,
        "by_saty": by_saty,
        "top_pn": top_pn,
        "pn_movers_fy24_to_fy25": {
            "fy_from": 2024,
            "fy_to": 2025,
            "gainers": pack_movers(both["delta"].sort_values(ascending=False).head(20)),
            "losers": pack_movers(both["delta"].sort_values(ascending=True).head(20)),
        },
        "concentration": {"FY2024": concentration(2024), "FY2025": concentration(2025)},
        "gps": gps_rows,
        "pms_summary": pms_summary,
        "pms_categories_total": pms_cats,
        "mix": mix_rows,
        "pbi_h1": None,
        "notes": [],
    }
    if code == "UMI":
        payload["notes"].append("Do not blend with UTI. IDS Israel = UMI only.")
    if code == "UTI":
        payload["notes"].append("Separate from UMI. Not the IDS Israel counterpart.")
    if not len(g):
        payload["notes"].append("No rows in sales_fact for this distributor_code.")
    return payload


def link_seed_packs(state: dict) -> None:
    """Point PORTUGAL/UMI at seed without recomputing."""
    if not SEED.exists():
        return
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    PACKS.mkdir(parents=True, exist_ok=True)
    for db in seed.get("distributors", []):
        code = db["distributor_code"]
        out = PACKS / f"{code}.json"
        # Enrich with H1 PBI drills if present
        drills = seed.get("pbi_h1_2026", {}).get("drills", {})
        order = seed.get("pbi_h1_2026", {}).get("order", {})
        key = "IMOTORS" if code == "PORTUGAL" else ("UMI" if code == "UMI" else None)
        if key and key in drills:
            db = dict(db)
            db["pbi_h1"] = {
                "sales": drills[key],
                "order": order.get("customers", {}).get(key),
                "sales_vs_demand": order.get("sales_vs_demand", {}).get(key),
                "period": seed["pbi_h1_2026"]["period"],
                "source": seed["pbi_h1_2026"]["source"],
            }
        out.write_text(json.dumps(db, indent=2), encoding="utf-8")
        for row in state["dbs"]:
            if row["code"] == code:
                row["status"] = "complete_seed"
                row["pack"] = str(out.relative_to(OUT)).replace("\\", "/")
                row["completed_at"] = row.get("completed_at") or now_iso()
                row["seed_pack"] = "../Imotors_UMI_Sales_Study"


def select_targets(state: dict, args) -> list[str]:
    codes = [d["code"] for d in state["dbs"]]
    if args.only:
        want = [c.strip().upper() for c in args.only.split(",") if c.strip()]
        return [c for c in codes if c in want]
    if args.from_db:
        start = args.from_db.strip().upper()
        if start not in codes:
            raise SystemExit(f"--from-db {start} not in rank list")
        codes = codes[codes.index(start) :]
    out = []
    for d in state["dbs"]:
        if d["code"] not in codes:
            continue
        if args.force or args.force_seed:
            if d["code"] in SEED_CODES and not args.force_seed and not args.force:
                continue
            out.append(d["code"])
            continue
        if d["status"] in ("complete", "complete_seed"):
            continue
        out.append(d["code"])
    return out


def write_network_summary(state: dict) -> Path:
    packs = []
    for d in state["dbs"]:
        p = PACKS / f"{d['code']}.json"
        if p.exists():
            packs.append(json.loads(p.read_text(encoding="utf-8")))
    summary = {
        "generated": now_iso(),
        "fiscal_definition": "ISZE FY = Apr–Mar. FY2024=Apr2024–Mar2025; FY2025=Apr2025–Mar2026.",
        "billing_max": state.get("billing_max"),
        "rank_basis": state.get("rank_basis"),
        "dbs": [],
    }
    for d in state["dbs"]:
        pack = next((p for p in packs if p["distributor_code"] == d["code"]), None)
        row = {
            "rank": d["rank"],
            "code": d["code"],
            "status": d["status"],
            "cy2025_proxy": d.get("fy_proxy_cy2025_sales"),
        }
        if pack:
            row["label"] = pack.get("label")
            row["fy2024"] = pack.get("fy_totals", {}).get("2024", {}).get("sales_eur")
            row["fy2025"] = pack.get("fy_totals", {}).get("2025", {}).get("sales_eur")
            row["fy_yoy_pct"] = pack.get("fy_yoy_pct")
            row["pms_total"] = (pack.get("pms_summary") or [{}])[0].get("capture_rate_total_wtd")
            row["pms_gap"] = (pack.get("pms_summary") or [{}])[0].get("revenue_gap_eur")
            row["top10_share"] = pack.get("concentration", {}).get("FY2025", {}).get("top10_share_pct")
            row["rows"] = pack.get("billing_span", {}).get("rows")
        summary["dbs"].append(row)
    path = OUT / "network_summary.json"
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true", help="Process pending DBs only")
    ap.add_argument("--only", type=str, default="", help="Comma-separated codes")
    ap.add_argument("--from-db", type=str, default="", help="Start from this ranked code")
    ap.add_argument("--force", action="store_true", help="Recompute even if complete (not seed unless forced)")
    ap.add_argument("--force-seed", action="store_true", help="Also recompute PORTUGAL/UMI from parquet")
    ap.add_argument("--rebuild-hub", action="store_true", help="Only refresh summary + state markers")
    ap.add_argument("--link-seed", action="store_true", default=True)
    args = ap.parse_args()
    if not args.resume and not args.only and not args.from_db and not args.rebuild_hub:
        args.resume = True

    PACKS.mkdir(parents=True, exist_ok=True)
    state = load_state()

    if args.link_seed and not args.force_seed:
        link_seed_packs(state)
        save_state(state)

    if args.rebuild_hub:
        write_network_summary(state)
        print("hub summary refreshed")
        return

    targets = select_targets(state, args)
    print(f"targets ({len(targets)}):", targets)
    if not targets:
        write_network_summary(state)
        print("nothing to do")
        return

    print("loading sales_fact…")
    df = load_sales()
    master = pd.read_csv(MASTER) if MASTER.exists() else pd.DataFrame(columns=["distributor_code", "legal_entity", "country"])
    state["billing_max"] = str(df["billing_date"].max().date())

    completed = []
    for code in targets:
        print(f"=== {code}")
        # mark in_progress
        for row in state["dbs"]:
            if row["code"] == code:
                row["status"] = "in_progress"
                row["started_at"] = now_iso()
        save_state(state)

        pack = build_db(df, code, master)
        out = PACKS / f"{code}.json"
        text = json.dumps(pack, indent=2)
        out.write_text(text, encoding="utf-8")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]

        for row in state["dbs"]:
            if row["code"] == code:
                row["status"] = "complete"
                row["pack"] = str(out.relative_to(OUT)).replace("\\", "/")
                row["completed_at"] = now_iso()
                row["sha256_12"] = digest
                row["rows"] = pack["billing_span"]["rows"]
                row["fy2025"] = pack.get("fy_totals", {}).get("2025", {}).get("sales_eur")
                row["fy_yoy_pct"] = pack.get("fy_yoy_pct")
        state["last_completed"] = code
        save_state(state)
        completed.append(code)
        print(f"  wrote {out.name} rows={pack['billing_span']['rows']} fy25={pack.get('fy_totals',{}).get('2025',{}).get('sales_eur')}")

    write_network_summary(state)
    pending = [d["code"] for d in state["dbs"] if d["status"] == "pending"]
    print("DONE this run:", completed)
    print("remaining pending:", pending)


if __name__ == "__main__":
    main()
