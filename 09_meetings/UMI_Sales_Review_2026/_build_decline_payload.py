"""Distributor sales-analysis payload. Template: set DB and rebuild.

Never blends the other Israel sold-to. Never loads raw billing XLSX.
Credits are not sales: CR lines are dropped from every mix/total (both
unsigned-positive history and signed-negative export notes).
Official monthly cut is the sales headline when the profile has pbi:.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ISZE / "01_data" / "00_derived"
OUT = ISZE / "09_meetings" / "UMI_Sales_Review_2026" / "_decline_payload.json"
sys.path.insert(0, str(ISZE / "04_tools" / "db_sales_review"))
from common import (  # noqa: E402
    is_warranty_campaign_text,
    load_catalog,
    load_profile,
    load_warranty_claim_pns,
    norm_pn,
)

DB = "UMI"
UMI = 1797
UTI = 1799
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


def official_cut(profile: dict) -> dict:
    p = profile.get("pbi") or {}
    return {
        "months": list(p.get("months") or ["Apr", "May", "Jun", "Jul"]),
        "sales": [int(x) for x in (p.get("sales") or [])],
        "prev_year": [int(x) for x in (p.get("prev_year") or [])],
        "budget": [int(x) for x in (p.get("budget") or [])],
        "source": str(p.get("source") or "Official sales cut"),
    }


def load_umi_sales() -> pd.DataFrame:
    sf = pd.read_parquet(DERIVED / "sales_fact.parquet")
    sap = pd.to_numeric(sf["sold_to_sap"], errors="coerce")
    umi = sf[sap == UMI].copy()
    uti_n = int((sap == UTI).sum())
    umi["pn"] = umi["part_number"].map(norm_pn)
    umi["eur"] = pd.to_numeric(umi["net_sales_value"], errors="coerce").fillna(0)
    umi["qty"] = pd.to_numeric(umi["billed_qty"], errors="coerce").fillna(0)
    umi["dt"] = pd.to_datetime(umi["billing_date"], errors="coerce")
    umi["saty"] = umi["saty"].map(saty_norm)
    umi = umi[umi["dt"].notna()]
    umi["src"] = "sales_fact"
    # Apr+ 2026 from official-aligned export
    exp = pd.read_csv(DERIVED / "q1fy2027_export_with_saty.csv", low_memory=False)
    st = exp["Sold_to"].map(sap_num)
    exp = exp[st == str(UMI)].copy()
    exp["dt"] = pd.to_datetime(exp["Billing Date"], errors="coerce")
    exp = exp[exp["dt"] >= "2026-04-01"]
    exp["pn"] = exp["Material"].map(norm_pn)
    exp["eur"] = pd.to_numeric(exp["EUR_Amount"], errors="coerce").fillna(0)
    exp["qty"] = pd.to_numeric(exp["Quantity"], errors="coerce").fillna(0)
    exp["saty"] = exp["SaTy"].map(saty_norm)
    exp["description"] = exp["Material_Number"].astype(str)
    exp["src"] = "export_apr"
    keep = ["dt", "pn", "eur", "qty", "saty", "description", "src"]
    hist = umi.loc[umi["dt"] < "2026-04-01", keep]
    out = pd.concat([hist, exp[keep]], ignore_index=True)
    out["is_credit"] = out["saty"] == "CR"
    out["is_saty_blank"] = out["saty"] == ""
    out["is_shell"] = out["pn"].fillna("").str.match(SHELL_RE)
    return out, uti_n, int((sap == UMI).sum())


def tag_warranty(df: pd.DataFrame, claim_pns: set[str]) -> pd.DataFrame:
    desc = df["description"].fillna("")
    pn = df["pn"].fillna("")
    on_claim = pn.isin(claim_pns)
    text = [
        is_warranty_campaign_text(p, d) for p, d in zip(pn.tolist(), desc.tolist())
    ]
    df = df.copy()
    df["is_warranty"] = on_claim | np.array(text, dtype=bool)
    return df


def bucket(row) -> str:
    if row["is_shell"]:
        return "Shell lubricants"
    if row["is_warranty"]:
        return "Warranty"
    return "Other commercial"


def window_mask(df, start, end):
    return (df["dt"] >= start) & (df["dt"] < end)


def sum_ex_cr(df) -> float:
    return float(df.loc[~df["is_credit"], "eur"].sum())


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
        g = x.groupby("pn", dropna=True).agg(**spec)
        return g

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
        qty_eff = (qb - qa) * pa
        px_eff = (pb - pa) * qb
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
                "qty_effect": r2(qty_eff),
                "price_effect": r2(px_eff),
            }
        )
    rows.sort(key=lambda r: r["d"])
    return rows[:n]


def enrich_pn(rows: list[dict], pms_cats: list[dict]) -> list[dict]:
    """Attach CY2025 total capture so the HTML can split warranty vs weak service parts."""
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
            and (
                cat_id in CRITICAL_PMS
                or grp in ("Brake parts", "Filters")
            )
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


def pms_block() -> dict:
    p = pd.read_csv(DERIVED / "pms_capture_by_db_year.csv")
    p["year"] = pd.to_numeric(p["year"], errors="coerce")
    # CY2026 in this file is a partial year against a full-year expected — do not use.
    p = p[p["year"].between(2023, 2025)]
    umi = p[(p["distributor_code"] == DB) & (p["line_type"] == "total")].copy()
    net = p[(p["line_type"] == "total") & (p["distributor_code"] != DB)].copy()
    years = sorted(int(y) for y in umi["year"].dropna().unique())
    cats = []
    for cat in umi["pms_category"].dropna().unique():
        series = []
        skip_best = False
        for y in years:
            u = umi[(umi["year"] == y) & (umi["pms_category"] == cat)]
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
        lab = str(umi.loc[umi["pms_category"] == cat, "category_label"].iloc[0])
        last = series[-1] if series else {}
        gen = p[
            (p["distributor_code"] == DB)
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
    uio = int(umi["uio_units"].iloc[0]) if not umi.empty else None
    return {
        "uio_units": uio,
        "uio_note": "UIO in this file is frozen across years — capture trend is volume vs a fixed parc proxy, not a live fleet series. Network capture excludes this distributor.",
        "line_type": "total",
        "categories": cats,
    }


def gps_block(wsum: dict, gps_key: str) -> dict:
    g = pd.read_csv(DERIVED / "gps_master.csv")
    row = g[g.iloc[:, 0].astype(str).str.strip() == gps_key]
    if row.empty:
        return {"available": False}
    r = row.iloc[0]
    uio = float(r["uio_2025"])
    rate_file = float(r["rate"])
    max_file = float(r["max_spend"])

    def gps_pct(num, rate=None):
        ceil = (uio * float(rate)) if rate else max_file
        return round(100.0 * float(num) / ceil, 2) if ceil else None

    bill = {}
    warr = {}
    net_our = {}
    gps_incl = {}
    gps_ex = {}
    for key, fy in (("fy2024", "FY2024"), ("fy2025", "FY2025"), ("fy2026", "FY2026")):
        tot = float(wsum[key]["total"])
        warr_e = float(wsum[key]["warranty"])
        bill[fy] = r2(tot)
        warr[fy] = r2(warr_e)
        net_our[fy] = r2(tot - warr_e)
        gps_incl[fy] = gps_pct(tot)
        gps_ex[fy] = gps_pct(tot - warr_e)

    rate_now = 262.50
    return {
        "available": True,
        "uio_file": r2(uio),
        "rate_in_file": r2(rate_file),
        "max_spend_file": r2(max_file),
        "bill": bill,
        "warr": warr,
        "net": net_our,
        "gps_pct_incl_warr": gps_incl,
        "gps_pct_ex_warr": gps_ex,
        "gps_pct_incl_warr_live_rate": {
            "FY2026": gps_pct(bill["FY2026"], rate_now),
        },
        "formula_incl": "GPS % including warranty = all billed parts € ÷ (parc × ISZE-net € per unit)",
        "formula_ex": "GPS % excluding warranty = billed € minus warranty € ÷ (parc × ISZE-net € per unit)",
        "formula": "GPS % excluding warranty = billed € minus warranty € ÷ (parc × ISZE-net € per unit)",
        "rate_current_fy27": rate_now,
        "note": "Commercial GPS is excluding warranty. Including warranty is the contractual lens. Same parc 18,349 × €250 for the three-year series. Live FY2027 rate €262.50 is shown as its own chip, not mixed into the trend.",
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


# Catalogue AIM groups that carry the mix story. Shell stays its own class.
AIM_GROUPS = [
    {"id": "Exhaust", "label": "Exhaust"},
    {"id": "Brake parts", "label": "Brakes"},
    {"id": "Body parts", "label": "Body"},
    {"id": "Lighting", "label": "Lighting"},
    {"id": "Filters", "label": "Filters"},
    {"id": "Steering", "label": "Steering"},
    {"id": "Electrical sensors", "label": "Sensors"},
    {"id": "Engine parts", "label": "Engine"},
]


def _aim_pack(y: pd.DataFrame) -> dict:
    ids = [g["id"] for g in AIM_GROUPS]
    nos = y[~y["is_shell"]]
    g = nos.groupby(nos["pr00_group"].fillna("Unclassified"))["eur"].sum()
    groups = {name: r2(g.get(name, 0)) for name in ids}
    warr = (
        r2(y.loc[y["is_warranty"], "eur"].sum()) if "is_warranty" in y.columns else 0.0
    )
    return {
        "total": r2(y["eur"].sum()),
        "shell": r2(y.loc[y["is_shell"], "eur"].sum()),
        "groups": groups,
        "other": r2(float(nos["eur"].sum()) - sum(groups.values())),
        "warranty": warr,
    }


def aim_slice(sl: pd.DataFrame) -> dict:
    x = sl[~sl["is_credit"]].copy()
    out = _aim_pack(x)
    if "is_warranty" in x.columns:
        out["ex_warr"] = _aim_pack(x[~x["is_warranty"]])
    else:
        out["ex_warr"] = {k: v for k, v in out.items() if k != "ex_warr"}
    return out


def q_label(q: str) -> str:
    return f"Q{q[-1]} {q[:4]}"


def aim_block(df: pd.DataFrame, slices: dict) -> dict:
    x = df[~df["is_credit"]].copy()
    x = x[(x["dt"] >= "2024-01-01") & (x["dt"] < "2026-07-01")]
    x["q"] = x["dt"].dt.to_period("Q").astype(str)
    quarterly = []
    for q, g in x.groupby("q"):
        row = aim_slice(g)
        row["q"] = str(q)
        row["label"] = q_label(str(q))
        quarterly.append(row)
    quarterly.sort(key=lambda r: r["q"])
    byq = {r["q"]: r for r in quarterly}

    def gq(q, gid):
        return float((byq.get(q) or {}).get("groups", {}).get(gid, 0) or 0)

    return {
        "note": (
            "AIM group from the parts catalogue. Warranty volume stays inside "
            "the family until you hide it — Exhaust is mostly DPD / warranty. "
            "Shell lubricants are a separate class, not an AIM group."
        ),
        "groups": AIM_GROUPS,
        "quarterly": quarterly,
        "windows": {k: aim_slice(sl) for k, sl in slices.items()},
        "highlights": {
            "exhaust_q2_2025": r2(gq("2025Q2", "Exhaust")),
            "exhaust_q3_2025": r2(gq("2025Q3", "Exhaust")),
            "exhaust_q4_2025": r2(gq("2025Q4", "Exhaust")),
            "brakes_q1_2025": r2(gq("2025Q1", "Brake parts")),
            "brakes_q2_2025": r2(gq("2025Q2", "Brake parts")),
            "brakes_q3_2025": r2(gq("2025Q3", "Brake parts")),
        },
    }


def main() -> None:
    profile = load_profile(DB)
    pbi = official_cut(profile)
    df, uti_rows, umi_sf_rows = load_umi_sales()
    claim = load_warranty_claim_pns(profile)
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
    wsum = {}
    slices = {}
    for k, (a, b) in windows.items():
        sl = df[window_mask(df, a, b)].copy()
        slices[k] = sl
        wsum[k] = {**split_sums(sl), "start": a, "end": b}

    # Official months vs invoice lines (credit notes are not sales)
    recon = []
    for i, label in enumerate(pbi["months"]):
        m = 4 + i
        start = f"2026-{m:02d}-01"
        end = f"2026-{m+1:02d}-01" if m < 12 else "2027-01-01"
        if m == 7:
            end = "2026-08-01"
        sl = df[window_mask(df, start, end)]
        inv = float(sl.loc[~sl["is_credit"], "eur"].sum())
        cr = float(sl.loc[sl["is_credit"], "eur"].sum())
        official = int(pbi["sales"][i]) if i < len(pbi["sales"]) else 0
        recon.append(
            {
                "month": label,
                "official": official,
                "prior_year": int(pbi["prev_year"][i]) if i < len(pbi["prev_year"]) else 0,
                "invoice_eur": r2(inv),
                "credit_note_eur": r2(cr),
                "gap_invoices_vs_official": r2(inv - official),
                "in_file": inv > 0 or cr != 0,
            }
        )

    fy_now = slices["amj_2026"]
    fy_pri = slices["amj_2025"]
    pbi_amj_now = int(sum(pbi["sales"][:3]))
    pbi_amj_py = int(sum(pbi["prev_year"][:3]))
    pbi_jul_now = int(pbi["sales"][3])
    pbi_jul_py = int(pbi["prev_year"][3])
    cy23, cy24, cy25 = wsum["cy2023"], wsum["cy2024"], wsum["cy2025"]
    waterfall = {
        "label": "Official Apr–Jun is the sales number. Invoice lines keep credit notes out.",
        "prior_total": wsum["amj_2025"]["total"],
        "now_total": wsum["amj_2026"]["total"],
        "d_total": r2(wsum["amj_2026"]["total"] - wsum["amj_2025"]["total"]),
        "d_shell": r2(wsum["amj_2026"]["shell"] - wsum["amj_2025"]["shell"]),
        "d_warranty": r2(wsum["amj_2026"]["warranty"] - wsum["amj_2025"]["warranty"]),
        "d_commercial": r2(
            wsum["amj_2026"]["commercial"] - wsum["amj_2025"]["commercial"]
        ),
        "jul_2025_total": wsum["jul_2025"]["total"],
        "jul_2025_warranty": wsum["jul_2025"]["warranty"],
        "jul_2026_total": wsum["jul_2026"]["total"],
        "pbi_ytd_now": int(sum(pbi["sales"])),
        "pbi_ytd_py": int(sum(pbi["prev_year"])),
        "pbi_ytd_d": int(sum(pbi["sales"]) - sum(pbi["prev_year"])),
        "pbi_ytd_dp": rpct(sum(pbi["sales"]), sum(pbi["prev_year"])),
        "pbi_amj_now": pbi_amj_now,
        "pbi_amj_py": pbi_amj_py,
        "pbi_amj_d": pbi_amj_now - pbi_amj_py,
        "pbi_jul_now": pbi_jul_now,
        "pbi_jul_py": pbi_jul_py,
        "pbi_jul_d": pbi_jul_now - pbi_jul_py,
        "jul_in_file": wsum["jul_2026"]["total"] > 0,
        "commercial_two_year_dp": rpct(cy25["commercial"], cy23["commercial"]),
        "warranty_share_cy2023": round(100.0 * cy23["warranty"] / cy23["total"], 1),
        "warranty_share_cy2024": round(100.0 * cy24["warranty"] / cy24["total"], 1),
        "warranty_share_cy2025": round(100.0 * cy25["warranty"] / cy25["total"], 1),
    }

    # PMS actual € in billing windows (not capture — capture is CY-complete only)
    def pms_eur(sl):
        x = sl[~sl["is_credit"]]
        out = {}
        for cat in CRITICAL_PMS:
            out[cat] = r2(x.loc[x["pms_category"] == cat, "eur"].sum())
        out["pms_basket"] = r2(x.loc[x["pms_category"].isin(CRITICAL_PMS), "eur"].sum())
        return out

    # group deltas FY YTD
    def group_delta(a, b, col, n=10):
        def g(d):
            x = d[~d["is_credit"]]
            return x.groupby(x[col].fillna("Unclassified"))["eur"].sum()

        ga, gb = g(a), g(b)
        idx = ga.index.union(gb.index)
        rows = []
        for k in idx:
            ea, eb = float(ga.get(k, 0)), float(gb.get(k, 0))
            rows.append({"name": str(k)[:40], "prior": r2(ea), "now": r2(eb), "d": r2(eb - ea)})
        rows.sort(key=lambda r: r["d"])
        return {"down": rows[:n], "up": list(reversed(rows[-n:]))}

    pms_pack = pms_block()
    pms_cats = pms_pack["categories"]

    payload = {
        "meta": {
            "db": DB,
            "customer": profile.get("name") or "Universal Motors Israel",
            "sold_to": UMI,
            "not": "UTI 1799",
            "as_of": str(df["dt"].max())[:10],
            "min_dt": str(df["dt"].min())[:10],
            "verification": "green 106/0 as of 2026-08-17",
            "credits": "Credit notes are not sales. CR lines dropped from mix and invoice totals.",
            "uti_rows_in_sales_fact": uti_rows,
            "umi_rows_sales_fact": umi_sf_rows,
            "warranty_claim_pns": len(claim["pns"]),
            "warranty_available": claim["available"],
            "warranty_tag_note": "Warranty tag is the current claim-PN list applied to all years. Commercial euro is independent of that tag.",
        },
        "pbi": pbi,
        "windows": wsum,
        "waterfall_fy_ytd": waterfall,
        "recon": recon,
        "monthly": monthly(df),
        "aim": aim_block(df, slices),
        "pms": pms_pack,
        "gps": gps_block(wsum, str(profile.get("gps_key") or DB)),
        "pms_eur_in_window": {
            "amj_2026": pms_eur(fy_now),
            "amj_2025": pms_eur(fy_pri),
            "fy27_ytd": pms_eur(slices["fy27_ytd"]),
            "fy26_ytd": pms_eur(slices["fy26_ytd"]),
            "cy_h1_2026": pms_eur(slices["cy_h1_2026"]),
            "cy_h1_2025": pms_eur(slices["cy_h1_2025"]),
        },
        "group_amj": group_delta(fy_pri, fy_now, "pr00_group"),
        "pms_cat_amj": group_delta(fy_pri, fy_now, "pms_category"),
        "pn": {
            "amj": enrich_pn(pn_delta(fy_pri, fy_now, 600), pms_cats),
            "cy_h1": enrich_pn(
                pn_delta(slices["cy_h1_2025"], slices["cy_h1_2026"], 600), pms_cats
            ),
            "l12": enrich_pn(
                pn_delta(slices["l12_prior"], slices["l12_now"], 600), pms_cats
            ),
            "jul_2025": enrich_pn(
                pn_delta(
                    df[window_mask(df, "2024-07-01", "2024-08-01")],
                    slices["jul_2025"],
                    40,
                ),
                pms_cats,
            ),
        },
        "bvp_share_cy2025": {
            "eur": r2(slices["cy2025"].loc[~slices["cy2025"]["is_credit"] & slices["cy2025"]["is_bvp"], "eur"].sum()),
            "total": wsum["cy2025"]["total"],
        },
    }
    tot = payload["bvp_share_cy2025"]["total"]
    payload["bvp_share_cy2025"]["pct"] = (
        round(100 * payload["bvp_share_cy2025"]["eur"] / tot, 1) if tot else None
    )
    for cut, rows in payload["pn"].items():
        payload["pn"][cut] = rows
        payload.setdefault("pn_effects", {})[cut] = {
            "n": len(rows),
            "qty_effect": r2(sum(r["qty_effect"] for r in rows)),
            "price_effect": r2(sum(r["price_effect"] for r in rows)),
        }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", OUT)
    print("as_of", payload["meta"]["as_of"], "windows", {k: v["total"] for k, v in wsum.items()})
    print("recon", recon)
    amj = wsum["amj_2026"]
    print("amj uncoded", amj["uncoded_share"], "eur", amj["uncoded_eur"], "lines", amj["uncoded_lines"])


if __name__ == "__main__":
    main()
