"""Process Duncan VIN list + James Marsh unpriced P700. Write JSON summaries."""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX")
VIN_XLSX = ROOT / r"Duncan_VIN_20260723\2026-07-23_VIN_List_23_07_2026.xlsx"
FLEET_XLSX = ROOT / r"Duncan_VIN_20260723\2026-01-15_Fleet_VIN_list_2014_-_2024_study.xlsx"
CBU_XLSX = ROOT / r"Duncan_VIN_20260723\2026-03-17_CBU_Master_Data_-_Appended.xlsx"
ARRIVALS = ROOT / r"Duncan_VIN_20260723\2026-07-17_P700_ITUK_TRUCK_ARRIVALS.xlsx"
ENQ = ROOT / r"Duncan_VIN_20260723\2026-07-27_VIN_engine_cab_enquiries_2020_2026.xlsx"
P700_JUL = ROOT / r"P700_Unpriced_JamesMarsh\2026-07-29_Unpriced_P700_Parts_.xlsx"
P700_JUN = ROOT / r"P700_Unpriced_JamesMarsh\2026-06-02_Unpriced_P700_Parts_.xlsx"
P700_BOOK = ROOT / r"P700_Unpriced_JamesMarsh\2026-06-02_Book1.xlsx"
OUT = ROOT / r"Duncan_VIN_20260723\_process.json"

N75_MODELS = {"N75", "NPR75", "NPR88"}
N_SERIES_RE = re.compile(r"^(N\d+|NLR|NMR|NNR|NPR|NQR|NHR)", re.I)
VIN_MID_RE = re.compile(r"^JAA([A-Z]{2,3})(\d{2})", re.I)


def vin_mid(vin: str) -> str:
    m = VIN_MID_RE.match(str(vin or "").strip().upper())
    if not m:
        return ""
    return f"{m.group(1)}{m.group(2)}"


def is_n75(model: str, vin: str) -> bool:
    m = str(model or "").strip().upper()
    if m in N75_MODELS or m.startswith("N75"):
        return True
    mid = vin_mid(vin)
    return mid in {"NPR75", "NPR88"}


def sheet_preview(path: Path, max_sheets: int = 6, max_rows: int = 8) -> dict:
    wb = load_workbook(path, read_only=True, data_only=True)
    out = {"sheets": wb.sheetnames, "preview": {}}
    for name in wb.sheetnames[:max_sheets]:
        ws = wb[name]
        rows = []
        for i, row in enumerate(ws.iter_rows(max_row=max_rows, values_only=True)):
            rows.append([("" if v is None else str(v)[:80]) for v in (row or [])[:20]])
        out["preview"][name] = {
            "max_row": ws.max_row,
            "max_col": ws.max_column,
            "rows": rows,
        }
    wb.close()
    return out


