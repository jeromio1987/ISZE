"""
Rebuild gps_billing_clean.json from current raw SAP files + surcharge spot-check.

Surcharge check: billing 22–30 Mar 2026 (9-day window after 21.03.2026)
compares billed unit price vs IE40 PR00 list (13.03.2026) on RUSH/VOR/SVOR lines.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS))
from _shared.paths import DATA_ROOT, DERIVED_DIR, RAW_SALES_DIR  # noqa: E402

PR00_CSV = (
    DATA_ROOT.parent / "03_analytics" / "Isuzu" / "data"
    / "IE40 Price list as of 13.03.2026 PR00_3_level_classified_ie40_export.csv"
)
JSON_OUT = DERIVED_DIR / "gps_billing_clean.json"
TRANSPORT_OUT = DERIVED_DIR / "gps_billing_transport_excluded.json"
SURCHARGE_STRIPPED_OUT = DERIVED_DIR / "gps_billing_surcharge_stripped.json"
SURCHARGE_OUT = DERIVED_DIR / "gps_surcharge_check_2026-03-19_31.csv"
SURCHARGE_SUMMARY = DERIVED_DIR / "gps_surcharge_check_2026-03-19_31_summary.json"

EXCL_BILLT = {"S1", "G2", "RE", "ZFD", "S2"}
EXCL_SATY = {"CR", "RE"}
EXPECTED = {"SOR": 0.0, "RUSH": 0.03, "VOR": 0.07, "SVOR": 0.11, "PRD": -0.03}
SURCHARGE = {"SOR": 1.0, "RUSH": 1.03, "VOR": 1.07, "SVOR": 1.11, "PRD": 0.97}

PAYER_DB = {
    "2194": "ITUK", "2575": "ITUK", "146": "ITUK", "89": "IUK", "2574": "IUK",
    "90": "IBX", "92": "Imotors", "519": "Imotors", "93": "ISD",
    "601": "ISD", "2516": "ISD", "66": "RSA", "86": "Norway",
    "2181": "Sverige", "76": "Ireland", "393": "Loutsios",
    "396": "ROM Auto", "537": "AutoWallis", "1759": "GasanZammit",
    "2679": "Nordic FI", "2027": "Danmark", "2751": "Danmark",
    "1576": "BL Iceland", "88": "MIDI", "105": "IMG",
    "2294": "CIS-KTK", "2731": "GA", "2733": "GA", "2732": "CBC", "2734": "CBC",
    "2372": "KIMA", "77": "TR", "2929": "Sverige2", "373": "IMIO",
}

# Year ownership — must match prism/scripts/build_sales_fact_from_cy.py (no double-count).
CY_FILE_YEARS: dict[str, set[int]] = {
    "CY2023-2024.XLSX": {2023},
    "CY2024-2025.XLSX": {2024, 2025},
    "sales_2026tillApril.XLSX": {2026},
}


def fy(dt: datetime) -> int:
    return dt.year + 1 if dt.month >= 4 else dt.year


def _dedupe_columns(cols: list) -> list:
    seen: dict[str, int] = {}
    out = []
    for c in cols:
        n = seen.get(c, 0)
        out.append(c if n == 0 else f"{c}_{n}")
        seen[c] = n + 1
    return out


def norm_pn(val) -> str | None:
    if pd.isna(val):
        return None
    s = re.sub(r"\.0$", "", str(val).strip())
    s = re.sub(r"\D", "", s)
    if not s or s.upper() == "TRANSPORT":
        return None
    return s.lstrip("0") or "0"


def parse_eur_price(val) -> float | None:
    if pd.isna(val):
        return None
    s = str(val).strip().replace("€", "").replace(" ", "")
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        v = float(s)
        return v if v > 0 else None
    except ValueError:
        return None


def read_std(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Sheet1", header=0)
    df.columns = _dedupe_columns(list(df.columns))
    df = df.rename(columns={
        "Billing Date": "billing_date",
        "BillT": "billt",
        "Payer": "payer",
        "Sold-to pt": "sold_to",
        "Material": "material",
        "Net value": "net_value",
        "Net Price": "net_price",
        "Billed Quantity": "qty",
        "SaTy": "saty",
    })
    df["billing_date"] = pd.to_datetime(df["billing_date"], errors="coerce")
    df = df.dropna(subset=["billing_date"])
    df["payer"] = pd.to_numeric(df["payer"], errors="coerce")
    df["sold_to"] = pd.to_numeric(df.get("sold_to"), errors="coerce")
    df["net_value"] = pd.to_numeric(df["net_value"], errors="coerce").fillna(0.0)
    df["net_price"] = pd.to_numeric(df.get("net_price"), errors="coerce")
    df["qty"] = pd.to_numeric(df.get("qty"), errors="coerce").fillna(0.0)
    df["billt"] = df["billt"].astype(str).str.strip().str.upper()
    df["saty"] = df["saty"].astype(str).str.strip().str.upper()
    df["material"] = df["material"].astype(str).str.strip().str.upper()
    return df


def read_cy2025(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Sheet1", header=0)
    df.columns = _dedupe_columns(list(df.columns))
    df = df.rename(columns={
        "Billing Date": "billing_date",
        "Sold-to pt": "payer",
        "Material": "material",
        "Net value": "net_value",
        "Net Price": "net_price",
        "Billed Quantity": "qty",
        "SaTy": "saty",
    })
    df["billing_date"] = pd.to_datetime(df["billing_date"], errors="coerce")
    df = df.dropna(subset=["billing_date"])
    df["payer"] = pd.to_numeric(df["payer"], errors="coerce")
    df["sold_to"] = df["payer"]
    df["net_value"] = pd.to_numeric(df["net_value"], errors="coerce").fillna(0.0)
    df["net_price"] = pd.to_numeric(df.get("net_price"), errors="coerce")
    df["qty"] = pd.to_numeric(df.get("qty"), errors="coerce").fillna(0.0)
    df["billt"] = "UNKNOWN"
    df["saty"] = df["saty"].astype(str).str.strip().str.upper()
    df["material"] = df["material"].astype(str).str.strip().str.upper()
    return df


def read_israel(path: Path) -> pd.DataFrame:
    df = read_std(path)
    df["db"] = df["sold_to"].apply(lambda x: "UTI" if x == 1799 else "UMI")
    return df


def _filter_owned_calendar_years(df: pd.DataFrame, owned_years: set[int] | None) -> pd.DataFrame:
    if not owned_years:
        return df
    cy = df["billing_date"].dt.year
    return df[cy.isin(owned_years)].copy()


def load_all_billing() -> pd.DataFrame:
    frames = []
    # Main files: skip Israel payers (handled by dedicated Israel extract).
    # CY2024-2025.XLSX supersedes CY2025.XLSX — same rule as build_sales_fact_from_cy.py.
    for reader, path, owned_years in [
        (read_std, RAW_SALES_DIR / "CY2023-2024.XLSX", CY_FILE_YEARS["CY2023-2024.XLSX"]),
        (read_std, RAW_SALES_DIR / "CY2024-2025.XLSX", CY_FILE_YEARS["CY2024-2025.XLSX"]),
        (read_std, DATA_ROOT / "sales_2026tillApril.XLSX", CY_FILE_YEARS["sales_2026tillApril.XLSX"]),
    ]:
        if not path.exists():
            print(f"SKIP (missing): {path}")
            continue
        d = reader(path)
        d = d[~d["payer"].isin([1797, 1799])]
        d = _filter_owned_calendar_years(d, owned_years)
        frames.append(d)
    iz = DATA_ROOT / "Sales_israel_1799&_1797.XLSX"
    if iz.exists():
        frames.append(read_israel(iz))
    if not frames:
        raise FileNotFoundError("No billing source files found under 01_data/")
    return pd.concat(frames, ignore_index=True)


def load_pr00() -> pd.DataFrame:
    raw = pd.read_csv(PR00_CSV, dtype=str)
    raw["pn_norm"] = raw["P/N"].map(norm_pn)
    raw["pr00_eur"] = raw["Price (EUR)"].map(parse_eur_price)
    pr = raw.dropna(subset=["pn_norm", "pr00_eur"])
    # if duplicate PN, keep max price (conservative catalogue)
    pr = pr.sort_values("pr00_eur").groupby("pn_norm", as_index=False).last()
    return pr[["pn_norm", "pr00_eur", "Description"]]


def assign_db(row: pd.Series) -> str:
    if pd.notna(row.get("db")):
        return row["db"]
    p = row.get("payer")
    if pd.isna(p):
        return "UNK_nan"
    return PAYER_DB.get(str(int(p)), f"UNK_{int(p)}")


def rebuild_json(df: pd.DataFrame) -> tuple[dict, dict, dict]:
    """Return (gps_billing_clean, transport_excluded, surcharge_stripped_by_db_fy)."""
    df = df.copy()
    df["db"] = df.apply(assign_db, axis=1)
    df["FY"] = df["billing_date"].apply(fy)
    df["json_keep"] = (~df["billt"].isin(EXCL_BILLT)) & (~df["saty"].isin(EXCL_SATY))
    df["is_transport"] = df["material"] == "TRANSPORT"
    df["surcharge_factor"] = df["saty"].map(SURCHARGE).fillna(1.0)

    gps: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    transport: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    stripped: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    kept = df[df["json_keep"] & ~df["is_transport"]].copy()
    kept["net_gps"] = kept["net_value"] / kept["surcharge_factor"]
    tr = df[df["json_keep"] & df["is_transport"]]

    for (db, fy_val), g in kept.groupby(["db", "FY"]):
        gps[db][str(int(fy_val))] = round(float(g["net_gps"].sum()), 2)
        stripped[db][str(int(fy_val))] = round(
            float(g["net_value"].sum() - g["net_gps"].sum()), 2
        )
    for (db, fy_val), v in tr.groupby(["db", "FY"])["net_value"].sum().items():
        transport[db][str(int(fy_val))] = round(float(v), 2)

    # legacy payer bucket → ITUK
    for fy_key in list(gps.get("UNK_146", {})):
        gps["ITUK"][fy_key] = round(
            gps["ITUK"].get(fy_key, 0) + gps["UNK_146"][fy_key], 2
        )
        stripped["ITUK"][fy_key] = round(
            stripped["ITUK"].get(fy_key, 0) + stripped.get("UNK_146", {}).get(fy_key, 0), 2
        )
    gps.pop("UNK_146", None)
    stripped.pop("UNK_146", None)

    return (
        {db: dict(fys) for db, fys in gps.items()},
        {db: dict(fys) for db, fys in transport.items()},
        {db: dict(fys) for db, fys in stripped.items()},
    )


def surcharge_check(df: pd.DataFrame, pr00: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    start = pd.Timestamp("2026-03-19")
    end = pd.Timestamp("2026-03-31")
    sub = df[
        (df["billing_date"] >= start)
        & (df["billing_date"] <= end)
        & (df["saty"].isin(["RUSH", "VOR", "SVOR", "SOR"]))
        & (df["material"] != "TRANSPORT")
        & (~df["billt"].isin(EXCL_BILLT))
        & (~df["saty"].isin(EXCL_SATY))
        & (df["qty"] > 0)
    ].copy()
    sub["pn_norm"] = sub["material"].map(norm_pn)
    sub = sub.merge(pr00, on="pn_norm", how="left")
    sub["billed_unit"] = sub["net_price"]
    miss = sub["billed_unit"].isna() | (sub["billed_unit"] <= 0)
    sub.loc[miss, "billed_unit"] = sub.loc[miss, "net_value"] / sub.loc[miss, "qty"]
    sub = sub[(sub["billed_unit"] > 0) & sub["pr00_eur"].notna()].copy()
    sub["premium_pct"] = sub["billed_unit"] / sub["pr00_eur"] - 1.0
    sub["expected_premium"] = sub["saty"].map(EXPECTED).fillna(0.0)
    sub["premium_gap_pp"] = (sub["premium_pct"] - sub["expected_premium"]) * 100
    sub["revenue_eur"] = sub["net_value"]

    summary: dict = {
        "window": "2026-03-19 to 2026-03-31 (FY2026 PR00 active from 19.03)",
        "pr00_file": str(PR00_CSV.name),
        "lines_total_in_window": int(len(df[(df.billing_date >= start) & (df.billing_date <= end)])),
    }

    raw_rv = df[
        (df["billing_date"] >= start) & (df["billing_date"] <= end)
        & df["saty"].isin(["RUSH", "VOR", "SVOR", "SOR"])
        & (df["material"] != "TRANSPORT")
    ]
    summary["lines_rush_vor_svor_sor"] = int(len(raw_rv))
    summary["lines_with_pr00_match"] = int(len(sub))
    summary["match_rate_pct"] = round(100 * len(sub) / max(len(raw_rv), 1), 1)

    by_saty = []
    for saty, g in sub.groupby("saty"):
        w = (g["revenue_eur"] / g["revenue_eur"].sum()) if g["revenue_eur"].sum() else g["revenue_eur"]
        med = float(g["premium_pct"].median())
        wavg = float((g["premium_pct"] * w).sum()) if w.sum() else float(g["premium_pct"].mean())
        by_saty.append({
            "saty": saty,
            "lines": int(len(g)),
            "revenue_eur": round(float(g["revenue_eur"].sum()), 2),
            "expected_premium_pct": round(EXPECTED.get(saty, 0) * 100, 2),
            "median_billed_vs_pr00_pct": round(med * 100, 2),
            "revenue_weighted_premium_pct": round(wavg * 100, 2),
            "median_gap_vs_expected_pp": round((med - EXPECTED.get(saty, 0)) * 100, 2),
            "pct_lines_within_1pp_of_expected": round(
                100 * (g["premium_gap_pp"].abs() <= 1).mean(), 1
            ),
        })
    summary["by_saty"] = sorted(by_saty, key=lambda x: -x["revenue_eur"])

    # SOR baseline same PN: expedited vs standard where both exist in window
    paired = []
    for pn, g in sub.groupby("pn_norm"):
        if g["saty"].nunique() < 2:
            continue
        sor = g[g["saty"] == "SOR"]["billed_unit"].median()
        if pd.isna(sor) or sor <= 0:
            continue
        for saty in ("RUSH", "VOR", "SVOR"):
            ex = g[g["saty"] == saty]
            if ex.empty:
                continue
            paired.append({
                "pn_norm": pn,
                "saty": saty,
                "sor_unit": sor,
                "expedited_unit_median": float(ex["billed_unit"].median()),
                "implied_premium_pct": round((float(ex["billed_unit"].median()) / sor - 1) * 100, 2),
                "expected_pct": round(EXPECTED[saty] * 100, 2),
            })
    summary["same_pn_sor_vs_expedited_pairs"] = len(paired)
    if paired:
        pdf = pd.DataFrame(paired)
        summary["same_pn_median_implied_premium"] = {
            saty: round(float(g["implied_premium_pct"].median()), 2)
            for saty, g in pdf.groupby("saty")
        }

    return sub, summary


def main() -> None:
    print("Loading raw SAP billing...")
    df = load_all_billing()
    print(f"  {len(df):,} lines  {df.billing_date.min().date()} – {df.billing_date.max().date()}")

    print("Rebuilding gps_billing_clean.json (JSON rules, TRANSPORT + surcharge stripped)...")
    gps, transport, stripped = rebuild_json(df)
    JSON_OUT.write_text(json.dumps(gps, indent=2), encoding="utf-8")
    TRANSPORT_OUT.write_text(json.dumps(transport, indent=2), encoding="utf-8")
    SURCHARGE_STRIPPED_OUT.write_text(json.dumps(stripped, indent=2), encoding="utf-8")
    print(f"  Saved {JSON_OUT}")
    print(f"  Transport excluded: {TRANSPORT_OUT}")
    print(f"  Surcharge stripped: {SURCHARGE_STRIPPED_OUT}")

    t24 = sum(v.get("2024", 0) for v in transport.values())
    t25 = sum(v.get("2025", 0) for v in transport.values())
    t26 = sum(v.get("2026", 0) for v in transport.values())
    s24 = sum(v.get("2024", 0) for v in stripped.values())
    s25 = sum(v.get("2025", 0) for v in stripped.values())
    s26 = sum(v.get("2026", 0) for v in stripped.values())
    print(f"  Transport FY24/25/26: EUR{t24:,.0f} / {t25:,.0f} / {t26:,.0f}")
    print(f"  Surcharge FY24/25/26: EUR{s24:,.0f} / {s25:,.0f} / {s26:,.0f}")

    for db in ("IBX", "ISD"):
        print(f"  {db} FY26 billing: EUR{gps.get(db, {}).get('2026', 0):,.0f}")

    print("\nLoading PR00 price list...")
    pr00 = load_pr00()
    print(f"  {len(pr00):,} parts with EUR price")

    print("\nSurcharge spot-check: 19–31 Mar 2026, RUSH/VOR/SVOR vs PR00...")
    detail, summary = surcharge_check(df, pr00)
    detail.to_csv(SURCHARGE_OUT, index=False)
    SURCHARGE_SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"  Detail: {SURCHARGE_OUT}")
    print(f"  Summary: {SURCHARGE_SUMMARY}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
