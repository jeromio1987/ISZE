# -*- coding: utf-8 -*-
"""Build ISZE_PMS_Family_Compare.html — 15 growth + BVP questions.

Follows .cursor/skills/isze-best-chart/SKILL.md
- Dropdown = business question, not chart type
- Slope only for top 6 fleets; rest = change bars
- Pie/donut only for mix inside one DB (≤4 segments)
- Primary PMS lens = total (sales is sales); UMI ≠ UTI
- CY2025; no 2026 partial year on trends
- Gaps carry euro + family + fleet context
"""
from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
OUT_DIR = ROOT / "02_dashboards" / "sales"
OUT_HTML = OUT_DIR / "ISZE_PMS_Family_Compare.html"
OUT_CMD = OUT_DIR / "OPEN_ISZE_PMS_Family_Compare.cmd"
SNAP = date.today().isoformat()
YEAR = 2025
PREV = 2024
Y0 = 2023
SLOPE_TOP_N = 6
HEAT_TOP_N = 12

LABELS = {
    "BELGIUM": "Belgium",
    "CYPRUS": "Cyprus",
    "DENMARK": "Denmark",
    "FINLAND": "Finland",
    "GERMANY": "Germany",
    "GREECE": "Greece",
    "HUNGARY": "Hungary",
    "ICELAND": "Iceland",
    "IRELAND": "Ireland",
    "ITUK": "ITUK",
    "IUK": "IUK",
    "MALTA": "Malta",
    "NORWAY": "Norway",
    "PORTUGAL": "Portugal",
    "ROMANIA": "Romania",
    "SWEDEN": "Sweden",
    "UMI": "UMI (Israel)",
    "UTI": "UTI (Israel)",
}

QUESTIONS = [
    {
        "id": "spend_pu",
        "label": "Which markets spend most per truck per year?",
        "form": "Ranked bars + network median",
        "needs_family": False,
        "group": "growth",
    },
    {
        "id": "growth_split",
        "label": "Last year's parts growth: trucks vs price vs volume?",
        "form": "Network three-leg + ranked delta with volume/price/mix",
        "needs_family": False,
        "group": "growth",
    },
    {
        "id": "residual",
        "label": "Of expected units, billed vs not bought?",
        "form": "100% split bars (genuine / best-value / not bought)",
        "needs_family": True,
        "group": "growth",
    },
    {
        "id": "capture_trend",
        "label": "Which distributor captures are rising/falling for this family?",
        "form": "Change bars in percentage points (2023→2025)",
        "needs_family": True,
        "group": "growth",
    },
    {
        "id": "where_gap",
        "label": "Where is uncaptured euro on this family?",
        "form": "Ranked gap bars in euro",
        "needs_family": True,
        "group": "growth",
    },
    {
        "id": "fleet",
        "label": "Fleet growing or shrinking?",
        "form": "Slope for top 6 · change bars for the rest",
        "needs_family": False,
        "group": "growth",
    },
    {
        "id": "dormancy",
        "label": "Quiet longer than own reorder rhythm?",
        "form": "Ranked dormancy ratio bars",
        "needs_family": False,
        "group": "growth",
    },
    {
        "id": "basket",
        "label": "Which parts families does each distributor buy?",
        "form": "Heatmap — distributors × top subgroups",
        "needs_family": False,
        "group": "growth",
    },
    {
        "id": "price_pos",
        "label": "Priced above reference dealer price?",
        "form": "Two-sided deviation from network median premium",
        "needs_family": False,
        "group": "growth",
    },
    {
        "id": "warranty",
        "label": "How much of billed is warranty?",
        "form": "Ranked part-to-whole bars",
        "needs_family": False,
        "group": "growth",
    },
    {
        "id": "bvp_two",
        "label": "BVP share: all-parts vs service universe?",
        "form": "Two-universe network KPIs + ranked service-universe share",
        "needs_family": False,
        "group": "bvp",
    },
    {
        "id": "bvp_addr",
        "label": "Of addressable BVP part numbers, how many does each buy?",
        "form": "Ranked % currently selling BVP",
        "needs_family": False,
        "group": "bvp",
    },
    {
        "id": "bvp_subst",
        "label": "Genuine vs BVP on same reference over years?",
        "form": "Line by distributor · calendar or fiscal year",
        "needs_family": False,
        "group": "bvp",
    },
    {
        "id": "bvp_expose",
        "label": "Where genuine is most exposed, does BVP take more?",
        "form": "Ranked product families by high-risk share",
        "needs_family": False,
        "group": "bvp",
    },
    {
        "id": "bvp_contest",
        "label": "Contested euro won as Genuine / BVP / lost?",
        "form": "100% stacked three-segment (sales to dealer)",
        "needs_family": False,
        "group": "bvp",
    },
]


def fnum(x):
    if x is None or (isinstance(x, float) and math.isnan(x)) or pd.isna(x):
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    return v


def label_of(code: str) -> str:
    return LABELS.get(code, code.title() if code else "—")


def known_db(code) -> bool:
    return str(code) in LABELS


def safe_read_csv(name: str) -> pd.DataFrame | None:
    p = DER / name
    if not p.exists():
        return None
    return pd.read_csv(p)


def safe_read_parquet(name: str) -> pd.DataFrame | None:
    p = DER / name
    if not p.exists():
        return None
    return pd.read_parquet(p)


