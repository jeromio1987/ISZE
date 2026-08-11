"""Build efficient pricing enquiry tables from 01_Pricing/_raw.

Canonical outputs (01_data/00_derived/):
  pricing_list_pn.parquet         — Price file 2026 calc book: class, BP, source, FOB, SP
  pricing_revision_cd.parquet     — IML PRICE CD: current vs new BP/class
  pricing_sim_pr00_l12m.parquet   — PR00 simulation L12M qty weights
  pricing_pr00_ie40.parquet       — IE40 PR00 list EUR (newest export)
  pricing_zpr1.parquet            — ZPR1/CIS customer × PN list prices
  pricing_zpr1_customers.parquet  — customer code dim
  pricing_pn_enquiry.parquet      — joined Spec enquiry view

Read: 01_data/01_Pricing/PRICING_DATA.md
"""
from __future__ import annotations

import re
from pathlib import Path

import openpyxl
import pandas as pd

ISZE = Path(__file__).resolve().parents[2]
RAW = ISZE / "01_data" / "01_Pricing" / "_raw"
DERIVED = ISZE / "01_data" / "00_derived"
CLASS_OK = set("CDFJMPVTYXZBEWG")

# Spec Layer 4 focus payers (Israel + large CIS rows in EXPORT_ZPR1)
ZPR1_KEY_CUSTOMERS = {
    "0000001797": "UMI",
    "0000001799": "UTI",
    "0000002222": "ISUZU_RUS_2222",
    "0000002295": "ISUZU_RUS_2295",
    "0000002372": "ZPR1_2372",
    "0000002733": "CBC_2733",
    "0000002734": "CBC_2734",
}


