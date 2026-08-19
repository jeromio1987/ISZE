"""Build the canonical distributor dimension.

Output: 01_data/00_derived/distributor_dimension.csv

The single source of truth for "which DB is this row about". Resolves the two
competing naming conventions in the estate:

  pms_summary_by_db.csv        country/DB codes   BELGIUM, DENMARK, SWEDEN
  gps_pure_sales_*.csv         SAP entities       IBX, Danmark, Sverige, ISD

Nothing here is guessed. Every mapping comes from a file:

  payer -> distributor_code    sales_with_crossref.parquet (sold_to + distributor_code)
  sold-to split                sales_fact.parquet (sold_to_sap, ~477k rows)
  entity names                 pricing_zpr1_customers.parquet
  CV / LCV / mixed scope       02_dashboards/fleet/ISZE_GPS_Dashboard.html (embedded DUAL)

Key fact: payer_code is NOT unique. Payer 1797 carries both Israel entities.
The join key is sold_to_sap: 1797 = Universal Motors Israel (UMI),
1799 = Universal Trucks Israel (UTI), confirmed by SAP customer name.

Run:  python 01_data/91_build/build_distributor_dimension.py
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]          # ...\ISZE
DERIVED = ROOT / "01_data" / "00_derived"
OUT = DERIVED / "distributor_dimension.csv"

FY = 2026  # fiscal year used for the euro reference column

# CV / LCV / mixed per DB, from the GPS dashboard's embedded DUAL classification.
# Covers the original 18 DBs only; the CIS / Middle-East DBs have no scope there.
SCOPE = {
    "ITUK": "CV", "UTI": "CV",
    "IUK": "LCV", "UMI": "LCV", "NORWAY": "LCV", "SWEDEN": "LCV", "DENMARK": "LCV",
    "FINLAND": "LCV", "ICELAND": "LCV", "ROMANIA": "LCV", "HUNGARY": "LCV",
    "GERMANY": "MIXED", "BELGIUM": "MIXED", "IRELAND": "MIXED", "CYPRUS": "MIXED",
    "GREECE": "MIXED", "MALTA": "MIXED", "PORTUGAL": "MIXED",
}
REGION = {
    "ITUK": "UK", "IUK": "UK", "UMI": "ISRAEL", "UTI": "ISRAEL",
    "NORWAY": "NORDICS", "SWEDEN": "NORDICS", "DENMARK": "NORDICS",
    "FINLAND": "NORDICS", "ICELAND": "NORDICS",
    "UKRAINE": "CIS", "ARMENIA": "CIS", "KAZAKHSTAN": "CIS",
    "GERMANY": "WEST", "BELGIUM": "WEST", "IRELAND": "WEST",
    "PORTUGAL": "SOUTH", "GREECE": "SOUTH", "CYPRUS": "SOUTH", "MALTA": "SOUTH",
    "ROMANIA": "EAST", "HUNGARY": "EAST", "PALESTINE": "MIDDLE_EAST",
}

# Excluded per business instruction (Jerome 2026-08-13): dormant, no sales activity.
EXCLUDED_SOLD_TO = {2929}

# Known NON-customers. These appear in billing / UIO / KPI source data but are not
# ISZE distributors, and must stay out of GPS / PMS / KPI tables and projections.
# Standing rule, not a judgement call made here.
NOT_CUSTOMERS = {
    77: "Turkey (AIOS / Anadolu Isuzu) - not an ISZE distributor",
    88: "MIDI Europe - not an ISZE distributor",
}


def fiscal_year(s: pd.Series) -> pd.Series:
    """FY runs Apr-Mar, labelled by the March-end calendar year."""
    return s.dt.year.where(s.dt.month < 4, s.dt.year + 1)


def main() -> None:
    # 1. sold-to level actuals -------------------------------------------------
    sf = pd.read_parquet(
        DERIVED / "sales_fact.parquet",
        columns=["billing_date", "sold_to_sap", "sold_to", "net_sales_value",
                 "saty", "material"],
    )
    sf["fy"] = fiscal_year(sf["billing_date"])
    cur = sf[sf["fy"] == FY].copy()
    cur["payer"] = pd.to_numeric(cur["sold_to"], errors="coerce").astype("Int64")
    cur["sold_to_sap"] = cur["sold_to_sap"].astype("Int64")

    agg = (cur.groupby(["sold_to_sap", "payer"])["net_sales_value"]
              .sum().round(0).astype("int64").reset_index()
              .rename(columns={"net_sales_value": f"fy{FY}_net_sales_eur"}))

    # Non-parts material buckets (audit Check 1): service fees, demurrage, transport.
    NON_PARTS = ("SERVICE", "COST DEMURRAGE", "TRANSPORT", "LATE PAYMENT INTEREST")
    mat = cur["material"].fillna("").str.upper()
    cur["is_non_parts"] = mat.str.startswith(NON_PARTS)
    nonparts = (cur.groupby("sold_to_sap")
                   .agg(non_parts_eur=("net_sales_value",
                                       lambda s: s[cur.loc[s.index, "is_non_parts"]].sum()),
                        lines=("net_sales_value", "size"))
                   .reset_index())
    agg = agg.merge(nonparts, on="sold_to_sap", how="left")

    # 2. payer -> distributor_code (authoritative) ------------------------------
    xr = pd.read_parquet(DERIVED / "sales_with_crossref.parquet",
                         columns=["distributor_code", "sold_to"])
    xr["payer"] = pd.to_numeric(xr["sold_to"], errors="coerce").astype("Int64")
    counts = xr.groupby(["payer", "distributor_code"]).size().reset_index(name="n")
    # Keep only payers that resolve to exactly one DB; Israel is handled below.
    unambiguous = (counts.groupby("payer")
                         .filter(lambda g: g["distributor_code"].nunique() == 1)
                         [["payer", "distributor_code"]])

    # 3. SAP customer names -----------------------------------------------------
    cu = pd.read_parquet(DERIVED / "pricing_zpr1_customers.parquet")
    cu["sold_to_sap"] = pd.to_numeric(cu["customer_code"], errors="coerce").astype("Int64")
    cu = (cu[["sold_to_sap", "customer_name"]]
          .dropna(subset=["sold_to_sap"]).drop_duplicates("sold_to_sap"))

    df = agg.merge(unambiguous, on="payer", how="left").merge(cu, on="sold_to_sap", how="left")

    # Israel: one payer, two sold-tos. Confirmed by SAP customer name.
    df.loc[df["sold_to_sap"] == 1797, "distributor_code"] = "UMI"
    df.loc[df["sold_to_sap"] == 1799, "distributor_code"] = "UTI"

    # 4. GPS module's label, so no module hardcodes a mapping -------------------
    gps_files = sorted(DERIVED.glob("gps_pure_sales_*.csv"))
    if gps_files:
        gps = pd.read_csv(gps_files[-1])
        gps["payer"] = pd.to_numeric(gps["payer_codes"], errors="coerce").astype("Int64")
        labels = gps.groupby("payer")["db"].apply(lambda s: sorted(set(s))).to_dict()

        def gps_label(row):
            labs = labels.get(row["payer"], [])
            if not labs:
                return ""
            if len(labs) == 1:
                return labs[0]
            dc = str(row["distributor_code"]).upper()
            return next((l for l in labs if l.upper() == dc), "|".join(labs))

        df["gps_db_label"] = df.apply(gps_label, axis=1)
    else:
        df["gps_db_label"] = ""

    # 5. classify ---------------------------------------------------------------
    df["scope"] = df["distributor_code"].map(SCOPE)
    df["region"] = df["distributor_code"].map(REGION)
    df["in_pms_source"] = df["distributor_code"].isin(SCOPE).map({True: "yes", False: "no"})

    eur_col = f"fy{FY}_net_sales_eur"
    df["non_parts_eur"] = df["non_parts_eur"].fillna(0).round(0).astype("int64")
    # A sold-to whose billing is entirely non-parts is an exclusion bucket, not a DB.
    mostly_non_parts = (df["non_parts_eur"] >= df[eur_col] * 0.999) & (df[eur_col] > 0)

    def role(r):
        # Standing exclusions win over every other classification, so a future
        # crossref row can never promote these back into the network.
        if r["sold_to_sap"] in NOT_CUSTOMERS:
            return "not_a_customer"
        if r["sold_to_sap"] in EXCLUDED_SOLD_TO:
            return "excluded_entity"
        if pd.notna(r["distributor_code"]):
            return "network_db"
        if mostly_non_parts.loc[r.name]:
            return "excluded_non_parts"
        return "direct_account"

    df["network_role"] = df.apply(role, axis=1)

    def note(r):
        if r["network_role"] == "not_a_customer":
            return NOT_CUSTOMERS[r["sold_to_sap"]]
        if r["network_role"] == "excluded_entity":
            return "Dormant, no sales activity - excluded per business instruction 2026-08-13"
        if r["network_role"] == "excluded_non_parts":
            return "Non-parts billing only (service fee / demurrage) - audit Check 1 exclusion"
        if r["network_role"] == "direct_account":
            return "Trades but is not a network distributor - no distributor_code in any source"
        if r["sold_to_sap"] in (1797, 1799):
            return "Israel: payer 1797 covers both entities; split is at sold_to_sap level"
        return ""

    df["note"] = df.apply(note, axis=1)

    df = (df.sort_values(eur_col, ascending=False)
            [["sold_to_sap", "payer", "distributor_code", "gps_db_label", "customer_name",
              "scope", "region", "network_role", "in_pms_source", eur_col,
              "non_parts_eur", "note"]]
            .rename(columns={"payer": "payer_code"}))
    df.to_csv(OUT, index=False, encoding="utf-8")

    # 6. report -----------------------------------------------------------------
    print(df.to_string(index=False))
    print()
    for r, g in df.groupby("network_role"):
        print(f"  {r:<20} {len(g):>3} rows   EUR {g[eur_col].sum():>12,}")
    print(f"  {'TOTAL':<20} {len(df):>3} rows   EUR {df[eur_col].sum():>12,}")
    net = sorted(df.loc[df["network_role"] == "network_db", "distributor_code"].unique())
    print(f"\nnetwork DBs: {len(net)}")
    for grp, test in [("CV", lambda c: SCOPE.get(c) == "CV"),
                      ("LCV", lambda c: SCOPE.get(c) == "LCV"),
                      ("MIXED", lambda c: SCOPE.get(c) == "MIXED"),
                      ("NORDICS", lambda c: REGION.get(c) == "NORDICS"),
                      ("CIS", lambda c: REGION.get(c) == "CIS")]:
        print(f"  {grp:<8} {[c for c in net if test(c)]}")
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