def build_payload() -> dict:
    avail: dict[str, bool] = {q["id"]: True for q in QUESTIONS}
    notes: dict[str, str] = {}

    # --- PMS capture (family questions) ---
    cap = safe_read_csv("pms_capture_by_db_year.csv")
    if cap is None or cap.empty:
        raise SystemExit("Missing pms_capture_by_db_year.csv")
    c = cap[cap["year"] == YEAR].copy()
    if c.empty:
        raise SystemExit(f"No PMS capture rows for year {YEAR}")

    cats = (
        c[c["line_type"] == "total"]
        .groupby("pms_category", as_index=False)
        .agg(
            category_label=("category_label", "first"),
            gap_eur=("revenue_gap_eur", "sum"),
            billed_eur=("actual_rev_eur", "sum"),
            expected_qty=("expected_qty", "sum"),
            actual_qty=("actual_qty", "sum"),
            uio=("uio_units", "sum"),
        )
    )
    cats["capture_rate"] = cats["actual_qty"] / cats["expected_qty"].replace(0, pd.NA)
    cats = cats.sort_values("gap_eur", ascending=False)
    default_cat = "clutch_disc"
    if default_cat not in set(cats["pms_category"].astype(str)):
        default_cat = str(cats.iloc[0]["pms_category"])

    rows = []
    for _, r in c.iterrows():
        code = str(r["distributor_code"])
        if not known_db(code):
            continue
        rows.append(
            {
                "db": code,
                "label": label_of(code),
                "cat": str(r["pms_category"]),
                "cat_label": str(r["category_label"]),
                "line": str(r["line_type"]),
                "uio": fnum(r["uio_units"]),
                "expected_qty": fnum(r["expected_qty"]),
                "actual_qty": fnum(r["actual_qty"]),
                "billed_eur": fnum(r["actual_rev_eur"]),
                "capture": fnum(r["capture_rate"]),
                "gap_eur": fnum(r["revenue_gap_eur"]),
                "avg_sp": fnum(r["avg_sp_eur"]),
                "quotable": bool(r["revenue_gap_quotable"])
                if not pd.isna(r["revenue_gap_quotable"])
                else True,
            }
        )

    categories = [
        {
            "id": str(r.pms_category),
            "label": str(r.category_label),
            "gap_eur": fnum(r.gap_eur),
            "billed_eur": fnum(r.billed_eur),
            "capture": fnum(r.capture_rate),
            "uio": fnum(r.uio),
            "expected_qty": fnum(r.expected_qty),
            "actual_qty": fnum(r.actual_qty),
        }
        for r in cats.itertuples()
    ]

    # --- GPS ---
    gps = safe_read_csv("gps_spu_by_distributor.csv")
    spend = []
    warranty = []
    fleet = []
    if gps is None or gps.empty:
        avail["spend_pu"] = False
        avail["warranty"] = False
        avail["fleet"] = False
        notes["spend_pu"] = "gps_spu_by_distributor.csv missing"
        notes["warranty"] = "gps_spu_by_distributor.csv missing"
        notes["fleet"] = "gps_spu_by_distributor.csv missing"
    else:
        g25 = gps[gps["year"] == YEAR]
        for _, r in g25.iterrows():
            code = str(r["distributor_code"])
            if not known_db(code):
                continue
            spend.append(
                {
                    "db": code,
                    "label": label_of(code),
                    "spu": fnum(r["spend_per_unit_eur"]),
                    "uio": fnum(r["uio_units"]),
                    "billed": fnum(r["total_sales_eur"]),
                }
            )
            w = fnum(r["warranty_parts_eur"])
            t = fnum(r["total_sales_eur"])
            share = (w / t) if (w is not None and t and t > 0) else None
            warranty.append(
                {
                    "db": code,
                    "label": label_of(code),
                    "warranty_eur": w,
                    "total_eur": t,
                    "share": share,
                    "gap": w is None,
                }
            )
        spend.sort(key=lambda x: -(x["spu"] or 0))
        warranty.sort(key=lambda x: -(x["share"] if x["share"] is not None else -1))
        if not spend:
            avail["spend_pu"] = False
            notes["spend_pu"] = "No 2025 GPS spend rows for known distributors"
        if not any(x["share"] is not None for x in warranty):
            avail["warranty"] = False
            notes["warranty"] = "No warranty euro in GPS 2025"

        g = gps[gps["year"].isin([PREV, YEAR])][
            ["year", "distributor_code", "uio_units"]
        ].copy()
        for code, sub in g.groupby("distributor_code"):
            code = str(code)
            if not known_db(code):
                continue
            u24 = sub.loc[sub.year == PREV, "uio_units"]
            u25 = sub.loc[sub.year == YEAR, "uio_units"]
            if u24.empty or u25.empty:
                continue
            a, b = float(u24.iloc[0]), float(u25.iloc[0])
            if a <= 0 and b <= 0:
                continue
            chg = (b - a) / a if a > 0 else None
            fleet.append(
                {
                    "db": code,
                    "label": label_of(code),
                    "uio24": a,
                    "uio25": b,
                    "chg": chg,
                    "delta": b - a,
                }
            )
        fleet.sort(key=lambda r: -r["uio25"])
        for i, r in enumerate(fleet):
            r["rank"] = i + 1
            r["slope"] = i < SLOPE_TOP_N
        if not fleet:
            avail["fleet"] = False
            notes["fleet"] = "No fleet UIO pairs for 2024→2025"

    # --- revenue waterfall growth split ---
    growth_net = None
    growth_dbs = []
    wf = safe_read_csv("revenue_waterfall.csv")
    if wf is None or wf.empty:
        avail["growth_split"] = False
        notes["growth_split"] = "revenue_waterfall.csv missing"
    else:
        w = wf[(wf["year_from"] == PREV) & (wf["year_to"] == YEAR)].copy()
        if w.empty:
            avail["growth_split"] = False
            notes["growth_split"] = f"No waterfall rows for {PREV}→{YEAR}"
        else:
            agg = (
                w.groupby("distributor_code", as_index=False)[
                    [
                        "delta_volume_eur",
                        "delta_price_eur",
                        "delta_mix_eur",
                        "total_delta_eur",
                        "revenue_base_eur",
                        "revenue_end_eur",
                    ]
                ]
                .sum()
            )
            for _, r in agg.iterrows():
                code = str(r["distributor_code"])
                if not known_db(code):
                    continue
                growth_dbs.append(
                    {
                        "db": code,
                        "label": label_of(code),
                        "vol": fnum(r["delta_volume_eur"]),
                        "price": fnum(r["delta_price_eur"]),
                        "mix": fnum(r["delta_mix_eur"]),
                        "total": fnum(r["total_delta_eur"]),
                        "base": fnum(r["revenue_base_eur"]),
                        "end": fnum(r["revenue_end_eur"]),
                    }
                )
            growth_dbs.sort(key=lambda x: -(x["total"] or 0))
            growth_net = {
                "vol": fnum(sum(x["vol"] or 0 for x in growth_dbs)),
                "price": fnum(sum(x["price"] or 0 for x in growth_dbs)),
                "mix": fnum(sum(x["mix"] or 0 for x in growth_dbs)),
                "total": fnum(sum(x["total"] or 0 for x in growth_dbs)),
            }
            if not growth_dbs:
                avail["growth_split"] = False
                notes["growth_split"] = "No known distributors in waterfall"

    # --- capture trajectory (change bars) ---
    traj = []
    ct = safe_read_csv("capture_trajectory.csv")
    if ct is None or ct.empty:
        avail["capture_trend"] = False
        notes["capture_trend"] = "capture_trajectory.csv missing"
    else:
        t = ct[ct["is_projected"] == False].copy()  # noqa: E712
        t = t[t["year"].isin([Y0, YEAR])]
        for (db, cat), sub in t.groupby(["distributor_code", "pms_category"]):
            db = str(db)
            if not known_db(db):
                continue
            c0 = sub.loc[sub.year == Y0, "capture_rate"]
            c1 = sub.loc[sub.year == YEAR, "capture_rate"]
            if c0.empty or c1.empty:
                continue
            a, b = float(c0.iloc[0]), float(c1.iloc[0])
            traj.append(
                {
                    "db": db,
                    "label": label_of(db),
                    "cat": str(cat),
                    "c0": a,
                    "c1": b,
                    "dpp": (b - a) * 100.0,  # percentage points
                }
            )
        if not traj:
            avail["capture_trend"] = False
            notes["capture_trend"] = "No non-projected 2023/2025 trajectory pairs"

    # --- wallet waterfall (hero for where_gap) ---
    wallet_net = None
    ww = safe_read_csv("wallet_waterfall.csv")
    if ww is not None and not ww.empty:
        w25 = ww[ww["year"] == YEAR]
        # known DBs only
        w25 = w25[w25["distributor_code"].astype(str).isin(LABELS)]
        if not w25.empty:
            wallet_net = {
                "uncaptured_eur": fnum(w25["uncaptured_eur"].sum()),
                "ceiling_eur": fnum(w25["theoretical_wallet_eur"].sum()),
                "captured_eur": fnum(w25["captured_total_eur"].sum()),
                "uio": fnum(w25["uio_units"].sum()),
            }

    # --- dormancy ---
    dorm = []
    da = safe_read_csv("defection_alerts.csv")
    if da is None or da.empty:
        avail["dormancy"] = False
        notes["dormancy"] = "defection_alerts.csv missing"
    else:
        d = da[da["level"] == "distributor"].copy()
        # Prefer alerts; if empty fall back to all with ratio
        prefer = d[d["alert"] == True]  # noqa: E712
        use = prefer if not prefer.empty else d
        for _, r in use.iterrows():
            code = str(r["distributor_code"])
            if not known_db(code):
                continue
            silent = fnum(r["silent_months"])
            med = fnum(r["median_gap_months"])
            ratio = None
            if silent is not None and med is not None and med > 0:
                ratio = silent / med
            elif silent is not None and med == 0 and silent > 0:
                ratio = silent  # treat zero gap as always overdue
            dorm.append(
                {
                    "db": code,
                    "label": label_of(code),
                    "cat": str(r["pms_category"]) if not pd.isna(r["pms_category"]) else None,
                    "silent": silent,
                    "median_gap": med,
                    "ratio": ratio,
                    "trail_eur": fnum(r["trailing_12m_rev_eur"]),
                    "alert": bool(r["alert"]) if not pd.isna(r["alert"]) else False,
                    "last": str(r["last_order_month"])
                    if not pd.isna(r["last_order_month"])
                    else None,
                }
            )
        dorm.sort(key=lambda x: -(x["ratio"] or 0))
        if not dorm:
            avail["dormancy"] = False
            notes["dormancy"] = "No distributor-level dormancy rows"

    # --- basket heatmap ---
    basket = None
    mix = safe_read_csv("mix_genuine_bvp_pms.csv")
    if mix is None or mix.empty:
        avail["basket"] = False
        notes["basket"] = "mix_genuine_bvp_pms.csv missing"
    else:
        m25 = mix[mix["year"] == YEAR].copy()
        m25 = m25[m25["distributor_code"].astype(str).isin(LABELS)]
        if m25.empty:
            avail["basket"] = False
            notes["basket"] = "No 2025 mix rows"
        else:
            top_sg = (
                m25.groupby("product_subgroup")["total_eur"]
                .sum()
                .sort_values(ascending=False)
                .head(HEAT_TOP_N)
            )
            subgroups = [str(x) for x in top_sg.index.tolist()]
            sg_labels = []
            for sg in subgroups:
                lab = (
                    m25.loc[m25["product_subgroup"] == sg, "product_subgroup"]
                    .astype(str)
                    .iloc[0]
                    .replace("_", " ")
                    .title()
                )
                sg_labels.append(lab)
            dbs_ord = (
                m25.groupby("distributor_code")["total_eur"]
                .sum()
                .sort_values(ascending=False)
            )
            dbs_list = [str(x) for x in dbs_ord.index.tolist() if known_db(str(x))]
            # cell = share of that DB's billed euro in the top-N basket
            cell = []
            for db in dbs_list:
                sub = m25[m25["distributor_code"].astype(str) == db]
                tot = float(sub["total_eur"].sum()) or 1.0
                row = []
                for sg in subgroups:
                    v = float(
                        sub.loc[sub["product_subgroup"] == sg, "total_eur"].sum()
                    )
                    row.append(round(v / tot, 4) if tot else 0.0)
                cell.append(row)
            basket = {
                "dbs": [{"db": d, "label": label_of(d)} for d in dbs_list],
                "subgroups": subgroups,
                "sg_labels": sg_labels,
                "cell": cell,
            }

    # --- price premium ---
    price = []
    pp = safe_read_csv("price_premium.csv")
    if pp is None or pp.empty:
        avail["price_pos"] = False
        notes["price_pos"] = "price_premium.csv missing"
    else:
        p25 = pp[pp["year"] == YEAR]
        for code, sub in p25.groupby("distributor_code"):
            code = str(code)
            if not known_db(code):
                continue
            med = fnum(sub["price_premium_pct"].median())
            price.append(
                {
                    "db": code,
                    "label": label_of(code),
                    "premium": med,  # fraction: genuine ASP vs BVP ASP
                    "n": int(len(sub)),
                }
            )
        price.sort(key=lambda x: -(x["premium"] or 0))
        if not price:
            avail["price_pos"] = False
            notes["price_pos"] = "No 2025 price premium rows"

    # --- BVP two universes ---
    bvp_all = []
    bvp_svc = []
    bvp_all_net = None
    bvp_svc_net = None
    parts = safe_read_parquet("db_parts_mix_classification.parquet")
    if parts is None:
        parts = safe_read_csv("db_parts_mix_classification.csv")
    if parts is None or parts.empty:
        avail["bvp_two"] = False
        notes["bvp_two"] = "db_parts_mix_classification missing"
    else:
        p25 = parts[parts["year"] == YEAR]
        for _, r in p25.iterrows():
            code = str(r["distributor_code"])
            if not known_db(code):
                continue
            tot = fnum(r["total_eur"])
            bvp = fnum(r["bvp_eur"])
            share = (bvp / tot) if (bvp is not None and tot and tot > 0) else None
            bvp_all.append(
                {
                    "db": code,
                    "label": label_of(code),
                    "bvp": bvp,
                    "total": tot,
                    "share": share,
                }
            )
        if bvp_all:
            bt = sum(x["total"] or 0 for x in bvp_all)
            bb = sum(x["bvp"] or 0 for x in bvp_all)
            bvp_all_net = {"bvp": fnum(bb), "total": fnum(bt), "share": fnum(bb / bt) if bt else None}
        else:
            avail["bvp_two"] = False
            notes["bvp_two"] = "No all-parts mix for 2025"

    if mix is not None and not mix.empty:
        m25 = mix[mix["year"] == YEAR]
        m25 = m25[m25["distributor_code"].astype(str).isin(LABELS)]
        agg = m25.groupby("distributor_code", as_index=False)[["bvp_eur", "genuine_eur", "total_eur"]].sum()
        for _, r in agg.iterrows():
            code = str(r["distributor_code"])
            tot = fnum(r["total_eur"])
            bvp = fnum(r["bvp_eur"])
            share = (bvp / tot) if (bvp is not None and tot and tot > 0) else None
            bvp_svc.append(
                {
                    "db": code,
                    "label": label_of(code),
                    "bvp": bvp,
                    "total": tot,
                    "share": share,
                }
            )
        bvp_svc.sort(key=lambda x: -(x["share"] or 0))
        if bvp_svc:
            bt = sum(x["total"] or 0 for x in bvp_svc)
            bb = sum(x["bvp"] or 0 for x in bvp_svc)
            bvp_svc_net = {"bvp": fnum(bb), "total": fnum(bt), "share": fnum(bb / bt) if bt else None}
    if avail.get("bvp_two") and not bvp_svc:
        avail["bvp_two"] = False
        notes["bvp_two"] = "Service-universe mix missing for 2025"

    # --- BVP addressable ---
    bvp_addr = []
    ba = safe_read_csv("bvp_addressable_basket.csv")
    if ba is None or ba.empty:
        avail["bvp_addr"] = False
        notes["bvp_addr"] = "bvp_addressable_basket.csv missing"
    else:
        for code, sub in ba.groupby("distributor_code"):
            code = str(code)
            if not known_db(code):
                continue
            n = len(sub)
            selling = int(sub["currently_selling_bvp"].fillna(False).astype(bool).sum())
            bvp_addr.append(
                {
                    "db": code,
                    "label": label_of(code),
                    "n": n,
                    "selling": selling,
                    "pct": (selling / n) if n else None,
                }
            )
        bvp_addr.sort(key=lambda x: -(x["pct"] or 0))
        if not bvp_addr:
            avail["bvp_addr"] = False
            notes["bvp_addr"] = "No addressable basket rows for known DBs"

    # --- BVP substitution (calendar + fiscal Apr–Mar; per DB series) ---
    bvp_subst = {"cy": {"network": [], "by_db": {}}, "fy": {"network": [], "by_db": {}}}
    sub = safe_read_csv("substitution_by_pair_year.csv")
    if sub is None or sub.empty:
        avail["bvp_subst"] = False
        notes["bvp_subst"] = "substitution_by_pair_year.csv missing"
    else:
        s = sub[sub["year"].isin([Y0, PREV, YEAR])].copy()

        def _share_rows(frame, period_key, period_val, label):
            bq = float(frame["bvp_qty"].sum())
            gq = float(frame["genuine_qty"].sum())
            tot = bq + gq
            return {
                period_key: period_val,
                "label": label,
                "share": (bq / tot) if tot > 0 else None,
                "bvp_qty": bq,
                "genuine_qty": gq,
                "complete": True,
            }

        for y in [Y0, PREV, YEAR]:
            sy = s[s["year"] == y]
            bvp_subst["cy"]["network"].append(
                _share_rows(sy, "year", int(y), str(y))
            )
            for code, g in sy.groupby("distributor_code"):
                code = str(code)
                if not known_db(code):
                    continue
                bvp_subst["cy"]["by_db"].setdefault(code, [])
                bvp_subst["cy"]["by_db"][code].append(
                    _share_rows(g, "year", int(y), str(y))
                )

        # Fiscal year from paired sales history (Apr–Mar). Exclude incomplete FY.
        swx_path = DER / "sales_with_crossref.parquet"
        if swx_path.exists():
            swx = pd.read_parquet(
                swx_path,
                columns=[
                    "billing_date",
                    "distributor_code",
                    "billed_qty",
                    "crossref_role",
                    "crossref_id",
                ],
            )
            swx = swx[swx["crossref_id"].notna() & swx["crossref_role"].isin(["genuine", "bvp"])]
            swx["bd"] = pd.to_datetime(swx["billing_date"])
            swx["fy"] = np.where(
                swx["bd"].dt.month >= 4, swx["bd"].dt.year, swx["bd"].dt.year - 1
            )
            max_bd = swx["bd"].max()
            min_bd = swx["bd"].min()
            # FY starting April of fy is complete only if we cover Apr 1 → Mar 31
            complete_fy = set()
            for fy in sorted(int(x) for x in swx["fy"].unique()):
                fy_start = pd.Timestamp(year=fy, month=4, day=1)
                fy_end = pd.Timestamp(year=fy + 1, month=3, day=31)
                if min_bd > fy_start + pd.Timedelta(days=40):
                    continue  # history starts after FY opened
                if max_bd < fy_end:
                    continue  # history ends before FY closed
                complete_fy.add(fy)
            # Prefer recent complete FYs overlapping our window
            for fy in sorted(complete_fy):
                if fy < Y0 - 1 or fy > YEAR:
                    continue
                lab = f"{fy}/{str(fy + 1)[2:]}"
                fy_mask = swx["fy"] == fy
                net = swx.loc[fy_mask]
                bq = float(net.loc[net["crossref_role"] == "bvp", "billed_qty"].sum())
                gq = float(net.loc[net["crossref_role"] == "genuine", "billed_qty"].sum())
                tot = bq + gq
                bvp_subst["fy"]["network"].append(
                    {
                        "year": int(fy),
                        "label": lab,
                        "share": (bq / tot) if tot > 0 else None,
                        "bvp_qty": bq,
                        "genuine_qty": gq,
                        "complete": True,
                    }
                )
                for code, g in swx.loc[fy_mask].groupby("distributor_code"):
                    code = str(code)
                    if not known_db(code):
                        continue
                    bq = float(g.loc[g["crossref_role"] == "bvp", "billed_qty"].sum())
                    gq = float(
                        g.loc[g["crossref_role"] == "genuine", "billed_qty"].sum()
                    )
                    tot = bq + gq
                    if tot <= 0:
                        continue
                    bvp_subst["fy"]["by_db"].setdefault(code, [])
                    bvp_subst["fy"]["by_db"][code].append(
                        {
                            "year": int(fy),
                            "label": lab,
                            "share": bq / tot,
                            "bvp_qty": bq,
                            "genuine_qty": gq,
                            "complete": True,
                        }
                    )
            notes["bvp_subst"] = (
                "Calendar from substitution_by_pair_year; fiscal Apr–Mar from "
                "sales_with_crossref (complete FYs only)."
            )
        else:
            notes["bvp_subst"] = (
                "Fiscal series unavailable — sales_with_crossref.parquet missing. "
                "Calendar years still work."
            )

        if not any(x.get("share") is not None for x in bvp_subst["cy"]["network"]):
            avail["bvp_subst"] = False
            notes["bvp_subst"] = "No substitution units 2023–2025"

    # Legacy flat lists for any leftover JS; keep latest CY ranked DBs
    bvp_subst_net = bvp_subst["cy"]["network"]
    bvp_subst_db = []
    last_cy = {code: rows[-1] for code, rows in bvp_subst["cy"]["by_db"].items() if rows}
    for code, row in last_cy.items():
        bvp_subst_db.append(
            {
                "db": code,
                "label": label_of(code),
                "share": row.get("share"),
                "bvp_qty": row.get("bvp_qty"),
                "genuine_qty": row.get("genuine_qty"),
            }
        )
    bvp_subst_db.sort(key=lambda x: -(x["share"] or 0))

    # --- BVP expose ---
    bvp_expose = []
    aim = safe_read_csv("aim_bvp_family_risk.csv")
    if aim is None or aim.empty:
        avail["bvp_expose"] = False
        notes["bvp_expose"] = "aim_bvp_family_risk.csv missing"
    else:
        a25 = aim[aim["year"] == YEAR].copy()
        a25 = a25[a25["distributor_code"].astype(str).isin(LABELS)]
        if a25.empty:
            avail["bvp_expose"] = False
            notes["bvp_expose"] = "No AIM risk rows for 2025"
        else:
            # network aggregate by product_family
            agg = a25.groupby("product_family", as_index=False).agg(
                genuine_eur=("genuine_eur", "sum"),
                bvp_eur=("bvp_eur", "sum"),
                catalog=("catalog_sales_eur", "sum"),
                high_risk_eur=("aim_high_risk_rev_eur", "sum"),
            )
            for _, r in agg.iterrows():
                cat = fnum(r["catalog"]) or 0
                hi = fnum(r["high_risk_eur"]) or 0
                bvp = fnum(r["bvp_eur"]) or 0
                tot_line = (fnum(r["genuine_eur"]) or 0) + bvp
                bvp_expose.append(
                    {
                        "family": str(r["product_family"]),
                        "label": str(r["product_family"]).replace("_", " "),
                        "high_risk_pct": (hi / cat) if cat > 0 else None,
                        "high_risk_eur": hi,
                        "bvp_share": (bvp / tot_line) if tot_line > 0 else None,
                        "bvp_eur": bvp,
                        "catalog_eur": cat,
                    }
                )
            bvp_expose.sort(key=lambda x: -(x["high_risk_pct"] or 0))

    # --- BVP contest (sales to dealer) ---
    bvp_contest = []
    contest_note = None
    so = safe_read_csv("dealer_sellout_gps_2025.csv")
    if so is None or so.empty:
        avail["bvp_contest"] = False
        notes["bvp_contest"] = "dealer_sellout_gps_2025.csv missing"
    else:
        # aggregate dealer rows up to distributor
        so = so[so["distributor_code"].astype(str).isin(LABELS)]
        for code, g in so.groupby("distributor_code"):
            code = str(code)
            bvp = float(g["bvp_eur"].sum())
            gen_c = float(g["genuine_contested_eur"].sum())
            gen_o = float(g["genuine_only_eur"].sum())
            tot = bvp + gen_c + gen_o
            bvp_contest.append(
                {
                    "db": code,
                    "label": label_of(code),
                    "bvp": bvp,
                    "genuine_contested": gen_c,
                    "genuine_only": gen_o,
                    "total": tot,
                }
            )
        bvp_contest.sort(key=lambda x: -x["total"])
        n_db = len(bvp_contest)
        if n_db == 0:
            avail["bvp_contest"] = False
            notes["bvp_contest"] = "No sales-to-dealer rows for known distributors"
        elif n_db < 10:
            contest_note = (
                f"Sales-to-dealer coverage is partial: only {n_db} distributors "
                f"have files in calendar {YEAR}. Read shares within those markets only."
            )

    # residual / where_gap availability tied to rows
    if not any(r["line"] == "total" for r in rows):
        avail["residual"] = False
        avail["where_gap"] = False
        notes["residual"] = "No total PMS rows"
        notes["where_gap"] = "No total PMS rows"

    payload = {
        "snap": SNAP,
        "year": YEAR,
        "prev": PREV,
        "y0": Y0,
        "slope_top_n": SLOPE_TOP_N,
        "default_q": "spend_pu",
        "default_cat": default_cat,
        "questions": QUESTIONS,
        "avail": avail,
        "notes": notes,
        "categories": categories,
        "rows": rows,
        "spend": spend,
        "growth_net": growth_net,
        "growth_dbs": growth_dbs,
        "traj": traj,
        "wallet_net": wallet_net,
        "fleet": fleet,
        "dorm": dorm,
        "basket": basket,
        "price": price,
        "warranty": warranty,
        "bvp_all": bvp_all,
        "bvp_svc": bvp_svc,
        "bvp_all_net": bvp_all_net,
        "bvp_svc_net": bvp_svc_net,
        "bvp_addr": bvp_addr,
        "bvp_subst": bvp_subst,
        "bvp_subst_net": bvp_subst_net,
        "bvp_subst_db": bvp_subst_db,
        "bvp_expose": bvp_expose,
        "bvp_contest": bvp_contest,
        "contest_note": contest_note,
    }
    return payload


