"""Build Mode A + deep-dive Sales Review deck for any distributor.

Usage:
    python build_full_deck.py --db IBX
    python build_full_deck.py --db UMI
    python build_full_deck.py --db HUNGARY

Deep-dive pages use customer-safe eyebrows (no INTERNAL stamp) so selected
slides can be shared. Numbers are computed from sales_fact / wallet_waterfall /
gps_master / AIM / warranty — not hard-coded per DB.

See: 04_tools/ppt_template_v2/DB_SALES_REVIEW_BLUEPRINT.md §7 (deep dive).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pptx import Presentation
from pptx.util import Inches

import common as C  # noqa: E402

ROOT = C.ISZE
TOOLS = ROOT / "04_tools" / "ppt_template_v2"
DBSR = ROOT / "04_tools" / "db_sales_review"
DER = ROOT / "01_data" / "00_derived"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(DBSR))

import isze_chart_theme as ct  # noqa: E402
import isze_deck_builder as db  # noqa: E402
from build_deck import (  # noqa: E402
    build as build_mode_a,
    card,
    eur,
    styled_table,
)

ct.FONT_FAMILY = "Calibri"
plt.rcParams["font.family"] = ct.FONT_FAMILY

# gps_key / profile key → warranty fiscal CSV `db` column
WARRANTY_DB = {
    "IBX": "IBX",
    "UMI": "UMI",
    "UTI": "UTI",
    "IUK": "IUK",
    "ITUK": "ITUK",
    "ISD": "ISD",
    "HUNGARY": "AutoWallis",
    "AutoWallis": "AutoWallis",
    "PETROS": "Greece",
    "Greece": "Greece",
    "NORWAY": "RSA",
    "RSA": "RSA",
    "SWEDEN": "Sverige",
    "PORTUGAL": "Imotors",
    "Imotors": "Imotors",
    "IRELAND": "Ireland",
    "Ireland": "Ireland",
    "FINLAND": "Nordic FI",
    "ROMANIA": "ROM Auto",
    "DENMARK": "Danmark",
    "ICELAND": "BL Iceland",
    "CYPRUS": "Loutsios",
    "MALTA": "GasanZammit",
}

PMS_CATS = ["oil_filter", "fuel_filter", "air_filter", "brake_pad", "brake_rotor"]
PMS_LABELS = {
    "oil_filter": "Oil filter",
    "fuel_filter": "Fuel filter",
    "air_filter": "Air filter",
    "brake_pad": "Brake pad",
    "brake_rotor": "Brake rotor",
}


def out_dir(key: str) -> Path:
    return C.OUT_ROOT / f"{key}_Sales_Review_2026"


def resolve_sold_to(profile: dict) -> int | None:
    if profile.get("sold_to") is not None:
        return int(profile["sold_to"])
    g = pd.read_csv(DER / "gps_billing_fy_ALLCUSTOMERS.csv")
    hit = g[g["canonical_name"] == profile["gps_key"]]
    if hit.empty:
        return None
    return int(float(str(hit["payer_codes"].iloc[0]).split(";")[0].split(",")[0]))


def warranty_row(profile: dict) -> dict[str, float]:
    key = profile["gps_key"]
    name = WARRANTY_DB.get(profile["key"]) or WARRANTY_DB.get(key) or key
    wf = pd.read_csv(DER / "distributor_warranty_expense_fiscal.csv")
    hit = wf[wf["db"] == name]
    if hit.empty:
        return {"fy2024": 0.0, "fy2025": 0.0, "fy2026": 0.0, "name": name}
    r = hit.iloc[0]
    return {
        "fy2024": float(r.get("warr_FY2024") or 0),
        "fy2025": float(r.get("warr_FY2025") or 0),
        "fy2026": float(r.get("warr_FY2026") or 0),
        "name": name,
    }


def load_hu_slice(sold_to: int) -> pd.DataFrame:
    sf = pd.read_parquet(DER / "sales_fact.parquet")
    m = (pd.to_numeric(sf["sold_to"], errors="coerce") == sold_to) | (
        pd.to_numeric(sf["sold_to_sap"], errors="coerce") == sold_to
    )
    hu = sf[m].copy()
    hu["billing_date"] = pd.to_datetime(hu["billing_date"], errors="coerce")
    hu = hu.dropna(subset=["billing_date"])
    hu["fy"] = np.where(
        hu["billing_date"].dt.month >= 4,
        hu["billing_date"].dt.year + 1,
        hu["billing_date"].dt.year,
    )
    hu["cy"] = hu["billing_date"].dt.year
    hu["part_number"] = hu["part_number"].map(C.norm_pn)
    return hu


def bucket_sales(hu: pd.DataFrame) -> pd.DataFrame:
    xref = pd.read_csv(DER / "genuine_bvp_crossref.csv", dtype=str)
    gen = set(xref["genuine_pn"].dropna().str.strip().map(C.norm_pn))
    bvp = set(xref["bvp_pn"].dropna().str.strip().map(C.norm_pn))
    pn = hu["part_number"]
    bucket = pd.Series("genuine_only", index=hu.index)
    bucket.loc[pn.isin(gen)] = "genuine_with_bvp_alt"
    bucket.loc[pn.isin(bvp)] = "bvp"
    out = hu.copy()
    out["bucket"] = bucket
    return out


def fy_wallet_mix(hu: pd.DataFrame) -> dict:
    hu = bucket_sales(hu)
    out = {}
    for fy in (2025, 2026):
        g = hu[hu["fy"] == fy]
        tot = g.groupby("bucket")["net_sales_value"].sum()
        total = float(tot.sum())
        out[fy] = {
            "total": total,
            "bvp": float(tot.get("bvp", 0)),
            "genuine_with_bvp_alt": float(tot.get("genuine_with_bvp_alt", 0)),
            "genuine_only": float(tot.get("genuine_only", 0)),
        }
        for k in ("bvp", "genuine_with_bvp_alt", "genuine_only"):
            out[fy][f"{k}_pct"] = out[fy][k] / total if total else 0.0
    return out


def fy_pms_billing(hu: pd.DataFrame) -> dict[str, dict[int, float]]:
    cat = C.load_catalog()
    j = hu.merge(cat[["part_number", "pms_category"]], on="part_number", how="left")
    out: dict[str, dict[int, float]] = {}
    for k in PMS_CATS:
        out[k] = {}
        for fy in (2025, 2026):
            sub = j[(j["fy"] == fy) & (j["pms_category"] == k)]
            out[k][fy] = float(sub["net_sales_value"].sum())
    return out


def brake_pad_mix(hu: pd.DataFrame) -> list[dict]:
    """Fiscal-year genuine vs BVP pad qty/€ share (FY-first)."""
    cat = C.load_catalog()
    xref = pd.read_csv(DER / "genuine_bvp_crossref.csv", dtype=str)
    bvp = set(xref["bvp_pn"].dropna().str.strip().map(C.norm_pn))
    j = hu.merge(cat[["part_number", "pms_category"]], on="part_number", how="left")
    pads = j[j["pms_category"] == "brake_pad"].copy()
    if pads.empty:
        return []
    pads["is_bvp"] = pads["part_number"].isin(bvp)
    qty_col = next((c for c in ("billed_qty", "billing_qty", "qty") if c in pads.columns), None)
    rows = []
    for y in (2025, 2026):
        g = pads[pads["fy"] == y]
        if g.empty:
            continue
        gen = g[~g["is_bvp"]]
        bv = g[g["is_bvp"]]
        gen_eur = float(gen["net_sales_value"].sum())
        bvp_eur = float(bv["net_sales_value"].sum())
        tot = gen_eur + bvp_eur
        rows.append({
            "year": y,
            "year_label": f"FY{y}",
            "gen_qty": float(gen[qty_col].sum()) if qty_col else 0.0,
            "bvp_qty": float(bv[qty_col].sum()) if qty_col else 0.0,
            "bvp_share_eur_pct": (bvp_eur / tot * 100) if tot else 0.0,
            "gen_eur": gen_eur,
            "bvp_eur": bvp_eur,
            "tot_eur": tot,
        })
    return rows


def top_pn_losers(hu: pd.DataFrame, n: int = 7) -> list[list[str]]:
    """Top FY24→FY25 PN drops outside PMS service categories."""
    cat = C.load_catalog()
    j = hu.merge(cat[["part_number", "pms_category", "pr00_group"]],
                 on="part_number", how="left")
    j = j[~j["pms_category"].isin(PMS_CATS)]
    a = j[j["fy"] == 2025].groupby("part_number")["net_sales_value"].sum()
    b = j[j["fy"] == 2026].groupby("part_number")["net_sales_value"].sum()
    # Prefer FY24→FY25 if both exist; else FY25→FY26
    a24 = j[j["fy"] == 2024].groupby("part_number")["net_sales_value"].sum()
    if a24.sum() > 0 and a.sum() > 0:
        prior, curr, label = a24, a, "FY24→FY25"
    else:
        prior, curr, label = a, b, "FY25→FY26"
    idx = prior.index.union(curr.index)
    delta = curr.reindex(idx, fill_value=0) - prior.reindex(idx, fill_value=0)
    worst = delta.nsmallest(n)
    # descriptions
    desc = {}
    if "description" in j.columns:
        desc = (
            j.dropna(subset=["part_number"])
            .groupby("part_number")["description"]
            .agg(lambda s: s.dropna().astype(str).iloc[0] if len(s.dropna()) else "")
            .to_dict()
        )
    rows = [["Part", "Description", "Δ EUR"]]
    for pn, d in worst.items():
        if d >= 0:
            continue
        rows.append([str(pn), str(desc.get(pn, ""))[:48], f"{d:,.0f}"])
    return rows, label


def fy_genuine_hole(hu: pd.DataFrame) -> dict:
    """FY2025→FY2026 genuine-only drop vs PMS-basket share (FY-first)."""
    hu = bucket_sales(hu)
    cat = C.load_catalog()
    j = hu.merge(cat[["part_number", "pms_category"]], on="part_number", how="left")
    out = {}
    for y in (2025, 2026):
        g = j[j["fy"] == y]
        out[y] = {
            "genuine_only": float(g.loc[g["bucket"] == "genuine_only", "net_sales_value"].sum()),
            "bvp": float(g.loc[g["bucket"] == "bvp", "net_sales_value"].sum()),
            "pms_genuine": float(
                g.loc[
                    (g["bucket"] == "genuine_only") & (g["pms_category"].isin(PMS_CATS)),
                    "net_sales_value",
                ].sum()
            ),
            "pms_bvp": float(
                g.loc[
                    (g["bucket"] == "bvp") & (g["pms_category"].isin(PMS_CATS)),
                    "net_sales_value",
                ].sum()
            ),
            "pms_total": float(
                g.loc[g["pms_category"].isin(PMS_CATS), "net_sales_value"].sum()
            ),
        }
    d_go = out[2026]["genuine_only"] - out[2025]["genuine_only"]
    d_pms_go = out[2026]["pms_genuine"] - out[2025]["pms_genuine"]
    d_pms_bvp = out[2026]["pms_bvp"] - out[2025]["pms_bvp"]
    share = (d_pms_go / d_go) if d_go else 0.0
    return {
        "d_genuine_only": d_go,
        "d_pms_genuine": d_pms_go,
        "d_pms_bvp": d_pms_bvp,
        "outside_share": 1.0 - share if d_go < 0 else None,
        "by_year": out,
        "label": "FY2025 → FY2026",
    }


def aim_rows(profile: dict) -> list[list[str]]:
    aim = pd.read_csv(DER / "aim_gps_matrix.csv")
    code = profile["pms_code"]
    sub = aim[(aim["distributor_code"] == code) & (aim["year"].isin([2023, 2024, 2025]))]
    rows = [["Year", "High-risk €", "High-risk %", "Quadrant"]]
    for _, r in sub.sort_values("year").iterrows():
        rows.append([
            str(int(r["year"])),
            eur(float(r["high_risk_rev_eur"])),
            f"{float(r['aim_high_risk_pct']) * 100:.1f}%",
            str(r.get("quadrant_label") or r.get("quadrant") or ""),
        ])
    return rows


def gps_fy_chart(path: Path, profile: dict, display: str) -> dict:
    """Fiscal GPS % + fiscal GPS % excl. warranty only (max 2 lines). FY-first."""
    code = profile["pms_code"]
    ww = pd.read_csv(DER / "wallet_waterfall.csv")
    ww = ww[(ww["distributor_code"] == code) & (ww["year"] <= 2025)]
    wallet_by_y = {
        int(r["year"]): float(r["theoretical_wallet_eur"]) for _, r in ww.iterrows()
    }

    gm = C.load_gps_master(profile)
    seg = C.load_segmented_gps(profile) or {}
    # ONE wallet for both lines, and it must be the wallet the headline GPS % is
    # already built on. Dividing the ex-warranty line by a different-year wallet
    # made the gap between the two lines read as a warranty effect when most of
    # it was a change of fleet base.
    w25 = float(seg.get("wallet_2025") or gm.get("max_spend") or 1)
    fy_frac = {2024: np.nan, 2025: np.nan, 2026: np.nan}
    if gm.get("gps_pct_FY2024") is not None:
        fy_frac[2024] = float(gm["gps_pct_FY2024"])
    for y in (2025, 2026):
        if seg.get(f"gps_FY{y}") is not None:
            fy_frac[y] = float(seg[f"gps_FY{y}"])
        elif gm.get(f"gps_pct_FY{y}") is not None:
            fy_frac[y] = float(gm[f"gps_pct_FY{y}"])
    fy_by_y = {y: (round(v * 100, 1) if not np.isnan(v) else np.nan)
               for y, v in fy_frac.items()}

    # Warranty is removed once, not twice. gps_master's net_FY* already has its
    # own (smaller) warranty figure taken out; the fiscal GPS warranty expense is
    # the fuller measure, so only the part not already removed comes off here.
    warr = warranty_row(profile)
    bills = {y: float(gm.get(f"bill_FY{y}") or 0) for y in (2024, 2025, 2026)}
    nets = {y: float(gm.get(f"net_FY{y}") or 0) for y in (2024, 2025, 2026)}
    fy_ex, warr_used = {}, {}
    for y, wk in ((2024, "fy2024"), (2025, "fy2025"), (2026, "fy2026")):
        if np.isnan(fy_frac[y]) or w25 <= 0:
            fy_ex[y] = np.nan
            warr_used[y] = 0.0
            continue
        num = fy_frac[y] * w25                              # reproduces the headline exactly
        already_out = max(bills[y] - num, 0.0)              # warranty/credits already netted off
        extra = max(float(warr[wk]) - already_out, 0.0)     # the incremental bite only
        warr_used[y] = max(float(warr[wk]), already_out)
        fy_ex[y] = round(max(num - extra, 0) / w25 * 100, 1)

    # X-axis = fiscal years with data (no empty CY slot)
    years = [y for y in (2024, 2025, 2026) if not np.isnan(fy_by_y.get(y, np.nan))]
    if not years:
        years = [2024, 2025, 2026]
    fy = [fy_by_y.get(y, np.nan) for y in years]
    fy_x = [fy_ex.get(y, np.nan) for y in years]

    fig, ax = ct._base_fig((10.2, 4.3))
    x = np.arange(len(years))
    # Max 2 lines: headline FY (red) + excl. warranty (charcoal)
    series = [
        ("Fiscal-year GPS %", fy, ct.RED, 2.8),
        ("Fiscal-year GPS % excl. warranty", fy_x, ct.CHARCOAL, 1.8),
    ]
    for name, vals, color, lw in series:
        arr = np.array(vals, dtype=float)
        mask = ~np.isnan(arr)
        if not mask.any():
            continue
        ax.plot(
            x[mask], arr[mask], color=color, linewidth=lw, zorder=3,
            marker="o", markersize=5 if color == ct.RED else 4,
            markerfacecolor=color, markeredgecolor=ct.WHITE, markeredgewidth=0.6,
        )
        i_last = int(np.where(mask)[0][-1])
        ax.annotate(
            f"{name}  {arr[i_last]:.1f}",
            (x[i_last], arr[i_last]),
            xytext=(8, 0), textcoords="offset points",
            va="center", ha="left", fontsize=9, color=color,
            fontweight="bold" if color == ct.RED else "normal",
        )
    ax.set_xticks(x)
    ax.set_xticklabels([f"FY{y}" for y in years], fontsize=11, color=ct.CHARCOAL)
    ax.margins(x=0.05)
    fig.subplots_adjust(right=0.72)
    ax.set_title(
        f"{display} GPS % — fiscal year (headline vs excl. warranty)",
        fontsize=12, color=ct.CHARCOAL, loc="left", fontweight="bold", pad=12,
    )
    ct._save(fig, str(path))

    return {
        "fy25": fy_by_y.get(2025),
        "fy26": fy_by_y.get(2026),
        "fy26_ex": fy_ex.get(2026),
        "fy25_ex": fy_ex.get(2025),
        "warr26": warr_used.get(2026) or warr["fy2026"],
        "net26": nets[2026],
        "wallet": w25,
        "show_pct": bool(seg.get("show_pct", True)),
        "uio_2025": seg.get("uio_2025"),
        "uio_2026": seg.get("uio_2026"),
    }


def append_deep_dive(prs: Presentation, profile: dict, page_start: int) -> int:
    key = profile["key"]
    display = profile.get("display") or profile.get("name") or key
    partner = profile.get("name") or display
    sold_to = resolve_sold_to(profile)
    if sold_to is None:
        raise SystemExit(f"Cannot resolve sold_to for {key} — set sold_to in db_profiles.yaml")

    hu = load_hu_slice(sold_to)
    fy = fy_wallet_mix(hu)
    fy_pms = fy_pms_billing(hu)
    hole = fy_genuine_hole(hu)
    pads = brake_pad_mix(hu)
    pn_rows, pn_label = top_pn_losers(hu)
    chart_dir = out_dir(key) / "charts_out"
    chart_dir.mkdir(exist_ok=True)
    page = page_start
    peers = C.pms_vs_network(profile)
    pms_year, _ = C.load_pms(profile)

    # divider
    s = db.build_content(
        prs,
        "Deep dive — detail behind the Mode A story",
        eyebrow=f"{display} · {partner}",
        page_no=page,
    )
    bullets = [
        f"Extra detail for meeting prep — pick which slides to share with {partner}.",
        "Mode A ends on the previous closing slide.",
        "Label in all charts: “Genuine with BVP alternative” "
        "(not “genuine contested”).",
    ]
    if key == "UMI":
        bullets.append("UMI only — never blend UTI into these figures or IDS views.")
    if key == "IBX":
        bullets.append(
            "IBX GPS % can look high because billing covers BE/NL/PL/LUX while the "
            "wallet denominator is Belgium-only — say so when quoting %."
        )
    db.bullet_list(s, bullets, Inches(0.32), Inches(1.45), Inches(12.0), Inches(4.5), size=15)
    page += 1

    # agenda
    s = db.build_content(prs, "Deep-dive agenda", eyebrow="Agenda", page_no=page)
    db.bullet_list(
        s,
        [
            "GPS — fiscal year (headline vs excl. warranty; max two lines)",
            "FY2025 → FY2026 wallet mix (Genuine / Genuine with BVP alternative / BVP)",
            "Where the money went — outside the service-parts basket (FY)",
            "Service parts: CY capture vs network + FY billing (capture % is CY-only by design)",
            "Brake pads — BVP share of total brake pad sales (FY)",
            "AIM exposure",
            "Warranty — two lenses",
            "How to use this in the meeting",
        ],
        Inches(0.32), Inches(1.35), Inches(12.0), Inches(5.2), size=15,
    )
    page += 1

    # GPS chart — FY only, max 2 lines. Skip the % chart when capture > 100%
    # (Ireland-class) so Mode A never plots a GPS percentage on that market.
    gps_seg = C.load_segmented_gps(profile) or {}
    skip_gps_pct = (not gps_seg.get("show_pct", True)) or bool(
        (profile.get("deck") or {}).get("skip_gps_pct")
    )
    if skip_gps_pct:
        s = db.build_content(
            prs, "GPS — amount view", eyebrow="GPS", page_no=page,
        )
        g26_net = gps_seg.get("net_FY2026")
        w25 = gps_seg.get("wallet_2025")
        uio25 = gps_seg.get("uio_2025")
        take = [
            "GPS compares actual parts purchases to the theoretical potential of the fleet.",
        ]
        if g26_net is not None:
            take.append(f"FY2026 purchases: {eur(g26_net)}.")
        if w25 is not None and uio25:
            take.append(
                f"CY2025 fleet potential: {eur(w25)} ({uio25:,.0f} vehicles)."
            )
        take.append(
            "Purchases sit above that theoretical potential — we discuss the amount "
            "and the per-vehicle rate, not a capture percentage."
        )
        for w in (profile.get("watch") or [])[:1]:
            if "GPS" in w or "gps" in w or "denominator" in w.lower():
                take.append(w)
                break
        db.bullet_list(s, take[:5], Inches(0.32), Inches(1.35), Inches(11.5),
                       Inches(4.0), size=14)
        page += 1
    else:
        ginfo = gps_fy_chart(chart_dir / "modeb_gps.png", profile, display)
        take = []
        if ginfo.get("fy25") is not None and ginfo.get("fy26") is not None:
            take.append(
                f"Red = fiscal-year GPS (frozen CY2025 wallet). "
                f"FY25 {ginfo['fy25']:.1f}% → FY26 {ginfo['fy26']:.1f}%."
            )
        elif ginfo.get("fy26") is not None:
            take.append(
                f"Red = fiscal-year GPS (frozen CY2025 wallet). FY26 headline "
                f"{ginfo['fy26']:.1f}%."
            )
        if ginfo.get("fy26_ex") is not None and ginfo.get("warr26"):
            share = ginfo["warr26"] / ginfo["net26"] * 100 if ginfo["net26"] else 0
            take.append(
                f"Black = the same GPS after removing warranty parts (€). FY26 ≈ "
                f"{ginfo['fy26_ex']:.1f}% "
                f"(warranty {eur(ginfo['warr26'])} ≈ {share:.0f}% of FY26 billing)."
            )
            take.append(
                f"Both lines divide by the same wallet ({eur(ginfo['wallet'])}), so the gap "
                "between them is warranty and nothing else."
            )
        if ginfo.get("uio_2025") and ginfo.get("uio_2026"):
            take.append(
                f"Fleet {ginfo['uio_2025']:,.0f} → {ginfo['uio_2026']:,.0f} "
                "(working year-end estimate under the FY2027 target)."
            )
        for w in (profile.get("watch") or [])[:1]:
            if "GPS" in w or "gps" in w or "denominator" in w.lower():
                take.append(w)
                break
        db.build_two_col(
            prs,
            title="GPS: fiscal year headline vs after warranty",
            chart_path=str(chart_dir / "modeb_gps.png"),
            eyebrow="GPS",
            page_no=page,
            takeaways=take or ["See chart."],
        )
        page += 1

    # FY wallet
    f25, f26 = fy[2025], fy[2026]
    if f25["total"] > 0:
        ct.bar_chart(
            ["Total", "Genuine only", "Genuine with\nBVP alternative", "BVP"],
            {
                "FY2025 €K": [
                    f25["total"] / 1000, f25["genuine_only"] / 1000,
                    f25["genuine_with_bvp_alt"] / 1000, f25["bvp"] / 1000,
                ],
                "FY2026 €K": [
                    f26["total"] / 1000, f26["genuine_only"] / 1000,
                    f26["genuine_with_bvp_alt"] / 1000, f26["bvp"] / 1000,
                ],
            },
            str(chart_dir / "modeb_fy_wallet.png"),
            title="FY2025 → FY2026 wallet mix (EUR K)",
            ylabel="EUR K", value_fmt="{:,.0f}", figsize=(10.2, 4.3),
        )
        s = db.build_content(
            prs, "FY2025 → FY2026 wallet mix", eyebrow="Wallet mix", page_no=page,
        )
        db.add_picture_fit(
            s, str(chart_dir / "modeb_fy_wallet.png"),
            Inches(0.32), Inches(1.25), Inches(7.6), Inches(3.6),
        )
        d_tot = f26["total"] - f25["total"]
        d_go = f26["genuine_only"] - f25["genuine_only"]
        db.bullet_list(
            s,
            [
                f"Total {eur(f25['total'])} → {eur(f26['total'])} "
                f"({d_tot / f25['total']:+.1%}).",
                f"Genuine only {eur(d_go)}.",
                f"Genuine with BVP alternative {eur(f26['genuine_with_bvp_alt'] - f25['genuine_with_bvp_alt'])}; "
                f"BVP {eur(f26['bvp'] - f25['bvp'])} "
                f"({f26['bvp_pct'] * 100:.1f}% of FY26 wallet).",
                "Display label locked: Genuine with BVP alternative.",
            ],
            Inches(8.1), Inches(1.35), Inches(4.7), Inches(4.5), size=13,
        )
        page += 1

        rows = [
            ["", "FY2025", "FY2026", "Δ"],
            ["Total", eur(f25["total"]), eur(f26["total"]), eur(d_tot)],
            ["Genuine only", eur(f25["genuine_only"]), eur(f26["genuine_only"]),
             eur(d_go)],
            ["Genuine with BVP alternative",
             eur(f25["genuine_with_bvp_alt"]), eur(f26["genuine_with_bvp_alt"]),
             eur(f26["genuine_with_bvp_alt"] - f25["genuine_with_bvp_alt"])],
            ["BVP", eur(f25["bvp"]), eur(f26["bvp"]),
             eur(f26["bvp"] - f25["bvp"])],
            ["BVP % of wallet", f"{f25['bvp_pct']*100:.1f}%",
             f"{f26['bvp_pct']*100:.1f}%",
             f"{(f26['bvp_pct']-f25['bvp_pct'])*100:+.1f} pp"],
        ]
        s = db.build_content(prs, "FY wallet mix — detail", eyebrow="Wallet mix", page_no=page)
        styled_table(
            s, rows, Inches(0.32), Inches(1.35), Inches(12.5), Inches(3.2),
            [Inches(4.0), Inches(2.7), Inches(2.7), Inches(3.1)],
            bold_last=False, size=13, left_cols=(0,),
        )
        page += 1

    # Drivers — plain English, FY-first
    s = db.build_content(
        prs,
        "Where the genuine drop sits (FY2025 → FY2026)",
        eyebrow="Drivers",
        page_no=page,
    )
    d_go = hole["d_genuine_only"]
    d_pms = hole["d_pms_genuine"]
    d_bvp = hole["d_pms_bvp"]
    outside = hole.get("outside_share")
    driver_bullets = [
        f"Genuine-only sales moved {eur(d_go)} from FY2025 to FY2026.",
        f"Of that, the routine service basket (filters, pads, rotors) moved "
        f"{eur(d_pms)} on genuine-only; BVP in that basket moved {eur(d_bvp)}.",
    ]
    if outside is not None and d_go < 0:
        driver_bullets.append(
            f"So about {outside * 100:.0f}% of the genuine-only drop sits "
            f"outside routine service parts."
        )
    elif d_go >= 0:
        driver_bullets.append(
            "Genuine-only did not fall on this FY cut — check category movers and H1 for pressure points."
        )
    driver_bullets.append(
        "Meeting line: check high-value assemblies / sensors before blaming "
        "the filter or pad menu."
    )
    db.bullet_list(s, driver_bullets, Inches(0.32), Inches(1.35), Inches(12.5), Inches(5.0), size=15)
    page += 1

    if len(pn_rows) > 1:
        s = db.build_content(
            prs,
            f"Largest part-number drops ({pn_label}) — outside service filters",
            eyebrow="Drivers",
            page_no=page,
        )
        styled_table(
            s, pn_rows, Inches(0.32), Inches(1.35), Inches(12.5), Inches(3.8),
            [Inches(3.2), Inches(6.0), Inches(3.3)],
            bold_last=False, size=12.5, left_cols=(0, 1),
        )
        db.bullet_list(
            s,
            ["Check warranty / campaign coding before calling competitive leakage."],
            Inches(0.32), Inches(5.4), Inches(12.5), Inches(1.0), size=13,
        )
        page += 1

    # PMS CY capture — categories whose rate breaches the model ceiling are
    # withheld here exactly as they are on the Mode A coverage slide.
    pms_ok, pms_withheld = C.quotable_pms(peers) if peers else ([], [])
    if peers and len(pms_ok) >= 3:
        keys = [k for k in PMS_CATS if k in pms_ok]
        ct.bar_chart(
            [PMS_LABELS[k] for k in keys],
            {
                display: [peers[k]["db"] for k in keys],
                "Network": [peers[k]["network"] for k in keys],
            },
            str(chart_dir / "modeb_pms.png"),
            title=f"Service-parts capture — CY{pms_year} full year vs network (%)",
            ylabel="% of fleet service demand captured",
            value_fmt="{:,.1f}", figsize=(10.2, 4.3),
        )
        gaps = []
        for k in keys:
            gaps.append(
                f"{PMS_LABELS[k]} {peers[k]['db']:.1f}% vs network {peers[k]['network']:.1f}%"
            )
        take = [
            f"Capture % is calendar-year (full CY{pms_year}). Fleet demand is modelled "
            "on calendar years — there is no matching fiscal-year capture %.",
            "; ".join(gaps[:3]) + ".",
            f"Next slide: fiscal-year € billing in the same {len(keys)} categories.",
        ]
        if pms_withheld:
            take.append(
                f"{', '.join(PMS_LABELS[k] for k in pms_withheld)} withheld — the modelled "
                "demand base does not hold for this market, so the rate is not quotable."
            )
        else:
            take.append("Primary lens = total capture (not genuine-only).")
        db.build_two_col(
            prs,
            title="Service-parts capture vs network (calendar year)",
            chart_path=str(chart_dir / "modeb_pms.png"),
            eyebrow="Service parts",
            page_no=page,
            takeaways=take,
        )
        page += 1

        ct.bar_chart(
            [PMS_LABELS[k] for k in keys],
            {
                "FY2025 €K": [fy_pms[k][2025] / 1000 for k in keys],
                "FY2026 €K": [fy_pms[k][2026] / 1000 for k in keys],
            },
            str(chart_dir / "modeb_pms_fy.png"),
            title=f"Same {len(keys)} categories — fiscal-year billing (EUR K)",
            ylabel="EUR K", value_fmt="{:,.1f}", figsize=(10.2, 4.3),
        )
        db.build_two_col(
            prs,
            title=f"Service-parts billing by fiscal year (same {len(keys)} lines)",
            chart_path=str(chart_dir / "modeb_pms_fy.png"),
            eyebrow="Service parts · FY",
            page_no=page,
            takeaways=[
                f"This is Sales-to-{partner} € in fiscal years — not capture % of fleet demand.",
                "Use both lenses — do not mix % capture with € billing.",
                "Primary = total sales in the basket.",
            ],
        )
        page += 1

    # Brake pads (FY)
    if pads:
        by_y = {r["year"]: r for r in pads}
        y0, y1 = 2025, 2026
        if y0 in by_y and y1 in by_y:
            s = db.build_content(
                prs,
                "Brake pads — BVP share of total brake pad sales (FY)",
                eyebrow="Brakes",
                page_no=page,
            )
            pad_rows = [
                ["", "FY2025", "FY2026"],
                ["Genuine pad sales (€)", eur(by_y[y0]["gen_eur"]), eur(by_y[y1]["gen_eur"])],
                ["BVP pad sales (€)", eur(by_y[y0]["bvp_eur"]), eur(by_y[y1]["bvp_eur"])],
                ["Genuine qty", f"{by_y[y0]['gen_qty']:.0f}", f"{by_y[y1]['gen_qty']:.0f}"],
                ["BVP qty", f"{by_y[y0]['bvp_qty']:.0f}", f"{by_y[y1]['bvp_qty']:.0f}"],
                [
                    "BVP share of pad sales (€)",
                    f"{by_y[y0]['bvp_share_eur_pct']:.0f}%",
                    f"{by_y[y1]['bvp_share_eur_pct']:.0f}%",
                ],
            ]
            styled_table(
                s, pad_rows, Inches(0.32), Inches(1.4), Inches(7.2), Inches(2.8),
                [Inches(3.6), Inches(1.8), Inches(1.8)],
                bold_last=False, size=12, left_cols=(0,),
            )
            pad_notes = [
                "BVP share = BVP € ÷ all brake-pad € billed (genuine + BVP). "
                "Not a PMS capture %.",
            ]
            if by_y[y1]["bvp_eur"] < 1 and by_y[y1]["gen_eur"] > 0:
                pad_notes.append(
                    f"{partner} pad sales are genuine-only in this cut "
                    f"(~{eur(by_y[y1]['gen_eur'], True)} FY26) — no BVP pad lines billed."
                )
            pad_notes.append(
                f"Wallet-level BVP is still only ~{f26['bvp_pct']*100:.1f}% of FY26 — "
                "do not generalise a pad story to the whole wallet."
            )
            db.bullet_list(
                s, pad_notes,
                Inches(7.7), Inches(1.3), Inches(5.1), Inches(4.5), size=13,
            )
            page += 1

    # AIM
    ar = aim_rows(profile)
    if len(ar) > 1:
        s = db.build_content(prs, "AIM exposure", eyebrow="AIM", page_no=page)
        styled_table(
            s, ar, Inches(0.32), Inches(1.35), Inches(12.5), Inches(2.4),
            [Inches(2.0), Inches(3.0), Inches(3.0), Inches(4.5)],
            bold_last=False, size=13, left_cols=(0, 3),
        )
        db.bullet_list(
            s,
            [
                "High-risk € is catalogue AIM exposure, not proven walk-out.",
                "Open on jobs not bought through the distributor — not a street IAM war alone.",
            ],
            Inches(0.32), Inches(4.1), Inches(12.5), Inches(2.0), size=14,
        )
        page += 1

    # Warranty
    warr = warranty_row(profile)
    claim = profile.get("warranty_cy2025_claim")
    s = db.build_content(prs, "Warranty — two real lenses", eyebrow="Warranty", page_no=page)
    card(
        s, Inches(0.32), Inches(1.35), Inches(6.0), Inches(3.2),
        "1", "CY2025 claim-price parts",
        [
            f"{eur(claim)} (claim-price basis)." if claim else "No claim-price figure in profile.",
            "Calendar-year claim price basis.",
            str(profile.get("warranty_note") or ""),
        ],
    )
    card(
        s, Inches(6.7), Inches(1.35), Inches(6.0), Inches(3.2),
        "2", "Fiscal GPS expense",
        [
            f"FY24 {eur(warr['fy2024'])} · FY25 {eur(warr['fy2025'])} · "
            f"FY26 {eur(warr['fy2026'])}.",
            f"Source row: {warr['name']}.",
            "Ex-warranty GPS = (net − warranty) ÷ frozen CY25 wallet.",
        ],
    )
    db.bullet_list(
        s,
        ["Both numbers are real — never mix them on one slide without labels."],
        Inches(0.32), Inches(4.9), Inches(12.5), Inches(1.2), size=13,
    )
    page += 1

    # Bridge
    s = db.build_content(prs, "How to use this in the meeting", eyebrow="Bridge", page_no=page)
    bridge = [
        ["If they say…", "You know…"],
        [
            "BVP is eating genuine",
            f"Wallet BVP ~{f26['bvp_pct']*100:.1f}%. Check pads as a local exception only.",
        ],
        [
            "GPS looks fine / too high",
            f"FY26 headline {ginfo.get('fy26')}%; excl. warranty ≈ {ginfo.get('fy26_ex')}%. "
            + ("IBX: Belgium-only denominator." if key == "IBX" else ""),
        ],
        [
            "Service parts are fine",
            f"CY{pms_year} capture vs network (previous slides) + FY billing lens.",
        ],
    ]
    if key == "UMI":
        bridge.append(["This is Israel network", "UMI only — UTI did not sit in IDS Israel."])
    styled_table(
        s, bridge, Inches(0.32), Inches(1.3), Inches(12.5), Inches(4.2),
        [Inches(4.2), Inches(8.3)], bold_last=False, size=12, left_cols=(0, 1),
    )
    page += 1

    db.build_closing(prs)
    return page


def build_full(db_key: str) -> Path:
    profile = C.load_profile(db_key)
    key = profile["key"]
    odir = out_dir(key)
    odir.mkdir(parents=True, exist_ok=True)

    print(f"[{key}] rebuilding Mode A …")
    from datetime import datetime, timezone
    canonical = odir / f"ISZE_{key}_Sales_Review_FY2027.pptx"
    share = odir / f"ISZE_{key}_Sales_Review_FY2027_share.pptx"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rebuild = odir / f"ISZE_{key}_Sales_Review_FY2027_rebuild_{stamp}.pptx"

    def _writable(path: Path) -> bool:
        try:
            if path.exists():
                with open(path, "a"):
                    pass
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
            return True
        except PermissionError:
            return False

    target = next((p for p in (canonical, share, rebuild) if _writable(p)), rebuild)
    if target != canonical:
        print(f"  (canonical PPTX locked — writing → {target.name})")

    os.environ["ISZE_DECK_OUT"] = str(target)
    mode_a_path = Path(build_mode_a(key))
    mode_a_only = odir / f"ISZE_{key}_Sales_Review_FY2027_ModeA_only.pptx"
    try:
        shutil.copy2(mode_a_path, mode_a_only)
        print(f"  Mode A backup → {mode_a_only}")
    except PermissionError:
        print(f"  Mode A backup skipped (locked): {mode_a_only.name}")

    print(f"[{key}] appending deep dive …")
    prs = Presentation(str(mode_a_path))
    n_a = len(prs.slides)
    append_deep_dive(prs, profile, page_start=n_a + 1)
    full = None
    for cand in (target, share, rebuild):
        try:
            prs.save(str(cand))
            full = cand
            if cand != target:
                print(f"  (save locked — wrote → {cand.name})")
            break
        except PermissionError:
            continue
    if full is None:
        raise SystemExit(f"[{key}] cannot save full deck — PPTX files locked")

    # Write a short manifest for GitHub / other agents
    manifest = {
        "db": key,
        "display": profile.get("display"),
        "partner": profile.get("name"),
        "mode_a_slides": n_a,
        "total_slides": len(prs.slides),
        "pptx": str(full),
        "mode_a_only": str(mode_a_only),
        "blueprint": str(TOOLS / "DB_SALES_REVIEW_BLUEPRINT.md"),
        "built_by": "build_full_deck.py",
    }
    (odir / "_full_deck_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"[{key}] FULL deck → {full}  ({len(prs.slides)} slides)")
    print(f"  Mode A: {n_a}  ·  Deep dive from slide {n_a + 1}")
    return full


def main():
    ap = argparse.ArgumentParser(description="Build Mode A + deep-dive sales review deck")
    ap.add_argument("--db", required=True, help="Profile key, e.g. IBX, UMI, HUNGARY")
    args = ap.parse_args()
    build_full(args.db.upper())


if __name__ == "__main__":
    main()