def process_vin() -> dict:
    df = pd.read_excel(VIN_XLSX, sheet_name=0)
    cols = [str(c).strip() for c in df.columns]
    df.columns = cols
    raw_n = int(len(df))
    # detect columns
    vin_col = next((c for c in cols if c.lower() == "vin"), cols[0])
    model_col = next((c for c in cols if "model" in c.lower() and "code" not in c.lower()), None)
    date_col = next((c for c in cols if "regist" in c.lower() or "date" in c.lower()), None)
    trans_cols = [c for c in cols if any(k in c.lower() for k in ("trans", "gear", "amt", "manual", "auto", "mt", "at"))]
    mile_cols = [c for c in cols if any(k in c.lower() for k in ("mile", "odo", "km", "kmh"))]
    df["_vin"] = df[vin_col].astype(str).str.strip().str.upper()
    df = df[df["_vin"].str.len() >= 11]
    df["_model"] = df[model_col].astype(str).str.strip().str.upper() if model_col else ""
    if date_col:
        df["_reg"] = pd.to_datetime(df[date_col], errors="coerce")
    else:
        df["_reg"] = pd.NaT
    df["_mid"] = df["_vin"].map(vin_mid)
    df["_n75"] = [is_n75(m, v) for m, v in zip(df["_model"], df["_vin"])]
    df["_year"] = df["_reg"].dt.year
    unique = df.drop_duplicates("_vin")
    n75 = unique[unique["_n75"]]
    recent = unique[unique["_reg"] >= pd.Timestamp("2025-01-01")]
    recent_n75 = n75[n75["_reg"] >= pd.Timestamp("2025-01-01")]
    these_days = unique[unique["_reg"] >= pd.Timestamp("2026-01-01")]
    these_n75 = n75[n75["_reg"] >= pd.Timestamp("2026-01-01")]
    last90 = unique[unique["_reg"] >= pd.Timestamp("2026-05-15")]
    last90_n75 = n75[n75["_reg"] >= pd.Timestamp("2026-05-15")]

    by_model = unique["_model"].value_counts().to_dict()
    by_mid = unique["_mid"].value_counts().to_dict()
    by_year = (
        unique.groupby(unique["_year"].fillna(-1).astype(int)).size().to_dict()
    )
    n75_by_year = (
        n75.groupby(n75["_year"].fillna(-1).astype(int)).size().to_dict()
    )
    n75_by_mid = n75["_mid"].value_counts().to_dict()
    n75_by_model = n75["_model"].value_counts().to_dict()

    # monthly 2025-2026
    ym = unique.dropna(subset=["_reg"]).copy()
    ym["_ym"] = ym["_reg"].dt.to_period("M").astype(str)
    monthly = ym.groupby("_ym").size().to_dict()
    n75_monthly = (
        ym[ym["_n75"]].groupby("_ym").size().to_dict()
        if len(ym)
        else {}
    )

    return {
        "path": str(VIN_XLSX),
        "columns": cols,
        "raw_rows": raw_n,
        "valid_vin_rows": int(len(df)),
        "unique_vins": int(len(unique)),
        "dup_extra_rows": int(len(df) - len(unique)),
        "transmission_cols": trans_cols,
        "mileage_cols": mile_cols,
        "n75_unique": int(len(n75)),
        "n75_share_of_unique": round(len(n75) / len(unique), 4) if len(unique) else None,
        "n_series_unique": int(unique["_model"].str.startswith("N").sum()),
        "by_model": {str(k): int(v) for k, v in by_model.items()},
        "by_vin_mid_top": {str(k): int(v) for k, v in list(by_mid.items())[:25]},
        "by_reg_year": {str(k): int(v) for k, v in sorted(by_year.items())},
        "n75_by_reg_year": {str(k): int(v) for k, v in sorted(n75_by_year.items())},
        "n75_by_vin_mid": {str(k): int(v) for k, v in n75_by_mid.items()},
        "n75_by_model": {str(k): int(v) for k, v in n75_by_model.items()},
        "reg_2025plus_unique": int(len(recent)),
        "reg_2025plus_n75": int(len(recent_n75)),
        "reg_2026_unique": int(len(these_days)),
        "reg_2026_n75": int(len(these_n75)),
        "reg_since_20260515_unique": int(len(last90)),
        "reg_since_20260515_n75": int(len(last90_n75)),
        "reg_min": str(unique["_reg"].min()) if unique["_reg"].notna().any() else None,
        "reg_max": str(unique["_reg"].max()) if unique["_reg"].notna().any() else None,
        "monthly_all": monthly,
        "monthly_n75": n75_monthly,
        "engine_pn_filled": int(df.iloc[:, 3].notna().sum()) if df.shape[1] > 3 else 0,
        "cab_wo_filled": int(df.iloc[:, 4].notna().sum()) if df.shape[1] > 4 else 0,
        "cab_w_filled": int(df.iloc[:, 5].notna().sum()) if df.shape[1] > 5 else 0,
        "sample_n75": n75[["_vin", "_model", "_mid", "_reg"]].head(8).astype(str).to_dict("records"),
    }


def process_fleet() -> dict:
    xl = pd.ExcelFile(FLEET_XLSX)
    out = {"path": str(FLEET_XLSX), "sheets": xl.sheet_names, "n35_n75": {}}
    df = pd.read_excel(xl, sheet_name="N35_N75")
    df.columns = [str(c).strip() for c in df.columns]
    vin_col = next(c for c in df.columns if c.lower() == "vin")
    df["_vin"] = df[vin_col].astype(str).str.strip().str.upper()
    df = df[df["_vin"].str.len() >= 11]
    df["_model"] = df["model"].astype(str).str.strip().str.upper() if "model" in df.columns else ""
    df["_reg"] = pd.to_datetime(df.get("registration_date"), errors="coerce")
    df["_mid"] = df["_vin"].map(vin_mid)
    df["_n75"] = [is_n75(m, v) for m, v in zip(df["_model"], df["_vin"])]
    u = df.drop_duplicates("_vin")
    n75 = u[u["_n75"]]
    out["n35_n75"] = {
        "rows": int(len(df)),
        "unique": int(len(u)),
        "n75": int(len(n75)),
        "by_model": {str(k): int(v) for k, v in u["_model"].value_counts().items()},
        "n75_by_year": {
            str(k): int(v)
            for k, v in n75.groupby(n75["_reg"].dt.year.fillna(-1).astype(int)).size().items()
        },
        "reg_min": str(u["_reg"].min()) if u["_reg"].notna().any() else None,
        "reg_max": str(u["_reg"].max()) if u["_reg"].notna().any() else None,
        "cols": list(df.columns),
    }
    return out


