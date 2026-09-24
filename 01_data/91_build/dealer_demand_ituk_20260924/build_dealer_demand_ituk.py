#!/usr/bin/env python3
"""
Dealer-level parts demand, ITUK (UK truck book), CY2025.

Internal draft. Reads only. Writes NEW dated CSVs under 01_data/00_derived/.
Never overwrites an existing file.

Method
------
We hold the fleet for the market, not for each dealer. So each dealer must be given a
share of the fleet before anything can be expected of them.

The share proxy tested here is the mileage-rhythm family: a dealer's share of oil filters
is used as their share of the trucks. A dealer who fits filters for X% of the network is
assumed to serve roughly X% of the trucks, so should buy about X% of every other service
part too.

The proxy is TESTED per family, not assumed: the dealer's filter share is compared with
their actual share of that family, and the residual is reported in percentage points and
in euro. The naive alternative (an equal split of the fleet) is scored on the same basis
so the page can say whether the proxy is worth anything.

Fleet denominator: gps_spu_by_distributor.csv, ITUK 2025 row, uio_units. Read, not typed.

Value basis: sell-out files carry quantities only. Euro = qty x the median CY2025
ISZE-to-distributor unit price for that part number (same convention as
03_analytics/Isuzu/prism/scripts/build_dealer_sellout_aim_gps.py, which produced
dealer_sellout_gps_2025.csv). This is what we billed the distributor, not the dealer
invoice, and quantity with no ISZE price is carried as a named share rather than dropped.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

DERIVED = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
BUILD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\dealer_demand_ituk_20260924")
PRISM = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism")

STAMP = "20260924"
YEAR = 2025
DIST = "ITUK"

# The mileage-rhythm family. Chosen, not fitted: filters are replaced on distance driven,
# so a dealer's filter count tracks the trucks they actually service. Failure-driven parts
# (clutch, brake) do not have that property and are tested against it, not assumed from it.
PROXY_CATEGORY = "oil_filter"

# The families the service-demand model covers. Anything not here cannot be judged by this
# method at all: a dealer who sold no body panels may simply have had no accident repair.
PMS_CATEGORIES = [
    "oil_filter", "air_filter", "fuel_filter", "blower_filter", "urea_filter",
    "brake_pad", "brake_rotor", "brake_shoe",
    "clutch_disc", "clutch_kit", "clutch_pressure_plate", "clutch_booster",
    "pilot_bearing", "release_bearing",
]
CATEGORY_LABEL = {
    "oil_filter": "Oil filter",
    "air_filter": "Air filter",
    "fuel_filter": "Fuel filter",
    "blower_filter": "Cabin / blower filter",
    "urea_filter": "Urea (AdBlue) filter",
    "brake_pad": "Brake pad",
    "brake_rotor": "Brake disc / rotor",
    "brake_shoe": "Brake shoe",
    "clutch_disc": "Clutch disc",
    "clutch_kit": "Clutch kit",
    "clutch_pressure_plate": "Clutch pressure plate",
    "clutch_booster": "Clutch booster",
    "pilot_bearing": "Pilot bearing",
    "release_bearing": "Release bearing",
}
# Families where the mileage rhythm genuinely holds, so the filter share is defensible.
RHYTHM = {"oil_filter", "air_filter", "fuel_filter", "blower_filter", "urea_filter"}
# Families driven by failure, not distance. The proxy is tested on them but is expected to
# be weak, and the page must say so rather than print a confident gap.
FAILURE_DRIVEN = set(PMS_CATEGORIES) - RHYTHM

MIN_NETWORK_QTY = 400      # below this the dealer split is noise, not a finding


def log(msg: str) -> None:
    print(msg, flush=True)


def q(x, nd=2):
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return None
    return round(float(x), nd)


def load_fleet() -> tuple[float, str, str]:
    """Read the fleet we bill against, from the GPS file that already publishes it."""
    gps = pd.read_csv(DERIVED / "gps_spu_by_distributor.csv")
    row = gps[(gps["distributor_code"] == DIST) & (gps["year"] == YEAR)]
    if row.empty:
        raise SystemExit(f"No {DIST} {YEAR} row in gps_spu_by_distributor.csv")
    r = row.iloc[0]
    return float(r["uio_units"]), str(r["uio_source"]), str(r["period_basis"])


def load_asp() -> pd.DataFrame:
    """Median CY2025 ISZE-to-distributor unit price per part number, ITUK."""
    sys.path.insert(0, str(PRISM))
    from config import SALES_FACT_PARQUET, resolve_mapping_path  # noqa
    from modules.data_prep import apply_distributor_codes, load_distributor_mapping  # noqa

    sales = pd.read_parquet(SALES_FACT_PARQUET)
    mapping = load_distributor_mapping(resolve_mapping_path())
    sales = apply_distributor_codes(sales, mapping)
    s = sales[(sales["year"] == YEAR) & (sales["distributor_code"] == DIST)].copy()
    if "line_kind" in s.columns:
        s = s[s["line_kind"] == "part"]
    s["part_number"] = s["part_number"].astype(str).str.strip().str.zfill(10)
    s = s[s["billed_qty"] > 0]
    s["asp_eur"] = s["net_sales_value"] / s["billed_qty"]
    s = s[s["asp_eur"] > 0]
    return s.groupby("part_number", as_index=False)["asp_eur"].median()


def load_dealer_lines() -> pd.DataFrame:
    """Dealer x part x month, CY2025, quantities only."""
    d = pd.read_csv(DERIVED / "dealer_sellout_long_ITUK_CY2025.csv", dtype={"part_number": str})
    d = d[d["period_grain"] == "month"].copy()
    d["part_number"] = d["part_number"].str.strip().str.zfill(10)
    d["qty"] = pd.to_numeric(d["qty"], errors="coerce").fillna(0)
    d["dealer_name"] = d["dealer_name"].astype(str).str.strip()
    d = d[d["dealer_name"] != ""]
    return d


def load_category_map() -> pd.DataFrame:
    """Part number -> PMS category. Two sources, both on disk; union them and say so."""
    a = pd.read_csv(DERIVED / "dealer_sellout_ituk_cy2025_by_pn.csv", dtype={"part_number": str})
    a["part_number"] = a["part_number"].str.strip().str.zfill(10)
    a = a[["part_number", "pms_category", "description"]].rename(
        columns={"pms_category": "cat_bypn"})

    b = pd.read_csv(DERIVED / "dealer_sellout_pn_audit.csv", dtype={"part_number": str})
    b["part_number"] = b["part_number"].str.strip().str.zfill(10)
    b = b[["part_number", "pms_category"]].rename(columns={"pms_category": "cat_audit"})

    m = a.merge(b, on="part_number", how="outer")
    m["cat"] = m["cat_bypn"].fillna("")
    m.loc[m["cat"] == "", "cat"] = m["cat_audit"].fillna("")
    m["cat_source"] = np.where(m["cat_bypn"].fillna("") != "", "by_pn", "")
    m.loc[(m["cat_source"] == "") & (m["cat_audit"].fillna("") != ""), "cat_source"] = "pn_audit"
    m = m[["part_number", "cat", "cat_source", "description"]].drop_duplicates("part_number")
    return m


def load_market_expected() -> pd.DataFrame:
    """Market expected euro per service family, on the truck-book basis, ITUK 2025.

    The table carries five fleet rows per category. Two of them (n_series_truck and
    shared_across_families) are near-duplicates of the same demand cut, so summing every
    row would roughly double every number. The truck book is the n_series_truck row, and
    its own fleet figure (22,190.9) sits within 1% of the fleet we bill against - that is
    the basis used here. The choice is reported on the page.
    """
    f = pd.read_csv(DERIVED / "pms_capture_by_family.csv")
    f["year"] = pd.to_numeric(f["year"], errors="coerce")
    i = f[(f["distributor_code"] == DIST) & (f["year"] == YEAR)].copy()
    truck = i[i["family"] == "n_series_truck"].copy()
    truck = truck[truck["pms_category"].isin(PMS_CATEGORIES)]
    out = truck[["pms_category", "fleet_units", "visits_per_year", "category_factor",
                 "expected_qty", "expected_eur", "billed_eur", "billed_units",
                 "avg_selling_price_eur"]].copy()
    out["category_label"] = out["pms_category"].map(CATEGORY_LABEL)
    return out.sort_values("expected_eur", ascending=False)


def main() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    fleet, fleet_src, fleet_basis = load_fleet()
    log(f"Fleet we bill against ({DIST} {YEAR}): {fleet:,.0f} trucks  source={fleet_src}  basis={fleet_basis}")

    asp = load_asp()
    lines = load_dealer_lines()
    cats = load_category_map()
    expected = load_market_expected()

    # ---- value the dealer lines -------------------------------------------------
    lines = lines.merge(asp, on="part_number", how="left")
    lines["valued_eur"] = lines["qty"] * lines["asp_eur"].fillna(0.0)
    lines = lines.merge(cats[["part_number", "cat", "cat_source"]], on="part_number", how="left")
    lines["cat"] = lines["cat"].fillna("")
    unvalued_qty = float(lines.loc[lines["asp_eur"].isna(), "qty"].sum())
    total_qty = float(lines["qty"].sum())
    log(f"Dealer lines {len(lines):,} | PNs {lines['part_number'].nunique():,} | "
        f"qty {total_qty:,.0f} | valued EUR {lines['valued_eur'].sum():,.2f} | "
        f"qty with no ISZE price {unvalued_qty/total_qty:.2%}")

    dealers = sorted(lines["dealer_name"].unique())
    n_dealers = len(dealers)
    total_by_dealer = lines.groupby("dealer_name")["qty"].sum()

    # ---- dealer share of the proxy family ---------------------------------------
    proxy = lines[lines["cat"] == PROXY_CATEGORY].groupby("dealer_name", as_index=False).agg(
        proxy_qty=("qty", "sum"))
    proxy["proxy_share"] = proxy["proxy_qty"] / proxy["proxy_qty"].sum()
    proxy = proxy.sort_values("proxy_share", ascending=False)

    # ---- per family: actual share, and the proxy residual ------------------------
    by_fam = (lines[lines["cat"].isin(PMS_CATEGORIES)]
              .groupby(["dealer_name", "cat"], as_index=False)
              .agg(qty=("qty", "sum"), eur=("valued_eur", "sum")))

    exp_map = expected.set_index("pms_category")
    cal_rows = []
    dealer_fam_rows = []
    for cat in PMS_CATEGORIES:
        if cat not in exp_map.index:
            continue
        exp_eur = float(exp_map.loc[cat, "expected_eur"])
        exp_qty = float(exp_map.loc[cat, "expected_qty"])
        net_qty = float(by_fam.loc[by_fam["cat"] == cat, "qty"].sum())
        net_eur = float(by_fam.loc[by_fam["cat"] == cat, "eur"].sum())
        judgeable = net_qty >= MIN_NETWORK_QTY

        sub = by_fam[by_fam["cat"] == cat].set_index("dealer_name")
        rows = []
        for dname in dealers:
            aq = float(sub["qty"].get(dname, 0.0))
            ae = float(sub["eur"].get(dname, 0.0))
            pshare = float(proxy.set_index("dealer_name")["proxy_share"].get(dname, 0.0))
            actual_share = aq / net_qty if net_qty > 0 else np.nan
            pred_eur = pshare * exp_eur
            rows.append({
                "dealer_name": dname,
                "family": cat,
                "family_label": CATEGORY_LABEL[cat],
                "family_kind": "mileage rhythm" if cat in RHYTHM else "failure driven",
                "proxy_share": pshare,
                "trucks_apportioned": pshare * fleet,
                "network_qty": aq,
                "network_eur": ae,
                "actual_share": actual_share,
                "expected_eur": pred_eur,
                "gap_eur": pred_eur - ae,
                "proxy_residual_pp": (actual_share - pshare) * 100 if net_qty > 0 else np.nan,
            })
        df_rows = pd.DataFrame(rows)
        dealer_fam_rows.append(df_rows)

        res = df_rows["proxy_residual_pp"].dropna()
        if len(res) and judgeable:
            mad = float(res.abs().mean())
            avg_share_pp = 100.0 / n_dealers
            mad_rel = mad / avg_share_pp
            # naive benchmark: split the fleet equally and expect the same of everyone
            naive = (df_rows["actual_share"].fillna(0) * 100) - avg_share_pp
            mad_naive = float(naive.abs().mean())
            rho = float(pd.Series(df_rows["proxy_share"]).corr(
                pd.Series(df_rows["actual_share"].fillna(0)), method="spearman"))
            # THE FALSIFICATION TEST: does the filter share beat dealer size alone?
            # If each dealer's total parts volume predicts their share of this family just
            # as well, then the "trucks per dealer" story is unproven - it is just size.
            size_share = (df_rows["dealer_name"].map(total_by_dealer) /
                          df_rows["dealer_name"].map(total_by_dealer).sum())
            rho_size = float(pd.Series(size_share).corr(
                pd.Series(df_rows["actual_share"].fillna(0)), method="spearman"))
            # how far the ratio actual/proxy spreads across dealers (1.0 = proxy exact)
            ratio = (df_rows["actual_share"].fillna(0) / df_rows["proxy_share"].replace(0, np.nan)).dropna()
            spread = float(ratio.quantile(0.9) / ratio.quantile(0.1)) if len(ratio) > 3 and ratio.quantile(0.1) > 0 else None
        else:
            mad = mad_naive = rho = rho_size = spread = None
            mad_rel = None

        if cat == PROXY_CATEGORY:
            basis = "definition"
        elif not judgeable:
            basis = "not judgeable"
        elif cat in RHYTHM and rho is not None and rho >= 0.6:
            basis = "calibrated"
        else:
            basis = "estimated"

        cal_rows.append({
            "family": cat,
            "family_label": CATEGORY_LABEL[cat],
            "family_kind": "mileage rhythm" if cat in RHYTHM else "failure driven",
            "network_qty": net_qty,
            "network_eur": net_eur,
            "expected_qty": exp_qty,
            "expected_eur": exp_eur,
            "network_gap_eur": exp_eur - net_eur,
            "capture_of_expected": (net_eur / exp_eur) if exp_eur > 0 else None,
            "mad_pp": mad,
            "mad_relative_to_average_share": mad_rel,
            "mad_pp_equal_split": mad_naive,
            "spearman_rho": rho,
            "spearman_rho_dealer_size_only": rho_size,
            "ratio_p90_over_p10": spread,
            "basis": basis,
        })
        log(f"  {CATEGORY_LABEL[cat]:<24} net {net_qty:>8,.0f} pcs  exp EUR {exp_eur:>12,.0f}  "
            f"billed EUR {net_eur:>11,.0f}  rho {('%.2f'%rho) if rho is not None else '  n/a'}  "
            f"size-only {('%.2f'%rho_size) if rho_size is not None else 'n/a'}  "
            f"MAD {('%.1f'%mad) if mad is not None else ' n/a'}pp ({('%.0f%%'%(100*mad_rel)) if mad_rel is not None else 'n/a'})  -> {basis}")

    calibration = pd.DataFrame(cal_rows).sort_values("expected_eur", ascending=False)
    dealer_family = pd.concat(dealer_fam_rows, ignore_index=True)

    # ---- dealer roll-up (judgeable families only) --------------------------------
    judge_cats = calibration.loc[~calibration["basis"].isin(["not judgeable", "definition"]), "family"].tolist()
    jf = dealer_family[dealer_family["family"].isin(judge_cats)]
    roll = jf.groupby("dealer_name", as_index=False).agg(
        expected_eur=("expected_eur", "sum"),
        billed_eur=("network_eur", "sum"),
        gap_eur=("gap_eur", "sum"),
    )
    roll = roll.merge(proxy[["dealer_name", "proxy_share"]], on="dealer_name", how="left")
    roll["trucks_apportioned"] = roll["proxy_share"] * fleet
    roll["proxy_absent"] = roll["proxy_share"].isna()
    roll["proxy_absent_note"] = np.where(
        roll["proxy_absent"],
        "Bought other parts but no oil filters, so no filter share exists and nothing is "
        "expected of them. A real observation about the dealer, not a measurement.",
        "")
    roll["all_book_billed_eur"] = roll["dealer_name"].map(
        lines.groupby("dealer_name")["valued_eur"].sum()).fillna(0.0)
    roll["families_judged"] = roll["dealer_name"].map(
        jf.groupby("dealer_name")["family"].nunique()).fillna(0).astype(int)
    roll["gap_basis"] = "expected side from the filter-share proxy"
    roll = roll.sort_values("gap_eur", ascending=False)

    # ---- the one number that governs everything below ----------------------------
    # Oil filter is the proxy family itself, so its residual is zero by construction.
    # The honest headline is the strongest INDEPENDENT family: a family that was never
    # used to build the shares, and which the proxy still lands on.
    def _headline_row():
        c = calibration[(calibration["family"].isin(RHYTHM)) &
                        (calibration["basis"] == "calibrated") &
                        (calibration["family"] != PROXY_CATEGORY)]
        if c.empty:
            return None
        return c.sort_values("spearman_rho", ascending=False).iloc[0]

    hb = _headline_row()
    if hb is None:
        head_mad = head_rho = head_fam = None
    else:
        head_mad, head_rho, head_fam = hb["mad_pp"], hb["spearman_rho"], hb["family"]

    # ---- how much of what dealers bought this method can even see ----------------
    cov = lines.copy()
    cov["is_service_family"] = cov["cat"].isin(PMS_CATEGORIES)
    cov_rows = []
    for cat in PMS_CATEGORIES:
        s = cov[cov["cat"] == cat]
        cov_rows.append({
            "family": cat,
            "family_label": CATEGORY_LABEL[cat],
            "network_qty": float(s["qty"].sum()),
            "network_eur": float(s["valued_eur"].sum()),
            "dealers_buying": int(s["dealer_name"].nunique()),
        })
    coverage = pd.DataFrame(cov_rows)
    coverage["qty_share_of_all_dealer_buys"] = (
        coverage["network_qty"] / cov["qty"].sum() if cov["qty"].sum() else None)
    coverage["eur_share_of_all_dealer_buys"] = (
        coverage["network_eur"] / cov["valued_eur"].sum() if cov["valued_eur"].sum() else None)

    # the one number that governs everything below
    service_qty_share = float(cov.loc[cov["is_service_family"], "qty"].sum() / cov["qty"].sum())
    service_eur_share = float(cov.loc[cov["is_service_family"], "valued_eur"].sum() / cov["valued_eur"].sum())

    # ---- write ------------------------------------------------------------------
    out_cal = DERIVED / f"dealer_demand_ituk_2025_calibration_by_family_{STAMP}.csv"
    out_df = DERIVED / f"dealer_demand_ituk_2025_dealer_by_family_{STAMP}.csv"
    out_roll = DERIVED / f"dealer_demand_ituk_2025_by_dealer_{STAMP}.csv"
    out_exp = DERIVED / f"dealer_demand_ituk_2025_market_expected_{STAMP}.csv"
    out_cov = DERIVED / f"dealer_demand_ituk_2025_coverage_{STAMP}.csv"
    out_meta = DERIVED / f"dealer_demand_ituk_2025_meta_{STAMP}.json"
    for p in (out_cal, out_df, out_roll, out_exp, out_cov, out_meta):
        if p.exists():
            raise SystemExit(f"REFUSING to overwrite existing file: {p}")

    calibration.to_csv(out_cal, index=False, encoding="utf-8-sig")
    dealer_family.to_csv(out_df, index=False, encoding="utf-8-sig")
    roll.to_csv(out_roll, index=False, encoding="utf-8-sig")
    expected.to_csv(out_exp, index=False, encoding="utf-8-sig")
    coverage.to_csv(out_cov, index=False, encoding="utf-8-sig")

    meta = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "market": "ITUK (UK truck book)",
        "year": YEAR,
        "fleet_we_bill_against": fleet,
        "fleet_source": fleet_src,
        "fleet_period_basis": fleet_basis,
        "fleet_note": "Read from gps_spu_by_distributor.csv, ITUK 2025 row, uio_units. "
                      "The wallet-waterfall fleet is not used.",
        "proxy_family": PROXY_CATEGORY,
        "dealers": n_dealers,
        "dealer_lines": int(len(lines)),
        "dealer_qty_total": total_qty,
        "valued_eur_total": float(lines["valued_eur"].sum()),
        "qty_without_isze_price_share": unvalued_qty / total_qty if total_qty else None,
        "value_convention": "qty x median CY2025 ISZE-to-distributor unit price per part number; "
                            "this is what we billed the distributor, not the dealer invoice.",
        "headline_calibration": {
            "family": head_fam,
            "spearman_rho": q(head_rho, 3),
            "mean_absolute_residual_pp": q(head_mad, 2),
            "proxy_family": PROXY_CATEGORY,
            "proxy_family_residual_pp": 0.0,
            "proxy_family_note": "Zero by construction: the filter share IS the family share, "
                                 "so it cannot be scored against itself. The headline family "
                                 "above was never used to build the shares.",
            "reading": "A dealer's oil-filter share is used as their share of the trucks. The "
                       "residual is how far that lands from the dealer's actual share of the family.",
        },
        "expected_basis": "pms_capture_by_family.csv, family = n_series_truck (truck book), ITUK 2025. "
                          "Not the sum of all fleet rows, which would double-count.",
        "labels": {
            "measured": "what the dealers actually bought (all dealer rows)",
            "calibrated": "expected side from the filter-share proxy, family passed the test",
            "estimated": "expected side from the filter-share proxy, family did not pass the test",
            "not judgeable": "family has no service-demand basis for this method at all",
        },
        "coverage_of_the_method": {
            "service_family_qty_share": service_qty_share,
            "service_family_eur_share": service_eur_share,
            "note": "Share of everything the 64 dealers bought that sits in a family this method "
                    "can judge at all. The rest is repair, body, electrical and hardware, which "
                    "has no service rhythm and is not part of this model.",
        },
        "falsification_test": {
            "question": "Does the filter share beat dealer size alone?",
            "method": "Spearman rank correlation of each dealer's share of the family against "
                      "(a) their share of network oil filters and (b) their total parts volume.",
            "reading": "Where the two are close, the proxy is not adding information beyond "
                       "'the big dealer is big'. That is the test of the stated method, and it "
                       "is reported as measured, not as assumed.",
            "by_family_pairs": [
                {"family": r["family_label"],
                 "rho_filter_share": q(r["spearman_rho"], 3),
                 "rho_size_only": q(r["spearman_rho_dealer_size_only"], 3),
                 "filter_share_adds": (None if (pd.isna(r["spearman_rho"]) or pd.isna(r["spearman_rho_dealer_size_only"]))
                                       else q(r["spearman_rho"] - r["spearman_rho_dealer_size_only"], 3))}
                for _, r in calibration.iterrows()
            ],
        },
        "israel": "Excluded entirely. No Israel row is read by this build. Separately: "
                  "01_data/90_INBOX/PPT_GPT_10csv_2026-09-19/06_dealer_master_geo.csv carries 78 rows "
                  "labelled Israel LCV. Jerome states we hold no dealer names for Israel, so those "
                  "rows are a labelling problem in that file. Recorded, not acted on, not read here.",
        "outputs": [str(p) for p in (out_cal, out_df, out_roll, out_exp, out_cov)],
    }
    out_meta.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    log("")
    log(f"Headline independent family: {head_fam} rho={q(head_rho,3)}  MAD={q(head_mad,2)} pp")
    log(f"Dealers: {n_dealers} | valued EUR {lines['valued_eur'].sum():,.2f}")
    for p in (out_cal, out_df, out_roll, out_exp, out_cov, out_meta):
        log("wrote " + str(p))


if __name__ == "__main__":
    main()
