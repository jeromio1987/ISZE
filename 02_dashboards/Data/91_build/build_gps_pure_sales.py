"""Rebuild gps_pure_sales from the derived sources named in
gps_pure_sales_2026-08-13.md, then exclude bare material SERVICE.

The 2026-08-13 CSV is a one-off artefact (no builder). This script is the
lineage. It does not open raw sales XLSX. It does not edit the live GPS
dashboard HTML.

  python 01_data/91_build/build_gps_pure_sales.py

Steps
  1. Reproduce every row of gps_pure_sales_2026-08-13.csv to the cent
     from ALLCUSTOMERS + sidecars + fiscal warranty.
  2. If that identity fails, stop. Do not write a new file.
  3. Subtract bare material SERVICE (the ALLCUSTOMERS filter only caught
     SERVICE FEE|COST DEMURRAGE|LATE PAYMENT). Proven: sold-to 373 / IMIO,
     one FY2026 DR row.
  4. Write gps_pure_sales_2026-08-13_v2.csv next to the original.
     The original file is left untouched.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
DERIVED = ROOT / "01_data" / "00_derived"
ORIGINAL = DERIVED / "gps_pure_sales_2026-08-13.csv"
OUT = DERIVED / "gps_pure_sales_2026-08-13_v2.csv"
TOL = 0.005  # one cent

WARRANTY_MISSING_DBS = {
    "CBC", "CIS-KTK", "GA", "IMG", "IMIO", "KIMA", "TR", "Sverige2",
}
THIN_DBS = {"TR", "IMIO", "Sverige2"}
MONEY_COLS = [
    "net_raw",
    "billing_clean_eur",
    "transport_eur",
    "surcharge_stripped_eur",
    "shell_lubricants_eur",
    "other_excl_eur",
    "saty_cr_excl_eur",
    "pure_sales_eur",
    "warranty_eur",
    "pure_sales_ex_warranty_eur",
]


def money(x) -> float:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return 0.0
    return round(float(x), 2)


def lookup_year(obj: dict, db: str, fy: int):
    node = obj.get(db)
    if not isinstance(node, dict):
        return None
    v = node.get(str(fy), node.get(fy))
    if v is None:
        return None
    if isinstance(v, dict):
        for k in ("transport_eur", "surcharge_stripped_eur", "eur", "value"):
            if k in v:
                return v[k]
        return next(iter(v.values())) if v else None
    return v


def notes_for(row: dict) -> str:
    flags = []
    fy = int(row["fy"])
    db = row["db"]
    if db in {"UMI", "UTI"}:
        flags.append("israel_split")
    warr = row["warranty_eur"]
    if warr is None or (isinstance(warr, float) and pd.isna(warr)):
        flags.append("warranty_missing")
    if fy == 2023:
        flags.append("fy23_partial")
        flags.append("fy23_shell_zero")
        flags.append("fy23_other_excl_zero")
    if fy == 2026:
        flags.append("fy26_other_excl_zero")
    if db == "ITUK" and money(row["other_excl_eur"]) > 0:
        flags.append("other_excl_all_on_ituk")
    if db == "UMI" and money(row["shell_lubricants_eur"]) > 0:
        flags.append("shell_all_on_umi")
    if money(row["saty_cr_excl_eur"]) > 0:
        flags.append("taxonomy_gap_vs_billing_clean")
    if db == "MIDI":
        flags.append("midi_non_gps_channel")
    if db == "Norway":
        flags.append("warranty_joined_as_RSA")
    if db == "RSA":
        flags.append("warranty_joined_as_Greece")
    if db in THIN_DBS:
        flags.append("thin_or_unmapped")
    extra = row.get("_extra_notes") or []
    flags.extend(extra)
    return "|".join(flags)


def load_warranty() -> dict[tuple[str, int], float]:
    w = pd.read_csv(DERIVED / "distributor_warranty_expense_fiscal.csv")
    out: dict[tuple[str, int], float] = {}
    for r in w.itertuples():
        db = r.db
        mapped = {"RSA": "Norway", "Greece": "RSA"}.get(db, db)
        for fy, col in ((2024, "warr_FY2024"), (2025, "warr_FY2025"), (2026, "warr_FY2026")):
            val = getattr(r, col)
            if pd.isna(val):
                continue
            out[(mapped, fy)] = money(val)
    return out


def reproduce() -> pd.DataFrame:
    ac = pd.read_csv(DERIVED / "gps_billing_fy_ALLCUSTOMERS.csv")
    clean = json.loads((DERIVED / "gps_billing_clean.json").read_text(encoding="utf-8"))
    trans = json.loads((DERIVED / "gps_billing_transport_excluded.json").read_text(encoding="utf-8"))
    surch = json.loads((DERIVED / "gps_billing_surcharge_stripped.json").read_text(encoding="utf-8"))
    wf = pd.read_csv(DERIVED / "gps_billing_fy_waterfall.csv")
    warr = load_warranty()

    wf_other = {int(r.FY): money(r.excl_other) for r in wf.itertuples()}
    wf_shell = {int(r.FY): money(r.excl_shell) for r in wf.itertuples()}
    wf_saty = {int(r.FY): money(r.excl_saty_cr) for r in wf.itertuples()}

    rows = []
    for r in ac.itertuples():
        fy = int(r.FY)
        db = r.canonical_name
        pure = money(r.net_gps)
        net_raw = money(r.net_raw)
        bc = lookup_year(clean, db, fy)
        billing_clean = money(bc) if bc is not None else pure
        transport = money(lookup_year(trans, db, fy) or 0)
        surcharge = money(lookup_year(surch, db, fy) or 0)
        shell = money(wf_shell.get(fy, 0)) if db == "UMI" and fy in (2024, 2025, 2026) else 0.0
        other = money(wf_other.get(fy, 0)) if db == "ITUK" and fy in (2024, 2025) else 0.0
        saty = 0.0
        if db == "Ireland" and fy == 2024:
            saty = 1120.50
        elif db == "ITUK" and fy == 2026:
            saty = 17600.00
        elif db == "IMG" and fy == 2026:
            saty = 10000.00
        warranty = warr.get((db, fy))
        if fy == 2023 or db in WARRANTY_MISSING_DBS:
            warranty = None
        # MIDI has warranty in the fiscal file but the original left FY2023 missing
        # and kept later years. RSA/Norway joined above.
        if db == "MIDI" and fy == 2023:
            warranty = None
        ex_w = None if warranty is None else money(pure - warranty)
        rec = {
            "fy": fy,
            "db": db,
            "payer_codes": r.payer_codes,
            "net_raw": net_raw,
            "billing_clean_eur": billing_clean,
            "transport_eur": transport,
            "surcharge_stripped_eur": surcharge,
            "shell_lubricants_eur": shell,
            "other_excl_eur": other,
            "saty_cr_excl_eur": saty,
            "pure_sales_eur": pure,
            "warranty_eur": warranty,
            "pure_sales_ex_warranty_eur": ex_w,
        }
        rec["notes"] = notes_for(rec)
        rows.append(rec)

    # Sanity: saty residuals should sum to waterfall excl_saty_cr (minus UNK_2686 €360 in FY26)
    for fy, expected in wf_saty.items():
        got = money(sum(r["saty_cr_excl_eur"] for r in rows if r["fy"] == fy))
        if fy == 2026:
            expected = money(expected - 360.00)  # UNK_2686, no ALLCUSTOMERS row
        if abs(got - expected) > TOL:
            raise SystemExit(f"saty_cr identity fail FY{fy}: got {got} expected {expected}")

    return pd.DataFrame(rows)


def is_blank(v) -> bool:
    if v is None:
        return True
    try:
        if pd.isna(v):
            return True
    except (TypeError, ValueError):
        pass
    return str(v).strip() in {"", "nan", "None"}


def blank_eq(a, b) -> bool:
    if is_blank(a) and is_blank(b):
        return True
    if is_blank(a) or is_blank(b):
        return False
    try:
        return abs(float(a) - float(b)) <= TOL
    except (TypeError, ValueError):
        return str(a) == str(b)


def compare(rebuilt: pd.DataFrame, original: pd.DataFrame) -> list[str]:
    diffs = []
    key = ["fy", "db"]
    m = rebuilt.merge(original, on=key, how="outer", suffixes=("_new", "_old"), indicator=True)
    extra = m[m["_merge"] != "both"]
    if len(extra):
        diffs.append(f"row-set mismatch: {extra[['fy','db','_merge']].to_string(index=False)}")
        return diffs
    cols = [c for c in original.columns if c not in key]
    for r in m.itertuples():
        for c in cols:
            a = getattr(r, f"{c}_new")
            b = getattr(r, f"{c}_old")
            if c in MONEY_COLS or c in {"notes", "payer_codes"}:
                if c == "notes":
                    if ("" if is_blank(a) else str(a)) != ("" if is_blank(b) else str(b)):
                        diffs.append(f"{int(r.fy)} {r.db} {c}: rebuilt={a!r} original={b!r}")
                elif c == "payer_codes":
                    if str(a).replace(".0", "") != str(b).replace(".0", ""):
                        diffs.append(f"{int(r.fy)} {r.db} {c}: rebuilt={a!r} original={b!r}")
                elif not blank_eq(a, b):
                    diffs.append(f"{int(r.fy)} {r.db} {c}: rebuilt={a} original={b}")
            elif str(a) != str(b):
                diffs.append(f"{int(r.fy)} {r.db} {c}: rebuilt={a!r} original={b!r}")
    return diffs


def bare_service_delta() -> tuple[int, float]:
    """Return (sold_to, eur) for material SERVICE. Aggregate only — no line dump."""
    sf = pd.read_parquet(
        DERIVED / "sales_fact.parquet",
        columns=["billing_date", "sold_to", "saty", "material", "net_sales_value"],
    )
    mat = sf["material"].astype(str).str.strip().str.upper()
    svc = sf[mat == "SERVICE"].copy()
    if svc.empty:
        raise SystemExit("no bare SERVICE rows in sales_fact.parquet")
    sold = pd.to_numeric(svc["sold_to"], errors="coerce").dropna().unique().tolist()
    if sold != [373]:
        raise SystemExit(f"bare SERVICE sold_to unexpected: {sold}")
    eur = money(svc["net_sales_value"].sum())
    return 373, eur


def apply_service_exclusion(df: pd.DataFrame, sold_to: int, eur: float) -> pd.DataFrame:
    out = df.copy()
    mask = (out["db"] == "IMIO") & (out["fy"] == 2026)
    if int(mask.sum()) != 1:
        raise SystemExit(f"expected one IMIO FY2026 row, got {int(mask.sum())}")
    idx = out.index[mask][0]
    if money(out.at[idx, "pure_sales_eur"]) != eur:
        raise SystemExit(
            f"IMIO FY2026 pure_sales_eur {out.at[idx, 'pure_sales_eur']} != SERVICE {eur}"
        )
    if str(out.at[idx, "payer_codes"]) not in {str(sold_to), str(int(sold_to))}:
        raise SystemExit(f"IMIO payer_codes {out.at[idx, 'payer_codes']} != {sold_to}")
    out.at[idx, "other_excl_eur"] = money(out.at[idx, "other_excl_eur"] + eur)
    out.at[idx, "pure_sales_eur"] = 0.00
    warr = out.at[idx, "warranty_eur"]
    if warr is None or (isinstance(warr, float) and pd.isna(warr)):
        out.at[idx, "pure_sales_ex_warranty_eur"] = pd.NA
    else:
        out.at[idx, "pure_sales_ex_warranty_eur"] = money(0.0 - float(warr))
    rec = out.loc[idx].to_dict()
    rec["_extra_notes"] = ["bare_service_excluded"]
    out.at[idx, "notes"] = notes_for(rec)
    return out


def fmt_money(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return f"{money(v):.2f}"


def write_csv(df: pd.DataFrame, path: Path) -> None:
    cols = [
        "fy", "db", "payer_codes", "net_raw", "billing_clean_eur", "transport_eur",
        "surcharge_stripped_eur", "shell_lubricants_eur", "other_excl_eur",
        "saty_cr_excl_eur", "pure_sales_eur", "warranty_eur",
        "pure_sales_ex_warranty_eur", "notes",
    ]
    out = df[cols].copy()
    for c in MONEY_COLS:
        out[c] = out[c].map(lambda v: "" if v is None or (isinstance(v, float) and pd.isna(v)) else f"{money(v):.2f}")
    out.to_csv(path, index=False)


def main() -> None:
    original = pd.read_csv(ORIGINAL)
    rebuilt = reproduce()
    diffs = compare(rebuilt, original)
    if diffs:
        print("REPRODUCE FAIL — not writing a new file.")
        for line in diffs[:40]:
            print(" ", line)
        if len(diffs) > 40:
            print(f"  … +{len(diffs) - 40} more")
        raise SystemExit(1)
    print(f"reproduce OK: {len(rebuilt)} rows match {ORIGINAL.name} to the cent")

    sold_to, eur = bare_service_delta()
    print(f"bare SERVICE: sold_to={sold_to} eur={eur:.2f} (one row, SaTy DR)")

    v2 = apply_service_exclusion(rebuilt, sold_to, eur)
    # every other row unchanged
    other_diffs = compare(
        v2[v2["db"] != "IMIO"].reset_index(drop=True),
        original[original["db"] != "IMIO"].reset_index(drop=True),
    )
    # notes on IMIO will differ; numbers on non-IMIO must match
    if other_diffs:
        print("SERVICE excl changed a non-IMIO row — abort.")
        for line in other_diffs[:20]:
            print(" ", line)
        raise SystemExit(1)

    old_fy26 = money(original.loc[original["fy"] == 2026, "pure_sales_eur"].sum())
    new_fy26 = money(v2.loc[v2["fy"] == 2026, "pure_sales_eur"].sum())
    print(f"FY2026 network pure_sales_eur {old_fy26:.2f} -> {new_fy26:.2f} (delta {-eur:.2f})")
    write_csv(v2, OUT)
    print(f"wrote {OUT}")
    print("original CSV left untouched; live ISZE_GPS_Dashboard.html not edited.")


if __name__ == "__main__":
    main()
