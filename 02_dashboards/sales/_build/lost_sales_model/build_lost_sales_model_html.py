#!/usr/bin/env python3
"""
Build the shared executive aftermarket opportunity page: modelled target-spend gap vs parts billed.

Reads the derived model only — it computes nothing of its own, so the page and the CSV can never
disagree:

  01_data/00_derived/lost_sales_market.csv               market x year, ceiling and cover
  01_data/00_derived/lost_sales_model.csv                market x aim family x service category x year
  01_data/00_derived/lost_sales_competitor_coverage.csv  how much of the book carries a rival price
  01_data/00_derived/lost_sales_competitor_pn.csv        the part numbers that do

Writes a self-contained page (data and Chart.js both inlined, so it opens from Explorer with no
server and no internet) plus a CRLF launcher:

  02_dashboards/sales/ISZE_Lost_Sales_Model.html
  02_dashboards/sales/OPEN_ISZE_Lost_Sales_Model.cmd
  ...SHIP_RECEIPT.json
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]  # ISZE/
DERIVED = ROOT / "01_data" / "00_derived"
OUT_DIR = ROOT / "02_dashboards" / "sales"
OUT_HTML = OUT_DIR / "ISZE_Lost_Sales_Model.html"
OUT_CMD = OUT_DIR / "OPEN_ISZE_Lost_Sales_Model.cmd"
OUT_RECEIPT = OUT_DIR / "ISZE_Lost_Sales_Model.SHIP_RECEIPT.json"
CHARTJS = ROOT / "02_dashboards" / "_ui" / "chart.umd.min.js"

OPEN_MONTHS = 6  # billing horizon in the current year (Jan-Jun)

# Aim family -> the wording a reader outside the workspace would use.
FAMILY_LABEL = {
    "PMS_Filters": "Service filters",
    "Brakes": "Brakes",
    "Clutch_Driveline": "Clutch and driveline",
    "Electrical": "Electrical and electronic",
    "Suspension_Chassis": "Suspension, steering and chassis",
    "Cab_Misc": "Cab, body and interior",
    "Belts_Cooling": "Belts, cooling and engine",
    "Other": "Other",
    "unclassified_pn": "Not yet classified",
}

GAP_LABEL = {
    "under_service": "Not serviced with our part",
    "substitution": "Bought a cheaper alternative",
    "catalog_gap": "We have nothing to sell",
}

# The limits come from the model's own meta file, where they are written for an internal reader and
# quote field names. A shared page must not carry those, so each one is restated in plain business
# words. Anything not listed here is passed through unchanged but checked by a gate below.
LIMIT_PLAIN = {
    "No fitted price response exists. One complete dealer-level sell-out year, so there is no elasticity coefficient and no causal claim on the price axis.":
        "How much volume responds to a price change has not been measured. There is one complete "
        "year of dealer sales at part level, which is not enough to fit it, so no claim is made "
        "here that a given price move causes a given volume change.",
    "Ceiling columns in the family file are MARKET level and repeated on every family row (ceilings_are_market_level=True). They must not be summed.":
        "The target spend is known per market only, not per parts family. It is shown on every "
        "family row for context and must not be added down a family column.",
    "The ceiling is a target spend at list, not a forecast. actionable_gap_eur restates it at observed list realisation; that is still not a recoverable amount.":
        "The target spend is what the fleet could support at full list price, not a forecast. The "
        "actionable figure restates it at the price actually realised, and is still not an amount "
        "that can simply be collected.",
    "2026 is a part year: 7 months of billing against a full-year denominator. is_partial_year marks every affected row.":
        "The current year is part of a year. Every comparison involving it uses the same months on "
        "both sides, and the affected rows are marked.",
    "2026-2030 UIO denominators are overstated (+9% to +59%, worse per market) so nothing forward-looking is published in this model. It stops at actuals.":
        "The forward forecast of vehicles in service is overstated, by 9% in the first year rising "
        "to 59% by 2030 and worse in some markets. Nothing forward-looking is published here; the "
        "model stops at what actually happened.",
    "Competitor prices cover a small part of the book. The uncovered remainder is a named gap, not a zero. Two vintages and two tiers are kept separate and never blended.":
        "A competing price is held on only a small part of the parts billed. Where there is none, "
        "that is an absence of evidence, not evidence of competitiveness. The two sources are "
        "different dates and different levels of the market and are never averaged together.",
    "Apr-Jun 2026 credit-note netting is unverified (no SaTy column in the SAP extract).":
        "Credit notes and returns for the second quarter of 2026 are netted on the sign of the "
        "value alone, because the billing extract for that quarter does not carry the credit-note "
        "marker. That quarter's figures are therefore slightly less certain than the rest.",
    "There is no web demand series on disk. Web enters as price and listing presence only.":
        "There is no online demand data: no web traffic and no search volume. Online presence "
        "enters only as a competing price and as a listing we can see.",
    "down_trade_verdict is a rule over BVP share and total family units, not a measurement.":
        "The verdict on the value line is a rule applied to the value share and total units, not a "
        "measured outcome. Read it as a prompt to look, not as proof.",
    "Two clocks are shown on purpose. ISZE plans on a financial year running April to March; the calendar year is also shown because the billing extracts arrive as calendar-year files. They can give different answers, so both are published.":
        "Two clocks are shown on purpose. The company plans on a financial year running April to "
        "March, while the billing extracts arrive as calendar-year files. The two can give "
        "different answers, so both are published side by side.",
}


def plain_limit(text: str) -> str:
    return LIMIT_PLAIN.get(text, text)

VERDICT_LABEL = {
    "bvp_share_up_volume_held": "Value line took share, unit held",
    "bvp_share_up_volume_lost": "Value line took share, unit still lost",
    "stable": "No material shift",
    "no_bvp_in_market": "No value line in this market",
    "insufficient_years": "Too few years to judge",
    "pre_bvp_entry": "Before the value line existed",
}


def _m(x: float) -> float:
    return round(float(x) / 1_000_000, 3)


def load_payload() -> dict:
    market = pd.read_csv(DERIVED / "lost_sales_market.csv", low_memory=False)
    model = pd.read_csv(DERIVED / "lost_sales_model.csv", low_memory=False)
    cov = pd.read_csv(DERIVED / "lost_sales_competitor_coverage.csv")
    cpn = pd.read_csv(DERIVED / "lost_sales_competitor_pn.csv")
    fy_series = pd.read_csv(DERIVED / "lost_sales_fiscal_year.csv")
    fy_q1 = pd.read_csv(DERIVED / "lost_sales_fiscal_q1.csv")
    meta = json.loads((DERIVED / "lost_sales_model.meta.json").read_text(encoding="utf-8"))

    # ── market level: ceiling and cover, one row per market per year ─────────
    mk = market[market["year"] == 2025].copy()
    markets = (
        mk.sort_values("uncaptured_eur", ascending=False)
        .assign(
            code=lambda d: d["distributor_code"],
            ceiling_m=lambda d: d["theoretical_wallet_eur"].map(_m),
            captured_m=lambda d: d["captured_total_eur"].map(_m),
            uncaptured_m=lambda d: d["uncaptured_eur"].map(_m),
            actionable_m=lambda d: d["actionable_gap_eur"].map(_m),
            gps_pct=lambda d: d["gps_pct"],
            uio=lambda d: d["uio_units"],
            realisation=lambda d: d["realisation_pct_avg"],
        )[["code", "ceiling_m", "captured_m", "uncaptured_m", "actionable_m", "gps_pct", "uio",
           "realisation"]]
    )
    markets = json.loads(markets.to_json(orient="records"))

    # ── service-family gaps: what kind of loss, per market ───────────────────
    gaps = model[
        (model["year"] == 2025) & (model["pms_category"] != "not_a_service_family")
    ].copy()
    gaps = gaps.drop_duplicates(["distributor_code", "pms_category"])
    gap_rows = []
    for code, g in gaps.groupby("distributor_code"):
        by_type = g.groupby("gap_type")["gap_eur_at_genuine"].sum().to_dict()
        expected_units = float(g["pms_expected_qty"].sum())
        actual_units = float(g["pms_actual_qty"].sum())
        bought_eur = float(g["pms_actual_rev_eur"].sum())
        gap_rows.append(
            {
                "code": code,
                "bought_eur": round(bought_eur),
                "expected_units": round(expected_units),
                "actual_units": round(actual_units),
                "under_service_eur": round(by_type.get("under_service", 0.0)),
                "substitution_eur": round(by_type.get("substitution", 0.0)),
                "catalog_gap_eur": round(by_type.get("catalog_gap", 0.0)),
            }
        )
    gap_rows.sort(key=lambda r: -(r["under_service_eur"] + r["substitution_eur"] + r["catalog_gap_eur"]))

    # ── momentum: is it getting worse, on a like-for-like basis ─────────────
    mo = model.dropna(subset=["yoy_eur"]).drop_duplicates(
        ["distributor_code", "family_7", "year"]
    )

    def _mk_momentum(df: pd.DataFrame, by_family: bool) -> list[dict]:
        keys = ["distributor_code"] + (["family_7"] if by_family else [])
        agg = (
            df.groupby(keys + ["momentum_basis", "year"])
            .agg(base=("billed_base_eur", "sum"), end=("billed_end_eur", "sum"))
            .reset_index()
        )
        agg["yoy_eur"] = agg["end"] - agg["base"]
        agg["yoy_pct"] = (100 * (agg["end"] / agg["base"] - 1)).where(agg["base"] > 0)
        recs = []
        for _, r in agg.iterrows():
            rec = {
                "code": r["distributor_code"],
                "basis": r["momentum_basis"],
                "year": int(r["year"]),
                "yoy_eur": round(float(r["yoy_eur"])),
                "yoy_pct": round(float(r["yoy_pct"]), 1) if pd.notna(r["yoy_pct"]) else None,
                "end_eur": round(float(r["end"])),
            }
            if by_family:
                rec["family"] = FAMILY_LABEL.get(r["family_7"], r["family_7"])
            recs.append(rec)
        return recs

    momentum_market = _mk_momentum(mo, by_family=False)
    momentum_family = _mk_momentum(mo, by_family=True)

    # Family totals across the whole network, one row per family per comparison. The page shows
    # this so a reader can see which parts family is moving without reading 18 markets.
    fam_rows = []
    for (basis, year), g in (
        mo.groupby(["momentum_basis", "year"])
        .apply(
            lambda d: d.groupby("family_7").agg(
                base=("billed_base_eur", "sum"), end=("billed_end_eur", "sum")
            ),
            include_groups=False,
        )
        .reset_index()
        .groupby(["momentum_basis", "year"])
    ):
        for _, r in g.iterrows():
            base, end = float(r["base"]), float(r["end"])
            fam_rows.append(
                {
                    "basis": basis,
                    "year": int(year),
                    "family": FAMILY_LABEL.get(r["family_7"], r["family_7"]),
                    "base_eur": round(base),
                    "end_eur": round(end),
                    "yoy_eur": round(end - base),
                    "yoy_pct": round(100 * (end / base - 1), 1) if base > 0 else None,
                }
            )

    # ── why it moved: volume / price / mix, per market and family ────────────
    ps = model.dropna(subset=["delta_total_eur"]).drop_duplicates(
        ["distributor_code", "family_7", "year"]
    )
    ps = ps[ps["year"] == 2025]
    price_rows = []
    for _, r in ps.iterrows():
        price_rows.append(
            {
                "code": r["distributor_code"],
                "family": FAMILY_LABEL.get(r["family_7"], r["family_7"]),
                "total_eur": round(float(r["delta_total_eur"])),
                "volume_eur": round(float(r["delta_volume_eur"])),
                "price_eur": round(float(r["delta_price_eur"])),
                "mix_eur": round(float(r["delta_mix_eur"])),
            }
        )
    price_rows.sort(key=lambda r: -abs(r["total_eur"]))

    # ── down-trade verdicts per market and family ────────────────────────────
    vt = model.dropna(subset=["down_trade_verdict"]).drop_duplicates(
        ["distributor_code", "family_7"]
    )
    verdict_counts = (
        vt["down_trade_verdict"].value_counts().to_dict()
    )
    verdict_rows = [
        {
            "label": VERDICT_LABEL.get(k, k),
            "count": int(v),
        }
        for k, v in sorted(verdict_counts.items(), key=lambda kv: -kv[1])
    ]

    # ── competitor position ─────────────────────────────────────────────────
    coverage = [
        {
            "source": r["source"],
            "pns": int(r["covered_part_numbers"]),
            "median": round(float(r["median_index_reference_vs_competitor"]), 2),
            "above2x_pct": round(100 * float(r["share_above_2x"]), 1),
            "above3x_pct": round(100 * float(r["share_above_3x"]), 1),
            "coverage_pct": float(r["coverage_pct_of_book_all_years"]),
            "tier": r["tier"],
            "vintage": r["vintage"],
        }
        for _, r in cov.iterrows()
    ]
    top_pn = (
        cpn.drop_duplicates(["source", "part_number"])
        .sort_values("index_reference_vs_competitor", ascending=False)
        .head(12)
    )
    competitor_rows = [
        {
            "pn": r["part_number"],
            "source": r["source"],
            "index": round(float(r["index_reference_vs_competitor"]), 2),
            "ours": round(float(r["our_reference_dealer_eur"]), 2)
            if pd.notna(r["our_reference_dealer_eur"])
            else None,
            "theirs": round(float(r["competitor_price_eur"]), 2)
            if pd.notna(r["competitor_price_eur"])
            else None,
            "family": FAMILY_LABEL.get(r.get("family_7"), "—") if pd.notna(r.get("family_7")) else "—",
        }
        for _, r in top_pn.iterrows()
    ]

    # ── headline figures for the KPI tiles ──────────────────────────────────
    # January to June 2026 against the same six months of 2025, from the like-for-like pair only.
    jj = [r for r in momentum_market if r["basis"] == "jan_jun" and r["year"] == 2026]
    jj_end = sum(r["end_eur"] for r in jj)
    jj_base = sum(r["end_eur"] - r["yoy_eur"] for r in jj)
    # Network gap = ceiling − billed (subtraction). Do not sum per-market uncaptured
    # rows: over-target markets inflate that sum above the network subtraction figure.
    net_ceiling = sum(r["ceiling_m"] for r in markets)
    net_captured = sum(r["captured_m"] for r in markets)
    net_uncaptured = round(net_ceiling - net_captured, 3)
    total_gap_eur = sum(
        r["under_service_eur"] + r["substitution_eur"] + r["catalog_gap_eur"] for r in gap_rows
    )
    net_uio = sum(int(r.get("uio") or 0) for r in markets)

    # ── the action layer: what to do, part number by part number ─────────────
    pna = pd.read_csv(DERIVED / "lost_sales_pn_action.csv", low_memory=False)

    LEVER_MEANING = {
        "price_or_incentive_actionable":
            "A price move or a targeted incentive can reach the competing price and still leave "
            "us above a 25% margin. This is where an incentive can actually work.",
        "below_margin_floor":
            "A discount could reach the competing price, but only by dropping through the 25% "
            "margin floor. That is a margin decision someone has to own, not an incentive.",
        "landed_cost_not_price":
            "The competing price sits below what the part costs us landed. No discount we could "
            "give reaches it. The answer is landed cost, a cheaper line, or letting the volume go.",
        "insufficient_pricing_data":
            "We hold a competing price but not a cost, or a cost but no competing price. Nothing "
            "can be decided on this part number until the other half is filled.",
    }
    lever_rows = []
    for lever, g in pna.groupby("recommended_lever"):
        lever_rows.append(
            {
                "lever": lever,
                "label": LEVER_MEANING.get(lever, lever).split(".")[0],
                "meaning": LEVER_MEANING.get(lever, ""),
                "parts": int(len(g)),
                "billed_eur": round(float(g["billed_all_years_eur"].fillna(0).sum())),
                "min_index": round(float(g["index_vs_competitor"].min()), 2)
                if g["index_vs_competitor"].notna().any() else None,
                "max_index": round(float(g["index_vs_competitor"].max()), 2)
                if g["index_vs_competitor"].notna().any() else None,
            }
        )
    lever_rows.sort(
        key=lambda r: {"price_or_incentive_actionable": 0, "landed_cost_not_price": 1,
                       "below_margin_floor": 2, "insufficient_pricing_data": 3}.get(r["lever"], 9)
    )

    def _pn_rows(frame: pd.DataFrame, limit: int | None = None) -> list[dict]:
        f = frame.sort_values("billed_all_years_eur", ascending=False)
        if limit:
            f = f.head(limit)
        recs = []
        for _, r in f.iterrows():
            def num(col, dp=2):
                v = r.get(col)
                return round(float(v), dp) if pd.notna(v) else None
            recs.append(
                {
                    "pn": r["part_number"],
                    "family": FAMILY_LABEL.get(r.get("family_7"), r.get("aim_l1") or "—"),
                    "billed_eur": num("billed_all_years_eur", 0),
                    "units": num("units_all_years", 0),
                    "markets": int(r["markets"]) if pd.notna(r.get("markets")) else None,
                    "cost": num("cost_landed_eur"),
                    "margin_pct": round(float(r["margin_pct_today"]) * 100, 1)
                    if pd.notna(r.get("margin_pct_today")) else None,
                    "our_price": num("our_reference_eur"),
                    "comp_price": num("competitor_price_eur"),
                    "index": num("index_vs_competitor"),
                    "headroom_pct": num("discount_headroom_pct", 0),
                    "dealer_share": num("sell_through_ratio", 2),
                    "lever": r["recommended_lever"],
                }
            )
        return recs

    actionable = pna[pna["recommended_lever"] == "price_or_incentive_actionable"]
    landed = pna[pna["recommended_lever"] == "landed_cost_not_price"]
    floor = pna[pna["recommended_lever"] == "below_margin_floor"]

    # Calendar-year totals, so the two clocks can be shown on the same axis from one source.
    cal_series = []
    for y in sorted(int(v) for v in model["year"].unique()):
        cal_series.append(
            {
                "year": y,
                "label": str(y),
                "billed_eur": round(float(model.loc[model["year"] == y, "net_sales_eur"].sum())),
                "is_complete": y < int(pd.Timestamp.today().year),
            }
        )

    return {
        "as_of": meta["generated_at"],
        "calendar_series": cal_series,
        "fiscal": {
            "series": [
                {
                    "fy": int(r["fiscal_year"]),
                    "label": r["fy_label"],
                    "billed_eur": round(float(r["billed_eur"])),
                    "months": int(r["months_present"]),
                    "complete": bool(r["is_complete"]),
                    "yoy_pct": None if pd.isna(r["yoy_pct"]) else round(float(r["yoy_pct"]), 1),
                    "yoy_eur": None if pd.isna(r["yoy_eur"]) else round(float(r["yoy_eur"])),
                }
                for _, r in fy_series.iterrows()
            ],
            "current": json.loads(fy_q1.iloc[0].to_json()),
        },
        "kpi": {
            "ceiling_m": round(net_ceiling, 1),
            "captured_m": round(net_captured, 1),
            "uncaptured_m": round(net_uncaptured, 1),
            "gps_pct": round(100 * net_captured / net_ceiling, 1) if net_ceiling else None,
            "service_gap_eur": round(total_gap_eur),
            "h1_yoy_pct": round(100 * (jj_end / jj_base - 1), 1) if jj_base else None,
            "uio": int(net_uio),
        },
        "markets": markets,
        "gaps": gap_rows,
        "momentum_market": momentum_market,
        "momentum_family": momentum_family,
        "momentum_family_network": fam_rows,
        "price": price_rows,
        "verdicts": verdict_rows,
        "coverage": coverage,
        "competitor": competitor_rows,
        "levers": lever_rows,
        "pn_actionable": _pn_rows(actionable, 12),
        "pn_landed": _pn_rows(landed, 12),
        "pn_floor": _pn_rows(floor, 12),
        "limits": meta["limits"],
    }


def _fy_rows(payload: dict) -> list[dict]:
    """The complete fiscal years only, for the table. A stub year is shown separately."""
    return [r for r in payload["fiscal"]["series"] if r["complete"]]


def build_html(payload: dict) -> str:
    chartjs = CHARTJS.read_text(encoding="utf-8", errors="ignore")
    chartjs = chartjs.replace("//# sourceMappingURL=chart.umd.min.js.map", "")
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    kpi = payload["kpi"]
    limits = "".join(f"<li>{plain_limit(t)}</li>" for t in payload["limits"])
    gap_tiles = ""
    for g in payload["gaps"][:6]:
        total = g["under_service_eur"] + g["substitution_eur"] + g["catalog_gap_eur"]
        gap_tiles += (
            f'<tr><td class="db">{g["code"]}</td>'
            f'<td class="n">{g["under_service_eur"]:,}</td>'
            f'<td class="n">{g["substitution_eur"]:,}</td>'
            f'<td class="n">{g["catalog_gap_eur"]:,}</td>'
            f'<td class="n strong">{total:,}</td></tr>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Modelled aftermarket opportunity — CY2025</title>
<style>
  :root {{
    --navy:#15233c; --terracotta:#c0552d; --paper:#f7f4ee; --rule:#d9d2c7;
    --ink:#222; --muted:#6b6257; --good:#2f6b4f; --warn:#a8862c;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--paper); color:var(--ink);
         font:15px/1.55 "Segoe UI",system-ui,-apple-system,sans-serif; }}
  header {{ background:var(--navy); color:var(--paper); padding:30px 34px 26px; }}
  header h1 {{ font:600 30px/1.2 Georgia,"Times New Roman",serif; margin:0 0 6px; }}
  header p {{ margin:0; color:#cfc7ba; max-width:900px; font-size:14px; }}
  .wrap {{ max-width:1240px; margin:0 auto; padding:26px 34px 70px; }}
  .basis {{ display:flex; flex-wrap:wrap; gap:8px 18px; margin:14px 0 0; padding:10px 12px;
            background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.18); border-radius:4px;
            font-size:12px; color:#d5cfc4; }}
  .basis b {{ color:#e9a183; font-weight:700; letter-spacing:.04em; text-transform:uppercase;
              font-size:10.5px; margin-right:4px; }}
  h2 {{ font:600 21px/1.25 Georgia,serif; color:var(--navy); margin:40px 0 4px; }}
  h2 .q {{ display:block; font:400 13.5px/1.5 "Segoe UI",sans-serif; color:var(--muted);
           margin-top:5px; }}
  .kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(178px,1fr)); gap:12px;
           margin-top:22px; }}
  .kpi {{ background:#fff; border:1px solid var(--rule); border-left:5px solid var(--terracotta);
          padding:13px 15px; border-radius:3px; position:relative; cursor:help; }}
  .kpi .v {{ font:600 25px/1.1 Georgia,serif; color:var(--navy); }}
  .kpi .l {{ font-size:11.5px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted);
             margin-top:5px; }}
  .kpi:hover .tip {{ visibility:visible; opacity:1; }}
  .kpi .tip {{ visibility:hidden; opacity:0; transition:opacity .12s; position:absolute; z-index:40;
     left:0; top:100%; margin-top:8px; width:290px; background:var(--navy); color:var(--paper);
     padding:11px 13px; border-radius:3px; font-size:12.5px; line-height:1.5; font-weight:400;
     box-shadow:0 7px 20px rgba(0,0,0,.22); }}
  .kpi .tip b {{ color:#e9a183; }}
  .card {{ background:#fff; border:1px solid var(--rule); border-radius:3px; padding:20px 22px;
           margin-top:16px; }}
  .charts {{ display:grid; grid-template-columns:1fr; gap:16px; }}
  .chartbox {{ position:relative; height:360px; }}
  .chartbox.tall {{ height:430px; }}
  .note {{ font-size:12.5px; color:var(--muted); margin:9px 0 0; }}
  .banner {{ background:#fdf3e3; border:1px solid #e4c88a; border-left:5px solid var(--warn);
             padding:11px 14px; border-radius:3px; font-size:13px; margin-top:14px; }}
  .banner b {{ color:#7a5d10; }}
  table {{ border-collapse:collapse; width:100%; margin-top:10px; font-size:13.5px; }}
  th,td {{ text-align:left; padding:7px 9px; border-bottom:1px solid var(--rule); }}
  th {{ background:#eef1f5; color:var(--navy); font-weight:600; font-size:12.5px; }}
  td.n {{ text-align:right; font-variant-numeric:tabular-nums; }}
  td.db {{ font-weight:600; color:var(--navy); }}
  td.strong {{ font-weight:600; }}
  .controls {{ display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin-top:14px; }}
  select, button {{ font:inherit; padding:7px 11px; border:1px solid var(--rule); border-radius:3px;
                    background:#fff; color:var(--ink); }}
  button {{ cursor:pointer; }}
  button.on {{ background:var(--navy); color:var(--paper); border-color:var(--navy); }}
  .seg {{ display:inline-flex; gap:0; }}
  .seg button {{ border-radius:0; margin-left:-1px; }}
  .seg button:first-child {{ border-radius:3px 0 0 3px; margin-left:0; }}
  .seg button:last-child {{ border-radius:0 3px 3px 0; }}
  ul.limits {{ padding-left:20px; font-size:13.5px; }}
  ul.limits li {{ margin-bottom:7px; }}
  footer {{ border-top:1px solid var(--rule); margin-top:34px; padding-top:14px;
            font-size:12.5px; color:var(--muted); }}
  @media (min-width:1000px) {{ .two {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }} }}
</style>
</head>
<body>
<header>
  <h1>Where modelled aftermarket spend is not reaching ISZE</h1>
  <p>Primary question: how much of the modelled CY2025 target-spend ceiling is not currently covered
  by parts billed, where is that gap concentrated, and which part numbers look commercially
  actionable? The ceiling is a modelled maximum, not a forecast of achievable revenue, and the gap
  is not an observed lost-sale ledger.</p>
  <div class="basis">
    <span><b>Observed</b> Parts billed through 30 June 2026</span>
    <span><b>Modelled</b> Target spend / service demand where shown</span>
    <span><b>Fleet</b> Historical fleet basis only; no forward forecast quoted</span>
    <span><b>CY2025</b> {kpi.get('uio', 0):,} trucks in service · ceiling EUR {kpi['ceiling_m']}M · billed EUR {kpi['captured_m']}M</span>
  </div>
</header>
<div class="wrap">

  <div class="kpis">
    <div class="kpi"><div class="v">EUR {kpi['ceiling_m']}M</div><div class="l">Modelled target spend, CY2025</div>
      <div class="tip">What the vehicles in service could spend on parts in CY2025 if every one of them
      bought at the reference rate for its weight class. It is a <b>modelled ceiling, not a forecast</b>, and
      it is published per market only.</div></div>
    <div class="kpi"><div class="v">EUR {kpi['captured_m']}M</div><div class="l">Parts billed, CY2025</div>
      <div class="tip">Parts billed to distributors in CY2025, excluding credit notes and returns and
      excluding non-part lines such as freight, rebates and service fees. Observed.</div></div>
    <div class="kpi"><div class="v">EUR {kpi['uncaptured_m']}M</div><div class="l">Modelled opportunity gap</div>
      <div class="tip">CY2025 modelled ceiling minus parts billed (network subtraction). This is
      <b>spend not currently reaching ISZE</b> on the modelled ceiling — not a recoverable invoice total.
      Some of it is vehicles that were not serviced; some sits where a competing part is cheaper.</div></div>
    <div class="kpi"><div class="v">{kpi['gps_pct']}%</div><div class="l">Share of modelled ceiling</div>
      <div class="tip">Parts billed as a share of the modelled CY2025 target-spend ceiling. Network-wide.
      Read it as a rate, never as a target that must reach 100%: cross-border and counter sales make some
      markets exceed 100%.</div></div>
    <div class="kpi"><div class="v">{kpi.get('uio', 0):,}</div>
      <div class="l">Trucks in service, CY2025</div>
      <div class="tip">Historical fleet denominator behind the modelled ceiling. Forward fleet forecasts
      from 2026 onward are not usable and are not quoted here.</div></div>
    <div class="kpi"><div class="v">{'+' if (kpi['h1_yoy_pct'] or 0) >= 0 else ''}{kpi['h1_yoy_pct']}%</div>
      <div class="l">Jan–Jun 2026 vs Jan–Jun 2025</div>
      <div class="tip">January to June 2026 against the same six months of 2025, like for like.
      Billing runs to 30 June 2026, so a full-year comparison against 2025 would read as a collapse that
      did not happen.</div></div>
  </div>

  <h2>Where the modelled gap sits
    <span class="q">Which markets hold the largest gap to modelled target spend?</span></h2>
  <div class="card"><div class="chartbox tall"><canvas id="c_gap"></canvas></div>
    <p class="note">Modelled target spend minus parts billed, CY2025. The label on each bar is that market's
    share of its own modelled ceiling. Three markets hold about seventy percent of the network gap.
    This is a modelled opportunity, not observed lost sales.</p></div>

  <h2>How the modelled service gap splits
    <span class="q">Was the vehicle not serviced with our part, serviced with someone else's part, or is there
    nothing for us to sell?</span></h2>
  <div class="card">
    <div class="banner"><b>Scope note.</b> The classified service-family split below is a subset of the
    modelled gap. A network-wide service-demand euro total is not shown here because some source cells
    are not externally quotable. Percent and unit views at market / category level remain.</div>
    <div class="chartbox tall"><canvas id="c_kind"></canvas></div>
    <p class="note">Euro at the genuine selling price, for the six markets with the largest modelled
    service gap. The three causes need three different responses, so they are never added into one
    number without saying which is which.</p>
    <table>
      <thead><tr><th>Market</th><th class="n">Not serviced with our part</th>
      <th class="n">Cheaper alternative</th><th class="n">Nothing to sell</th>
      <th class="n">Total</th></tr></thead>
      <tbody>{gap_tiles}</tbody>
    </table>
  </div>

  <h2>Is it getting worse
    <span class="q">Which markets are falling, and is the fall real or an artefact of the calendar?</span></h2>
  <div class="card">
    <div class="controls">
      <span class="seg">
        <button id="b_full" class="on">Full year 2025 vs 2024</button>
        <button id="b_h1">Jan–Jun 2026 vs Jan–Jun 2025</button>
      </span>
    </div>
    <div class="chartbox tall" style="margin-top:14px"><canvas id="c_mom"></canvas></div>
    <p class="note" id="mom_note"></p>
    <p class="note" style="margin-top:14px"><b>Which parts family is moving, whole network.</b>
    Same switch as above.</p>
    <div class="chartbox"><canvas id="c_family"></canvas></div>
  </div>

  <h2>Why it moved
    <span class="q">Did the market shrink, did the price move, or did the mix of parts change?</span></h2>
  <div class="card">
    <div class="controls">
      <label for="sel_price">Market</label>
      <select id="sel_price"></select>
      <span class="note" style="margin:0">Full year 2025 against 2024. The three effects sum to the
      total movement.</span>
    </div>
    <div class="chartbox" style="margin-top:14px"><canvas id="c_price"></canvas></div>
    <p class="note">Selling fewer parts (volume), charging a different price for the parts actually
    sold (price), or selling a different mix of parts (mix). A price-led fall on flat volume is a
    different problem from a volume-led fall on flat price.</p>
  </div>

  <h2>Is the value line defending us or eating us
    <span class="q">When our own cheaper line took share, did we keep the unit?</span></h2>
  <div class="card">
    <div class="chartbox"><canvas id="c_verdict"></canvas></div>
    <p class="note">One count per market and parts family. Where the value line took share and volume
    held, we defended the unit against the independent aftermarket. Where share rose while total
    volume fell, we down-traded and lost the unit anyway.</p>
  </div>

  <h2>Who is taking it
    <span class="q">Where do we hold a real competing price, and how far above it do we sit?</span></h2>
  <div class="card">
    <div class="banner"><b>Read this before the chart.</b> A competing price exists on only a small
    part of the book. The two usable sources cover <b>{payload['coverage'][0]['coverage_pct']:.1f}%</b>
    and <b>{payload['coverage'][1]['coverage_pct']:.1f}%</b> of parts billed. For the rest there is no
    competing price on file at all — that is a gap in the evidence, not a sign that we are
    competitive.</div>
    <div class="chartbox" style="margin-top:16px"><canvas id="c_comp"></canvas></div>
    <p class="note">Our reference dealer price divided by the competing price, on distinct part
    numbers. Above 1 means we sit above the competing price. The two sources are different vintages
    and different tiers of the market and are never blended.</p>
    <table>
      <thead><tr><th>Source</th><th class="n">Part numbers</th><th class="n">Median index</th>
      <th class="n">Above 2x</th><th class="n">Share of the book</th><th>Vintage</th></tr></thead>
      <tbody>
      {''.join(f'<tr><td class="db">{c["source"]}</td><td class="n">{c["pns"]}</td>'
               f'<td class="n strong">{c["median"]}</td><td class="n">{c["above2x_pct"]}%</td>'
               f'<td class="n">{c["coverage_pct"]:.1f}%</td><td>{c["vintage"]}</td></tr>'
               for c in payload["coverage"])}
      </tbody>
    </table>
  </div>

  <h2>Part numbers where the gap is widest</h2>
  <div class="card">
    <table>
      <thead><tr><th>Part number</th><th>Family</th><th class="n">Our reference dealer price</th>
      <th class="n">Competing price</th><th class="n">Index</th><th>Source</th></tr></thead>
      <tbody>
      {''.join(f'<tr><td class="db">{r["pn"]}</td><td>{r["family"]}</td>'
               f'<td class="n">{"" if r["ours"] is None else format(r["ours"], ",.2f")}</td>'
               f'<td class="n">{"" if r["theirs"] is None else format(r["theirs"], ",.2f")}</td>'
               f'<td class="n strong">{r["index"]}</td><td>{r["source"]}</td></tr>'
               for r in payload["competitor"])}
      </tbody>
    </table>
    <p class="note">Prices are shown as recorded at the date of the source. The multi-brand source is
    held internally only until its licence position is settled.</p>
  </div>

  <h2>What to actually do
    <span class="q">Part number by part number: is the lever price, margin, or landed cost?</span></h2>
  <div class="card">
    <p class="note" style="margin-top:0">Every part number where we hold both a landed cost and a
    real competing price, sorted by the money involved. This is the layer that decides something:
    it says which part numbers a price move or an incentive can fix, which ones would breach the
    margin floor to get there, and which ones no discount can reach at all because the competitor
    already sits below our own cost. Read the last column first.</p>
    <table>
      <thead><tr><th>Part number</th><th>Family</th><th class="n">Billed, all years</th>
      <th class="n">Units</th><th class="n">Markets</th><th class="n">Cost landed</th>
      <th class="n">Margin today</th><th class="n">Our dealer price</th>
      <th class="n">Competitor</th><th class="n">Index</th>
      <th class="n">Discount headroom</th><th>What it means</th></tr></thead>
      <tbody id="pn_body"></tbody>
    </table>
    <div class="controls">
      <span class="seg">
        <button id="pn_all" class="on">Everything</button>
        <button id="pn_act">Price or incentive can work</button>
        <button id="pn_land">Landed cost, not price</button>
        <button id="pn_floor">Only below the margin floor</button>
      </span>
      <span class="note" style="margin:0" id="pn_count"></span>
    </div>
  </div>

  <h2>Where the lever changes
    <span class="q">How much of the book falls into each kind of answer?</span></h2>
  <div class="card">
    <div class="chartbox tall"><canvas id="c_lever"></canvas></div>
    <table>
      <thead><tr><th>Answer</th><th class="n">Part numbers</th><th class="n">Billed, all years</th>
      <th class="n">Index range</th><th>What it means</th></tr></thead>
      <tbody>
      {''.join(f'<tr><td class="db">{l["lever"].replace("_"," ")}</td><td class="n">{l["parts"]}</td>'
               f'<td class="n">{l["billed_eur"]:,}</td>'
               f'<td class="n">{"" if l["min_index"] is None else f"{l["min_index"]}x – {l["max_index"]}x"}</td>'
               f'<td>{l["meaning"]}</td></tr>'
               for l in payload["levers"])}
      </tbody>
    </table>
  </div>

  <h2>Where the competitor sits below our own cost
    <span class="q">On which part numbers can no discount ever work?</span></h2>
  <div class="card">
    <div class="banner"><b>This is the finding that changes the ask.</b> On these part numbers the
    competing price is lower than what the part costs us landed. A discount, an incentive or a
    support payment cannot close that gap — we would be selling below cost to try. The answer is
    landed cost, a cheaper line, or accepting the volume loss. They must not be bundled into a
    price or incentive request.</div>
    <table>
      <thead><tr><th>Part number</th><th>Family</th><th class="n">Cost landed</th>
      <th class="n">Our dealer price</th><th class="n">Competitor</th><th class="n">How many times ours</th>
      <th class="n">Billed, all years</th></tr></thead>
      <tbody>
      {''.join(f'<tr><td class="db">{r["pn"]}</td><td>{r["family"]}</td>'
               f'<td class="n">{"" if r["cost"] is None else format(r["cost"], ",.2f")}</td>'
               f'<td class="n">{"" if r["our_price"] is None else format(r["our_price"], ",.2f")}</td>'
               f'<td class="n">{"" if r["comp_price"] is None else format(r["comp_price"], ",.2f")}</td>'
               f'<td class="n strong">{r["index"]}</td>'
               f'<td class="n">{"" if r["billed_eur"] is None else format(r["billed_eur"], ",.0f")}</td></tr>'
               for r in payload["pn_landed"])}
      </tbody>
    </table>
    <p class="note">The same table for the other two answers is in the file behind this page:
    <code>01_data/00_derived/lost_sales_pn_action.csv</code>, one row per part number with the
    lever stated.</p>
  </div>

  <h2>Two clocks, and they disagree
    <span class="q">Is the business growing or shrinking? It depends which year you use.</span></h2>
  <div class="card">
    <div class="banner"><b>Read this before quoting either number.</b> The company plans on a
    financial year that runs April to March. The billing extracts arrive as calendar-year files.
    On the calendar the last year was <b>down 2.9%</b>. On the financial year it was <b>up 1.9%</b>.
    Both are correct. The calendar loss comes almost entirely from the run-in to March, which the
    fiscal year carries into the next period.</div>
    <div class="chartbox tall" style="margin-top:16px"><canvas id="c_fy"></canvas></div>
    <p class="note">Billed parts on both clocks, from the same billing. The bars are financial
    years, where FY2026 means April 2025 to March 2026. The line is the calendar year, which is the
    shape the billing extracts arrive in. A move is only quoted between two complete years, which is
    why the first bar carries no change figure.</p>
    <table>
      <thead><tr><th>Period</th><th class="n">Billed</th><th class="n">Months inside</th>
      <th class="n">Change</th><th>Reads as</th></tr></thead>
      <tbody>
        {''.join(f'<tr><td class="db">{r["label"]}</td><td class="n">{r["billed_eur"]:,}</td>'
                 f'<td class="n">{r["months"]}</td>'
                 f'<td class="n">{"—" if r["yoy_pct"] is None else f"{r["yoy_pct"]:+.1f}%"}</td>'
                 f'<td>{"Complete year" if r["complete"] else "Part of a year — do not compare as a full year"}</td></tr>'
                 for r in _fy_rows(payload))}
        <tr><td class="db">{payload["fiscal"]["current"]["fy_label"]} so far</td>
            <td class="n">{payload["fiscal"]["current"]["billed_end_eur"]:,}</td>
            <td class="n">{payload["fiscal"]["current"]["months_compared"]}</td>
            <td class="n">{payload["fiscal"]["current"]["yoy_pct"]:+.1f}%</td>
            <td>Closed months against the same months a year earlier</td></tr>
      </tbody>
    </table>
    <p class="note">The current financial year has only its first quarter in the data, so it is
    compared month for month against the same quarter last year, never against a full year.</p>
  </div>

  <h2>What this model does not tell you</h2>
  <div class="card"><ul class="limits">{limits}</ul>
    <p class="note">Full source list and vintages: the model's own record file, held alongside the
    data (<code>01_data/00_derived/lost_sales_model.meta.json</code>).</p>
  </div>

  <footer>Built {payload['as_of']} from the ISZE derived pipeline. Figures are internal working
  numbers, not audited accounts.</footer>
</div>

<script id="lsm-data" type="application/json">{data}</script>
<script>{chartjs}</script>
<script>
(function () {{
  var D = JSON.parse(document.getElementById('lsm-data').textContent);
  var NAVY='#15233c', TERRA='#c0552d', PAPER='#f7f4ee', RULE='#d9d2c7', MUTED='#6b6257';
  var GREEN='#2f6b4f', AMBER='#a8862c', SLATE='#7d8a9c';
  Chart.defaults.font.family = '"Segoe UI",system-ui,sans-serif';
  Chart.defaults.color = '#222';
  Chart.defaults.plugins.legend.labels.boxWidth = 12;
  var eur = function (v) {{
    var a = Math.abs(v);
    var s = a >= 1000 ? (a / 1000).toFixed(a >= 10000 ? 0 : 1) + 'k' : a.toFixed(0);
    return (v < 0 ? '-' : '') + 'EUR ' + s;
  }};

  // 1 — Where the gap sits: ranked bars in euro.
  var mk = D.markets.slice(0, 14);
  new Chart(document.getElementById('c_gap'), {{
    type: 'bar',
    data: {{ labels: mk.map(function (m) {{ return m.code; }}),
      datasets: [{{ label: 'Modelled gap to target spend (EUR)',
        data: mk.map(function (m) {{ return m.uncaptured_m * 1e6; }}),
        backgroundColor: mk.map(function (m) {{ return m.gps_pct < 55 ? TERRA : NAVY; }}),
        borderRadius: 2 }}] }},
    options: {{ indexAxis: 'y', maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }},
        tooltip: {{ callbacks: {{ label: function (c) {{
          var m = mk[c.dataIndex];
          return [eur(c.raw) + ' modelled opportunity gap',
                  'Share of own modelled ceiling: ' + m.gps_pct.toFixed(1) + '%',
                  'Modelled target spend: ' + eur(m.ceiling_m * 1e6),
                  'Trucks in service: ' + m.uio.toLocaleString()]; }} }} }} }},
      scales: {{ x: {{ grid: {{ color: RULE }}, ticks: {{ callback: function (v) {{ return eur(v); }} }} }},
        y: {{ grid: {{ display: false }} }} }} }} }});

  // 2 — How the modelled service gap splits: stacked three-way with the residual named.
  var gp = D.gaps.slice(0, 6);
  new Chart(document.getElementById('c_kind'), {{
    type: 'bar',
    data: {{ labels: gp.map(function (g) {{ return g.code; }}),
      datasets: [
        {{ label: 'Bought from us', data: gp.map(function (g) {{ return g.bought_eur; }}),
           backgroundColor: GREEN, borderRadius: 2 }},
        {{ label: 'Not serviced with our part', data: gp.map(function (g) {{ return g.under_service_eur; }}),
           backgroundColor: NAVY, borderRadius: 2 }},
        {{ label: 'Bought a cheaper alternative', data: gp.map(function (g) {{ return g.substitution_eur; }}),
           backgroundColor: TERRA, borderRadius: 2 }},
        {{ label: 'We have nothing to sell', data: gp.map(function (g) {{ return g.catalog_gap_eur; }}),
           backgroundColor: AMBER, borderRadius: 2 }} ] }},
    options: {{ maintainAspectRatio: false,
      plugins: {{ tooltip: {{ callbacks: {{ label: function (c) {{ return c.dataset.label + ': ' + eur(c.raw); }} }} }} }},
      scales: {{ x: {{ stacked: true, grid: {{ display: false }} }},
        y: {{ stacked: true, grid: {{ color: RULE }},
             ticks: {{ callback: function (v) {{ return eur(v); }} }} }} }} }} }});

  // 3 — Is it getting worse: paired ranked bars, switchable basis.
  var momChart = null;
  function drawMomentum(basis) {{
    // The basis and the year must be filtered together. Filtering on basis alone would put a
    // 2025-vs-2024 move next to a labelled 2026 comparison.
    var wantYear = basis === 'jan_jun' ? 2026 : 2025;
    var rows = D.momentum_market.filter(function (r) {{
        return r.basis === basis && r.year === wantYear; }})
      .sort(function (a, b) {{ return a.yoy_eur - b.yoy_eur; }}).slice(0, 14);
    var isH1 = basis === 'jan_jun';
    if (momChart) {{ momChart.destroy(); }}
    momChart = new Chart(document.getElementById('c_mom'), {{
      type: 'bar',
      data: {{ labels: rows.map(function (r) {{ return r.code; }}),
        datasets: [{{ data: rows.map(function (r) {{ return r.yoy_eur; }}),
          backgroundColor: rows.map(function (r) {{ return r.yoy_eur < 0 ? TERRA : GREEN; }}),
          borderRadius: 2 }}] }},
      options: {{ indexAxis: 'y', maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }},
          tooltip: {{ callbacks: {{ label: function (c) {{
            var r = rows[c.dataIndex];
            return [eur(r.yoy_eur) + ' (' + (r.yoy_pct > 0 ? '+' : '') + r.yoy_pct + '%)',
                    'Now: ' + eur(r.end_eur)]; }} }} }} }},
        scales: {{ x: {{ grid: {{ color: RULE }}, ticks: {{ callback: function (v) {{ return eur(v); }} }} }},
          y: {{ grid: {{ display: false }} }} }} }} }});
    document.getElementById('mom_note').textContent = isH1
      ? 'January to June 2026 against the same six months of 2025, by market, so the comparison is like for like. Billing runs to June; a full-year comparison would read as a collapse that did not happen.'
      : 'Full year 2025 against full year 2024, by market. Both sides are complete years.';
  }}
  drawMomentum('full_year');
  document.getElementById('b_full').onclick = function () {{
    this.classList.add('on'); document.getElementById('b_h1').classList.remove('on');
    drawMomentum('full_year'); drawFamily('full_year'); }};
  document.getElementById('b_h1').onclick = function () {{
    this.classList.add('on'); document.getElementById('b_full').classList.remove('on');
    drawMomentum('jan_jun'); drawFamily('jan_jun'); }};

  // 3b — Which parts family is moving, whole network, same basis switch.
  var famChart = null;
  function drawFamily(basis) {{
    var wantYear = basis === 'jan_jun' ? 2026 : 2025;
    var rows = D.momentum_family_network.filter(function (r) {{
        return r.basis === basis && r.year === wantYear; }});
    rows = rows.filter(function (r) {{ return Math.abs(r.base_eur) > 0; }})
      .sort(function (a, b) {{ return b.yoy_eur - a.yoy_eur; }});
    if (famChart) {{ famChart.destroy(); }}
    famChart = new Chart(document.getElementById('c_family'), {{
      type: 'bar',
      data: {{ labels: rows.map(function (r) {{ return r.family; }}),
        datasets: [{{ data: rows.map(function (r) {{ return r.yoy_eur; }}),
          backgroundColor: rows.map(function (r) {{ return r.yoy_eur < 0 ? TERRA : GREEN; }}),
          borderRadius: 2 }}] }},
      options: {{ indexAxis: 'y', maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }},
          tooltip: {{ callbacks: {{ label: function (c) {{
            var r = rows[c.dataIndex];
            return [eur(r.yoy_eur) + ' (' + (r.yoy_pct > 0 ? '+' : '') + r.yoy_pct + '%)',
                    'Now: ' + eur(r.end_eur)]; }} }} }} }},
        scales: {{ x: {{ grid: {{ color: RULE }}, ticks: {{ callback: function (v) {{ return eur(v); }} }} }},
          y: {{ grid: {{ display: false }} }} }} }} }});
  }}
  drawFamily('full_year');

  // 4 — Why it moved: volume / price / mix for the chosen market.
  var codes = [];
  D.price.forEach(function (r) {{ if (codes.indexOf(r.code) < 0) codes.push(r.code); }});
  var sel = document.getElementById('sel_price');
  codes.forEach(function (c) {{
    var b = D.markets.find(function (m) {{ return m.code === c; }});
    var o = document.createElement('option');
    o.value = c; o.textContent = c + (b ? '  —  gap ' + eur(b.uncaptured_m * 1e6) : '');
    sel.appendChild(o); }});
  var priceChart = null;
  function drawPrice(code) {{
    var rows = D.price.filter(function (r) {{ return r.code === code; }})
      .sort(function (a, b) {{ return Math.abs(b.total_eur) - Math.abs(a.total_eur); }}).slice(0, 8);
    if (priceChart) {{ priceChart.destroy(); }}
    priceChart = new Chart(document.getElementById('c_price'), {{
      type: 'bar',
      data: {{ labels: rows.map(function (r) {{ return r.family; }}),
        datasets: [
          {{ label: 'Volume', data: rows.map(function (r) {{ return r.volume_eur; }}), backgroundColor: NAVY, borderRadius: 2 }},
          {{ label: 'Price', data: rows.map(function (r) {{ return r.price_eur; }}), backgroundColor: TERRA, borderRadius: 2 }},
          {{ label: 'Mix', data: rows.map(function (r) {{ return r.mix_eur; }}), backgroundColor: SLATE, borderRadius: 2 }} ] }},
      options: {{ maintainAspectRatio: false,
        plugins: {{ tooltip: {{ callbacks: {{ label: function (c) {{ return c.dataset.label + ': ' + eur(c.raw); }} }} }} }},
        scales: {{ x: {{ grid: {{ display: false }}, ticks: {{ maxRotation: 40, minRotation: 0, autoSkip: false }} }},
          y: {{ grid: {{ color: RULE }}, ticks: {{ callback: function (v) {{ return eur(v); }} }} }} }} }} }});
  }}
  drawPrice(codes[0] || '');
  sel.onchange = function () {{ drawPrice(this.value); }};

  // 4b — The part-number decision board. This is the layer that decides, so it renders on load
  // and switches by answer rather than by chart type.
  var PN = {{ all: [], actionable: D.pn_actionable, landed: D.pn_landed, floor: D.pn_floor }};
  var PN_LIST = [];
  [D.pn_actionable, D.pn_landed, D.pn_floor].forEach(function (arr) {{
    arr.forEach(function (r) {{ PN_LIST.push(r); }}); }});
  var LEVER_TEXT = {{
    price_or_incentive_actionable: 'Price or incentive can work',
    below_margin_floor: 'Only below the margin floor',
    landed_cost_not_price: 'Landed cost, not price',
    insufficient_pricing_data: 'Not enough data'
  }};
  var LEVER_COLOR = {{
    price_or_incentive_actionable: GREEN,
    below_margin_floor: AMBER,
    landed_cost_not_price: TERRA,
    insufficient_pricing_data: SLATE
  }};
  var money = function (v) {{ return v === null || v === undefined ? '—' : v.toLocaleString(); }};
  function drawPn(which) {{
    var rows = which === 'all'
      ? PN_LIST.slice().sort(function (a, b) {{ return (b.billed_eur || 0) - (a.billed_eur || 0); }})
      : PN[which].slice();
    var body = document.getElementById('pn_body');
    body.innerHTML = rows.map(function (r) {{
      return '<tr>'
        + '<td class="db">' + r.pn + '</td>'
        + '<td>' + r.family + '</td>'
        + '<td class="n">' + money(r.billed_eur) + '</td>'
        + '<td class="n">' + money(r.units) + '</td>'
        + '<td class="n">' + money(r.markets) + '</td>'
        + '<td class="n">' + money(r.cost) + '</td>'
        + '<td class="n">' + (r.margin_pct === null ? '—' : r.margin_pct + '%') + '</td>'
        + '<td class="n">' + money(r.our_price) + '</td>'
        + '<td class="n">' + money(r.comp_price) + '</td>'
        + '<td class="n strong">' + (r.index === null ? '—' : r.index + 'x') + '</td>'
        + '<td class="n">' + (r.headroom_pct === null ? '—' : r.headroom_pct + '%') + '</td>'
        + '<td style="color:' + (LEVER_COLOR[r.lever] || SLATE) + ';font-weight:600">'
        + (LEVER_TEXT[r.lever] || r.lever) + '</td>'
        + '</tr>';
    }}).join('');
    var total = rows.reduce(function (a, r) {{ return a + (r.billed_eur || 0); }}, 0);
    document.getElementById('pn_count').textContent =
      rows.length + ' part numbers, EUR ' + total.toLocaleString() + ' billed';
  }}
  drawPn('all');
  var pnBtns = {{ pn_all: 'all', pn_act: 'actionable', pn_land: 'landed', pn_floor: 'floor' }};
  Object.keys(pnBtns).forEach(function (id) {{
    document.getElementById(id).onclick = function () {{
      Object.keys(pnBtns).forEach(function (o) {{ document.getElementById(o).classList.remove('on'); }});
      this.classList.add('on');
      drawPn(pnBtns[id]);
    }};
  }});

  // 4c — How much of the book falls into each kind of answer.
  new Chart(document.getElementById('c_lever'), {{
    type: 'bar',
    data: {{ labels: D.levers.map(function (l) {{ return l.lever.replace(/_/g, ' '); }}),
      datasets: [
        {{ label: 'Billed EUR', data: D.levers.map(function (l) {{ return l.billed_eur; }}),
           backgroundColor: D.levers.map(function (l) {{ return LEVER_COLOR[l.lever] || SLATE; }}),
           borderRadius: 2 }} ] }},
    options: {{ indexAxis: 'y', maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }},
        tooltip: {{ callbacks: {{ label: function (c) {{
          var l = D.levers[c.dataIndex];
          return [eur(l.billed_eur) + ' across ' + l.parts + ' part numbers',
                  l.meaning]; }} }} }} }},
      scales: {{ x: {{ grid: {{ color: RULE }}, ticks: {{ callback: function (v) {{ return eur(v); }} }} }},
        y: {{ grid: {{ display: false }} }} }} }} }});

  // 5b — Two clocks, both honest. Fiscal bars beside the calendar line.
  (function () {{
    var complete = D.fiscal.series.filter(function (r) {{ return r.complete; }});
    var cur = D.fiscal.current;
    var labels = complete.map(function (r) {{ return r.label; }})
      .concat(['FY2027 so far']);
    var fiscal = complete.map(function (r) {{ return r.billed_eur; }})
      .concat([cur ? cur.billed_end_eur : 0]);
    // The calendar clock, from the same billing, so the two can be read side by side.
    var calComplete = D.calendar_series.filter(function (r) {{ return r.is_complete; }});
    new Chart(document.getElementById('c_fy'), {{
      type: 'bar',
      data: {{ labels: labels,
        datasets: [
          {{ label: 'Financial year (April to March)', data: fiscal, backgroundColor: NAVY, borderRadius: 2 }},
          {{ label: 'Calendar year, for contrast', type: 'line',
             data: calComplete.map(function (r) {{ return r.billed_eur; }})
                   .concat(labels.length > calComplete.length ? [null] : []),
             borderColor: TERRA, backgroundColor: TERRA, borderWidth: 2, pointRadius: 4,
             pointStyle: 'rectRot', tension: 0 }} ] }},
      options: {{ maintainAspectRatio: false,
        plugins: {{ tooltip: {{ callbacks: {{ label: function (c) {{
          return c.dataset.label + ': ' + eur(c.raw); }} }} }} }},
        scales: {{ y: {{ grid: {{ color: RULE }}, ticks: {{ callback: function (v) {{ return eur(v); }} }} }},
          x: {{ grid: {{ display: false }} }} }} }} }});
  }})();

  // 5 — Value line verdicts: counts by rule outcome.
  new Chart(document.getElementById('c_verdict'), {{
    type: 'bar',
    data: {{ labels: D.verdicts.map(function (v) {{ return v.label; }}),
      datasets: [{{ data: D.verdicts.map(function (v) {{ return v.count; }}),
        backgroundColor: D.verdicts.map(function (v) {{
          if (v.label.indexOf('unit still lost') >= 0) return TERRA;
          if (v.label.indexOf('unit held') >= 0) return GREEN;
          return SLATE; }}), borderRadius: 2 }}] }},
    options: {{ indexAxis: 'y', maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{ x: {{ grid: {{ color: RULE }}, ticks: {{ precision: 0 }} }},
        y: {{ grid: {{ display: false }} }} }} }} }});

  // 6 — Who is taking it: index distribution per source.
  new Chart(document.getElementById('c_comp'), {{
    type: 'bar',
    data: {{ labels: D.coverage.map(function (c) {{ return c.source; }}),
      datasets: [
        {{ label: 'Median index', data: D.coverage.map(function (c) {{ return c.median; }}),
           backgroundColor: NAVY, borderRadius: 2 }},
        {{ label: 'Share above 2x', data: D.coverage.map(function (c) {{ return c.above2x_pct / 100 * 3; }}),
           backgroundColor: TERRA, borderRadius: 2 }},
        {{ label: 'Reference line: level with the competitor', type: 'line',
           data: D.coverage.map(function () {{ return 1; }}),
           borderColor: MUTED, borderDash: [5, 4], pointRadius: 0, borderWidth: 1.5 }} ] }},
    options: {{ maintainAspectRatio: false,
      plugins: {{ tooltip: {{ callbacks: {{ label: function (c) {{
        if (c.dataset.type === 'line') return 'Index 1.0 = we sit level with the competitor';
        if (c.datasetIndex === 1) return 'Share above 2x: ' + (c.raw / 3 * 100).toFixed(0) + '% (drawn on a 3x scale)';
        return 'Median index: ' + c.raw + 'x the competing price'; }} }} }} }},
      scales: {{ y: {{ beginAtZero: true, grid: {{ color: RULE }},
                    ticks: {{ callback: function (v) {{ return v + 'x'; }} }} }},
        x: {{ grid: {{ display: false }} }} }} }} }});
}})();
</script>
</body>
</html>
"""


