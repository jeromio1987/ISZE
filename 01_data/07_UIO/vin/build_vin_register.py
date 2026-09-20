"""
Build unified JP VIN register (SKD + CBU) — separate project, not wired into PRISM.

Input:  01_data/07_UIO/vin/raw/VIN_list_JP_*.xlsx
Output: VIN_register.parquet (+ slim CSV), model_dimension.csv, build summary JSON

Does NOT invent AT/MT. Europe JAA VINs encode series/GVW/WB/serial — not transmission.
Transmission stays unknown until an ISZJ model→gearbox map is supplied.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RAW_DIR = HERE / "raw"
ASOF = date(2026, 7, 27)  # rolling 60m anchor (session date)
ROLLING_MONTHS = 60

# Soft labels only — not PRISM DB keys. ITUK/UTI out of scope for this extract.
DB_LABEL = {
    "IE": "Ireland",
    "PT": "Portugal",
    "DE": "Germany",
    "BE": "Belgium",
    "MT": "Malta",
    "CY": "Cyprus",
    "GR": "Greece",
}

# Series → nominal GVW in tonnes. The chassis number is NOT a tonnage: an FRR90 is an 11–12 t
# truck and an FSR90 is 13.5 t, but reading "90" as 9.0 t made both look like 9-tonners and made
# the 3,238-truck register look like 26,689 t when it is really 19,687 t (V20_SPEC §Problem 7).
#
# NL/NM/NN/NP and FR/FS are ISZJ series prefixes. Where a range is quoted (FRR 11–12 t) the lower
# bound is used so the figure is not overstated.
SERIES_GVW_T = {
    "NLR": 3.5,    # N35 Grafter
    "NKR": 3.5,    # older N35 designation
    "NMR": 5.5,
    "NNR": 6.5,
    "NPR": 7.5,    # NPR75 — the one case the old numeric map got right
    "NQR": 7.5,
    "FRR": 11.0,   # FRR90, 11–12 t
    "FSR": 13.5,   # FSR90, 13.5 t
}

# Numeric suffix → nominal GVW. Kept ONLY to record what the code says, never to set gvw_t.
GVW_FROM_CODE = {
    "75": 7.5,
    "85": 8.5,
    "87": 8.7,
    "88": 8.8,
    "90": 9.0,
}

SCOPE_EXCLUDE_DB = {"ITUK", "UK", "UTI", "UMI"}  # this extract is "all other CV DBs"


def _clean_col(c: str) -> str:
    return re.sub(r"\s+", " ", str(c).replace("\n", " ")).strip().upper()


def _latest_raw() -> Path:
    files = sorted(RAW_DIR.glob("VIN_list_JP_*.xlsx"))
    if not files:
        raise FileNotFoundError(f"No VIN_list_JP_*.xlsx under {RAW_DIR}")
    return files[-1]


def _parse_db(raw) -> tuple[str, str | None, str | None]:
    """Return (db_primary, db_origin, db_destination). Handles 'PT to BE'."""
    s = str(raw or "").strip()
    if not s or s.lower() == "nan":
        return "", None, None
    m = re.match(r"^([A-Za-z]+)\s+to\s+([A-Za-z]+)$", s, re.I)
    if m:
        origin, dest = m.group(1).upper(), m.group(2).upper()
        return dest, origin, dest
    return s.upper(), None, None


def _parse_model(name: str) -> dict:
    s = str(name or "").strip()
    out = {
        "iszj_model_name": s,
        "series": None,
        "gvw_code": None,
        "gvw_t": None,
        "gvw_t_source": None,
        "hand_code": None,  # L≈LHD, U≈RHD (ISZJ convention on export names)
        "model_suffix": None,
        "wheelbase_code": None,
    }
    if not s:
        return out
    # e.g. NPR75L-HL5VAYE / FRR90SL-HAEH / NLR87AL-ED5LAYE
    m = re.match(
        r"^([A-Z]{2,3})(\d{2,3})([A-Z]{0,3})(?:-(.+))?$",
        s.replace(" ", ""),
        re.I,
    )
    if not m:
        return out
    series, gvw, hand, suffix = m.group(1).upper(), m.group(2), m.group(3).upper(), m.group(4)
    out["series"] = series
    out["gvw_code"] = gvw
    # Tonnage comes from the series, not the number. Fall back to the numeric code only when the
    # series is unknown, and say so, so a bad decode is visible instead of silent.
    if series in SERIES_GVW_T:
        out["gvw_t"] = SERIES_GVW_T[series]
        out["gvw_t_source"] = "series"
    else:
        out["gvw_t"] = GVW_FROM_CODE.get(gvw)
        out["gvw_t_source"] = "numeric_code" if out["gvw_t"] else None
    # Prefer single trailing L/U as hand; FRR90SL → hand SL kept as cab pack, last char if L/U
    if hand in {"L", "U"}:
        out["hand_code"] = hand
    elif hand.endswith(("L", "U")) and len(hand) <= 3:
        out["hand_code"] = hand[-1]
        out["cab_pack"] = hand
    elif hand:
        out["cab_pack"] = hand
    if suffix:
        suf = suffix.strip().upper()
        out["model_suffix"] = suf
        out["wheelbase_code"] = suf[0] if suf else None
    return out


def _parse_vin(vin: str) -> dict:
    v = str(vin or "").strip().upper()
    out = {
        "vin": v,
        "vin_ok_len": len(v) == 17,
        "vin_wmi": v[:3] if len(v) >= 3 else None,
        "vin_series_nf": None,
        "vin_model_embed": None,
        "vin_wb_code": None,
        "vin_plant_digit": None,
        "vin_serial": None,
    }
    if len(v) != 17:
        return out
    # Europe JP export pattern observed: JAA/JAL + N/F + series letter + R + GVW + WB + … + 7 + serial
    out["vin_series_nf"] = v[3]  # N or F
    out["vin_model_embed"] = v[3:9]  # e.g. NPR75 / FRR90 / NLR88
    out["vin_wb_code"] = v[8]
    out["vin_plant_digit"] = v[10]
    out["vin_serial"] = v[11:]
    return out


def _read_sheet(path: Path, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet, dtype=object)
    df.columns = [_clean_col(c) for c in df.columns]
    rename = {
        "DB": "db_raw",
        "N OR F": "nf",
        "SKD PROD. MONTH": "prod_month",
        "CBU PROD. MONTH": "prod_month",
        "ISZJ MODEL NAME": "iszj_model_name",
        "MODEL CODE": "model_code",
        "LOT": "lot",
        "VIN": "vin",
        "ENGINE NUMBER": "engine_number",
        "KEY NUMBER": "key_number",
        "IMB CODE": "imb_code",
        "ASSEMBLY DATE ACTUAL": "assembly_date",
        "SHIPMENT DATE": "shipment_date",
        "INVOICE MONTH": "invoice_month",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    keep = [
        "db_raw",
        "nf",
        "prod_month",
        "iszj_model_name",
        "model_code",
        "lot",
        "vin",
        "engine_number",
        "key_number",
        "imb_code",
        "assembly_date",
        "shipment_date",
        "invoice_month",
    ]
    for c in keep:
        if c not in df.columns:
            df[c] = None
    df = df[keep].copy()
    df["build_type"] = sheet.upper()
    # Stable string/object cols (mixed int/str from Excel breaks parquet)
    for c in (
        "db_raw",
        "nf",
        "iszj_model_name",
        "model_code",
        "lot",
        "vin",
        "engine_number",
        "key_number",
        "imb_code",
    ):
        df[c] = df[c].map(lambda x: None if pd.isna(x) else str(x).strip())
    # Drop fully empty rows
    df = df[df["vin"].notna() & (df["vin"].astype(str).str.strip() != "") & (df["vin"] != "None")]
    return df


def _to_month_start(s) -> pd.Series:
    return pd.to_datetime(s, errors="coerce").dt.to_period("M").dt.to_timestamp()


def build(asof: date = ASOF) -> pd.DataFrame:
    raw = _latest_raw()
    parts = [_read_sheet(raw, "SKD"), _read_sheet(raw, "CBU")]
    df = pd.concat(parts, ignore_index=True)

    parsed_db = df["db_raw"].map(_parse_db)
    df["db_code"] = [p[0] for p in parsed_db]
    df["db_origin"] = [p[1] for p in parsed_db]
    df["db_destination"] = [p[2] for p in parsed_db]
    df["db_label"] = df["db_code"].map(DB_LABEL)
    df["reexport_flag"] = df["db_origin"].notna()

    model_bits = df["iszj_model_name"].map(_parse_model).apply(pd.Series)
    vin_bits = df["vin"].map(_parse_vin).apply(pd.Series)
    # Avoid duplicate iszj_model_name / vin columns from expand
    for c in ("iszj_model_name", "vin"):
        if c in model_bits.columns:
            model_bits = model_bits.drop(columns=[c])
        if c in vin_bits.columns:
            vin_bits = vin_bits.drop(columns=[c])
    df = pd.concat([df, model_bits, vin_bits], axis=1)

    for c in ("prod_month", "assembly_date", "shipment_date", "invoice_month"):
        df[c] = pd.to_datetime(df[c], errors="coerce")

    # Cohort date: prefer invoice_month, else shipment, else assembly
    df["cohort_date"] = df["invoice_month"].fillna(df["shipment_date"]).fillna(df["assembly_date"])
    df["invoice_year"] = df["invoice_month"].dt.year
    df["asof_date"] = pd.Timestamp(asof)
    start = (pd.Timestamp(asof) - pd.DateOffset(months=ROLLING_MONTHS)).normalize()
    df["rolling_60m_start"] = start
    df["in_pms_rolling_60m"] = df["cohort_date"].notna() & (df["cohort_date"] >= start)

    df["scope_cv_ex_ituk_uti"] = ~df["db_code"].isin(SCOPE_EXCLUDE_DB)
    # Transmission: deliberately unknown — do not invent from VIN/suffix
    df["transmission"] = "unknown"
    df["transmission_source"] = "none"
    df["transmission_confidence"] = "none"

    df["source_file"] = raw.name
    df["built_at"] = datetime.now().isoformat(timespec="seconds")

    # Column order
    front = [
        "vin",
        "vin_ok_len",
        "build_type",
        "db_raw",
        "db_code",
        "db_label",
        "db_origin",
        "db_destination",
        "reexport_flag",
        "nf",
        "iszj_model_name",
        "model_code",
        "series",
        "gvw_code",
        "gvw_t",
        "gvw_t_source",
        "hand_code",
        "model_suffix",
        "wheelbase_code",
        "transmission",
        "transmission_source",
        "transmission_confidence",
        "engine_number",
        "key_number",
        "imb_code",
        "lot",
        "prod_month",
        "assembly_date",
        "shipment_date",
        "invoice_month",
        "invoice_year",
        "cohort_date",
        "asof_date",
        "rolling_60m_start",
        "in_pms_rolling_60m",
        "scope_cv_ex_ituk_uti",
        "vin_wmi",
        "vin_series_nf",
        "vin_model_embed",
        "vin_wb_code",
        "vin_plant_digit",
        "vin_serial",
        "source_file",
        "built_at",
    ]
    extra = [c for c in df.columns if c not in front]
    return df[front + extra]


def main() -> None:
    df = build()
    out_parquet = HERE / "VIN_register.parquet"
    out_csv = HERE / "VIN_register.csv"
    out_models = HERE / "model_dimension.csv"
    out_sum = HERE / "VIN_register_summary.json"

    df.to_parquet(out_parquet, index=False)
    df.to_csv(out_csv, index=False)

    models = (
        df.groupby(
            ["iszj_model_name", "series", "gvw_code", "gvw_t", "hand_code", "model_suffix", "transmission"],
            dropna=False,
        )
        .size()
        .reset_index(name="vin_count")
        .sort_values(["series", "iszj_model_name"])
    )
    models.to_csv(out_models, index=False)

    summary = {
        "asof_date": str(ASOF),
        "rolling_months": ROLLING_MONTHS,
        "rolling_60m_start": str(df["rolling_60m_start"].iloc[0].date()),
        "source_file": str(df["source_file"].iloc[0]),
        "n_vins": int(len(df)),
        "n_vins_ok_len": int(df["vin_ok_len"].sum()),
        "n_skd": int((df["build_type"] == "SKD").sum()),
        "n_cbu": int((df["build_type"] == "CBU").sum()),
        "n_in_pms_rolling_60m": int(df["in_pms_rolling_60m"].sum()),
        "n_scope_ex_ituk_uti": int(df["scope_cv_ex_ituk_uti"].sum()),
        "by_db": df["db_code"].value_counts(dropna=False).to_dict(),
        "by_series": df["series"].value_counts(dropna=False).to_dict(),
        "by_nf": df["nf"].value_counts(dropna=False).to_dict(),
        "by_invoice_year": {
            str(int(k)) if pd.notna(k) else "null": int(v)
            for k, v in df["invoice_year"].value_counts(dropna=False).items()
        },
        "transmission_status": "all unknown — Europe JAA VIN + model suffix not validated for AT/MT/AMT",
        "outputs": {
            "parquet": str(out_parquet),
            "csv": str(out_csv),
            "model_dimension": str(out_models),
        },
    }
    out_sum.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