def process_cbu() -> dict:
    xl = pd.ExcelFile(CBU_XLSX)
    out = {"path": str(CBU_XLSX), "sheets": xl.sheet_names, "cols": {}, "trans_flags": {}}
    # first sheet only, sample columns
    df = pd.read_excel(xl, sheet_name=0, nrows=5)
    out["cols"][xl.sheet_names[0]] = [str(c) for c in df.columns]
    # scan headers of all sheets for transmission / mileage
    for name in xl.sheet_names[:6]:
        d0 = pd.read_excel(xl, sheet_name=name, nrows=0)
        cols = [str(c) for c in d0.columns]
        hits = [c for c in cols if any(k in c.lower() for k in ("trans", "gear", "manual", "auto", "amt", "mile", "odo"))]
        if hits:
            out["trans_flags"][name] = hits
    return out


def process_arrivals() -> dict:
    prev = sheet_preview(ARRIVALS)
    df = pd.read_excel(ARRIVALS, sheet_name=0)
    df.columns = [str(c).strip() for c in df.columns]
    return {
        "path": str(ARRIVALS),
        "preview": prev,
        "cols": list(df.columns),
        "rows": int(len(df)),
        "head": df.head(20).astype(str).to_dict("records"),
    }


def process_enq() -> dict:
    df = pd.read_excel(ENQ, sheet_name=0)
    df.columns = [str(c).strip() for c in df.columns]
    return {
        "path": str(ENQ),
        "cols": list(df.columns),
        "rows": int(len(df)),
        "head": df.head(12).astype(str).to_dict("records"),
    }


def process_p700(path: Path) -> dict:
    prev = sheet_preview(path, max_sheets=8, max_rows=40)
    xl = pd.ExcelFile(path)
    sheets = {}
    for name in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=name)
        df.columns = [str(c).strip() if str(c) != "nan" else f"col_{i}" for i, c in enumerate(df.columns)]
        # try find PN-like column
        pn_col = None
        for c in df.columns:
            cl = c.lower()
            if any(k in cl for k in ("part", "material", "pn", "item", "sku")):
                pn_col = c
                break
        pns = []
        if pn_col:
            s = df[pn_col].dropna().astype(str).str.strip()
            pns = [x for x in s.tolist() if re.search(r"\d{7,}", x)]
        sheets[name] = {
            "rows": int(len(df)),
            "cols": list(df.columns),
            "pn_col": pn_col,
            "pns": pns,
            "records": df.astype(str).to_dict("records")[:80],
        }
    return {"path": str(path), "preview": prev, "sheets": sheets}


def duncan_quotes() -> list:
    meta = json.loads((ROOT / r"Duncan_VIN_20260723\_outlook_pull.json").read_text(encoding="utf-8"))
    slim = []
    for q in meta.get("duncan_quotes", []):
        snip = q.get("snip") or ""
        keep = False
        for key in ("47%", "47 percent", "6-8", "6 to 8", "6 – 8", "transmission", "manual"):
            if key.lower() in snip.lower() or key.lower() in (q.get("subj") or "").lower():
                keep = True
        # drop hotel noise
        if "hotel" in (q.get("subj") or "").lower():
            keep = False
        if not keep:
            continue
        slim.append(
            {
                "when": q.get("when"),
                "subj": q.get("subj"),
                "hits": q.get("hits"),
                "snip": snip[:3500],
            }
        )
    return slim


def main() -> None:
    data = {
        "ran": datetime.now().isoformat(timespec="seconds"),
        "vin_jul23": process_vin(),
        "fleet_jan15": process_fleet(),
        "cbu_mar17": process_cbu(),
        "p700_arrivals": process_arrivals(),
        "enq_jul27": process_enq(),
        "p700_jul29": process_p700(P700_JUL),
        "p700_jun02": process_p700(P700_JUN),
        "p700_book": process_p700(P700_BOOK),
        "duncan_quotes": duncan_quotes(),
    }
    OUT.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    print("WROTE", OUT)
    v = data["vin_jul23"]
    print("VIN unique", v["unique_vins"], "N75", v["n75_unique"], "2026 N75", v["reg_2026_n75"])
    print("P700 jul rows", data["p700_jul29"]["sheets"])


if __name__ == "__main__":
    main()