def norm_pn(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        digits = str(int(value))
    else:
        digits = re.sub(r"\D", "", str(value).strip())
    if len(digits) < 8:
        return None
    return digits.zfill(10)


def norm_customer_code(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    digits = re.sub(r"\D", "", str(value).strip())
    if not digits:
        return None
    return digits.zfill(10)


def parse_eur(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return pd.NA
    if isinstance(value, str):
        value = value.strip().replace(",", ".")
        if not value:
            return pd.NA
    return pd.to_numeric(value, errors="coerce")


def map_cd_class(raw) -> str | None:
    """PRICE CD uses 2-char codes (XC, XD…); pricing formula needs 1-letter class."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    s = str(raw).strip().upper()
    if not s or s in {"NAN", "NONE"}:
        return None
    if len(s) == 1 and s in CLASS_OK:
        return s
    if s[-1] in CLASS_OK:
        return s[-1]
    return s[0] if s[0] in CLASS_OK else None


def _sheet_rows(path: Path, sheet=0):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    name = wb.sheetnames[sheet] if isinstance(sheet, int) else sheet
    ws = wb[name]
    it = ws.iter_rows(values_only=True)
    header = [str(x).strip() if x is not None else "" for x in next(it)]
    rows = list(it)
    wb.close()
    return header, rows


def _col(header: list[str], *names: str) -> int:
    lower = {h.lower(): i for i, h in enumerate(header)}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    raise KeyError(f"None of {names} in header {header}")


def build_price_file() -> Path:
    path = RAW / "Price_file_2026_full.xlsx"
    header, rows = _sheet_rows(path)
    recs = []
    for r in rows:
        pn = norm_pn(r[0])
        if not pn:
            continue
        newest = norm_pn(r[1]) or pn
        cls = str(r[4]).strip().upper() if r[4] is not None else ""
        if cls in {"NAN", "NONE", "#N/A"}:
            cls = ""
        src = str(r[5]).strip().upper() if r[5] is not None else ""
        if src in {"NAN", "NONE", "#N/A"}:
            src = ""
        recs.append(
            {
                "part_number": pn,
                "newest_pn": newest,
                "description": ("" if r[2] is None else str(r[2]).strip()),
                "bp_jpy": pd.to_numeric(r[3], errors="coerce"),
                "price_class": cls or None,
                "source": src or None,
                "fob_eur": pd.to_numeric(r[6], errors="coerce"),
                "sp_eur": pd.to_numeric(r[7], errors="coerce"),
                "gm": pd.to_numeric(r[8], errors="coerce"),
                "is_superseded_row": pn != newest,
                "source_file": path.name,
            }
        )
    df = pd.DataFrame.from_records(recs)
    out = DERIVED / "pricing_list_pn.parquet"
    df.to_parquet(out, index=False)
    df.to_csv(DERIVED / "pricing_list_pn.csv", index=False)
    print(f"pricing_list_pn: {len(df):,} rows → {out.name}")
    return out


def build_revision_cd() -> Path:
    path = RAW / "CY2026_Price_Revision_PRICE_CD.xlsx"
    header, rows = _sheet_rows(path)
    recs = []
    for r in rows:
        pn = norm_pn(r[0])
        if not pn:
            continue
        new_cls_raw = None if r[3] is None else str(r[3]).strip().upper()
        cur_cls_raw = None if r[5] is None else str(r[5]).strip().upper()
        bp_new = pd.to_numeric(r[2], errors="coerce")
        bp_cur = pd.to_numeric(r[4], errors="coerce")
        recs.append(
            {
                "part_number": pn,
                "description": ("" if r[1] is None else str(r[1]).strip()),
                "bp_jpy_new": bp_new,
                "bp_jpy_current": bp_cur,
                "bp_jpy_delta": (bp_new - bp_cur)
                if pd.notna(bp_new) and pd.notna(bp_cur)
                else pd.NA,
                "part_class_new_raw": new_cls_raw,
                "part_class_current_raw": cur_cls_raw,
                "price_class_new": map_cd_class(new_cls_raw),
                "price_class_current": map_cd_class(cur_cls_raw),
                "class_changed": bool(new_cls_raw != cur_cls_raw),
                "bp_changed": bool(
                    pd.notna(bp_new) and pd.notna(bp_cur) and bp_new != bp_cur
                ),
                "eple": r[6],
                "figkey": r[7],
                "example_model": ("" if r[8] is None else str(r[8]).strip()),
                "source_file": path.name,
                "source_sheet": "PRICE CD 250912",
            }
        )
    df = pd.DataFrame.from_records(recs)
    out = DERIVED / "pricing_revision_cd.parquet"
    df.to_parquet(out, index=False)
    changed = df[df["bp_changed"] | df["class_changed"]]
    changed.to_csv(DERIVED / "pricing_revision_cd_changed.csv", index=False)
    print(
        f"pricing_revision_cd: {len(df):,} rows "
        f"(changed {len(changed):,}) → {out.name}"
    )
    return out


def build_sim_pr00() -> Path:
    path = RAW / "pricing_simulation_2026_5pct.xlsx"
    header, rows = _sheet_rows(path, "PR00 simulation")
    recs = []
    for r in rows:
        pn = norm_pn(r[0])
        if not pn:
            continue
        cls = str(r[4]).strip().upper() if r[4] is not None else ""
        if cls in {"", "0", "NAN", "NONE"}:
            cls = None
        src = str(r[3]).strip().upper() if r[3] is not None else ""
        if src in {"", "NAN", "NONE", "#N/A"}:
            src = None
        recs.append(
            {
                "part_number": pn,
                "qty_l12m": pd.to_numeric(r[1], errors="coerce"),
                "description": ("" if r[2] is None else str(r[2]).strip()),
                "source": src,
                "price_class": cls,
                "bp_jpy_2025": pd.to_numeric(r[5], errors="coerce"),
                "bp_jpy_2026": pd.to_numeric(r[6], errors="coerce"),
                "sp_eur_2025": pd.to_numeric(r[13], errors="coerce"),
                "sp_eur_2026": pd.to_numeric(r[14], errors="coerce"),
                "source_file": path.name,
                "market": "PR00",
            }
        )
    df = pd.DataFrame.from_records(recs)
    out = DERIVED / "pricing_sim_pr00_l12m.parquet"
    df.to_parquet(out, index=False)
    df.to_csv(DERIVED / "pricing_sim_pr00_l12m.csv", index=False)
    print(f"pricing_sim_pr00_l12m: {len(df):,} rows → {out.name}")
    return out


def build_pr00_ie40() -> Path:
    """Newest IE40 PR00 list EUR export (Price Condition Type = PR00)."""
    candidates = [
        RAW / "Price_file_PR00_IE40_20260810.xlsx",
        RAW / "parts_master_20260528.xlsx",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        raise FileNotFoundError("No IE40 PR00 / parts master file in _raw")

    header, rows = _sheet_rows(path)
    i_pn = _col(header, "P/N")
    i_newest = _col(header, "Newest P/N")
    i_desc = _col(header, "Description")
    i_org = _col(header, "Sales Org")
    i_coo = _col(header, "Country of Origin")
    i_price = _col(header, "Price")
    i_cur = _col(header, "Currency") if "Currency" in header else None
    i_vs = _col(header, "Valid Start") if "Valid Start" in header else None
    i_ve = _col(header, "Valid End") if "Valid End" in header else None
    i_fig = _col(header, "Fig No.") if "Fig No." in header else None
    i_key = _col(header, "Key No.") if "Key No." in header else None
    i_cond = (
        _col(header, "Price Condition Type")
        if "Price Condition Type" in header
        else None
    )

    recs = []
    for r in rows:
        pn = norm_pn(r[i_pn])
        if not pn:
            continue
        newest = norm_pn(r[i_newest]) or pn
        cond = ""
        if i_cond is not None and r[i_cond] is not None:
            cond = str(r[i_cond]).strip().upper()
        recs.append(
            {
                "sales_org": ("" if r[i_org] is None else str(r[i_org]).strip()),
                "part_number": pn,
                "newest_pn": newest,
                "description": ("" if r[i_desc] is None else str(r[i_desc]).strip()),
                "price_condition": cond or "PR00",
                "sp_eur": parse_eur(r[i_price]),
                "currency": (
                    ""
                    if i_cur is None or r[i_cur] is None
                    else str(r[i_cur]).strip()
                ),
                "valid_start": None if i_vs is None else r[i_vs],
                "valid_end": None if i_ve is None else r[i_ve],
                "country_of_origin": (
                    "" if r[i_coo] is None else str(r[i_coo]).strip()
                ),
                "fig_no": None if i_fig is None else r[i_fig],
                "key_no": None if i_key is None else r[i_key],
                "is_superseded_row": pn != newest,
                "source_file": path.name,
            }
        )
    df = pd.DataFrame.from_records(recs)
    out = DERIVED / "pricing_pr00_ie40.parquet"
    df.to_parquet(out, index=False)
    # Back-compat alias used by earlier docs
    df.to_parquet(DERIVED / "pricing_parts_master.parquet", index=False)
    print(f"pricing_pr00_ie40: {len(df):,} rows ← {path.name}")
    return out


def build_zpr1() -> Path:
    path = RAW / "EXPORT_ZPR1_20260810.xlsx"
    if not path.exists():
        # fallback any EXPORT_ZPR1*.xlsx
        matches = sorted(RAW.glob("EXPORT_ZPR1*.xlsx"))
        if not matches:
            raise FileNotFoundError("No EXPORT_ZPR1 file in _raw")
        path = matches[-1]

    header, rows = _sheet_rows(path)
    i_code = _col(header, "Customer Code")
    i_name = _col(header, "Customer")
    i_pn = _col(header, "P/N")
    i_newest = _col(header, "Newest P/N")
    i_desc = _col(header, "Description")
    i_coo = _col(header, "Country of Origin")
    i_price = _col(header, "Price")
    i_fig = _col(header, "Fig No.") if "Fig No." in header else None
    i_key = _col(header, "Key No.") if "Key No." in header else None

    recs = []
    cust = {}
    for r in rows:
        code = norm_customer_code(r[i_code])
        pn = norm_pn(r[i_pn])
        if not code or not pn:
            continue
        name = "" if r[i_name] is None else str(r[i_name]).strip()
        cust[code] = name
        newest = norm_pn(r[i_newest]) or pn
        alias = ZPR1_KEY_CUSTOMERS.get(code, "")
        recs.append(
            {
                "customer_code": code,
                "customer_name": name,
                "customer_alias": alias or None,
                "part_number": pn,
                "newest_pn": newest,
                "description": ("" if r[i_desc] is None else str(r[i_desc]).strip()),
                "sp_eur_zpr1": parse_eur(r[i_price]),
                "country_of_origin": (
                    "" if r[i_coo] is None else str(r[i_coo]).strip()
                ),
                "fig_no": None if i_fig is None else r[i_fig],
                "key_no": None if i_key is None else r[i_key],
                "is_superseded_row": pn != newest,
                "source_file": path.name,
            }
        )
    df = pd.DataFrame.from_records(recs)
    out = DERIVED / "pricing_zpr1.parquet"
    df.to_parquet(out, index=False)

    dim = pd.DataFrame(
        [
            {
                "customer_code": c,
                "customer_name": n,
                "customer_alias": ZPR1_KEY_CUSTOMERS.get(c),
                "n_pn_rows": int((df.customer_code == c).sum()),
            }
            for c, n in sorted(cust.items())
        ]
    )
    dim.to_parquet(DERIVED / "pricing_zpr1_customers.parquet", index=False)
    dim.to_csv(DERIVED / "pricing_zpr1_customers.csv", index=False)

    # Wide key-customer SP for fast PR00 vs ZPR1 compare
    key = df[df["customer_code"].isin(ZPR1_KEY_CUSTOMERS)].copy()
    wide = (
        key.pivot_table(
            index="part_number",
            columns="customer_alias",
            values="sp_eur_zpr1",
            aggfunc="max",
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    # prefix columns
    rename = {
        c: f"zpr1_sp_{c}"
        for c in wide.columns
        if c != "part_number"
    }
    wide = wide.rename(columns=rename)
    wide.to_parquet(DERIVED / "pricing_zpr1_key_wide.parquet", index=False)

    print(
        f"pricing_zpr1: {len(df):,} rows · {df.customer_code.nunique()} customers "
        f"← {path.name}"
    )
    print(f"pricing_zpr1_key_wide: {len(wide):,} PNs")
    return out


def build_enquiry_view() -> Path:
    """PR00-centric enquiry: list + CD + L12M + IE40 list + key ZPR1 SPs."""
    lst = pd.read_parquet(DERIVED / "pricing_list_pn.parquet")
    cd = pd.read_parquet(DERIVED / "pricing_revision_cd.parquet")[
        [
            "part_number",
            "bp_jpy_current",
            "bp_jpy_new",
            "bp_jpy_delta",
            "part_class_current_raw",
            "part_class_new_raw",
            "price_class_current",
            "price_class_new",
            "class_changed",
            "bp_changed",
            "example_model",
        ]
    ]
    sim = pd.read_parquet(DERIVED / "pricing_sim_pr00_l12m.parquet")[
        ["part_number", "qty_l12m", "sp_eur_2025", "sp_eur_2026"]
    ].rename(
        columns={
            "qty_l12m": "qty_l12m_sim",
            "sp_eur_2025": "sp_eur_2025_sim",
            "sp_eur_2026": "sp_eur_2026_sim",
        }
    )
    pr00 = pd.read_parquet(DERIVED / "pricing_pr00_ie40.parquet")[
        ["part_number", "sp_eur", "newest_pn", "valid_start", "valid_end"]
    ].rename(
        columns={
            "sp_eur": "sp_eur_pr00_ie40",
            "newest_pn": "newest_pn_ie40",
            "valid_start": "pr00_valid_start",
            "valid_end": "pr00_valid_end",
        }
    )
    # one row per PN in IE40 (prefer non-superseded / max price if dups)
    pr00 = (
        pr00.sort_values(["part_number", "sp_eur_pr00_ie40"], ascending=[True, False])
        .drop_duplicates("part_number", keep="first")
    )
    zwide = pd.read_parquet(DERIVED / "pricing_zpr1_key_wide.parquet")

    out = (
        lst.merge(cd, on="part_number", how="left")
        .merge(sim, on="part_number", how="left")
        .merge(pr00, on="part_number", how="left")
        .merge(zwide, on="part_number", how="left")
    )
    # Israel vs PR00 differential where both exist (UMI)
    if "zpr1_sp_UMI" in out.columns:
        out["zpr1_umi_vs_pr00"] = out["zpr1_sp_UMI"] / out["sp_eur_pr00_ie40"]
    if "zpr1_sp_UTI" in out.columns:
        out["zpr1_uti_vs_pr00"] = out["zpr1_sp_UTI"] / out["sp_eur_pr00_ie40"]

    path = DERIVED / "pricing_pn_enquiry.parquet"
    out.to_parquet(path, index=False)
    bp_flag = out["bp_changed"].fillna(False)
    if bp_flag.dtype == object:
        bp_flag = bp_flag.map(lambda x: bool(x) if pd.notna(x) else False)
    else:
        bp_flag = bp_flag.astype(bool)
    slim = out[out["qty_l12m_sim"].notna() | bp_flag]
    slim.to_csv(DERIVED / "pricing_pn_enquiry_active.csv", index=False)
    print(f"pricing_pn_enquiry: {len(out):,} rows; active CSV {len(slim):,}")
    return path


def main() -> None:
    DERIVED.mkdir(parents=True, exist_ok=True)
    build_price_file()
    build_revision_cd()
    build_sim_pr00()
    build_pr00_ie40()
    build_zpr1()
    build_enquiry_view()
    print("done")


if __name__ == "__main__":
    main()
