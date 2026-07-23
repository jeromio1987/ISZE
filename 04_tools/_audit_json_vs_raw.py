"""
Reconcile gps_billing_clean.json against raw SAP sales (same files as gps_full_run_v2).

Layers per DB × FY:
  1. raw_gross          — all lines, no filter
  2. raw_json_rules     — BillT + SaTy CR/RE only (JSON builder logic)
  3. transport_in_json — TRANSPORT material still inside layer 2
  4. stored_json        — gps_billing_clean.json on disk
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS))
from _shared.paths import DATA_ROOT, DERIVED_DIR, RAW_SALES_DIR  # noqa: E402

JSON_PATH = DERIVED_DIR / "gps_billing_clean.json"
OUT_CSV = DERIVED_DIR / "gps_json_vs_raw_audit.csv"

EXCL_BILLT = {"S1", "G2", "RE", "ZFD", "S2"}
EXCL_SATY = {"CR", "RE"}
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
    "1797": "UMI", "1799": "UTI",
}


def fy(dt) -> int:
    return dt.year + 1 if dt.month >= 4 else dt.year


def _dedupe_columns(cols: list) -> list:
    seen: dict[str, int] = {}
    out = []
    for c in cols:
        n = seen.get(c, 0)
        out.append(c if n == 0 else f"{c}_{n}")
        seen[c] = n + 1
    return out


def read_std(path: Path, label: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Sheet1", header=0)
    df.columns = _dedupe_columns(list(df.columns))
    df = df.rename(columns={
        "Billing Date": "billing_date",
        "BillT": "billt",
        "Payer": "payer",
        "Payer_1": "db_name",
        "Sold-to pt": "sold_to",
        "Material": "material_num",
        "Net value": "net_value",
        "SaTy": "saty",
    })
    df["billing_date"] = pd.to_datetime(df["billing_date"], errors="coerce")
    df = df.dropna(subset=["billing_date"])
    df["payer"] = pd.to_numeric(df["payer"], errors="coerce")
    df["sold_to"] = pd.to_numeric(df.get("sold_to"), errors="coerce")
    df["net_value"] = pd.to_numeric(df["net_value"], errors="coerce").fillna(0.0)
    df["billt"] = df["billt"].astype(str).str.strip().str.upper()
    df["saty"] = df["saty"].astype(str).str.strip().str.upper()
    df["material_num"] = df["material_num"].astype(str).str.strip().str.upper()
    df["source"] = label
    return df


def read_cy2025(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Sheet1", header=0)
    df.columns = _dedupe_columns(list(df.columns))
    df = df.rename(columns={
        "Billing Date": "billing_date",
        "Sold-to pt": "payer",
        "DB": "db_name",
        "Material": "material_num",
        "Net value": "net_value",
        "SaTy": "saty",
    })
    df["billing_date"] = pd.to_datetime(df["billing_date"], errors="coerce")
    df = df.dropna(subset=["billing_date"])
    df["payer"] = pd.to_numeric(df["payer"], errors="coerce")
    df["sold_to"] = df["payer"]
    df["net_value"] = pd.to_numeric(df["net_value"], errors="coerce").fillna(0.0)
    df["billt"] = "UNKNOWN"
    df["saty"] = df["saty"].astype(str).str.strip().str.upper()
    df["material_num"] = df["material_num"].astype(str).str.strip().str.upper()
    df["source"] = "CY2025"
    return df


def canon_db(row: pd.Series) -> str:
    if pd.notna(row.get("db")):
        return str(row["db"])
    p = row["payer"]
    if pd.isna(p):
        return "UNK_nan"
    key = str(int(p))
    return PAYER_DB.get(key, f"UNK_{key}")


def bucket(df: pd.DataFrame, mask: pd.Series) -> dict[tuple[str, int], float]:
    sub = df.loc[mask].copy()
    sub["db"] = sub.apply(canon_db, axis=1)
    sub["FY"] = sub["billing_date"].apply(fy)
    out: dict[tuple[str, int], float] = defaultdict(float)
    for (db, fy_val), val in sub.groupby(["db", "FY"])["net_value"].sum().items():
        out[(db, int(fy_val))] += float(val)
    return out


def bucket_gps(df: pd.DataFrame, mask: pd.Series) -> dict[tuple[str, int], float]:
    sub = df.loc[mask].copy()
    sub["db"] = sub.apply(canon_db, axis=1)
    sub["FY"] = sub["billing_date"].apply(fy)
    sub["net_gps"] = sub["net_value"] / sub["saty"].map(SURCHARGE).fillna(1.0)
    out: dict[tuple[str, int], float] = defaultdict(float)
    for (db, fy_val), val in sub.groupby(["db", "FY"])["net_gps"].sum().items():
        out[(db, int(fy_val))] += float(val)
    for fy_val in {k[1] for k in out if k[0] == "UNK_146"}:
        out[("ITUK", fy_val)] = out.get(("ITUK", fy_val), 0) + out.get(("UNK_146", fy_val), 0)
        out.pop(("UNK_146", fy_val), None)
    return out


def load_stored_json() -> dict:
    raw = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    # merge UNK_146 → ITUK (toggle convention)
    for y, v in raw.get("UNK_146", {}).items():
        raw.setdefault("ITUK", {})[y] = raw.get("ITUK", {}).get(y, 0) + v
    return raw


def main() -> None:
    stored = load_stored_json()

    df = pd.concat([
        read_std(RAW_SALES_DIR / "CY2023-2024.XLSX", "CY2023-2024"),
        read_cy2025(RAW_SALES_DIR / "CY2025.XLSX"),
        read_std(DATA_ROOT / "sales_2026tillApril.XLSX", "sales_2026tillApril"),
    ], ignore_index=True)
    df = df[~df["payer"].isin([1797, 1799])]
    iz = DATA_ROOT / "Sales_israel_1799&_1797.XLSX"
    if iz.exists():
        from rebuild_gps_billing_and_surcharge_check import read_israel  # noqa: WPS433
        df = pd.concat([df, read_israel(iz)], ignore_index=True)

    df["is_transport"] = df["material_num"] == "TRANSPORT"
    df["json_keep"] = (~df["billt"].isin(EXCL_BILLT)) & (~df["saty"].isin(EXCL_SATY))

    gps_mask = df["json_keep"] & ~df["is_transport"]
    gross = bucket(df, pd.Series(True, index=df.index))
    json_kept = bucket(df, df["json_keep"])
    no_tr = bucket_gps(df, gps_mask)

    print("RAW files combined:", len(df), "rows")
    print("Date range:", df.billing_date.min().date(), "–", df.billing_date.max().date())
    print()

    # Network FY24-26
    print("=== NETWORK: raw → JSON rules → stored JSON (FY24–26) ===")
    hdr = f"{'FY':<5} {'Raw gross':>12} {'Raw+JSON':>12} {'-Transport':>12} {'Stored':>12} {'RawJSON-Stored':>14} {'Transport':>10}"
    print(hdr)
    for fy_val in (2024, 2025, 2026):
        g = sum(v for (_, y), v in gross.items() if y == fy_val)
        j = sum(v for (_, y), v in json_kept.items() if y == fy_val)
        t = sum(v for (_, y), v in no_tr.items() if y == fy_val)
        s = sum(float(stored.get(db, {}).get(str(fy_val), 0) or 0) for db in stored)
        tr = j - t
        print(f"FY{fy_val} {g:12,.0f} {j:12,.0f} {t:12,.0f} {s:12,.0f} {s-t:12,.0f}")

    tr_all = sum(json_kept.get(k, 0) - no_tr.get(k, 0) for k in json_kept if k[1] in (2024, 2025, 2026))
    tr_lines = df[df["is_transport"] & df["json_keep"]]
    print(f"\nTRANSPORT inside JSON rules (FY24–26): EUR{tr_all:,.0f} across {len(tr_lines):,} lines")
    print("SaTy on TRANSPORT lines:", df.loc[df.is_transport, "saty"].value_counts().head(5).to_dict())

    GPS_DBS = [
        "ITUK", "IUK", "UTI", "UMI", "ISD", "IBX", "Imotors", "Sverige", "Norway",
        "Ireland", "RSA", "AutoWallis", "ROM Auto", "Nordic FI", "Danmark",
        "GasanZammit", "Loutsios", "BL Iceland",
    ]

    rows = []
    print("\n=== PER DB: stored JSON vs raw (transport + surcharge stripped) ===")
    print(f"{'DB':<11} {'FY':<4} {'Stored':>11} {'Expected':>11} {'Diff':>10} {'Transport':>10}")
    for db in GPS_DBS:
        for fy_val in (2024, 2025, 2026):
            s = float(stored.get(db, {}).get(str(fy_val), 0) or 0)
            exp = no_tr.get((db, fy_val), 0.0)
            tr = json_kept.get((db, fy_val), 0.0) - exp
            diff = s - exp
            rows.append({
                "db": db, "fy": fy_val,
                "raw_gross": gross.get((db, fy_val), 0),
                "raw_json_rules": json_kept.get((db, fy_val), 0.0),
                "stored_json": s,
                "diff_rebuild_minus_stored": exp - s,
                "transport_in_json": tr,
                "raw_minus_transport": exp,
            })
            if abs(diff) > 1000:
                print(f"{db:<11} {fy_val} {s:11,.0f} {exp:11,.0f} {diff:10,.0f} {tr:10,.0f}")

    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    # Match rate
    close = sum(1 for r in rows if abs(r["diff_rebuild_minus_stored"]) <= 5)
    print(f"\nDB×FY cells within EUR5: {close}/{len(rows)}")
    print(f"CSV: {OUT_CSV}")

    # FY25 waterfall on raw
    fy_val = 2025
    sub = df[df["billing_date"].apply(fy) == fy_val]
    print(f"\n=== FY{fy_val} waterfall (all DBs, raw file) ===")
    g0 = sub["net_value"].sum()
    g1 = sub.loc[~sub["billt"].isin(EXCL_BILLT), "net_value"].sum()
    g2 = sub.loc[sub["json_keep"], "net_value"].sum()
    tr = sub.loc[sub["json_keep"] & sub["is_transport"], "net_value"].sum()
    s = sum(float(stored.get(db, {}).get(str(fy_val), 0) or 0) for db in stored)
    print(f"  Raw gross:           EUR{g0:,.0f}")
    print(f"  After BillT filter:  EUR{g1:,.0f}  (−{g0-g1:,.0f})")
    print(f"  After SaTy CR/RE:    EUR{g2:,.0f}  (= raw JSON rules)")
    print(f"  TRANSPORT in JSON:   EUR{tr:,.0f}")
    print(f"  Stored JSON total:   EUR{s:,.0f}")
    print(f"  RawJSON − Stored:    EUR{g2-s:,.0f}")


if __name__ == "__main__":
    main()