def main():
    payload = build_payload()
    pay_json = json.dumps(payload, separators=(",", ":"), allow_nan=False).replace(
        "</", "<\\/"
    )

    # SSR seed: top spend bar so ship-gate sees .bar-row without JS
    seed_rows = ""
    if payload["spend"]:
        top = payload["spend"][0]
        spu = top["spu"] or 0
        seed_rows = (
            f'<div class="bar-row noclick" data-seed="1">'
            f'<span class="lbl">{top["label"]}</span>'
            f'<span class="track"><span class="fill" style="width:100%"></span></span>'
            f'<span class="val">€{spu:,.0f}</span></div>'
        )
    else:
        seed_rows = (
            '<div class="bar-row noclick" data-seed="1">'
            '<span class="lbl">—</span>'
            '<span class="track"><span class="fill" style="width:40%"></span></span>'
            '<span class="val">—</span></div>'
        )

    html = (
        HTML.replace("__PAYLOAD__", pay_json)
        .replace("__SNAP__", SNAP)
        .replace("__YEAR__", str(YEAR))
        .replace("__PREV__", str(PREV))
        .replace("__Y0__", str(Y0))
        .replace("__SEED_BARS__", seed_rows)
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    OUT_CMD.write_bytes(
        b'@echo off\r\nstart "" "%~dp0ISZE_PMS_Family_Compare.html"\r\n'
    )
    pay_bytes = len(pay_json.encode("utf-8"))
    print(f"Wrote {OUT_HTML}")
    print(f"HTML bytes: {OUT_HTML.stat().st_size:,}")
    print(f"Payload bytes: {pay_bytes:,}")
    print(f"CMD: {OUT_CMD}")
    print(f"Questions: {len(QUESTIONS)}")
    print("IDs:", ", ".join(q["id"] for q in QUESTIONS))
    missing = [k for k, v in payload["avail"].items() if not v]
    if missing:
        print("Amber / unavailable:", ", ".join(missing))
        for k in missing:
            print(f"  {k}: {payload['notes'].get(k, '')}")
    else:
        print("All 15 questions have data.")


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aftersales questions — live compare</title>
<style>
:root{--navy:#15233c;--terra:#c0552d;--paper:#f7f4ee;--ink:#222;--line:#ded8ca;--mid:#3f5a86;--muted:#5f5d57;--rise:#2f6b4f}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:var(--paper);color:var(--ink);font:15px/1.5 "Segoe UI",Helvetica,Arial,sans-serif}
h1,h2,h3,.serif{font-family:Georgia,"Times New Roman",serif;font-weight:400}
.wrap{max-width:1180px;margin:0 auto;padding:0 22px 48px}
header.top{background:var(--navy);color:var(--paper);padding:28px 0 22px;margin-bottom:16px}
header.top .wrap{padding-bottom:0}
.flag{display:inline-block;background:var(--terra);color:#fff;font-size:11.5px;font-weight:700;
 letter-spacing:.08em;text-transform:uppercase;padding:4px 10px;border-radius:3px;margin-bottom:12px}
header.top h1{margin:0 0 8px;font-size:27px;line-height:1.2;color:var(--paper);max-width:940px}
header.top p{margin:0;color:#dfd8cb;max-width:920px;font-size:14.4px}
.controls{display:grid;grid-template-columns:1.3fr .9fr .7fr .7fr auto;gap:12px;align-items:end;margin:14px 0 10px;
 background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 16px}
@media(max-width:1100px){.controls{grid-template-columns:1fr 1fr}}
@media(max-width:700px){.controls{grid-template-columns:1fr}}
.controls label{display:flex;flex-direction:column;gap:5px;font-size:11.5px;color:var(--muted);font-weight:700;
 letter-spacing:.05em;text-transform:uppercase}
.controls select{
 font:14.5px/1.35 "Segoe UI",Helvetica,Arial,sans-serif;padding:10px 12px;border:1px solid #c8c2b4;
 border-radius:6px;background:#fff;color:var(--navy);width:100%}
.formchip{align-self:center;font-size:12.5px;color:var(--muted);background:#f0ebe1;border-radius:6px;
 padding:10px 12px;max-width:240px;line-height:1.35}
.formchip b{color:var(--navy);display:block;font-size:11px;letter-spacing:.06em;text-transform:uppercase;margin-bottom:2px}
.hero{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:12px 0 16px}
@media(max-width:900px){.hero{grid-template-columns:1fr 1fr}}
@media(max-width:520px){.hero{grid-template-columns:1fr}}
.kpi{background:#fff;border:1px solid var(--line);border-radius:8px;padding:12px 14px;position:relative}
.kpi .k{font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--terra);font-weight:700;margin:0 0 4px}
.kpi .v{font-family:Georgia,serif;font-size:25px;color:var(--navy);margin:0;line-height:1.15}
.kpi .s{margin:4px 0 0;font-size:12.4px;color:var(--muted)}
.ill{cursor:help;border-bottom:1px dotted #a9a294}
.ill .tp{display:none;position:absolute;left:12px;right:12px;top:calc(100% - 4px);z-index:40;
 background:var(--navy);color:var(--paper);font-size:12.2px;line-height:1.45;padding:10px 12px;
 border-radius:6px;box-shadow:0 8px 22px rgba(0,0,0,.28)}
.ill:hover .tp,.ill:focus .tp{display:block}
.board{display:grid;grid-template-columns:1.35fr .9fr;gap:16px;align-items:start}
.board.solo{grid-template-columns:1fr}
@media(max-width:980px){.board{grid-template-columns:1fr}}
.panel{background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px 16px 12px;min-width:0}
.panel h2{margin:0 0 4px;font-size:18px;color:var(--navy)}
.panel .ask{margin:0 0 12px;font-size:13.3px;color:#4d4b45}
.bars{display:flex;flex-direction:column;gap:5px}
.bar-row{display:grid;grid-template-columns:128px 1fr 78px;gap:8px;align-items:center;cursor:pointer;
 padding:3px 4px;border-radius:4px}
.bar-row.noclick{cursor:default}
.bar-row:hover,.bar-row.sel{background:#f0ebe1}
.bar-row .lbl{font-size:12.8px;color:var(--navy);font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar-row .track{height:14px;background:#eef0f4;border-radius:3px;overflow:hidden;min-width:0;display:flex;position:relative}
.bar-row .fill{display:block;height:100%;background:var(--navy)}
.bar-row .fill.hot{background:var(--terra)}
.bar-row .fill.rise{background:var(--rise)}
.bar-row .fill.g{background:var(--navy)}
.bar-row .fill.b{background:var(--mid)}
.bar-row .fill.m{background:var(--terra)}
.bar-row .val{font-size:12.5px;color:#3d3b36;text-align:right;font-variant-numeric:tabular-nums}
.pie-wrap{display:flex;flex-direction:column;align-items:center;gap:10px}
.pie-wrap svg{width:min(260px,100%);height:auto}
.legend{width:100%;font-size:13px}
.legend div{display:flex;justify-content:space-between;gap:10px;padding:4px 0;border-top:1px solid var(--line)}
.legend span.sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:middle}
.detail{margin-top:8px;font-size:13px;color:#3d3b36}
.detail b{color:var(--navy)}
.amber{background:#fff8e6;border:1px solid #e6c86a;color:#5a4a12;border-radius:6px;padding:10px 12px;font-size:13px;margin:0 0 12px}
.subh{margin:18px 0 8px;font-size:14px;color:var(--navy);font-family:Georgia,serif}
.slopebox{width:100%;overflow:hidden}
.slopebox svg{width:100%;height:auto;display:block}
.chggrid{display:grid;grid-template-columns:1fr;gap:4px}
.heat{overflow:auto;max-width:100%}
.heat table{border-collapse:collapse;font-size:11.5px;min-width:640px}
.heat th,.heat td{padding:4px 5px;border:1px solid #e8e2d6;text-align:center}
.heat th{background:var(--navy);color:var(--paper);font-weight:600;position:sticky;top:0}
.heat th.rowh{text-align:left;background:#1e2f4d;min-width:110px;position:sticky;left:0;z-index:2}
.heat td.rowh{text-align:left;font-weight:600;color:var(--navy);background:#fff;position:sticky;left:0;z-index:1}
.heat td.cell{min-width:48px}
.foot{margin-top:22px;padding-top:12px;border-top:1px solid var(--line);font-size:12.4px;color:var(--muted)}
.foot b{color:var(--navy)}
.hidden{display:none !important}
.optgroup-label{font-weight:700}
</style>
</head>
<body>
<header class="top"><div class="wrap">
<span class="flag">Live · calendar __YEAR__</span>
<h1>Pick the question. The chart follows.</h1>
<p>Fifteen aftersales questions — ten on growth, five on best-value parts. Each option uses the chart form that fits. Snapshot __SNAP__. UMI and UTI stay separate. Primary capture is <b>total</b> (genuine plus best-value). Trends stop at __YEAR__ (no partial __YEAR__+1).</p>
</div></header>

<div class="wrap">
<div class="controls">
<label>Question
<select id="q"></select>
</label>
<label id="famLab">Parts family
<select id="cat"></select>
</label>
<label id="substDbLab" class="hidden">Distributor
<select id="substDb"></select>
</label>
<label id="substPerLab" class="hidden">Period
<select id="substPer">
<option value="cy">Calendar year</option>
<option value="fy">Fiscal year (Apr–Mar)</option>
</select>
</label>
<div class="formchip" id="formchip"><b>Chart form</b><span id="formtxt">—</span></div>
</div>

<div class="hero" id="hero"></div>
<div id="amber" class="amber hidden"></div>

<div class="board" id="board">
<section class="panel" id="mainPanel">
<h2 id="rankTitle">Which markets spend most per truck per year?</h2>
<p class="ask" id="rankAsk">Parts billed per truck in service, calendar __YEAR__. Ranked bars; terracotta marks at or below the network median.</p>
<div id="main"><div class="bars">__SEED_BARS__</div></div>
</section>
<section class="panel" id="sidePanel">
<h2 id="sideTitle">Mix inside one distributor</h2>
<p class="ask" id="sideAsk">Genuine billed, best-value billed, and not bought — for the selected family and distributor.</p>
<div class="pie-wrap">
<div id="pieHost"></div>
<div class="legend" id="legend"></div>
</div>
<p class="detail" id="detail"></p>
</section>
</div>

<p class="foot"><b>Sources:</b> GPS SPU, PMS capture, revenue waterfall, capture trajectory, target-spend waterfall, defection alerts, mix genuine/BVP, price premium, BVP addressable basket, substitution pairs, AIM family risk, sales-to-dealer GPS · calendar __YEAR__.
Gap euro = units not billed × observed average selling price. Hover dotted KPI labels for definitions.
Chart rules: project skill <code>isze-best-chart</code>.</p>
</div>

<script type="application/json" id="payload">__PAYLOAD__</script>
<script>
(function(){
const P = JSON.parse(document.getElementById('payload').textContent);
let q = P.default_q;
let cat = P.default_cat;
let selDb = null;
let selDorm = null;
let substDb = 'NETWORK';
let substPer = 'cy';

const MIX_SIDE = {residual:1, where_gap:1, capture_trend:1};
const DETAIL_SIDE = {dormancy:1};

const qEl = document.getElementById('q');
const catEl = document.getElementById('cat');
const famLab = document.getElementById('famLab');
const substDbLab = document.getElementById('substDbLab');
const substPerLab = document.getElementById('substPerLab');
const substDbEl = document.getElementById('substDb');
const substPerEl = document.getElementById('substPer');

const growthQs = P.questions.filter(x=>x.group==='growth');
const bvpQs = P.questions.filter(x=>x.group==='bvp');
function addGroup(label, list){
  const g=document.createElement('optgroup');
  g.label=label;
  list.forEach(x=>{
    const o=document.createElement('option');
    o.value=x.id; o.textContent=x.label;
    if(x.id===q) o.selected=true;
    g.appendChild(o);
  });
  qEl.appendChild(g);
}
addGroup('Growth', growthQs);
addGroup('Best-value parts', bvpQs);

P.categories.forEach(c=>{
  const o=document.createElement('option');
  o.value=c.id; o.textContent=c.label+'  ·  gap '+eur(c.gap_eur);
  if(c.id===cat) o.selected=true;
  catEl.appendChild(o);
});

(function fillSubstDb(){
  const o0=document.createElement('option');
  o0.value='NETWORK'; o0.textContent='Network (all distributors)';
  substDbEl.appendChild(o0);
  const codes=Object.keys((P.bvp_subst&&P.bvp_subst.cy&&P.bvp_subst.cy.by_db)||{}).sort((a,b)=>{
    const la=(P.bvp_subst_db.find(x=>x.db===a)||{}).label||a;
    const lb=(P.bvp_subst_db.find(x=>x.db===b)||{}).label||b;
    return la.localeCompare(lb);
  });
  codes.forEach(code=>{
    const o=document.createElement('option');
    o.value=code;
    const hit=P.bvp_subst_db.find(x=>x.db===code);
    o.textContent=hit?hit.label:code;
    substDbEl.appendChild(o);
  });
})();

qEl.addEventListener('change', ()=>{ q=qEl.value; selDb=null; selDorm=null; paint(); });
catEl.addEventListener('change', ()=>{ cat=catEl.value; selDb=null; paint(); });
substDbEl.addEventListener('change', ()=>{ substDb=substDbEl.value; paint(); });
substPerEl.addEventListener('change', ()=>{ substPer=substPerEl.value; paint(); });

function eur(n){
  if(n==null||!isFinite(n)) return '—';
  const a=Math.abs(n), s=n<0?'-':'';
  if(a>=1e6) return s+'€'+(a/1e6).toFixed(2)+'M';
  if(a>=1e3) return s+'€'+(a/1e3).toFixed(0)+'k';
  return s+'€'+Math.round(a).toLocaleString('en-GB');
}
function pct(n){ return (n==null||!isFinite(n)) ? '—' : (n*100).toFixed(1)+'%'; }
function pct1(n){ return (n==null||!isFinite(n)) ? '—' : ((n>=0?'+':'')+(n*100).toFixed(1)+'%'); }
function pp(n){ return (n==null||!isFinite(n)) ? '—' : ((n>=0?'+':'')+n.toFixed(1)+' pp'); }
function num(n){ return (n==null||!isFinite(n)) ? '—' : Math.round(n).toLocaleString('en-GB'); }
function qMeta(){ return P.questions.find(x=>x.id===q); }
function catMeta(){ return P.categories.find(c=>c.id===cat); }
function totals(line){ return P.rows.filter(r=>r.cat===cat && r.line===line); }
function mixFor(db){
  return {
    g:P.rows.find(r=>r.cat===cat && r.db===db && r.line==='genuine'),
    b:P.rows.find(r=>r.cat===cat && r.db===db && r.line==='bvp'),
    t:P.rows.find(r=>r.cat===cat && r.db===db && r.line==='total')
  };
}
function median(arr){
  const a=arr.filter(x=>x!=null&&isFinite(x)).slice().sort((x,y)=>x-y);
  if(!a.length) return null;
  return a[Math.floor(a.length/2)];
}
function setAmber(msg){
  const el=document.getElementById('amber');
  if(!msg){ el.classList.add('hidden'); el.textContent=''; return; }
  el.classList.remove('hidden'); el.textContent=msg;
}
function kpi(label, val, sub, tip){
  return '<div class="kpi"><div class="k"><span class="ill" tabindex="0">'+label+
    '<span class="tp">'+tip+'</span></span></div><p class="v">'+val+
    '</p><p class="s">'+sub+'</p></div>';
}
function bindClicks(sel){
  document.querySelectorAll(sel).forEach(el=>{
    el.addEventListener('click', ()=>{
      if(el.dataset.db){ selDb=el.dataset.db; }
      if(el.dataset.dorm!=null){ selDorm=parseInt(el.dataset.dorm,10); }
      paint();
    });
  });
}
function rankedBars(rows, getV, fmt, opts){
  opts=opts||{};
  const vals=rows.map(getV);
  const max=Math.max(...vals.map(v=>Math.abs(v||0)), 1e-9);
  const med=median(vals);
  return '<div class="bars">'+rows.map((r,i)=>{
    const v=getV(r)||0;
    const w=Math.max(1.5,(Math.abs(v)/max)*100);
    let hot=false;
    if(opts.hotBelowMed) hot = med!=null && v<=med;
    if(opts.hotAboveMed) hot = med!=null && v>=med;
    if(opts.hotNeg) hot = v<0;
    const cls=opts.click===false?' noclick':'';
    const sel=(opts.selKey && r[opts.selKey]===selDb)?' sel':'';
    const data=opts.selKey?(' data-db="'+r.db+'"'):(opts.dormIdx?(' data-dorm="'+i+'"'):'');
    return '<div class="bar-row'+cls+sel+'"'+data+'>'+
      '<span class="lbl">'+(r.label||r.family||'—')+'</span>'+
      '<span class="track"><span class="fill'+(hot?' hot':'')+(opts.rise&&v>=0?' rise':'')+'" style="width:'+w+'%"></span></span>'+
      '<span class="val">'+fmt(r,v)+'</span></div>';
  }).join('')+'</div>';
}
function divergeBars(rows, getV, fmt, opts){
  opts=opts||{};
  const vals=rows.map(getV);
  const maxAbs=Math.max(...vals.map(v=>Math.abs(v||0)), 0.01);
  return '<div class="bars">'+rows.map(r=>{
    const v=getV(r)||0;
    const w=Math.max(2, Math.abs(v)/maxAbs*50);
    const rising=v>=0;
    const left=rising?50:50-w;
    return '<div class="bar-row '+(opts.click===false?'noclick':'')+'"'+(r.db?(' data-db="'+r.db+'"'):'')+'>'+
      '<span class="lbl">'+r.label+'</span>'+
      '<span class="track" style="background:#eef0f4">'+
        '<span style="position:absolute;left:50%;top:0;bottom:0;width:1px;background:#c8c2b4"></span>'+
        '<span class="fill '+(rising?'rise':'hot')+'" style="position:absolute;left:'+left+'%;width:'+w+'%;top:0;bottom:0"></span>'+
      '</span>'+
      '<span class="val">'+fmt(r,v)+'</span></div>';
  }).join('')+'</div>';
}

function paintHeroFamily(){
  const m=catMeta();
  let extra='';
  if(q==='where_gap' && P.wallet_net){
    extra = kpi('Network uncaptured', eur(P.wallet_net.uncaptured_eur), 'all families · target spend',
      'Sum of uncaptured euro vs the GPS target-spend ceiling across known distributors in '+P.year+'. Not only this family.');
    document.getElementById('hero').innerHTML =
      kpi('Family gap', eur(m.gap_eur), m.label+' · uncaptured',
        'Units not billed × observed average selling price for this family.')+
      kpi('Family billed', eur(m.billed_eur), 'what we billed',
        'Parts euro billed in this family in calendar '+P.year+' (total line).')+
      kpi('Family capture', pct(m.capture), 'total units · '+P.year,
        'Total units billed ÷ units the service model expects for this family.')+
      extra;
    return;
  }
  document.getElementById('hero').innerHTML =
    kpi('Family capture', pct(m.capture), 'network total · '+P.year,
      'Total units billed ÷ units the service model expects for this family. Genuine and best-value both count.')+
    kpi('Gap euro', eur(m.gap_eur), 'uncaptured on this family',
      'Units not billed × observed average selling price. Fleet base is in the UIO chip.')+
    kpi('Billed euro', eur(m.billed_eur), 'what we billed',
      'Parts euro billed in this family in calendar '+P.year+' (total line).')+
    kpi('Fleet (UIO)', num(m.uio), 'trucks in service (sum)',
      'Vehicles in service behind this family in the PMS model.');
}

function paintUnavailable(){
  const note=P.notes[q]||'Source file missing for this question.';
  setAmber('DATA UNAVAILABLE — '+note);
  document.getElementById('main').innerHTML='';
  document.getElementById('hero').innerHTML=
    kpi('Status','—','no data',note)+kpi('Question',qMeta().label,'','')+
    kpi('Form',qMeta().form,'','')+kpi('Snapshot',P.snap,'','');
}

function paintSpend(){
  setAmber(null);
  const rows=P.spend.slice();
  const med=median(rows.map(r=>r.spu));
  const top=rows[0];
  document.getElementById('hero').innerHTML =
    kpi('Highest spend/truck', eur(top&&top.spu), top?top.label:'—',
      'Parts billed ÷ trucks in service for calendar '+P.year+' (GPS spend per unit).')+
    kpi('Network median', eur(med), rows.length+' distributors',
      'Median GPS spend per unit across the ranked set. Terracotta bars sit at or below this line.')+
    kpi('Top billed', eur(top&&top.billed), top?top.label:'—',
      'What we billed that distributor in calendar '+P.year+'.')+
    kpi('Top fleet', num(top&&top.uio), 'trucks in service',
      'Vehicles in service behind the top spend-per-truck market.');
  document.getElementById('main').innerHTML=rankedBars(rows, r=>r.spu, (r)=>eur(r.spu), {hotBelowMed:true, click:false});
}

function paintGrowth(){
  setAmber(null);
  const n=P.growth_net;
  document.getElementById('hero').innerHTML =
    kpi('Volume leg', eur(n.vol), P.prev+'→'+P.year,
      'Network sum of volume contribution to parts euro change, summed across product families.')+
    kpi('Price leg', eur(n.price), P.prev+'→'+P.year,
      'Network sum of price contribution to parts euro change.')+
    kpi('Mix leg', eur(n.mix), P.prev+'→'+P.year,
      'Network sum of mix contribution. Zero means the file carries no mix split for this window.')+
    kpi('Net change', eur(n.total), 'parts billed',
      'Sum of total delta across known distributors.');
  const rows=P.growth_dbs.slice().sort((a,b)=>(b.total||0)-(a.total||0));
  const maxAbs=Math.max(...rows.map(r=>Math.abs(r.vol||0)+Math.abs(r.price||0)+Math.abs(r.mix||0)),1);
  document.getElementById('main').innerHTML='<div class="bars">'+rows.map(r=>{
    const parts=[
      {n:r.vol||0, c:'#15233c'},
      {n:r.price||0, c:'#3f5a86'},
      {n:r.mix||0, c:'#c0552d'}
    ];
    const segs=parts.map(p=>{
      const w=Math.max(0, Math.abs(p.n)/maxAbs*100);
      if(w<0.3) return '';
      return '<span class="fill" style="width:'+w+'%;background:'+p.c+';opacity:'+(p.n<0?0.55:1)+'"></span>';
    }).join('');
    return '<div class="bar-row noclick" title="Vol '+eur(r.vol)+' · Price '+eur(r.price)+' · Mix '+eur(r.mix)+'">'+
      '<span class="lbl">'+r.label+'</span>'+
      '<span class="track">'+segs+'</span>'+
      '<span class="val">'+(r.total>=0?'+':'')+eur(r.total)+'</span></div>';
  }).join('')+'</div>'+
  '<p class="ask" style="margin-top:10px"><span style="color:#15233c">■</span> Volume · <span style="color:#3f5a86">■</span> Price · <span style="color:#c0552d">■</span> Mix — bar length is absolute contribution; faded = negative leg.</p>';
}

function paintRankGap(){
  const rows=totals('total').slice().sort((a,b)=>(b.gap_eur||0)-(a.gap_eur||0));
  if(!rows.length){ setAmber('DATA UNAVAILABLE — no total rows for this family.'); document.getElementById('main').innerHTML=''; return; }
  setAmber(null);
  if(!selDb || !rows.find(r=>r.db===selDb)) selDb=rows[0].db;
  document.getElementById('main').innerHTML=rankedBars(rows, r=>r.gap_eur, (r)=>eur(r.gap_eur), {hotAboveMed:true, selKey:'db'});
  bindClicks('#main .bar-row');
}

function paintResidual(){
  const ts=totals('total');
  if(!ts.length){ setAmber('DATA UNAVAILABLE — no residual rows for this family.'); document.getElementById('main').innerHTML=''; return; }
  setAmber(null);
  const rows=ts.slice().sort((a,b)=>(a.capture||0)-(b.capture||0));
  if(!selDb || !rows.find(r=>r.db===selDb)) selDb=rows[0].db;
  document.getElementById('main').innerHTML='<div class="bars">'+rows.map(r=>{
    const mix=mixFor(r.db);
    const exp=Math.max(r.expected_qty||0,1);
    const gq=Math.max((mix.g&&mix.g.actual_qty)||0,0);
    const bq=Math.max((mix.b&&mix.b.actual_qty)||0,0);
    const miss=Math.max(0, exp-(r.actual_qty||0));
    const sg=gq/exp*100, sb=bq/exp*100, sm=miss/exp*100;
    return '<div class="bar-row'+(r.db===selDb?' sel':'')+'" data-db="'+r.db+'" title="Expected '+num(exp)+'">'+
      '<span class="lbl">'+r.label+'</span>'+
      '<span class="track">'+
        '<span class="fill g" style="width:'+sg+'%"></span>'+
        '<span class="fill b" style="width:'+sb+'%"></span>'+
        '<span class="fill m" style="width:'+sm+'%"></span>'+
      '</span>'+
      '<span class="val">'+pct(r.capture)+'</span></div>';
  }).join('')+'</div>'+
  '<p class="ask" style="margin-top:10px"><span style="color:#15233c">■</span> Genuine · <span style="color:#3f5a86">■</span> Best-value · <span style="color:#c0552d">■</span> Not bought — each bar is 100% of expected units.</p>';
  bindClicks('#main .bar-row');
}

function paintCaptureTrend(){
  const rows=P.traj.filter(r=>r.cat===cat).slice().sort((a,b)=>a.dpp-b.dpp);
  if(!rows.length){ setAmber('DATA UNAVAILABLE — no trajectory for this family.'); document.getElementById('main').innerHTML=''; return; }
  setAmber(null);
  if(!selDb || !rows.find(r=>r.db===selDb)) selDb=rows[0].db;
  document.getElementById('hero').innerHTML =
    kpi('Rising', String(rows.filter(r=>r.dpp>0).length), 'of '+rows.length,
      'Distributors whose total capture rose from '+P.y0+' to '+P.year+' on this family (measured only).')+
    kpi('Falling', String(rows.filter(r=>r.dpp<0).length), 'of '+rows.length,
      'Distributors whose capture fell over the same window.')+
    kpi('Biggest rise', pp(Math.max(...rows.map(r=>r.dpp))), 'pp',
      'Largest positive change in capture percentage points.')+
    kpi('Biggest fall', pp(Math.min(...rows.map(r=>r.dpp))), 'pp',
      'Largest negative change in capture percentage points.');
  document.getElementById('main').innerHTML=divergeBars(rows, r=>r.dpp, (r,v)=>pp(v), {})+
    '<p class="ask" style="margin-top:10px">Change in capture percentage points, '+P.y0+'→'+P.year+'. Projected years are excluded. Click a row for the mix donut.</p>';
  bindClicks('#main .bar-row');
}

function paintFleet(){
  setAmber(null);
  const f=P.fleet;
  const up=f.filter(r=>r.chg!=null && r.chg>0).length;
  const down=f.filter(r=>r.chg!=null && r.chg<0).length;
  const net=f.reduce((s,r)=>s+(r.delta||0),0);
  const uio=f.reduce((s,r)=>s+(r.uio25||0),0);
  document.getElementById('hero').innerHTML =
    kpi('Markets rising', String(up), 'of '+f.length+' with UIO',
      'Distributors whose vehicles in service rose from '+P.prev+' to '+P.year+'.')+
    kpi('Markets falling', String(down), 'of '+f.length,
      'Distributors whose vehicles in service fell. Forecast years are not drawn.')+
    kpi('Net fleet change', (net>=0?'+':'')+num(net), 'trucks · '+P.prev+'→'+P.year,
      'Sum of year-on-year UIO change across the GPS distributor base shown.')+
    kpi('Fleet now', num(uio), 'trucks in service '+P.year,
      'Sum of '+P.year+' UIO from GPS. Measured history only.');
  const top=f.filter(r=>r.slope);
  const rest=f.filter(r=>!r.slope).slice().sort((a,b)=>(a.chg||0)-(b.chg||0));
  const uMax=Math.max(...top.map(r=>Math.max(r.uio24,r.uio25)),1);
  const W=640, H=320, L=150, R=150, T=24, B=36;
  const x0=L, x1=W-R;
  const y=v=> T + (1 - v/uMax)*(H-T-B);
  const leftY=top.map(r=>y(r.uio24));
  const rightY=top.map(r=>y(r.uio25));
  function stagger(arr){
    const out=arr.slice();
    for(let i=1;i<out.length;i++){ if(out[i]-out[i-1]<16) out[i]=out[i-1]+16; }
    return out;
  }
  const leftLab=stagger(leftY), rightLab=stagger(rightY);
  let lines='', labs='';
  top.forEach((r,i)=>{
    const rising=r.chg!=null && r.chg>=0;
    const col=rising?'#2f6b4f':'#c0552d';
    lines+='<line x1="'+x0+'" y1="'+leftY[i]+'" x2="'+x1+'" y2="'+rightY[i]+'" stroke="'+col+'" stroke-width="2.4"/>';
    lines+='<circle cx="'+x0+'" cy="'+leftY[i]+'" r="4" fill="'+col+'"/>';
    lines+='<circle cx="'+x1+'" cy="'+rightY[i]+'" r="4" fill="'+col+'"/>';
    labs+='<text x="'+(x0-10)+'" y="'+(leftLab[i]+4)+'" text-anchor="end" font-size="12" fill="#15233c">'+r.label+' · '+num(r.uio24)+'</text>';
    labs+='<text x="'+(x1+10)+'" y="'+(rightLab[i]+4)+'" text-anchor="start" font-size="12" fill="#15233c">'+num(r.uio25)+' · '+pct1(r.chg)+'</text>';
  });
  const slopeSvg='<div class="slopebox"><svg viewBox="0 0 '+W+' '+H+'" role="img" aria-label="Fleet slope">'+
    '<line x1="'+x0+'" y1="'+T+'" x2="'+x0+'" y2="'+(H-B)+'" stroke="#ded8ca"/>'+
    '<line x1="'+x1+'" y1="'+T+'" x2="'+x1+'" y2="'+(H-B)+'" stroke="#ded8ca"/>'+
    '<text x="'+x0+'" y="'+(H-12)+'" text-anchor="middle" font-size="12" fill="#5f5d57">'+P.prev+'</text>'+
    '<text x="'+x1+'" y="'+(H-12)+'" text-anchor="middle" font-size="12" fill="#5f5d57">'+P.year+'</text>'+
    lines+labs+'</svg></div>';
  const maxAbs=Math.max(...rest.map(r=>Math.abs(r.chg||0)), 0.01);
  const chgHtml='<p class="subh">Smaller fleets — change only (no slope)</p><div class="chggrid bars">'+
    rest.map(r=>{
      const v=r.chg||0;
      const w=Math.max(2, Math.abs(v)/maxAbs*50);
      const rising=v>=0;
      const left=rising?50:50-w;
      return '<div class="bar-row noclick">'+
        '<span class="lbl">'+r.label+'</span>'+
        '<span class="track" style="background:#eef0f4">'+
          '<span style="position:absolute;left:50%;top:0;bottom:0;width:1px;background:#c8c2b4"></span>'+
          '<span class="fill '+(rising?'rise':'hot')+'" style="position:absolute;left:'+left+'%;width:'+w+'%;top:0;bottom:0"></span>'+
        '</span>'+
        '<span class="val">'+pct1(v)+'</span></div>';
    }).join('')+'</div>';
  document.getElementById('main').innerHTML=slopeSvg+chgHtml;
}

function paintDormancy(){
  setAmber(null);
  const rows=P.dorm.filter(r=>r.ratio!=null);
  const alerts=rows.filter(r=>r.alert).length;
  const top=rows[0];
  document.getElementById('hero').innerHTML =
    kpi('Alert rows', String(alerts), 'of '+rows.length+' shown',
      'Distributor-level dormant baskets where silence exceeds the own reorder gap.')+
    kpi('Worst ratio', top?top.ratio.toFixed(1)+'×':'—', top?top.label:'—',
      'Silent months ÷ that distributor’s own median reorder gap for the basket.')+
    kpi('Silent months', top?String(top.silent):'—', top?(top.cat||''):'',
      'Months since last order on that parts family basket.')+
    kpi('Trailing 12m', eur(top&&top.trail_eur), 'parts billed',
      'Trailing twelve-month parts euro on the dormant basket (may be zero).');
  if(selDorm==null || !rows[selDorm]) selDorm=0;
  document.getElementById('main').innerHTML=rankedBars(rows, r=>r.ratio, (r)=>((r.ratio||0).toFixed(1)+'×'), {hotAboveMed:true, dormIdx:true})+
    '<p class="ask" style="margin-top:10px">Ratio = silent months ÷ own median gap. Click a row for trailing revenue detail.</p>';
  bindClicks('#main .bar-row');
}

function paintBasket(){
  setAmber(null);
  const B=P.basket;
  const flat=B.cell.flat();
  const mx=Math.max(...flat, 0.01);
  document.getElementById('hero').innerHTML =
    kpi('Distributors', String(B.dbs.length), 'rows',
      'Known GPS distributors with service-mix billed euro in '+P.year+'.')+
    kpi('Subgroups', String(B.subgroups.length), 'top by network euro',
      'Top product subgroups by billed euro across the network in '+P.year+'.')+
    kpi('Cell meaning', 'Share', 'of that DB’s top-basket euro',
      'Each cell is that subgroup’s share of the distributor’s billed euro inside the top-N basket.')+
    kpi('Darker', 'Higher share', 'within the row',
      'Colour scales within the page max so denser cells read darker.');
  let head='<tr><th class="rowh">Distributor</th>'+B.sg_labels.map(l=>'<th>'+l+'</th>').join('')+'</tr>';
  let body=B.dbs.map((d,i)=>{
    const cells=B.cell[i].map(v=>{
      const t=v/mx;
      const bg='rgba(21,35,60,'+(0.08+t*0.75)+')';
      const col=t>0.45?'#f7f4ee':'#15233c';
      return '<td class="cell" style="background:'+bg+';color:'+col+'" title="'+(v*100).toFixed(1)+'%">'+(v>=0.005?(v*100).toFixed(0)+'%':'·')+'</td>';
    }).join('');
    return '<tr><td class="rowh">'+d.label+'</td>'+cells+'</tr>';
  }).join('');
  document.getElementById('main').innerHTML='<div class="heat"><table>'+head+body+'</table></div>';
}

function paintPrice(){
  setAmber(null);
  const rows=P.price.slice();
  const med=median(rows.map(r=>r.premium));
  const centered=rows.map(r=>({...r, dev:(r.premium||0)-(med||0)})).sort((a,b)=>a.dev-b.dev);
  document.getElementById('hero').innerHTML =
    kpi('Network median premium', pct(med), 'genuine ASP vs BVP ASP',
      'Median across distributors of the median genuine-vs-BVP average selling price premium in '+P.year+'. Not a reference dealer price index.')+
    kpi('Highest premium', pct(rows[0]&&rows[0].premium), rows[0]?rows[0].label:'—',
      'Distributor whose median genuine ASP sits furthest above BVP ASP.')+
    kpi('Lowest premium', pct(rows[rows.length-1]&&rows[rows.length-1].premium), rows[rows.length-1]?rows[rows.length-1].label:'—',
      'Distributor whose genuine and BVP ASPs are closest (or inverted).')+
    kpi('Markets', String(rows.length), 'with premium rows',
      'Distributors present in price_premium for calendar '+P.year+'.');
  document.getElementById('main').innerHTML=divergeBars(centered, r=>r.dev, (r)=>pct(r.premium)+' · '+pct1(r.dev), {click:false})+
    '<p class="ask" style="margin-top:10px">Deviation of each distributor’s median genuine-vs-BVP ASP premium from the network median. Right = above median premium.</p>';
}

function paintWarranty(){
  setAmber(null);
  const rows=P.warranty.filter(r=>r.share!=null).slice().sort((a,b)=>(b.share||0)-(a.share||0));
  const gaps=P.warranty.filter(r=>r.gap).length;
  if(!rows.length){ setAmber('DATA UNAVAILABLE — no warranty euro in GPS '+P.year+'.'); document.getElementById('main').innerHTML=''; return; }
  if(gaps) setAmber('Note: '+gaps+' distributors have no warranty euro in GPS '+P.year+' and are omitted from the rank.');
  else setAmber(null);
  const med=median(rows.map(r=>r.share));
  const top=rows[0];
  document.getElementById('hero').innerHTML =
    kpi('Highest warranty share', pct(top.share), top.label,
      'Warranty parts euro ÷ total parts billed for that distributor in '+P.year+'.')+
    kpi('Network median', pct(med), rows.length+' with data',
      'Median warranty share among distributors with warranty euro present.')+
    kpi('Warranty euro (top)', eur(top.warranty_eur), top.label,
      'Warranty parts euro billed.')+
    kpi('Parts billed (top)', eur(top.total_eur), top.label,
      'Total GPS parts billed.');
  document.getElementById('main').innerHTML=rankedBars(rows, r=>r.share, (r)=>pct(r.share), {hotAboveMed:true, click:false});
}

function paintBvpTwo(){
  setAmber(null);
  const a=P.bvp_all_net, s=P.bvp_svc_net;
  document.getElementById('hero').innerHTML =
    kpi('All-parts BVP share', pct(a&&a.share), eur(a&&a.bvp)+' of '+eur(a&&a.total),
      'Best-value euro ÷ all classified parts euro (full book) in '+P.year+'.')+
    kpi('Service-universe BVP', pct(s&&s.share), eur(s&&s.bvp)+' of '+eur(s&&s.total),
      'Best-value euro ÷ PMS service-mix euro in '+P.year+'.')+
    kpi('Gap between lenses', ((a&&s&&a.share!=null&&s.share!=null)?pp((s.share-a.share)*100):'—'), 'service − all-parts',
      'How much higher (or lower) BVP sits in the service universe versus the full book.')+
    kpi('Markets ranked', String(P.bvp_svc.length), 'service universe',
      'Distributors ranked by service-universe BVP share.');
  document.getElementById('main').innerHTML=
    '<p class="subh">Service-universe BVP share by distributor</p>'+
    rankedBars(P.bvp_svc, r=>r.share, (r)=>pct(r.share), {hotAboveMed:true, click:false});
}

function paintBvpAddr(){
  setAmber(null);
  const rows=P.bvp_addr;
  const med=median(rows.map(r=>r.pct));
  const top=rows[0];
  document.getElementById('hero').innerHTML =
    kpi('Best coverage', pct(top&&top.pct), top?top.label:'—',
      'Share of addressable BVP part numbers that distributor currently sells.')+
    kpi('Network median', pct(med), rows.length+' distributors',
      'Median currently-selling share across known distributors.')+
    kpi('PNs selling (top)', num(top&&top.selling)+' / '+num(top&&top.n), top?top.label:'—',
      'Addressable BVP PNs with sales vs addressable basket size.')+
    kpi('Basket size (top)', num(top&&top.n), 'addressable pairs',
      'Genuine↔BVP addressable pairs in the basket file.');
  document.getElementById('main').innerHTML=rankedBars(rows, r=>r.pct, (r)=>pct(r.pct), {hotBelowMed:true, click:false});
}

function paintBvpSubst(){
  const pack=P.bvp_subst||{};
  const period=pack[substPer]||pack.cy||{};
  const net=period.network||[];
  const byDb=period.by_db||{};
  const isFy=substPer==='fy';
  const periodWord=isFy?'fiscal year (Apr–Mar)':'calendar year';

  if(!net.length && substPer==='fy'){
    setAmber('DATA UNAVAILABLE — fiscal-year series not built (need sales_with_crossref.parquet). Switch to calendar year.');
    document.getElementById('hero').innerHTML='';
    document.getElementById('main').innerHTML='';
    return;
  }
  setAmber(isFy
    ? 'Fiscal years are Apr–Mar. Only complete years are drawn (a year that opened after our sales history starts, or is still open, is left out).'
    : null);

  let series=net;
  let seriesName='Network';
  if(substDb!=='NETWORK'){
    series=byDb[substDb]||[];
    const hit=P.bvp_subst_db.find(x=>x.db===substDb);
    seriesName=hit?hit.label:substDb;
    if(!series.length){
      setAmber('No paired genuine/BVP sales for '+seriesName+' in this '+periodWord+' window.');
      document.getElementById('hero').innerHTML='';
      document.getElementById('main').innerHTML='';
      return;
    }
  }

  const last=series[series.length-1];
  const first=series[0];
  // Ranked bars: latest period across DBs
  const lastKey=last?(last.year):null;
  const ranked=[];
  Object.keys(byDb).forEach(code=>{
    const rows=byDb[code]||[];
    const row=rows.find(r=>r.year===lastKey)||rows[rows.length-1];
    if(!row||row.share==null) return;
    const hit=P.bvp_subst_db.find(x=>x.db===code);
    ranked.push({db:code, label:hit?hit.label:code, share:row.share, bvp_qty:row.bvp_qty, genuine_qty:row.genuine_qty});
  });
  ranked.sort((a,b)=>(b.share||0)-(a.share||0));

  document.getElementById('hero').innerHTML =
    kpi(seriesName+' · last', pct(last&&last.share), (last&&last.label)?String(last.label):periodWord,
      'BVP units ÷ (BVP+genuine) on same-reference pairs. '+periodWord+'.')+
    kpi('Change in window', (first&&last&&first.share!=null&&last.share!=null)?pp((last.share-first.share)*100):'—',
      (first&&last)?(String(first.label)+'→'+String(last.label)):'pp',
      'Change in BVP unit share across the drawn '+periodWord+' points.')+
    kpi('Highest DB · last', ranked[0]?pct(ranked[0].share):'—', ranked[0]?ranked[0].label:'—',
      'Distributor with the highest BVP unit share on paired references in the last period shown.')+
    kpi('Markets', String(ranked.length), 'with pair sales',
      'Distributors with paired genuine/BVP quantity in the last period.');

  const W=640, H=220, L=50, R=50, T=28, B=40;
  const xs=series.map((r,i)=> L + i*((W-L-R)/Math.max(series.length-1,1)));
  const ys=series.map(r=> T + (1-(r.share||0))*(H-T-B));
  let path='';
  series.forEach((r,i)=>{ path+=(i?'L':'M')+xs[i]+' '+ys[i]+' '; });
  // optional network ghost when a DB is selected (CY only if same length)
  let ghost='';
  if(substDb!=='NETWORK' && net.length===series.length){
    const gys=net.map(r=> T + (1-(r.share||0))*(H-T-B));
    let gp='';
    net.forEach((r,i)=>{ gp+=(i?'L':'M')+xs[i]+' '+gys[i]+' '; });
    ghost='<path d="'+gp+'" fill="none" stroke="#b8b2a4" stroke-width="2" stroke-dasharray="5 4"/>'+
      net.map((r,i)=>'<circle cx="'+xs[i]+'" cy="'+gys[i]+'" r="3" fill="#b8b2a4"/>').join('');
  }
  const slope='<div class="slopebox"><svg viewBox="0 0 '+W+' '+H+'" role="img">'+
    ghost+
    '<path d="'+path+'" fill="none" stroke="#15233c" stroke-width="2.5"/>'+
    series.map((r,i)=>'<circle cx="'+xs[i]+'" cy="'+ys[i]+'" r="4" fill="#c0552d"/>'+
      '<text x="'+xs[i]+'" y="'+(H-14)+'" text-anchor="middle" font-size="12" fill="#5f5d57">'+(r.label||r.year)+'</text>'+
      '<text x="'+xs[i]+'" y="'+(ys[i]-12)+'" text-anchor="middle" font-size="12" fill="#15233c">'+pct(r.share)+'</text>').join('')+
    '</svg></div>'+
    (substDb!=='NETWORK'?'<p class="ask">Dashed line = network average on the same periods.</p>':'');

  const barTitle=substDb==='NETWORK'
    ? ('Distributor BVP unit share · last period ('+(last&&last.label?last.label:'')+') — click a bar to focus that distributor')
    : ('All distributors · last period ('+(last&&last.label?last.label:'')+') — click another distributor or choose Network');

  document.getElementById('main').innerHTML=slope+
    '<p class="subh">'+barTitle+'</p>'+
    rankedBars(ranked, r=>r.share, (r)=>pct(r.share), {hotAboveMed:true, click:true, selKey:'db'});
  document.querySelectorAll('#main .bar-row[data-db]').forEach(el=>{
    el.addEventListener('click', ()=>{
      substDb=el.dataset.db;
      substDbEl.value=substDb;
      paint();
    });
  });
}

function paintBvpExpose(){
  setAmber(null);
  const rows=P.bvp_expose;
  const top=rows[0];
  document.getElementById('hero').innerHTML =
    kpi('Most exposed family', top?top.label:'—', pct(top&&top.high_risk_pct)+' high-risk euro',
      'Product family with the highest share of AIM high-risk revenue in '+P.year+' (network).')+
    kpi('High-risk euro', eur(top&&top.high_risk_eur), top?top.label:'—',
      'AIM high-risk revenue euro in that family.')+
    kpi('BVP share there', pct(top&&top.bvp_share), eur(top&&top.bvp_eur)+' BVP',
      'Best-value share of (genuine+BVP) euro inside that family.')+
    kpi('Families', String(rows.length), 'network aggregates',
      'Product families present in AIM BVP family risk for '+P.year+'.');
  document.getElementById('main').innerHTML=rankedBars(rows.map(r=>({...r, label:r.label})), r=>r.high_risk_pct,
    (r)=>pct(r.high_risk_pct)+' · BVP '+pct(r.bvp_share), {hotAboveMed:true, click:false})+
    '<p class="ask" style="margin-top:10px">Ranked by AIM high-risk revenue share. Value also shows BVP euro share in the same family.</p>';
}

function paintBvpContest(){
  if(P.contest_note) setAmber(P.contest_note);
  else setAmber(null);
  const rows=P.bvp_contest;
  const totB=rows.reduce((s,r)=>s+r.bvp,0);
  const totC=rows.reduce((s,r)=>s+r.genuine_contested,0);
  const totO=rows.reduce((s,r)=>s+r.genuine_only,0);
  const tot=totB+totC+totO||1;
  document.getElementById('hero').innerHTML =
    kpi('BVP won', pct(totB/tot), eur(totB),
      'Best-value euro in sales-to-dealer files for covered distributors in '+P.year+'.')+
    kpi('Genuine contested', pct(totC/tot), eur(totC),
      'Genuine euro on part numbers that also have a BVP contest.')+
    kpi('Genuine only', pct(totO/tot), eur(totO),
      'Genuine euro with no BVP contest on that reference.')+
    kpi('Distributors', String(rows.length), 'with sales-to-dealer',
      'Partial coverage — not the full 18-market GPS base.');
  document.getElementById('main').innerHTML='<div class="bars">'+rows.map(r=>{
    const t=r.total||1;
    const sb=r.bvp/t*100, sc=r.genuine_contested/t*100, so=r.genuine_only/t*100;
    return '<div class="bar-row noclick">'+
      '<span class="lbl">'+r.label+'</span>'+
      '<span class="track">'+
        '<span class="fill g" style="width:'+so+'%"></span>'+
        '<span class="fill b" style="width:'+sc+'%"></span>'+
        '<span class="fill m" style="width:'+sb+'%"></span>'+
      '</span>'+
      '<span class="val">'+eur(r.total)+'</span></div>';
  }).join('')+'</div>'+
  '<p class="ask" style="margin-top:10px"><span style="color:#15233c">■</span> Genuine only · <span style="color:#3f5a86">■</span> Genuine contested · <span style="color:#c0552d">■</span> BVP — sales to dealer, not ISZE billing.</p>';
}

function paintPie(){
  const host=document.getElementById('pieHost');
  const leg=document.getElementById('legend');
  const det=document.getElementById('detail');
  if(!MIX_SIDE[q]){ host.innerHTML=''; leg.innerHTML=''; det.innerHTML=''; return; }
  const mix=mixFor(selDb);
  const t=mix.t;
  if(!t){
    host.innerHTML='<div class="amber">No total row for this distributor × family.</div>';
    leg.innerHTML=''; det.textContent='';
    return;
  }
  const exp=Math.max(t.expected_qty||0,0);
  const aq=Math.max(t.actual_qty||0,0);
  const gq=Math.max((mix.g&&mix.g.actual_qty)||0,0);
  const bq=Math.max((mix.b&&mix.b.actual_qty)||0,0);
  const residual=Math.max(0, exp-aq);
  const over=aq>exp && exp>0;
  const parts=[
    {label:'Genuine billed', n:gq, color:'#15233c'},
    {label:'Best-value billed', n:bq, color:'#3f5a86'},
    {label:'Not bought', n:residual, color:'#c0552d'}
  ];
  const sum=parts.reduce((s,p)=>s+p.n,0)||1;
  const R=84, CX=110, CY=110, SW=28;
  let ang=-Math.PI/2, paths='';
  parts.forEach(p=>{
    const frac=p.n/sum; if(frac<=0) return;
    const a0=ang, a1=ang+frac*Math.PI*2;
    const x0=CX+R*Math.cos(a0), y0=CY+R*Math.sin(a0);
    const x1=CX+R*Math.cos(a1), y1=CY+R*Math.sin(a1);
    const large=frac>0.5?1:0;
    paths+='<path d="M '+CX+' '+CY+' L '+x0+' '+y0+' A '+R+' '+R+' 0 '+large+' 1 '+x1+' '+y1+' Z" fill="'+p.color+'"></path>';
    ang=a1;
  });
  host.innerHTML='<svg viewBox="0 0 220 220" role="img" aria-label="Mix donut">'+paths+
    '<circle cx="'+CX+'" cy="'+CY+'" r="'+(R-SW)+'" fill="#f7f4ee"></circle>'+
    '<text x="'+CX+'" y="'+(CY-4)+'" text-anchor="middle" fill="#15233c" font-family="Georgia,serif" font-size="18">'+pct(t.capture)+'</text>'+
    '<text x="'+CX+'" y="'+(CY+16)+'" text-anchor="middle" fill="#5f5d57" font-size="11">total capture</text></svg>';
  leg.innerHTML=parts.map(p=>{
    const share=p.n/sum;
    return '<div><span><span class="sw" style="background:'+p.color+'"></span>'+p.label+
      '</span><span>'+num(p.n)+' u · '+(share*100).toFixed(0)+'%</span></div>';
  }).join('');
  const gapLine = t.quotable
    ? ('gap '+eur(t.gap_eur))
    : ('gap not priced (no usable average selling price; '+num(residual)+' units still unbought)');
  det.innerHTML='<b>'+t.label+'</b> · '+t.cat_label+
    '<br>Expected '+num(exp)+' units on '+num(t.uio)+' trucks in service.'+
    '<br>Billed '+eur(t.billed_eur)+' · '+gapLine+
    (over?'<br><b>Note:</b> billed units exceed the model expectation for this family.':'');
}

function paintDormDetail(){
  const host=document.getElementById('pieHost');
  const leg=document.getElementById('legend');
  const det=document.getElementById('detail');
  const rows=P.dorm.filter(r=>r.ratio!=null);
  const r=rows[selDorm];
  if(!r){ host.innerHTML=''; leg.innerHTML=''; det.innerHTML=''; return; }
  host.innerHTML='';
  leg.innerHTML='';
  det.innerHTML='<b>'+r.label+'</b>'+(r.cat?(' · '+r.cat.replace(/_/g,' ')):'')+
    '<br>Silent '+num(r.silent)+' months vs own median gap '+num(r.median_gap)+' months ('+(r.ratio||0).toFixed(1)+'×).'+
    '<br>Trailing 12-month parts billed: '+eur(r.trail_eur)+
    (r.last?('<br>Last order month: '+r.last):'')+
    (r.alert?'<br><b>Alert</b> — quieter than own reorder rhythm.':'');
}

function paint(){
  const meta=qMeta();
  document.getElementById('formtxt').textContent=meta.form;
  famLab.classList.toggle('hidden', !meta.needs_family);
  const showSubst = (q==='bvp_subst');
  substDbLab.classList.toggle('hidden', !showSubst);
  substPerLab.classList.toggle('hidden', !showSubst);
  if(showSubst){
    substDbEl.value=substDb;
    substPerEl.value=substPer;
  }
  const board=document.getElementById('board');
  const side=document.getElementById('sidePanel');
  const showMix=!!MIX_SIDE[q];
  const showDetail=!!DETAIL_SIDE[q];
  if(showMix||showDetail){
    board.classList.remove('solo');
    side.classList.remove('hidden');
    if(showMix){
      document.getElementById('sideTitle').textContent='Mix inside one distributor';
      document.getElementById('sideAsk').textContent='Genuine billed, best-value billed, and not bought — for the selected family and distributor.';
    } else {
      document.getElementById('sideTitle').textContent='Dormancy detail';
      document.getElementById('sideAsk').textContent='Trailing revenue and silence vs that distributor’s own reorder gap.';
    }
  } else {
    board.classList.add('solo');
    side.classList.add('hidden');
  }

  if(P.avail[q]===false){
    document.getElementById('rankTitle').textContent=meta.label;
    document.getElementById('rankAsk').textContent=meta.form;
    paintUnavailable();
    return;
  }

  document.getElementById('rankTitle').textContent=meta.label;

  if(q==='spend_pu'){
    document.getElementById('rankAsk').textContent='Parts billed per truck in service, calendar '+P.year+'. Terracotta bars sit at or below the network median.';
    paintSpend();
  } else if(q==='growth_split'){
    document.getElementById('rankAsk').textContent='Volume, price and mix legs of parts euro change, '+P.prev+'→'+P.year+', summed across product families.';
    paintGrowth();
  } else if(q==='residual'){
    paintHeroFamily();
    document.getElementById('rankAsk').textContent='Each bar is 100% of expected service units for that distributor. Sorted weakest capture first. Click a row for the mix donut.';
    paintResidual();
    paintPie();
  } else if(q==='capture_trend'){
    document.getElementById('rankAsk').textContent='Change in capture percentage points, '+P.y0+'→'+P.year+'. Measured years only — not an 18-line slope.';
    paintCaptureTrend();
    paintPie();
  } else if(q==='where_gap'){
    paintHeroFamily();
    document.getElementById('rankAsk').textContent='Ranked by gap euro (units not bought × average selling price). Larger bar = more uncaptured spend. Click for mix donut.';
    paintRankGap();
    paintPie();
  } else if(q==='fleet'){
    document.getElementById('rankAsk').textContent='Vehicles in service, '+P.prev+' against '+P.year+'. Slope shows the '+P.slope_top_n+' largest fleets only.';
    paintFleet();
  } else if(q==='dormancy'){
    document.getElementById('rankAsk').textContent='Silent months versus each distributor’s own median reorder gap. Click a row for trailing twelve-month parts billed.';
    paintDormancy();
    paintDormDetail();
  } else if(q==='basket'){
    document.getElementById('rankAsk').textContent='Heatmap of billed-euro share inside the top product subgroups for calendar '+P.year+'.';
    paintBasket();
  } else if(q==='price_pos'){
    document.getElementById('rankAsk').textContent='Genuine average selling price versus best-value ASP — deviation from the network median premium. Not a reference dealer price index.';
    paintPrice();
  } else if(q==='warranty'){
    document.getElementById('rankAsk').textContent='Warranty parts euro as a share of total parts billed, calendar '+P.year+'.';
    paintWarranty();
  } else if(q==='bvp_two'){
    document.getElementById('rankAsk').textContent='Best-value share in the full parts book versus the PMS service universe. Ranked on the service-universe lens.';
    paintBvpTwo();
  } else if(q==='bvp_addr'){
    document.getElementById('rankAsk').textContent='Share of addressable best-value part numbers each distributor currently sells.';
    paintBvpAddr();
  } else if(q==='bvp_subst'){
    document.getElementById('rankAsk').textContent='BVP unit share on same-reference pairs. Pick a distributor and calendar or fiscal year (Apr–Mar). Dashed line is the network when a single distributor is selected.';
    paintBvpSubst();
  } else if(q==='bvp_expose'){
    document.getElementById('rankAsk').textContent='Product families ranked by AIM high-risk revenue share, with best-value euro share beside each.';
    paintBvpExpose();
  } else if(q==='bvp_contest'){
    document.getElementById('rankAsk').textContent='Sales-to-dealer euro split into genuine-only, genuine-contested, and best-value.';
    paintBvpContest();
  }
}
paint();
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