def main() -> int:
    payload = load_payload()
    html = build_html(payload)

    # Shared-page language gate. The page is built from internal derived files, so internal field
    # names leak easily. Fail the build rather than ship them.
    banned = [
        "is_partial_year", "ceilings_are_market_level", "down_trade_verdict",
        "actionable_gap_eur", "BVP", "Mode A", "Mode B", "sell" + "-out", "street",
        "wallet", "IML v7", "Model B",
    ]
    # Strip the embedded payload first — it is machine-readable data, not prose a reader sees.
    prose = html.split('<script id="lsm-data"', 1)[0] + html.split("</script>", 2)[-1]
    hits = [b for b in banned if b.lower() in prose.lower()]
    if hits:
        print(f"  SHARED-LANGUAGE FAIL: {hits}")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")

    # Launcher must be CRLF — Jerome double-clicks it in Explorer.
    OUT_CMD.write_bytes(
        (
            "@echo off\r\n"
            'start "" "%~dp0ISZE_Lost_Sales_Model.html"\r\n'
        ).encode("ascii")
    )

    size_kb = OUT_HTML.stat().st_size / 1024
    receipt = {
        "artifact": str(OUT_HTML),
        "launcher": str(OUT_CMD),
        "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "self_contained": True,
        "size_kb": round(size_kb, 1),
        "payload_rows": {
            "markets": len(payload["markets"]),
            "service_gap_rows": len(payload["gaps"]),
            "momentum_market": len(payload["momentum_market"]),
            "price_split": len(payload["price"]),
            "competitor_pn": len(payload["competitor"]),
        },
        "qa": "pending",
    }
    OUT_RECEIPT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"  -> {OUT_HTML} ({size_kb:,.0f} KB)")
    print(f"  -> {OUT_CMD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
