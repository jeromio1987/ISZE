"""Per-DB sales-analysis payload (UMI rooms, this distributor's numbers).

Writes 09_meetings/{OPERATING_DB}_Operating_Dashboard_2026/_sales_analysis.json
Never loads raw billing XLSX. Credits are not sales.
GPS is NOT computed here — the renderer injects the operating-ledger GPS spine.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ISZE / "01_data" / "00_derived"
MEETINGS = ISZE / "09_meetings"
sys.path.insert(0, str(ISZE / "04_tools" / "db_sales_review"))
from common import (  # noqa: E402
    is_warranty_campaign_text,
    load_catalog,
    load_profile,
    load_warranty_claim_pns,
    list_profiles,
    norm_pn,
)

SHELL_RE = re.compile(r"^5500")
SATY_BLANK = {"", "NAN", "NONE", "NAT", "<NA>", "NULL"}
CRITICAL_PMS = [
    "oil_filter",
    "fuel_filter",
    "air_filter",
    "urea_filter",
    "blower_filter",
    "brake_pad",
    "brake_shoe",
    "brake_rotor",
    "clutch_disc",
    "clutch_kit",
]
UTI = 1799
FAMILY_LABELS = {
    "Exhaust": "Exhaust",
    "Brake parts": "Brakes",
    "Body parts": "Body",
    "Lighting": "Lighting",
    "Filters": "Filters",
    "Steering": "Steering",
    "Electrical sensors": "Sensors",
    "Engine parts": "Engine",
    "Air conditioning": "Aircon",
    "Hydraulic / mechanical": "Hydraulics",
    "Miscellaneous": "Misc",
    "Clutch parts": "Clutch",
    "Injectors": "Injectors",
    "Cooling": "Cooling",
    "Transmission parts": "Transmission",
    "Gaskets / seals": "Gaskets",
    "Fuel system": "Fuel",
    "Hardware": "Hardware",
    "Suspension": "Suspension",
    "Air system": "Air system",
    "Mirrors": "Mirrors",
    "Turbo": "Turbo",
    "Starter / alternator": "Starter / alt",
    "Belts": "Belts",
    "Consumables": "Consumables",
    "Unclassified": "Unclassified",
}
FAM_EUR_MIN = 4000
FAM_SHARE_MIN = 0.03
# Window pairs shown on the family chart — union names the quarterly table.
AIM_WIN_PAIRS = [
    ("amj_2026", "amj_2025"),
    ("cy_h1_2026", "cy_h1_2025"),
    ("l12_now", "l12_prior"),
    ("fy2026", "fy2025"),
    ("cy2025", "cy2024"),
]


def r2(x) -> float:
    return round(float(x or 0), 2)


def rpct(a, b) -> float | None:
    if b in (0, None) or (isinstance(b, float) and abs(b) < 1e-9):
        return None
    return round(100.0 * (float(a) - float(b)) / float(b), 1)


def sap_num(s) -> str:
    return str(s).replace(".0", "").strip()


def saty_norm(s) -> str:
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ""
    t = str(s).strip().upper()
    if t in SATY_BLANK:
        return ""
    return t


def eur_k(v: float) -> str:
    n = round(float(v or 0))
    sign = "−" if n < 0 else ""
    a = abs(n)
    if a >= 1_000_000:
        return f"{sign}€{a/1_000_000:.2f}m"
    if a >= 10_000:
        return f"{sign}€{a/1000:.0f}k"
    return f"{sign}€{a:,}"


def profile_for_operating_db(operating_db: str) -> dict:
    key = operating_db.upper()
    p = None
    try:
        p = load_profile(key)
    except SystemExit:
        p = None
    if p is None:
        import yaml
        from common import PROFILES  # noqa: PLC0415
        cfg = yaml.safe_load(PROFILES.read_text(encoding="utf-8"))
        for k, raw in (cfg.get("distributors") or {}).items():
            if str(raw.get("dashboard_key") or k).upper() == key:
                p = dict(raw)
                p["key"] = k
                p["defaults"] = cfg["defaults"]
                break
        if p is None:
            p = {
                "key": key,
                "name": key,
                "dashboard_key": key,
                "pms_code": key,
                "defaults": cfg["defaults"],
            }
    sys.path.insert(0, str(HERE))
    from build_ledger import REGISTRY  # noqa: PLC0415
    reg = REGISTRY.get(key) or REGISTRY.get(str(p.get("dashboard_key") or "").upper()) or {}
    if p.get("sold_to") is None and reg.get("sold_to"):
        st = list(reg["sold_to"])
        p = dict(p)
        p["sold_to"] = st[0] if len(st) == 1 else st
    if not p.get("name") and reg.get("display"):
        p["name"] = reg["display"]
    if not p.get("pms_code"):
        p["pms_code"] = key
    return p


def pbi_cut(profile: dict) -> dict:
    p = profile.get("pbi") or {}
    months = list(p.get("months") or [])
    sales = list(p.get("sales") or [])
    prev = list(p.get("prev_year") or [])
    budget = list(p.get("budget") or [])
    complete = bool(
        months
        and sales
        and prev
        and len(months) == len(sales) == len(prev)
        and all(v is not None for v in sales + prev)
    )
    return {
        "available": complete,
        "months": months if complete else [],
        "sales": [int(x) for x in sales] if complete else [],
        "prev_year": [int(x) for x in prev] if complete else [],
        "budget": [int(x) for x in budget] if complete and len(budget) == len(months) else [],
        "source": str(p.get("source") or "") if complete else "",
        "label": "Official sales" if complete else "Billing",
    }


def _sold_to_set(profile: dict) -> set[int]:
    raw = profile.get("sold_to")
    if raw is None:
        raise SystemExit(
            f"{profile.get('key')} has no sold_to — sales analysis needs a sold-to filter"
        )
    if isinstance(raw, (list, tuple)):
        return {int(x) for x in raw}
    return {int(raw)}


def load_db_sales(profile: dict) -> pd.DataFrame:
    sold_tos = _sold_to_set(profile)
    sold_to_s = {str(x) for x in sold_tos}
    sf = pd.read_parquet(DERIVED / "sales_fact.parquet")
    sap = pd.to_numeric(sf["sold_to_sap"], errors="coerce")
    hist = sf[sap.isin(sold_tos)].copy()
    hist["pn"] = hist["part_number"].map(norm_pn)
    hist["eur"] = pd.to_numeric(hist["net_sales_value"], errors="coerce").fillna(0)
    hist["qty"] = pd.to_numeric(hist["billed_qty"], errors="coerce").fillna(0)
    hist["dt"] = pd.to_datetime(hist["billing_date"], errors="coerce")
    hist["saty"] = hist["saty"].map(saty_norm)
    hist = hist[hist["dt"].notna()]
    hist["src"] = "sales_fact"
    keep = ["dt", "pn", "eur", "qty", "saty", "description", "src"]
    hist = hist.loc[hist["dt"] < "2026-04-01", keep]

    exp_path = DERIVED / "q1fy2027_export_with_saty.csv"
    frames = [hist]
    if exp_path.exists():
        exp = pd.read_csv(exp_path, low_memory=False)
        st = exp["Sold_to"].map(sap_num)
        exp = exp[st.isin(sold_to_s)].copy()
        exp["dt"] = pd.to_datetime(exp["Billing Date"], errors="coerce")
        exp = exp[exp["dt"] >= "2026-04-01"]
        if not exp.empty:
            exp["pn"] = exp["Material"].map(norm_pn)
            exp["eur"] = pd.to_numeric(exp["EUR_Amount"], errors="coerce").fillna(0)
            exp["qty"] = pd.to_numeric(exp["Quantity"], errors="coerce").fillna(0)
            exp["saty"] = exp["SaTy"].map(saty_norm)
            exp["description"] = exp["Material_Number"].astype(str)
            exp["src"] = "export_apr"
            frames.append(exp[keep])

    out = pd.concat(frames, ignore_index=True)
    out["is_credit"] = out["saty"] == "CR"
    out["is_saty_blank"] = out["saty"] == ""
    out["is_shell"] = out["pn"].fillna("").str.match(SHELL_RE)
    return out


def tag_warranty(df: pd.DataFrame, claim_pns: set[str]) -> pd.DataFrame:
    desc = df["description"].fillna("")
    pn = df["pn"].fillna("")
    on_claim = pn.isin(claim_pns)
    text = [is_warranty_campaign_text(p, d) for p, d in zip(pn.tolist(), desc.tolist())]
    df = df.copy()
    df["is_warranty"] = on_claim | np.array(text, dtype=bool)
    return df


def window_mask(df, start, end):
    return (df["dt"] >= start) & (df["dt"] < end)


def split_sums(df) -> dict:
    x = df[~df["is_credit"]]
    blank = x[x["is_saty_blank"]] if "is_saty_blank" in x.columns else x.iloc[0:0]
    tot = float(x["eur"].sum())
    return {
        "total": r2(tot),
        "shell": r2(x.loc[x["is_shell"], "eur"].sum()),
        "warranty": r2(x.loc[~x["is_shell"] & x["is_warranty"], "eur"].sum()),
        "commercial": r2(x.loc[~x["is_shell"] & ~x["is_warranty"], "eur"].sum()),
        "qty": r2(x["qty"].sum()),
        "qty_shell": r2(x.loc[x["is_shell"], "qty"].sum()),
        "qty_warranty": r2(x.loc[~x["is_shell"] & x["is_warranty"], "qty"].sum()),
        "qty_commercial": r2(x.loc[~x["is_shell"] & ~x["is_warranty"], "qty"].sum()),
        "lines": int(len(x)),
        "uncoded_lines": int(len(blank)),
        "uncoded_eur": r2(blank["eur"].sum()) if len(blank) else 0.0,
        "uncoded_share": round(100.0 * float(blank["eur"].sum()) / tot, 1) if tot else 0.0,
        "credit_lines": int(df["is_credit"].sum()) if "is_credit" in df.columns else 0,
        "credit_eur": r2(df.loc[df["is_credit"], "eur"].sum()) if "is_credit" in df.columns else 0.0,
    }


def pn_delta(a: pd.DataFrame, b: pd.DataFrame, n=12) -> list[dict]:
    def agg(d):
        x = d[~d["is_credit"]]
        spec = {
            "eur": ("eur", "sum"),
            "qty": ("qty", "sum"),
            "desc": ("description", "first"),
            "shell": ("is_shell", "max"),
            "warranty": ("is_warranty", "max"),
            "pms": ("pms_category", "first"),
            "group": ("pr00_group", "first"),
        }
        if "is_bvp" in x.columns:
            spec["bvp"] = ("is_bvp", "max")
        return x.groupby("pn", dropna=True).agg(**spec)

    ga, gb = agg(a), agg(b)
    idx = ga.index.union(gb.index)
    rows = []
    for pn in idx:
        ea = float(ga.loc[pn, "eur"]) if pn in ga.index else 0.0
        eb = float(gb.loc[pn, "eur"]) if pn in gb.index else 0.0
        qa = float(ga.loc[pn, "qty"]) if pn in ga.index else 0.0
        qb = float(gb.loc[pn, "qty"]) if pn in gb.index else 0.0
        pa = ea / qa if qa else 0.0
        pb = eb / qb if qb else 0.0
        src = gb.loc[pn] if pn in gb.index else ga.loc[pn]
        rows.append(
            {
                "pn": pn,
                "desc": str(src.get("desc") or "")[:60].strip(),
                "group": str(src.get("group") or "")[:40],
                "pms": str(src.get("pms") or ""),
                "shell": bool(src.get("shell")),
                "warranty": bool(src.get("warranty")),
                "bvp": bool(src.get("bvp")) if "bvp" in src.index else False,
                "eur_prior": r2(ea),
                "eur_now": r2(eb),
                "d": r2(eb - ea),
                "qty_prior": r2(qa),
                "qty_now": r2(qb),
                "qty_effect": r2((qb - qa) * pa),
                "price_effect": r2((pb - pa) * qb),
            }
        )
    rows.sort(key=lambda r: r["d"])
    return rows[:n]


def enrich_pn(rows: list[dict], pms_cats: list[dict]) -> list[dict]:
    by_id = {c["id"]: c for c in pms_cats}

    def info_for(pms: str) -> dict:
        pms = (pms or "").strip()
        if pms in by_id:
            return by_id[pms]
        for cid in CRITICAL_PMS:
            if pms == cid or pms.startswith(cid + "_"):
                return by_id.get(cid) or {}
        return {}

    out = []
    for r in rows:
        info = info_for(r.get("pms") or "")
        cap = info.get("cy2025_pct")
        net = info.get("network_pct")
        cat_id = info.get("id") or ""
        low = bool(
            cat_id in CRITICAL_PMS
            and cap is not None
            and (cap < 30.0 or (net is not None and cap < float(net) - 8.0))
        )
        still = float(r.get("eur_now") or 0) > 1 and float(r.get("qty_now") or 0) > 0
        grp = str(r.get("group") or "")
        spa = bool(
            still
            and not r.get("shell")
            and not r.get("warranty")
            and not r.get("bvp")
            and float(r.get("d") or 0) < 0
            and float(r.get("eur_prior") or 0) >= 300
            and (cat_id in CRITICAL_PMS or grp in ("Brake parts", "Filters"))
        )
        out.append(
            {
                **r,
                "pms_label": info.get("label") or "",
                "pms_capture_pct": cap,
                "pms_network_pct": net,
                "low_pms": low,
                "still_selling": still,
                "did_not_repeat": (not still) and float(r.get("eur_prior") or 0) > 0,
                "spa_watch": spa,
            }
        )
    return out


def pms_block(pms_code: str) -> dict:
    p = pd.read_csv(DERIVED / "pms_capture_by_db_year.csv")
    p["year"] = pd.to_numeric(p["year"], errors="coerce")
    p = p[p["year"].between(2023, 2025)]
    mine = p[(p["distributor_code"] == pms_code) & (p["line_type"] == "total")].copy()
    net = p[(p["line_type"] == "total") & (p["distributor_code"] != pms_code)].copy()
    years = sorted(int(y) for y in mine["year"].dropna().unique())
    cats = []
    for cat in mine["pms_category"].dropna().unique():
        series = []
        skip_best = False
        for y in years:
            u = mine[(mine["year"] == y) & (mine["pms_category"] == cat)]
            n = net[(net["year"] == y) & (net["pms_category"] == cat)]
            if u.empty:
                continue
            rate = float(u["capture_rate"].iloc[0])
            nrate = None
            if not n.empty:
                exp = float(pd.to_numeric(n["expected_qty"], errors="coerce").sum())
                act = float(pd.to_numeric(n["actual_qty"], errors="coerce").sum())
                nrate = (act / exp) if exp else None
            if rate > 1.0:
                skip_best = True
            series.append(
                {
                    "year": int(y),
                    "capture_pct": round(rate * 100, 2),
                    "actual_qty": r2(u["actual_qty"].iloc[0]),
                    "expected_qty": r2(u["expected_qty"].iloc[0]),
                    "rev": r2(u["actual_rev_eur"].iloc[0]),
                    "gap": r2(u["revenue_gap_eur"].iloc[0]),
                    "quotable": bool(u["revenue_gap_quotable"].iloc[0]),
                    "network_pct": round(nrate * 100, 2) if nrate is not None else None,
                }
            )
        lab = str(mine.loc[mine["pms_category"] == cat, "category_label"].iloc[0])
        last = series[-1] if series else {}
        gen = p[
            (p["distributor_code"] == pms_code)
            & (p["line_type"] == "genuine")
            & (p["pms_category"] == cat)
            & (p["year"] == 2025)
        ]
        genuine_pct = (
            round(float(gen["capture_rate"].iloc[0]) * 100, 2) if not gen.empty else None
        )
        cats.append(
            {
                "id": cat,
                "label": lab,
                "critical": cat in CRITICAL_PMS,
                "skip_best_series": skip_best,
                "series": series,
                "cy2025_pct": last.get("capture_pct"),
                "genuine_cy2025_pct": genuine_pct,
                "network_pct": last.get("network_pct"),
                "gap": last.get("gap"),
                "quotable": last.get("quotable"),
            }
        )
    cats.sort(key=lambda c: (c["cy2025_pct"] is None, -(c["cy2025_pct"] or 0)))
    uio = int(mine["uio_units"].iloc[0]) if not mine.empty else None
    return {
        "uio_units": uio,
        "uio_note": "Parc in this capture file is frozen across years. Network capture excludes this distributor.",
        "line_type": "total",
        "categories": cats,
    }


def monthly(df: pd.DataFrame) -> list[dict]:
    x = df[~df["is_credit"]].copy()
    x["ym"] = x["dt"].dt.to_period("M").astype(str)
    rows = []
    for ym, g in x.groupby("ym"):
        rows.append(
            {
                "ym": ym,
                "total": r2(g["eur"].sum()),
                "shell": r2(g.loc[g["is_shell"], "eur"].sum()),
                "warranty": r2(g.loc[~g["is_shell"] & g["is_warranty"], "eur"].sum()),
                "commercial": r2(g.loc[~g["is_shell"] & ~g["is_warranty"], "eur"].sum()),
            }
        )
    rows.sort(key=lambda r: r["ym"])
    return rows


def _group_sums(sl: pd.DataFrame, hide_warr: bool = True) -> pd.Series:
    nos = sl[~sl["is_credit"] & ~sl["is_shell"]]
    if hide_warr and "is_warranty" in nos.columns:
        nos = nos[~nos["is_warranty"]]
    return nos.groupby(nos["pr00_group"].fillna("Unclassified"))["eur"].sum()


def choose_family_groups(
    now: pd.DataFrame, prior: pd.DataFrame, hide_warr: bool = True
) -> tuple[list[dict], list[dict], bool]:
    """Named families from THIS pair of windows. Unclassified never gets a named bar."""
    gn, gp = _group_sums(now, hide_warr), _group_sums(prior, hide_warr)
    tot_n = float(gn.sum()) or 1.0
    tot_p = float(gp.sum()) or 1.0
    idx = gn.index.union(gp.index)
    scored = []
    leftover_now = []
    for name in idx:
        a = float(gn.get(name, 0))
        b = float(gp.get(name, 0))
        mx = max(a, b)
        share = max(a / tot_n, b / tot_p)
        row = {
            "id": str(name),
            "label": FAMILY_LABELS.get(str(name), str(name)[:18]),
            "now": r2(a),
            "prior": r2(b),
        }
        if str(name) != "Unclassified" and (mx >= FAM_EUR_MIN or share >= FAM_SHARE_MIN):
            scored.append((mx, a, row))
        else:
            leftover_now.append((a, str(name)))
    scored.sort(key=lambda t: t[1], reverse=True)
    groups = [t[2] for t in scored]
    leftover_now.sort(reverse=True)
    other_parts = [
        {"id": n, "eur": r2(v), "share_pct": round(100.0 * v / tot_n, 1)}
        for v, n in leftover_now
        if v >= 1
    ]
    nos = now[~now["is_credit"]]
    show_shell = float(nos.loc[nos["is_shell"], "eur"].sum()) >= 50 or float(
        prior.loc[~prior["is_credit"] & prior["is_shell"], "eur"].sum()
    ) >= 50
    return groups, other_parts, show_shell


def union_named_ids(slices: dict) -> tuple[list[str], bool]:
    seen: set[str] = set()
    show_shell = False
    for now_k, pri_k in AIM_WIN_PAIRS:
        if now_k not in slices or pri_k not in slices:
            continue
        groups, _, sh = choose_family_groups(slices[now_k], slices[pri_k], hide_warr=True)
        show_shell = show_shell or sh
        for g in groups:
            if g["id"] != "Unclassified":
                seen.add(g["id"])
    cy = _group_sums(slices["cy2025"], hide_warr=True) if "cy2025" in slices else pd.Series(dtype=float)
    ids = sorted(seen, key=lambda i: float(cy.get(i, 0)), reverse=True)
    return ids, show_shell


def _aim_pack(y: pd.DataFrame, named_ids: list[str]) -> dict:
    nos = y[~y["is_shell"]]
    g = nos.groupby(nos["pr00_group"].fillna("Unclassified"))["eur"].sum()
    groups = {str(name): r2(val) for name, val in g.items()}
    named_sum = sum(float(groups.get(i, 0)) for i in named_ids)
    tot_nos = float(nos["eur"].sum())
    uncl = r2(groups.get("Unclassified", 0))
    classified = tot_nos - uncl
    warr = r2(y.loc[y["is_warranty"], "eur"].sum()) if "is_warranty" in y.columns else 0.0
    return {
        "total": r2(y["eur"].sum()),
        "shell": r2(y.loc[y["is_shell"], "eur"].sum()),
        "groups": groups,
        "other": r2(tot_nos - named_sum),
        "unclassified": uncl,
        "classified_eur": r2(classified),
        "classified_pct": round(100.0 * classified / tot_nos, 1) if tot_nos else None,
        "warranty": warr,
    }


def aim_slice(sl: pd.DataFrame, named_ids: list[str]) -> dict:
    x = sl[~sl["is_credit"]].copy()
    out = _aim_pack(x, named_ids)
    if "is_warranty" in x.columns:
        out["ex_warr"] = _aim_pack(x[~x["is_warranty"]], named_ids)
    return out


def q_label(q: str) -> str:
    return f"Q{q[-1]} {q[:4]}"


def aim_block(df: pd.DataFrame, slices: dict) -> dict:
    group_ids, show_shell = union_named_ids(slices)
    cy_groups, cy_other, _ = choose_family_groups(
        slices["cy2025"], slices["cy2024"], hide_warr=True
    )
    x = df[~df["is_credit"]].copy()
    x = x[(x["dt"] >= "2024-01-01") & (x["dt"] < "2026-07-01")]
    x["q"] = x["dt"].dt.to_period("Q").astype(str)
    quarterly = []
    for q, g in x.groupby("q"):
        row = aim_slice(g, group_ids)
        row["q"] = str(q)
        row["label"] = q_label(str(q))
        quarterly.append(row)
    quarterly.sort(key=lambda r: r["q"])
    cy = aim_slice(slices["cy2025"], group_ids)
    painted = cy.get("ex_warr") or cy
    other_eur = float(painted.get("other") or 0)
    tot = float(painted.get("total") or 0) or 1.0
    leftover = ", ".join(
        f"{p['id']} €{p['eur']:,.0f}" for p in cy_other[:8]
    ) or "none"
    cov = painted.get("classified_pct")
    note = (
        "Catalogue family is PR00 group on the parts catalogue. "
        f"{cov}% of Calendar 2025 commercial euros have a family name. "
        "The clustered bars name families from the selected window "
        f"(at least €{FAM_EUR_MIN:,.0f} in either year, or {100*FAM_SHARE_MIN:.0f}% of the window). "
        "Other is unclassified plus families below that cut — not every classified euro."
    )
    if not show_shell:
        note += " No Shell lubricant lines in this book, so Shell is not on the chart."
    if other_eur >= 1:
        note += (
            f" On Calendar 2025 with warranty hidden, Other is {other_eur:,.0f} € "
            f"({100*other_eur/tot:.0f}%): {leftover}."
        )
    groups = [
        {"id": g, "label": FAMILY_LABELS.get(g, g[:18])} for g in group_ids
    ]
    line_ids = [g["id"] for g in cy_groups[:5]] or group_ids[:5]
    return {
        "note": note,
        "groups": groups,
        "labels": FAMILY_LABELS,
        "min_eur": FAM_EUR_MIN,
        "min_share": FAM_SHARE_MIN,
        "show_shell": show_shell,
        "other_parts": cy_other,
        "line_ids": line_ids,
        "quarterly": quarterly,
        "windows": {k: aim_slice(sl, group_ids) for k, sl in slices.items()},
    }


def tone(dp: float | None, invert: bool = False) -> str:
    if dp is None:
        return ""
    bad = dp < 0
    if invert:
        bad = not bad
    if abs(dp) < 0.6:
        return ""
    return "bad" if bad else "good"


def build_verdict(name: str, wsum: dict, pbi: dict, as_of: str) -> dict:
    h1n, h1p = wsum["cy_h1_2026"], wsum["cy_h1_2025"]
    amj_n, amj_p = wsum["amj_2026"], wsum["amj_2025"]
    q1n, q1p = wsum["q1_2026"], wsum["q1_2025"]
    cy23, cy24, cy25 = wsum["cy2023"], wsum["cy2024"], wsum["cy2025"]
    h1_dp = rpct(h1n["total"], h1p["total"])
    com_h1 = rpct(h1n["commercial"], h1p["commercial"])
    amj_dp = rpct(amj_n["total"], amj_p["total"])
    q1_dp = rpct(q1n["total"], q1p["total"])
    two_yr = rpct(cy25["commercial"], cy23["commercial"])
    w_share = round(100.0 * cy25["warranty"] / cy25["total"], 1) if cy25["total"] else None

    chips = []
    if pbi["available"]:
        ytd_dp = rpct(sum(pbi["sales"]), sum(pbi["prev_year"]))
        chips.append(
            {
                "label": "Official YTD",
                "value": f"{ytd_dp:+.1f}%" if ytd_dp is not None else "—",
                "sub": f"{eur_k(sum(pbi['sales']))} vs {eur_k(sum(pbi['prev_year']))}",
                "cls": tone(ytd_dp),
                "tip": "Official sales cut. Credit notes are not sales.",
            }
        )
    chips.append(
        {
            "label": "Billing H1",
            "value": f"{h1_dp:+.1f}%" if h1_dp is not None else "—",
            "sub": f"{eur_k(h1n['total'])} vs {eur_k(h1p['total'])} · Jan–Jun",
            "cls": tone(h1_dp),
            "tip": "ISZE billing, credit notes out. Not an official Power BI cut.",
        }
    )
    chips.append(
        {
            "label": "Commercial H1",
            "value": f"{com_h1:+.1f}%" if com_h1 is not None else "—",
            "sub": f"{eur_k(h1n['commercial'])} vs {eur_k(h1p['commercial'])}",
            "cls": tone(com_h1),
            "tip": (
                "Billing minus Shell lubricants minus warranty-tagged lines."
                if (h1n["shell"] or h1p["shell"])
                else "Billing minus warranty-tagged lines. This book has no Shell lubricant lines."
            ),
        }
    )
    chips.append(
        {
            "label": "Apr–Jun billing",
            "value": f"{amj_dp:+.1f}%" if amj_dp is not None else "—",
            "sub": f"{eur_k(amj_n['total'])} vs {eur_k(amj_p['total'])}",
            "cls": tone(amj_dp),
            "tip": "April–June billing. Credit notes are not sales.",
        }
    )
    chips.append(
        {
            "label": "Commercial 2023→2025",
            "value": f"{two_yr:+.1f}%" if two_yr is not None else "—",
            "sub": f"{eur_k(cy23['commercial'])} → {eur_k(cy25['commercial'])} · warranty share {w_share}%",
            "cls": tone(two_yr),
            "tip": "Calendar commercial euro, warranty tagged on the current claim-PN list.",
        }
    )

    unit_chips = [
        {
            "label": "H1 units",
            "value": f"{rpct(h1n['qty'], h1p['qty']) or 0:+.1f}%",
            "sub": f"{int(h1n['qty']):,} vs {int(h1p['qty']):,}",
            "cls": tone(rpct(h1n["qty"], h1p["qty"])),
            "tip": "Billed units, calendar January–June, credits out.",
        },
        {
            "label": "H1 commercial units",
            "value": f"{rpct(h1n['qty_commercial'], h1p['qty_commercial']) or 0:+.1f}%",
            "sub": f"Commercial € {rpct(h1n['commercial'], h1p['commercial']) or 0:+.1f}%",
            "cls": tone(rpct(h1n["qty_commercial"], h1p["qty_commercial"])),
            "tip": "Units on commercial lines (not Shell, not warranty-tagged).",
        },
        {
            "label": "Apr–Jun commercial units",
            "value": f"{rpct(amj_n['qty_commercial'], amj_p['qty_commercial']) or 0:+.1f}%",
            "sub": f"{int(amj_p['qty_commercial']):,} → {int(amj_n['qty_commercial']):,}",
            "cls": tone(rpct(amj_n["qty_commercial"], amj_p["qty_commercial"])),
            "tip": "April–June commercial units versus the same months last year.",
        },
    ]

    callouts = []
    callouts.append(
        {
            "tone": "default",
            "html": (
                f"Billing through {as_of}. Calendar H1 is <b>{eur_k(h1n['total'])} vs {eur_k(h1p['total'])}"
                f" ({h1_dp:+.1f}%)</b>. Commercial in that window is <b>{com_h1:+.1f}%</b>. "
                "Credit notes are not sales."
            ),
        }
    )
    if q1_dp is not None and h1_dp is not None and q1_dp < h1_dp - 8:
        callouts.append(
            {
                "tone": "warn",
                "html": (
                    f"Q1 billing is <b>{q1_dp:+.1f}%</b> ({eur_k(q1n['total'])} vs {eur_k(q1p['total'])}). "
                    f"H1 is milder at {h1_dp:+.1f}% — later months recovered some of the hole. "
                    "There is no official sales cut on file for this distributor."
                ),
            }
        )
    w23 = round(100.0 * cy23["warranty"] / cy23["total"], 1) if cy23["total"] else 0
    if w_share is not None and w_share >= 40:
        callouts.append(
            {
                "tone": "warn",
                "html": (
                    f"Warranty is <b>{w_share}%</b> of calendar 2025 ({w23}% in 2023). "
                    f"Commercial over two years is {two_yr:+.1f}%."
                ),
            }
        )
    else:
        callouts.append(
            {
                "tone": "default",
                "html": (
                    f"Warranty is <b>{w_share}%</b> of calendar 2025 billed euro — not the majority of the book. "
                    f"Commercial 2023→2025 is <b>{two_yr:+.1f}%</b> "
                    f"({eur_k(cy23['commercial'])} → {eur_k(cy24['commercial'])} → {eur_k(cy25['commercial'])})."
                ),
            }
        )
    if wsum["jul_2026"]["total"] <= 0:
        callouts.append(
            {
                "tone": "warn",
                "html": (
                    "July this year is not in the billing file yet, so July cannot be split. "
                    "Do not read an official July miss from this pack."
                ),
            }
        )

    return {
        "has_pbi": pbi["available"],
        "chips": chips,
        "unit_chips": unit_chips,
        "callouts": callouts,
        "cover_line": (
            f"{name}: billed sales versus last year. Credit notes are not sales."
            if not pbi["available"]
            else f"{name}: official sales versus last year. Credit notes are not sales."
        ),
    }


def build_for(operating_db: str) -> Path:
    profile = profile_for_operating_db(operating_db)
    out_db = str(profile.get("dashboard_key") or operating_db).upper()
    outdir = MEETINGS / f"{out_db}_Operating_Dashboard_2026"
    outdir.mkdir(parents=True, exist_ok=True)
    pbi = pbi_cut(profile)
    df = load_db_sales(profile)
    try:
        claim = load_warranty_claim_pns(profile)
    except Exception:
        claim = {"pns": set(), "available": False}
    df = tag_warranty(df, claim["pns"])
    cat = load_catalog()
    df = df.merge(cat, left_on="pn", right_on="part_number", how="left")
    xref = pd.read_csv(DERIVED / "genuine_bvp_crossref.csv", dtype=str)
    bvp_pns = set(xref["bvp_pn"].map(norm_pn).dropna())
    df["is_bvp"] = df["pn"].isin(bvp_pns)

    windows = {
        "cy2023": ("2023-01-01", "2024-01-01"),
        "cy2024": ("2024-01-01", "2025-01-01"),
        "cy2025": ("2025-01-01", "2026-01-01"),
        "cy_h1_2025": ("2025-01-01", "2025-07-01"),
        "cy_h1_2026": ("2026-01-01", "2026-07-01"),
        "q1_2025": ("2025-01-01", "2025-04-01"),
        "q1_2026": ("2026-01-01", "2026-04-01"),
        "fy2024": ("2023-04-01", "2024-04-01"),
        "fy2025": ("2024-04-01", "2025-04-01"),
        "fy2026": ("2025-04-01", "2026-04-01"),
        "amj_2025": ("2025-04-01", "2025-07-01"),
        "amj_2026": ("2026-04-01", "2026-07-01"),
        "jul_2025": ("2025-07-01", "2025-08-01"),
        "jul_2026": ("2026-07-01", "2026-08-01"),
        "fy27_ytd": ("2026-04-01", "2026-08-01"),
        "fy26_ytd": ("2025-04-01", "2025-08-01"),
        "l12_now": ("2025-08-01", "2026-08-01"),
        "l12_prior": ("2024-08-01", "2025-08-01"),
    }
    wsum, slices = {}, {}
    for k, (a, b) in windows.items():
        sl = df[window_mask(df, a, b)].copy()
        slices[k] = sl
        wsum[k] = {**split_sums(sl), "start": a, "end": b}

    recon = []
    if pbi["available"]:
        for i, label in enumerate(pbi["months"]):
            m = 4 + i
            start = f"2026-{m:02d}-01"
            end = f"2026-{m + 1:02d}-01" if m < 12 else "2027-01-01"
            sl = df[window_mask(df, start, end)]
            inv = float(sl.loc[~sl["is_credit"], "eur"].sum())
            cr = float(sl.loc[sl["is_credit"], "eur"].sum())
            official = int(pbi["sales"][i])
            recon.append(
                {
                    "month": label,
                    "official": official,
                    "prior_year": int(pbi["prev_year"][i]),
                    "invoice_eur": r2(inv),
                    "credit_note_eur": r2(cr),
                    "gap_invoices_vs_official": r2(inv - official),
                    "in_file": inv > 0 or cr != 0,
                }
            )
    else:
        for i, label in enumerate(["Apr", "May", "Jun"]):
            m = 4 + i
            start = f"2026-{m:02d}-01"
            end = f"2026-{m + 1:02d}-01"
            sl = df[window_mask(df, start, end)]
            pri = df[window_mask(df, f"2025-{m:02d}-01", f"2025-{m + 1:02d}-01")]
            inv = float(sl.loc[~sl["is_credit"], "eur"].sum())
            cr = float(sl.loc[sl["is_credit"], "eur"].sum())
            recon.append(
                {
                    "month": label,
                    "official": None,
                    "prior_year": r2(float(pri.loc[~pri["is_credit"], "eur"].sum())),
                    "invoice_eur": r2(inv),
                    "credit_note_eur": r2(cr),
                    "gap_invoices_vs_official": None,
                    "in_file": inv > 0 or cr != 0,
                }
            )

    as_of = str(df["dt"].max())[:10]
    pms_pack = pms_block(str(profile.get("pms_code") or out_db))
    pms_cats = pms_pack["categories"]
    fy_now, fy_pri = slices["amj_2026"], slices["amj_2025"]

    def pms_eur(sl):
        x = sl[~sl["is_credit"]]
        out = {cat: r2(x.loc[x["pms_category"] == cat, "eur"].sum()) for cat in CRITICAL_PMS}
        out["pms_basket"] = r2(x.loc[x["pms_category"].isin(CRITICAL_PMS), "eur"].sum())
        return out

    payload = {
        "meta": {
            "db": profile["key"],
            "operating_db": out_db,
            "customer": profile.get("name"),
            "country": profile.get("country"),
            "as_of": as_of,
            "min_dt": str(df["dt"].min())[:10],
            "credits": "Credit notes are not sales. CR lines dropped from mix and invoice totals.",
            "warranty_claim_pns": len(claim["pns"]),
            "warranty_available": claim["available"],
            "warranty_tag_note": "Warranty tag is the current claim-PN list applied to all years.",
            "gps_note": "GPS is the operating-dashboard spine (V19 × current D-Max rate). Not a second wallet.",
        },
        "pbi": pbi,
        "verdict": build_verdict(profile.get("name") or out_db, wsum, pbi, as_of),
        "windows": wsum,
        "recon": recon,
        "monthly": monthly(df),
        "aim": aim_block(df, slices),
        "pms": pms_pack,
        "pms_eur_in_window": {
            "amj_2026": pms_eur(fy_now),
            "amj_2025": pms_eur(fy_pri),
            "cy_h1_2026": pms_eur(slices["cy_h1_2026"]),
            "cy_h1_2025": pms_eur(slices["cy_h1_2025"]),
        },
        "pn": {
            "amj": enrich_pn(pn_delta(fy_pri, fy_now, 400), pms_cats),
            "cy_h1": enrich_pn(
                pn_delta(slices["cy_h1_2025"], slices["cy_h1_2026"], 400), pms_cats
            ),
            "l12": enrich_pn(
                pn_delta(slices["l12_prior"], slices["l12_now"], 400), pms_cats
            ),
        },
        "hygiene": {
            "uncoded_share_amj": wsum["amj_2026"]["uncoded_share"],
            "uncoded_eur_amj": wsum["amj_2026"]["uncoded_eur"],
            "uncoded_lines_amj": wsum["amj_2026"]["uncoded_lines"],
            "credit_eur_h1": wsum["cy_h1_2026"]["credit_eur"],
            "jul_in_file": wsum["jul_2026"]["total"] > 0,
        },
    }
    path = outdir / "_sales_analysis.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print("wrote", path, "as_of", as_of, "H1", wsum["cy_h1_2026"]["total"], "vs", wsum["cy_h1_2025"]["total"])
    return path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="GREECE", help="Operating-dashboard key (GREECE) or profile key (PETROS)")
    a = ap.parse_args()
    build_for(a.db)


if __name__ == "__main__":
    main()
