"""Build per-distributor composite AFTERSALES-RISK ranking.

Answers: "which customers carry the most aftersales risk?" by blending four
per-DB signals into one weighted intensity index (0-100), latest year.

Signals (each min-max normalised 0..1 across DBs; higher = more risk):
  1. Eucon street-undercut exposure  — price level, channel-grossed (EXTERNAL walk-out)
  2. AIM scraper high-risk %          — direct aftermarket flag        (EXTERNAL)
  3. Contested BVP capture            — own genuine<->BVP crossref     (INTERNAL down-trade)
  4. VOR / urgent line share          — stocking-miss urgency proxy

PRICE LEVEL — we sit upstream in the circle. ISZE prices are IE40 list to the
distributor. To compare apples-to-apples against aftermarket at the counter we
gross up through the channel: distributor +40%, then dealer +27.5%
  street genuine = list x 1.40 x 1.275 = x1.785
Eucon undercut = aftermarket avg price < street genuine price. At list level only
25/44 benchmarked PNs are undercut; at street level 40/44 are -- that channel
effect is the whole point of this view.

NOTE: the composite is a weighted INTENSITY index, not a euro sum. Internal
down-trade (BVP) and external walk-out (Eucon/AIM) are never added as euros --
they are different threats (see aim-leakage.md alert). Euro magnitudes are
reported in separate columns for context.

Output: ISZE/Data/derived/db_aftersales_risk.csv
Run:    python -m streamlit ... no -- just  `python scripts/build_db_aftersales_risk.py`
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import DERIVED_DIR  # noqa: E402
from modules.strategic_build import load_sales_mapped  # noqa: E402

# --- tunable weights (must sum to 1.0) --------------------------------------
WEIGHTS = {
    "eucon_price": 0.35,    # external price walk-out, channel-grossed
    "aim_scraper": 0.25,    # external aftermarket flag
    "contested_bvp": 0.25,  # internal down-trade pressure
    "vor_urgent": 0.15,     # urgency / stocking-miss proxy
}

# --- channel gross-up (we sit upstream) -------------------------------------
DB_MARKUP = 1.40      # ISZE list -> distributor
DEALER_MARKUP = 1.275  # distributor -> dealer/street
STREET_FACTOR = DB_MARKUP * DEALER_MARKUP  # = 1.785


def _minmax(s: pd.Series) -> pd.Series:
    s = s.astype(float).fillna(0.0)
    lo, hi = s.min(), s.max()
    if hi <= lo:
        return pd.Series(0.0, index=s.index)
    return (s - lo) / (hi - lo)


def _norm_pn(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)


def main() -> None:
    derived = Path(DERIVED_DIR)

    # ---- 1. AIM scraper (per DB) + canonical net-sales denominator ----------
    aim = pd.read_csv(derived / "aim_exposure_by_db_year.csv")
    year = int(aim["year"].max())
    aim = aim[aim["year"] == year][
        ["distributor_code", "net_sales_eur", "high_risk_rev_eur", "high_risk_rev_pct"]
    ].copy()

    # ---- 2. Contested / BVP capture (own insight, per DB) -------------------
    mix = pd.read_parquet(derived / "db_parts_mix_classification.parquet")
    mix = mix[mix["year"] == year][
        ["distributor_code", "contested_eur", "contested_bvp_capture", "bvp_pct"]
    ].copy()

    # ---- 3. VOR / urgent share (per DB) -------------------------------------
    vor = pd.read_csv(derived / "vor_profile.csv")
    vor = vor[vor["year"] == year].copy()
    tot_lines = vor.groupby("distributor_code")["line_count"].sum().rename("total_lines")
    urg_lines = (
        vor[vor["order_type"].isin(["vor", "urgent"])]
        .groupby("distributor_code")["line_count"]
        .sum()
        .rename("urgent_lines")
    )
    vor_share = pd.concat([tot_lines, urg_lines], axis=1).fillna(0.0)
    vor_share["vor_urgent_share"] = (
        vor_share["urgent_lines"] / vor_share["total_lines"].replace(0, pd.NA)
    ).fillna(0.0)
    vor_share = vor_share.reset_index()[["distributor_code", "vor_urgent_share"]]

    # ---- 4. Eucon street-undercut exposure, rolled up per DB ----------------
    eu = pd.read_csv(derived / "eucon_price_gap.csv")
    eu["street_price"] = eu["ISZE_IE40_Price_EUR"] * STREET_FACTOR
    eu["street_undercut"] = eu["Avg_Competitor_EUR"] < eu["street_price"]
    undercut_pns = set(_norm_pn(eu.loc[eu["street_undercut"], "pn"]))

    sales = load_sales_mapped()
    sales = sales[sales["year"] == year].copy()
    sales["pn_key"] = _norm_pn(sales["part_number"])
    sales["_undercut"] = sales["pn_key"].isin(undercut_pns)
    eucon_db = (
        sales[sales["_undercut"]]
        .groupby("distributor_code")["net_sales_value"]
        .sum()
        .rename("eucon_undercut_rev_eur")
        .reset_index()
    )

    # ---- merge everything on distributor_code -------------------------------
    df = (
        aim.merge(mix, on="distributor_code", how="left")
        .merge(vor_share, on="distributor_code", how="left")
        .merge(eucon_db, on="distributor_code", how="left")
    )
    df["eucon_undercut_rev_eur"] = df["eucon_undercut_rev_eur"].fillna(0.0)
    df["eucon_undercut_pct"] = (
        df["eucon_undercut_rev_eur"] / df["net_sales_eur"].replace(0, pd.NA)
    ).fillna(0.0)
    df["contested_bvp_capture"] = df["contested_bvp_capture"].fillna(0.0)
    df["high_risk_rev_pct"] = df["high_risk_rev_pct"].fillna(0.0)
    df["vor_urgent_share"] = df["vor_urgent_share"].fillna(0.0)

    # ---- normalise signals and weight ---------------------------------------
    df["n_eucon"] = _minmax(df["eucon_undercut_pct"])
    df["n_aim"] = _minmax(df["high_risk_rev_pct"])
    df["n_contested"] = _minmax(df["contested_bvp_capture"])
    df["n_vor"] = _minmax(df["vor_urgent_share"])

    df["risk_score"] = 100.0 * (
        WEIGHTS["eucon_price"] * df["n_eucon"]
        + WEIGHTS["aim_scraper"] * df["n_aim"]
        + WEIGHTS["contested_bvp"] * df["n_contested"]
        + WEIGHTS["vor_urgent"] * df["n_vor"]
    )

    df = df.sort_values("risk_score", ascending=False).reset_index(drop=True)
    df.insert(0, "rank", df.index + 1)
    df.insert(1, "year", year)

    cols = [
        "rank", "year", "distributor_code", "risk_score", "net_sales_eur",
        # raw signal intensities
        "eucon_undercut_pct", "high_risk_rev_pct", "contested_bvp_capture", "vor_urgent_share",
        # euro magnitudes (context, never summed across threat types)
        "eucon_undercut_rev_eur", "high_risk_rev_eur", "contested_eur", "bvp_pct",
        # normalised components
        "n_eucon", "n_aim", "n_contested", "n_vor",
    ]
    df = df[[c for c in cols if c in df.columns]]

    out = derived / "db_aftersales_risk.csv"
    df.to_csv(out, index=False)

    print(f"[build_db_aftersales_risk] year={year} | {len(df)} distributors")
    print(f"  weights: {WEIGHTS}")
    print(f"  street factor: x{STREET_FACTOR} | undercut PNs: {len(undercut_pns)}")
    print(f"  wrote -> {out}")
    print(df.head(10)[
        ["rank", "distributor_code", "risk_score", "eucon_undercut_pct",
         "high_risk_rev_pct", "contested_bvp_capture", "vor_urgent_share"]
    ].to_string(index=False))


if __name__ == "__main__":
    main()
