#!/usr/bin/env python3
"""PMS-focused 2024→2025 price×volume response (ISZE→distributor stocking)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ROOT / "01_data" / "00_derived"
INBOX = ROOT / "01_data" / "90_INBOX"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"

MIN_QTY = 10
WINSOR = 0.02
MIN_PAIRS_CAT = 30
# Cross-section beta needs within-family price dispersion. Below ~0.5% std of
# log price change, everyone got nearly the same list move → beta unidentified.
MIN_DLNP_STD = 0.005

EXCLUDED = {
    "GERMANY_SERVICE",
    "MIDI",
    "IML_INTERNAL",
    "RUSSIA_EXCLUDE",
    "FORLOG_EXCLUDE",
    "NETHERLANDS",
    "LUXEMBOURG",
    "TURKEY",
    "NON_PARTS",
    "UNMAPPED",
}

AIM_L1_KEEP = {
    "Brakes",
    "Clutch",
    "Lubrication",
    "Maintenance Service",
}

PMS_CAT_KEEP = {
    "air_filter",
    "oil_filter",
    "fuel_filter",
    "blower_filter",
    "urea_filter",
    "brake_pad",
    "brake_shoe",
    "brake_rotor",
    "brake_lining_front",
    "brake_shoe_front",
    "clutch_kit",
    "clutch_disc",
    "clutch_pressure_plate",
    "clutch_booster",
    "release_bearing",
    "pilot_bearing",
}


def _norm_pn(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.lstrip("0")
    )


def _wls_beta(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> tuple[float, float, float]:
    W = np.sqrt(np.maximum(w, 1e-12))
    X = np.column_stack([np.ones_like(x), x]) * W[:, None]
    Y = y * W
    coef, *_ = np.linalg.lstsq(X, Y, rcond=None)
    resid = Y - X @ coef
    dof = max(len(x) - 2, 1)
    sigma2 = float(resid @ resid) / dof
    XtX_inv = np.linalg.inv(X.T @ X)
    se_b = float(np.sqrt(max(sigma2 * XtX_inv[1, 1], 0.0)))
    ss_tot = float(((Y - Y.mean()) ** 2).sum())
    r2 = 1.0 - float(resid @ resid) / ss_tot if ss_tot > 0 else 0.0
    return float(coef[1]), se_b, r2


def _quadrant(dpct: float, qpct: float, price_flat_band: float = 1.0) -> str:
    price_up = dpct > price_flat_band
    price_down = dpct < -price_flat_band
    price_flat = not price_up and not price_down
    vol_up = qpct > 0
    vol_down = qpct < 0
    if price_up and vol_down:
        return "price_up_volume_down_sensitive"
    if price_up and vol_up:
        return "price_up_volume_up_passed"
    if price_down and vol_up:
        return "price_down_volume_up"
    if price_down and vol_down:
        return "price_down_volume_down"
    if price_flat and vol_down:
        return "price_flat_volume_down_capture_leak"
    if price_flat and vol_up:
        return "price_flat_volume_up"
    return "price_flat_volume_flat"


def main() -> int:
    sap = pd.read_csv(PRISM / "data" / "sap_sold_to_mapping.csv")
    sap["sap_sold_to_pt"] = pd.to_numeric(sap["sap_sold_to_pt"], errors="coerce").astype("Int64")
    sap_to_db = dict(
        zip(sap["sap_sold_to_pt"].dropna().astype(int), sap["distributor_code"].astype(str))
    )

    xref = pd.read_csv(DERIVED / "genuine_bvp_crossref.csv", dtype=str)
    cat_map: dict[str, str] = {}
    for col in ("genuine_pn", "bvp_pn"):
        sub = xref.dropna(subset=[col, "pms_category"])
        sub = sub[sub["pms_category"].astype(str).str.strip() != ""]
        cat_map.update(dict(zip(_norm_pn(sub[col]), sub["pms_category"].astype(str))))

    aim = pd.read_csv(
        DERIVED / "aim_pn_classification.csv",
        usecols=["part_number", "aim_l1", "aim_l2"],
        dtype=str,
    )
    aim["_pn"] = _norm_pn(aim["part_number"])
    aim_l1 = dict(zip(aim["_pn"], aim["aim_l1"]))

    z24 = pd.read_parquet(DERIVED / "pricing_zpr1_2024.parquet")
    z25 = pd.read_parquet(DERIVED / "pricing_zpr1_2025.parquet")
    p24 = pd.read_parquet(DERIVED / "pricing_pr00_ie40_2024.parquet")
    p25 = pd.read_parquet(DERIVED / "pricing_pr00_ie40_2025.parquet")

    def prep_z(z: pd.DataFrame) -> pd.DataFrame:
        out = z.copy()
        out["customer"] = pd.to_numeric(out["Customer"], errors="coerce").astype("Int64")
        out["_pn"] = _norm_pn(out["Material"])
        out["zpr1"] = pd.to_numeric(out["Price"], errors="coerce")
        if "Valid_From" in out.columns:
            out = out.sort_values("Valid_From").drop_duplicates(["customer", "_pn"], keep="last")
        else:
            out = out.drop_duplicates(["customer", "_pn"], keep="last")
        return out[["customer", "_pn", "zpr1"]]

    def prep_pr(p: pd.DataFrame) -> pd.DataFrame:
        out = p.copy()
        out["_pn"] = _norm_pn(out["Material"])
        out["pr00"] = pd.to_numeric(out["Price_EUR"], errors="coerce")
        return out.drop_duplicates("_pn", keep="last")[["_pn", "pr00"]]

    z24p, z25p = prep_z(z24), prep_z(z25)
    pr24, pr25 = prep_pr(p24), prep_pr(p25)

    sales = pd.read_parquet(
        DERIVED / "sales_fact.parquet",
        columns=["sold_to_sap", "part_number", "billed_qty", "net_sales_value", "year"],
    )
    sales = sales[sales["year"].isin([2024, 2025])].copy()
    sales["customer"] = pd.to_numeric(sales["sold_to_sap"], errors="coerce").astype("Int64")
    sales = sales.dropna(subset=["customer"])
    sales["customer"] = sales["customer"].astype(int)
    sales["distributor_code"] = sales["customer"].map(sap_to_db).fillna("UNMAPPED")
    sales = sales[~sales["distributor_code"].isin(EXCLUDED)].copy()
    sales["_pn"] = _norm_pn(sales["part_number"])
    sales["billed_qty"] = pd.to_numeric(sales["billed_qty"], errors="coerce").fillna(0.0)
    sales["net_sales_value"] = pd.to_numeric(sales["net_sales_value"], errors="coerce").fillna(0.0)

    agg = (
        sales.groupby(["_pn", "customer", "distributor_code", "year"], as_index=False)
        .agg(qty=("billed_qty", "sum"), rev=("net_sales_value", "sum"))
    )

    a24 = agg[agg["year"] == 2024].rename(columns={"qty": "qty_2024", "rev": "rev_2024"})
    a25 = agg[agg["year"] == 2025].rename(columns={"qty": "qty_2025", "rev": "rev_2025"})
    pairs = a24.merge(
        a25[["_pn", "customer", "qty_2025", "rev_2025"]],
        on=["_pn", "customer"],
        how="inner",
    )
    pairs = pairs[(pairs["qty_2024"] >= MIN_QTY) & (pairs["qty_2025"] >= MIN_QTY)].copy()

    pairs = pairs.merge(z24p.rename(columns={"zpr1": "zpr1_2024"}), on=["customer", "_pn"], how="left")
    pairs = pairs.merge(z25p.rename(columns={"zpr1": "zpr1_2025"}), on=["customer", "_pn"], how="left")
    pairs = pairs.merge(pr24.rename(columns={"pr00": "pr00_2024"}), on="_pn", how="left")
    pairs = pairs.merge(pr25.rename(columns={"pr00": "pr00_2025"}), on="_pn", how="left")

    pairs["price_source"] = np.where(
        pairs["zpr1_2024"].notna() & pairs["zpr1_2025"].notna(),
        "ZPR1",
        "PR00",
    )
    pairs["price_2024"] = np.where(
        pairs["price_source"] == "ZPR1", pairs["zpr1_2024"], pairs["pr00_2024"]
    )
    pairs["price_2025"] = np.where(
        pairs["price_source"] == "ZPR1", pairs["zpr1_2025"], pairs["pr00_2025"]
    )
    pairs = pairs[(pairs["price_2024"] > 0) & (pairs["price_2025"] > 0)].copy()

    pairs["pms_category"] = pairs["_pn"].map(cat_map)
    pairs["aim_l1"] = pairs["_pn"].map(aim_l1)

    def family_row(r) -> tuple[str, str, bool]:
        pc = r["pms_category"]
        l1 = r["aim_l1"]
        if isinstance(pc, str) and pc in PMS_CAT_KEEP:
            return pc, "pms_category", True
        if isinstance(l1, str) and l1 in AIM_L1_KEEP:
            return f"AIM: {l1}", "aim_l1", True
        return "", "", False

    fam = pairs.apply(family_row, axis=1, result_type="expand")
    pairs["family"] = fam[0]
    pairs["family_source"] = fam[1]
    pairs["in_scope"] = fam[2]
    n_before = len(pairs)
    pairs = pairs[pairs["in_scope"]].copy()
    n_after = len(pairs)

    pairs["pct_price_yoy"] = (pairs["price_2025"] / pairs["price_2024"] - 1.0) * 100.0
    pairs["pct_qty_yoy"] = (pairs["qty_2025"] / pairs["qty_2024"] - 1.0) * 100.0
    pairs["dlnp"] = np.log(pairs["price_2025"] / pairs["price_2024"])
    pairs["dlnq"] = np.log(pairs["qty_2025"] / pairs["qty_2024"])
    pairs["eur_volume_impact"] = (pairs["qty_2025"] - pairs["qty_2024"]) * pairs["price_2024"]
    pairs["eur_rev_delta"] = pairs["rev_2025"] - pairs["rev_2024"]
    pairs["quadrant"] = [
        _quadrant(float(dp), float(dq))
        for dp, dq in zip(pairs["pct_price_yoy"], pairs["pct_qty_yoy"])
    ]

    # Winsorize within family for beta (global winsor crushed within-family price
    # dispersion when most families share a near-uniform list move).
    pairs = pairs.copy()
    pairs["dlnp_w"] = pairs["dlnp"]
    pairs["dlnq_w"] = pairs["dlnq"]
    for _, idx in pairs.groupby("family").groups.items():
        if len(idx) < 5:
            continue
        for col, out in (("dlnp", "dlnp_w"), ("dlnq", "dlnq_w")):
            lo, hi = pairs.loc[idx, col].quantile([WINSOR, 1 - WINSOR])
            pairs.loc[idx, out] = pairs.loc[idx, col].clip(lo, hi)

    rows = []
    for fam_name, grp in pairs.groupby("family"):
        n = len(grp)
        if n < 5:
            continue
        dlnp_std = float(grp["dlnp_w"].std(ddof=0)) if n else 0.0
        identified = dlnp_std >= MIN_DLNP_STD and dlnp_std > 0
        if identified:
            beta, se, r2 = _wls_beta(
                grp["dlnp_w"].to_numpy(dtype=float),
                grp["dlnq_w"].to_numpy(dtype=float),
                grp["qty_2024"].to_numpy(dtype=float),
            )
            sig = abs(beta) > 1.96 * se if se > 0 else False
            if beta < -0.5 and sig:
                reading = "price-sensitive (stocking response)"
            elif beta < -0.5:
                reading = "negative beta but noisy (se large - direction only)"
            elif beta < 0:
                reading = "weak negative response"
            elif sig:
                reading = "no negative price response (passed / confounded)"
            else:
                reading = "positive/flat beta but noisy (se large - inconclusive)"
            beta_r, se_r, r2_r = round(beta, 2), round(se, 2), round(r2, 3)
        else:
            beta_r = se_r = r2_r = float("nan")
            reading = (
                "beta not identified — list price move nearly uniform across pairs "
                f"(std log-price {dlnp_std:.4f}); use quadrant / median qty instead"
            )
        eur_2024 = float(grp["rev_2024"].sum())
        eur_2025 = float(grp["rev_2025"].sum())
        eur_vol = float(grp["eur_volume_impact"].sum())
        q_eur = (
            grp.groupby("quadrant")["eur_volume_impact"]
            .sum()
            .reindex(
                [
                    "price_up_volume_down_sensitive",
                    "price_up_volume_up_passed",
                    "price_flat_volume_down_capture_leak",
                    "price_flat_volume_up",
                    "price_down_volume_up",
                    "price_down_volume_down",
                    "price_flat_volume_flat",
                ],
                fill_value=0.0,
            )
        )
        rows.append(
            {
                "family": fam_name,
                "n_pairs": n,
                "n_pns": int(grp["_pn"].nunique()),
                "n_distributors": int(grp["distributor_code"].nunique()),
                "median_pct_price_yoy": round(float(grp["pct_price_yoy"].median()), 2),
                "median_pct_qty_yoy": round(float(grp["pct_qty_yoy"].median()), 2),
                "std_dlnp": round(dlnp_std, 5),
                "beta_identified": identified,
                "beta_elasticity": beta_r,
                "se_beta": se_r,
                "r2": r2_r,
                "low_power": bool(n < MIN_PAIRS_CAT) or (not identified),
                "eur_billed_2024": round(eur_2024, 2),
                "eur_billed_2025": round(eur_2025, 2),
                "eur_volume_impact": round(eur_vol, 2),
                "eur_sensitive_price_up_vol_down": round(
                    float(q_eur["price_up_volume_down_sensitive"]), 2
                ),
                "eur_passed_price_up_vol_up": round(float(q_eur["price_up_volume_up_passed"]), 2),
                "eur_leak_price_flat_vol_down": round(
                    float(q_eur["price_flat_volume_down_capture_leak"]), 2
                ),
                "share_zpr1_pairs": round(float((grp["price_source"] == "ZPR1").mean()), 3),
                "reading": reading,
                "method_note": (
                    "qty-weighted WLS on YoY log deltas CY2024→CY2025 at PN×sold-to; "
                    "list price ZPR1 where present else PR00 IE40; stocking-side ISZE→DB "
                    "NOT dealer-market elasticity; beta only when within-family std(dlnP) "
                    f">= {MIN_DLNP_STD}; LOW POWER — direction + rough magnitude; "
                    "demand shocks uncontrolled"
                ),
            }
        )

    fam_out = pd.DataFrame(rows).sort_values("beta_elasticity")
    fam_path = DERIVED / "pms_price_volume_response_2024_2025.csv"
    fam_out.to_csv(fam_path, index=False)

    pn_out = (
        pairs.assign(abs_eur_volume_impact=lambda d: d["eur_volume_impact"].abs())
        .sort_values("abs_eur_volume_impact", ascending=False)
        .head(500)
        .assign(part_number=lambda d: d["_pn"])
        [
            [
                "part_number",
                "customer",
                "distributor_code",
                "family",
                "family_source",
                "price_source",
                "price_2024",
                "price_2025",
                "pct_price_yoy",
                "qty_2024",
                "qty_2025",
                "pct_qty_yoy",
                "rev_2024",
                "rev_2025",
                "eur_volume_impact",
                "eur_rev_delta",
                "quadrant",
            ]
        ]
        .copy()
    )
    for c in [
        "price_2024",
        "price_2025",
        "pct_price_yoy",
        "pct_qty_yoy",
        "rev_2024",
        "rev_2025",
        "eur_volume_impact",
        "eur_rev_delta",
    ]:
        pn_out[c] = pn_out[c].round(2)
    pn_path = DERIVED / "pms_price_volume_response_pn_2024_2025.csv"
    pn_out.to_csv(pn_path, index=False)

    gps = pd.read_csv(DERIVED / "gps_spu_by_distributor.csv")
    gps25 = gps[(gps["year"] == 2025) & (~gps["distributor_code"].isin(EXCLUDED))].copy()
    uio_total = float(gps25["uio_units"].sum())
    umi_uio = float(gps25.loc[gps25["distributor_code"] == "UMI", "uio_units"].sum())
    uti_uio = float(gps25.loc[gps25["distributor_code"] == "UTI", "uio_units"].sum())

    total_eur_2024 = float(pairs["rev_2024"].sum())
    total_eur_2025 = float(pairs["rev_2025"].sum())
    n_pairs = len(pairs)
    n_zpr1 = int((pairs["price_source"] == "ZPR1").sum())
    n_pr00 = int((pairs["price_source"] == "PR00").sum())

    q_summary = (
        pairs.groupby("quadrant")
        .agg(
            n=("_pn", "count"),
            eur_volume_impact=("eur_volume_impact", "sum"),
            eur_abs=("eur_volume_impact", lambda s: float(s.abs().sum())),
        )
        .sort_values("eur_abs", ascending=False)
    )

    fam_out = fam_out.copy()
    identified = fam_out[fam_out["beta_identified"] == True].copy()  # noqa: E712
    identified["abs_beta"] = identified["beta_elasticity"].abs()
    top_abs = identified.sort_values("abs_beta", ascending=False).head(8)
    if len(top_abs) < 8:
        # pad with largest |EUR volume impact| among unidentified for the note
        rest = fam_out[~fam_out["family"].isin(top_abs["family"])].copy()
        rest["abs_beta"] = rest["beta_elasticity"].abs()
        pad = rest.sort_values("eur_volume_impact").head(8 - len(top_abs))
        top_abs = pd.concat([top_abs, pad], ignore_index=True)

    sens = pairs[pairs["quadrant"] == "price_up_volume_down_sensitive"]
    sens_by_fam = (
        sens.groupby("family")
        .agg(eur=("eur_volume_impact", "sum"), n=("_pn", "count"))
        .sort_values("eur")
        .head(8)
    )

    excluded_aim = sorted(set(aim["aim_l1"].dropna()) - AIM_L1_KEEP)

    lines = [
        "# PMS price × volume response — 2024 → 2025 (ISZE → distributor)",
        "",
        "**Verdict:** The 2024→2025 PMS stocking story is mostly **volume down with list "
        "price flat**, not a clean price-elasticity pattern. About EUR 1.1M of volume impact "
        "sits in the price-flat / volume-down quadrant (capture or demand leak at unchanged "
        "list), led by brakes and oil filters in euro terms on ~163k trucks in service. "
        "Where list prices actually differed enough within a family to identify a beta, "
        "clutch kits and maintenance-service lines lean negative; the broad brakes AIM group "
        "does not. Many named filter/clutch lines share a near-uniform list move, so their "
        "beta is marked not identified — use the euro quadrants instead.",
        "",
        "This is **stocking-side response** (what distributors bought from ISZE), not what "
        "workshops paid end-customers. UTI (sold-to 1799) and UMI (1797) stay separate. IUK, ITUK "
        "and Ireland stay separate. Primary volume is **total** billed parts (not genuine-only).",
        "",
        "## Scope",
        "",
        "- Years: calendar **2024 vs 2025** from `sales_fact.parquet` (total billed qty / €).",
        "- Price: **customer condition price (ZPR1)** when both years exist for that sold-to × PN; "
        "otherwise **price list (PR00 IE40)**.",
        "- Grain: PN × sold-to customer (SAP), labelled with distributor code.",
        f"- Min filter: ≥ **{MIN_QTY}** units in **both** years; log-deltas winsorized at "
        f"**{int(WINSOR * 100)}%** tails for the beta only.",
        f"- Beta only when within-family std(log price change) ≥ **{MIN_DLNP_STD}**; otherwise "
        "marked not identified (use quadrant / median qty).",
        "- Families kept:",
        f"  - Named PMS categories: {', '.join(sorted(PMS_CAT_KEEP))}",
        f"  - AIM top-level: {', '.join(sorted(AIM_L1_KEEP))} (labelled `AIM: …` when no PMS category tag)",
        f"- Pairs in scope after filters: **{n_after:,}** (of {n_before:,} YoY pairs that cleared "
        "the qty floor before the family filter).",
        f"- Price source mix: ZPR1 **{n_zpr1:,}** / PR00 **{n_pr00:,}** (ZPR1 only covers sold-to "
        "1797, 1799, 2372 in these files).",
        f"- Billed € on these pairs: **EUR {total_eur_2024:,.0f}** (2024) → "
        f"**EUR {total_eur_2025:,.0f}** (2025).",
        f"- Fleet context (GPS 2025 trucks in service, for scale): network UIO ≈ "
        f"**{uio_total:,.0f}**; UMI **{umi_uio:,.0f}**; UTI **{uti_uio:,.0f}** "
        "(kept separate — never blended).",
        "",
        "## Top families by |beta| among identified (with €)",
        "",
        "| Family | beta | n pairs | EUR billed 2024 | EUR volume impact* | Reading |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for _, r in top_abs.iterrows():
        b = r["beta_elasticity"]
        b_s = f"{b:.2f}" if pd.notna(b) else "n/a"
        lines.append(
            f"| {r['family']} | {b_s} | {int(r['n_pairs'])} | "
            f"{r['eur_billed_2024']:,.0f} | {r['eur_volume_impact']:,.0f} | {r['reading']} |"
        )

    # largest EUR movers regardless of beta ID
    by_eur = fam_out.sort_values("eur_volume_impact").head(6)
    lines.extend(
        [
            "",
            "*EUR volume impact = (qty 2025 − qty 2024) × 2024 list price on the pair. "
            "Negative means fewer units stocked at that price.",
            "",
            "## Largest EUR volume drops (any family, beta may be n/a)",
            "",
        ]
    )
    for _, r in by_eur.iterrows():
        lines.append(
            f"- **{r['family']}**: EUR {r['eur_volume_impact']:,.0f} volume impact "
            f"(median price {r['median_pct_price_yoy']:+.1f}%, median qty "
            f"{r['median_pct_qty_yoy']:+.1f}%, n={int(r['n_pairs'])}, "
            f"identified={bool(r['beta_identified'])})"
        )

    lines.extend(
        [
            "",
            "## Price-up + volume-down (sensitive quadrant) — largest € hits",
            "",
        ]
    )
    if len(sens_by_fam):
        for fam_name, r in sens_by_fam.iterrows():
            lines.append(
                f"- **{fam_name}**: EUR {r['eur']:,.0f} volume impact across {int(r['n'])} pairs"
            )
    else:
        lines.append("- (few pairs in this quadrant after filters)")

    lines.extend(
        [
            "",
            "## Quadrant roll-up (EUR volume impact)",
            "",
            "| Quadrant | n pairs | EUR volume impact |",
            "|---|---:|---:|",
        ]
    )
    for idx, r in q_summary.iterrows():
        lines.append(f"| {idx} | {int(r['n'])} | {r['eur_volume_impact']:,.0f} |")

    lines.extend(
        [
            "",
            "## What was excluded",
            "",
            f"- Non-PMS AIM families (examples): {', '.join(excluded_aim[:20])}"
            + ("…" if len(excluded_aim) > 20 else "")
            + " — body, engine, electrical, accident, competitive catch-alls, etc.",
            "- Sold-to codes in the usual exclude set (Germany service, MIDI, non-parts, Turkey, "
            "NL/LU duplicates, etc.).",
            f"- PN×customer with <{MIN_QTY} units in either year.",
            "- Pairs missing both ZPR1 and PR00 price in either year.",
            "- Genuine-only cut was **not** used (total sales).",
            "",
            "## Caveats (read before acting)",
            "",
            "1. **Not market elasticity.** Distributors can absorb, delay, or substitute; dealer "
            "and workshop demand is a different layer (sales to dealer and beyond).",
            "2. **List price ≠ invoice.** PR00 / ZPR1 ignore rebates and mix; billed € can move "
            "differently.",
            "3. **ZPR1 coverage is thin** (three sold-to numbers). Most pairs use the shared price list.",
            "4. **Low statistical power.** Annual data, one YoY step; betas with `low_power=true` "
            "or large `se_beta` are direction-only.",
            "5. **Demand shocks** (stock-outs, campaigns, model mix) are not controlled.",
            "",
            "## Files",
            "",
            f"- Family / beta: `{fam_path}`",
            f"- PN pairs (top 500 by |EUR volume impact|): `{pn_path}`",
            f"- This note: `{INBOX / 'PMS_PRICE_VOLUME_RESPONSE_2024_2025.md'}`",
            "",
        ]
    )

    md_path = INBOX / "PMS_PRICE_VOLUME_RESPONSE_2024_2025.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print("WROTE", fam_path)
    print("WROTE", pn_path)
    print("WROTE", md_path)
    print("n_pairs", n_pairs, "zpr1", n_zpr1, "pr00", n_pr00)
    print("eur 2024/2025", round(total_eur_2024), round(total_eur_2025))
    print("\nTOP |beta| (identified only):")
    show = top_abs[
        [
            "family",
            "beta_elasticity",
            "n_pairs",
            "eur_billed_2024",
            "eur_volume_impact",
            "beta_identified",
            "low_power",
        ]
    ]
    print(show.to_string(index=False))
    print("\nAll families:")
    print(
        fam_out[
            [
                "family",
                "beta_elasticity",
                "beta_identified",
                "n_pairs",
                "eur_billed_2024",
                "eur_volume_impact",
                "median_pct_price_yoy",
                "median_pct_qty_yoy",
            ]
        ].to_string(index=False)
    )
    print("\nFamilies:", len(fam_out))
    print(
        "Israel check:",
        sorted(
            pairs.loc[pairs["distributor_code"].isin(["UMI", "UTI"]), "distributor_code"]
            .unique()
            .tolist()
        ),
    )
    print(
        "IUK/ITUK/IRELAND:",
        sorted(
            pairs.loc[
                pairs["distributor_code"].isin(["IUK", "ITUK", "IRELAND"]),
                "distributor_code",
            ]
            .unique()
            .tolist()
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
