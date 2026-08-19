#!/usr/bin/env python3
"""
DB→DLR commercial stack — replenishment + revision queue + elasticity (network).

Runs all three builds. Does NOT run +3% alloc or mutate pricing engine targets.

Outputs (01_data/00_derived/):
  replenishment_bridge.parquet          — network × PN × month
  replenishment_bridge_ituk_dealer.parquet
  replenishment_summary_cy2025.parquet  — network × PN annual + pipeline class
  replenishment_exceptions_cy2025.csv   — top leakage / overstock
  revision_exception_queue.csv          — PN × DB revision guardrails (no alloc)
  price_elasticity_db_dlr_network.csv   — ITUK + UTI + IRELAND + IUK proxies
  db_dlr_commercial_stack.meta.json

Legacy: still refreshes price_elasticity_db_dlr_ituk_uti.csv (ITUK+UTI subset).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import db_dlr_commercial_common as C  # noqa: E402

OUT_BRIDGE = C.DERIVED / "replenishment_bridge.parquet"
OUT_BRIDGE_DEALER = C.DERIVED / "replenishment_bridge_ituk_dealer.parquet"
OUT_SUMMARY = C.DERIVED / "replenishment_summary_cy2025.parquet"
OUT_REPL_EX = C.DERIVED / "replenishment_exceptions_cy2025.csv"
OUT_REVISION = C.DERIVED / "revision_exception_queue.csv"
OUT_ELASTIC = C.DERIVED / "price_elasticity_db_dlr_network.csv"
OUT_ELASTIC_LEGACY = C.DERIVED / "price_elasticity_db_dlr_ituk_uti.csv"
OUT_META = C.DERIVED / "db_dlr_commercial_stack.meta.json"
BUILDER_VERSION = "db-dlr-stack-v1"


def build_replenishment() -> dict:
    bridge_parts = []
    dealer_parts = []
    for db in C.NETWORK_DBS:
        bill_m = C.load_billing_monthly((db,), C.YEAR)
        sell_m = C.load_sellout_network_monthly(db, C.YEAR)
        if bill_m.empty and sell_m.empty:
            continue
        merged = bill_m.merge(
            sell_m,
            on=["distributor_code", "part_number", "year_month"],
            how="outer",
        )
        for col in ("bill_qty", "bill_eur", "sellout_qty"):
            if col in merged.columns:
                merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0)
        merged["grain"] = "network_pn"
        merged["dealer_name"] = ""
        merged["sell_through_ratio"] = np.where(
            merged["bill_qty"] > 0,
            merged["sellout_qty"] / merged["bill_qty"],
            np.nan,
        )
        merged["pipeline_signal"] = [
            C.classify_pipeline(b, s)
            for b, s in zip(merged["bill_qty"], merged["sellout_qty"])
        ]
        bridge_parts.append(merged)
        if db == "ITUK":
            _, dealer_m = C.load_ituk_sellout_monthly(C.YEAR)
            if not dealer_m.empty:
                d = dealer_m.merge(
                    bill_m,
                    on=["distributor_code", "part_number", "year_month"],
                    how="left",
                )
                d["bill_qty"] = pd.to_numeric(d.get("bill_qty"), errors="coerce").fillna(0)
                d["bill_eur"] = pd.to_numeric(d.get("bill_eur"), errors="coerce").fillna(0)
                d["sell_through_ratio"] = np.where(
                    d["bill_qty"] > 0,
                    d["sellout_qty"] / d["bill_qty"],
                    np.nan,
                )
                d["pipeline_signal"] = [
                    C.classify_pipeline(b, s)
                    for b, s in zip(d["bill_qty"], d["sellout_qty"])
                ]
                d["grain"] = "dealer_pn"
                dealer_parts.append(d)

    bridge = pd.concat(bridge_parts, ignore_index=True) if bridge_parts else pd.DataFrame()
    dealer = pd.concat(dealer_parts, ignore_index=True) if dealer_parts else pd.DataFrame()

    bill_a = C.load_billing_annual(C.NETWORK_DBS, C.YEAR)
    sell_a = pd.concat(
        [C.load_sellout_network_annual(db, C.YEAR) for db in C.NETWORK_DBS],
        ignore_index=True,
    )
    summary = bill_a.merge(sell_a, on=["distributor_code", "part_number"], how="outer")
    for col in ("bill_qty", "bill_eur", "sellout_qty"):
        summary[col] = pd.to_numeric(summary.get(col), errors="coerce").fillna(0)
    summary["sell_through_ratio"] = np.where(
        summary["bill_qty"] > 0,
        summary["sellout_qty"] / summary["bill_qty"],
        np.nan,
    )
    summary["pipeline_signal"] = [
        C.classify_pipeline(b, s) for b, s in zip(summary["bill_qty"], summary["sellout_qty"])
    ]
    summary["year"] = C.YEAR

    exc = summary[
        summary["pipeline_signal"].isin(
            ("leakage_high_sellthrough", "leakage_no_bill", "overstock_low_sellthrough", "overstock_no_sellout")
        )
    ].copy()
    exc["rank_key"] = np.where(
        exc["pipeline_signal"].str.startswith("leakage"),
        exc["sellout_qty"],
        exc["bill_qty"],
    )
    exc = exc.sort_values(["distributor_code", "pipeline_signal", "rank_key"], ascending=[True, True, False])
    exc = exc.groupby(["distributor_code", "pipeline_signal"]).head(100)

    if not bridge.empty:
        bridge.to_parquet(OUT_BRIDGE, index=False)
    if not dealer.empty:
        dealer.to_parquet(OUT_BRIDGE_DEALER, index=False)
    if not summary.empty:
        summary.to_parquet(OUT_SUMMARY, index=False)
    if not exc.empty:
        exc.to_csv(OUT_REPL_EX, index=False)

    return {
        "bridge_rows": int(len(bridge)),
        "dealer_rows": int(len(dealer)),
        "summary_rows": int(len(summary)),
        "exception_rows": int(len(exc)),
        "by_db": summary.groupby("distributor_code").size().to_dict() if not summary.empty else {},
    }


def _israel_note(db: str) -> str:
    if db == "UTI":
        return "UTI_only_not_UMI"
    if db == "IRELAND":
        return "IRELAND_not_IUK_not_IMIE"
    if db == "IUK":
        return "IUK_not_ITUK"
    if db == "GREECE":
        return "GREECE_Petros_network_pn"
    return ""


def _recommended_action(row: pd.Series, proxy_adverse: bool) -> str:
    if row.get("ks_has_quote") and pd.notna(row.get("ks_price_index")) and row["ks_price_index"] > 1.05:
        return "REVIEW_IAM_UNDERCUT"
    if proxy_adverse:
        return "REVIEW_PROXY_ADVERSE"
    sig = str(row.get("pipeline_signal") or "")
    if sig.startswith("leakage"):
        return "REVIEW_LEAKAGE"
    if sig.startswith("overstock"):
        return "REVIEW_OVERSTOCK"
    if row.get("ks_has_quote") and pd.notna(row.get("ks_price_index")) and row["ks_price_index"] < 0.95:
        return "RAISE_OK_ROOM_VS_IAM"
    if pd.notna(row.get("planned_sp_pct_chg_2025_2026")) and float(row["planned_sp_pct_chg_2025_2026"]) > 8:
        return "REVIEW_HIGH_LIST_EXPOSURE"
    return "HOLD_DEFAULT"


def build_revision_queue(summary: pd.DataFrame, elastic: pd.DataFrame) -> dict:
    cat_map = C.load_category_map()
    sim = C.load_sim_sp()
    ks = C.load_ks_pn_index()

    base = summary.copy()
    base["_pn"] = C.norm_pn(base["part_number"])
    base["category"] = base["_pn"].map(cat_map).fillna("AIM: Unclassified")

    adverse_cats = set()
    if not elastic.empty:
        m = (
            (elastic["measure_kind"] == "proxy")
            & (elastic["method"] == "cross_section_lnq_lnp_asp")
            & (pd.to_numeric(elastic["beta"], errors="coerce") < -0.5)
        )
        if "low_power" in elastic.columns:
            m &= ~elastic["low_power"].astype(str).str.lower().isin(("true", "1", "yes"))
        for _, r in elastic.loc[m].iterrows():
            adverse_cats.add((r["distributor_code"], r["category"]))

    list_exposure = {}
    if not elastic.empty:
        le = elastic[elastic["method"] == "list_shock_exposure_2025_2026"]
        for _, r in le.iterrows():
            list_exposure[(r["distributor_code"], r["category"])] = r.get(
                "sellout_wtd_sp_pct_chg_2025_2026"
            )

    q = base.merge(sim, on="part_number", how="left")
    q = q.merge(ks, on="part_number", how="left", suffixes=("", "_ks"))

    q["proxy_adverse"] = q.apply(
        lambda r: (r["distributor_code"], r["category"]) in adverse_cats,
        axis=1,
    )
    q["category_list_exposure_pct"] = q.apply(
        lambda r: list_exposure.get((r["distributor_code"], r["category"]), np.nan),
        axis=1,
    )
    q["recommended_action"] = q.apply(
        lambda r: _recommended_action(r, bool(r["proxy_adverse"])),
        axis=1,
    )
    q["flags"] = (
        "NO_ALLOC_RUN|planned_list_from_sim|ks_gbp_eur="
        + str(C.GBP_EUR)
        + "|reference_sellout_x"
        + str(C.STREET_FACTOR)
    )

    cols = [
        "distributor_code",
        "part_number",
        "category",
        "bill_qty",
        "bill_eur",
        "sellout_qty",
        "sell_through_ratio",
        "pipeline_signal",
        "planned_sp_pct_chg_2025_2026",
        "category_list_exposure_pct",
        "pr00_eur",
        "reference_sellout_eur",
        "shop_gbp",
        "ks_price_index",
        "ks_has_quote",
        "ks_status",
        "proxy_adverse",
        "recommended_action",
        "flags",
    ]
    cols = [c for c in cols if c in q.columns]
    out = q[cols].sort_values(
        ["distributor_code", "recommended_action", "sellout_qty"],
        ascending=[True, True, False],
    )
    out.to_csv(OUT_REVISION, index=False)
    return {
        "rows": int(len(out)),
        "action_counts": out["recommended_action"].value_counts().to_dict(),
        "ks_matched": int(out["ks_has_quote"].fillna(False).sum()) if "ks_has_quote" in out.columns else 0,
    }


def build_elasticity_network() -> tuple[pd.DataFrame, dict]:
    """Extend ITUK/UTI elasticity builder to IRELAND + IUK."""
    import build_price_elasticity_db_dlr_ituk_uti as el  # noqa: WPS433

    cat_map = el.category_map()
    rows_meta: dict = {"blocked_yoy": True}
    sell_parts = []

    for db in C.NETWORK_DBS:
        g = C.load_sellout_network_annual(db, C.YEAR)
        if g.empty:
            rows_meta[db.lower()] = {"error": f"no {db} sell-out"}
            continue
        g = g.rename(columns={"sellout_qty": "qty"})
        g["grain"] = "network_pn"
        g["source_file"] = f"commercial_stack_{db}"
        g["n_dealers"] = 0
        if db == "ITUK":
            C._ensure_prism()
            from modules.dealer_sales_loader import load_ituk_dealer_sales  # noqa: WPS433

            ituk = load_ituk_dealer_sales(C.YEAR)
            g["n_dealers"] = int(ituk["dealer_name"].nunique()) if not ituk.empty else 0
        sell_parts.append(g)
        rows_meta[db.lower()] = {
            "n_pn": int(g["part_number"].nunique()),
            "qty": float(g["qty"].sum()),
            "years": [C.YEAR],
            "grain_raw": "dealer_pn" if db == "ITUK" else "network_pn",
        }

    if not sell_parts:
        return pd.DataFrame(), rows_meta

    sell = pd.concat(sell_parts, ignore_index=True)
    sell["part_number"] = sell["part_number"].map(el.normalize_pn)
    sell = sell.dropna(subset=["part_number"])
    sell = sell[sell["qty"] > 0]

    asp = el.load_asp_cy(C.YEAR)
    asp = asp[asp["distributor_code"].isin(C.NETWORK_DBS)]
    sim = el.load_sim_sp()
    panel = sell.merge(asp, on=["distributor_code", "part_number"], how="left")
    panel = el.attach_category(panel, cat_map)

    rows: list[dict] = []
    for db in C.NETWORK_DBS:
        info = rows_meta.get(db.lower(), {})
        rows.append(
            {
                "distributor_code": db,
                "israel_note": _israel_note(db),
                "grain": "network_pn",
                "category": "(all)",
                "measure_kind": "blocked",
                "method": "yoy_arc_elasticity",
                "n_pns": info.get("n_pn", 0),
                "n_pairs": 0,
                "sellout_qty_total": info.get("qty", 0),
                "median_price_eur": "",
                "median_dlnp_pct": "",
                "beta": "",
                "se_beta": "",
                "r2": "",
                "low_power": True,
                "sellout_wtd_sp_pct_chg_2025_2026": "",
                "price_axis": "would need DB→DLR invoice or pass-through series across ≥2 CY",
                "volume_axis": "DB→DLR sell-out qty YoY (need ≥2 full CY)",
                "reading": "insufficient_sellout_years",
                "caveat": f"True arc elasticity blocked. Coverage: {info}.",
            }
        )
    rows.extend(el.proxy_cross_section(panel))
    rows.extend(el.proxy_list_exposure(panel, sim))

    out = pd.DataFrame(rows)
    cols = [
        "distributor_code",
        "israel_note",
        "grain",
        "category",
        "measure_kind",
        "method",
        "n_pns",
        "n_pairs",
        "sellout_qty_total",
        "median_price_eur",
        "median_dlnp_pct",
        "beta",
        "se_beta",
        "r2",
        "low_power",
        "sellout_wtd_sp_pct_chg_2025_2026",
        "price_axis",
        "volume_axis",
        "reading",
        "caveat",
    ]
    out = out[cols]
    out.to_csv(OUT_ELASTIC, index=False)
    legacy = out[out["distributor_code"].isin(("ITUK", "UTI"))]
    legacy.to_csv(OUT_ELASTIC_LEGACY, index=False)
    return out, rows_meta


def main() -> int:
    print("=== Phase 1: Replenishment bridge ===")
    repl_meta = build_replenishment()
    print(repl_meta)

    summary = pd.read_parquet(OUT_SUMMARY) if OUT_SUMMARY.exists() else pd.DataFrame()

    print("\n=== Phase 3: Elasticity network (before revision queue needs it) ===")
    elastic, el_meta = build_elasticity_network()
    print(f"elasticity rows={len(elastic)} dbs={C.NETWORK_DBS}")

    print("\n=== Phase 2: Revision exception queue (no +3% alloc) ===")
    rev_meta = build_revision_queue(summary, elastic)
    print(rev_meta)

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "builder_version": BUILDER_VERSION,
        "year": C.YEAR,
        "distributors": list(C.NETWORK_DBS),
        "no_alloc_run": True,
        "replenishment": repl_meta,
        "revision_queue": rev_meta,
        "elasticity_dbs": el_meta,
        "outputs": {
            "replenishment_bridge": str(OUT_BRIDGE.relative_to(C.ISZE_ROOT)),
            "replenishment_bridge_ituk_dealer": str(OUT_BRIDGE_DEALER.relative_to(C.ISZE_ROOT)),
            "replenishment_summary": str(OUT_SUMMARY.relative_to(C.ISZE_ROOT)),
            "replenishment_exceptions": str(OUT_REPL_EX.relative_to(C.ISZE_ROOT)),
            "revision_exception_queue": str(OUT_REVISION.relative_to(C.ISZE_ROOT)),
            "price_elasticity_db_dlr_network": str(OUT_ELASTIC.relative_to(C.ISZE_ROOT)),
            "price_elasticity_db_dlr_ituk_uti_legacy": str(OUT_ELASTIC_LEGACY.relative_to(C.ISZE_ROOT)),
        },
        "notes": [
            "Revision queue uses planned SP % from pricing_sim_pr00_l12m — not an alloc run.",
            "KS price index = min(AM,GEN) shop GBP × gbp_eur / (PR00 × 1.785).",
            "UTI ≠ UMI; IUK ≠ ITUK; IRELAND ≠ IUK.",
            "Elasticity rows remain measure_kind=proxy until second full CY sell-out.",
        ],
    }
    with open(OUT_META, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    print(f"\nwrote meta -> {OUT_META}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
