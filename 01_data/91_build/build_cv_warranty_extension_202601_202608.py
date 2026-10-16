"""Truck (CV) warranty parts euros by month and distributor, with the August 2026 export wired in.

Reads (read-only):
  01_data/06_Warranty/{Warranty_CV_2025, CV Warranty, CV warranty01_03_2026}.xlsx   the five sheets the commercial datasets use
  01_data/CV_Warranty_01-08_2026.xlsx                                              new export, bill months 202512-202608
Writes:
  01_data/00_derived/warranty_cv_monthly_202504_202608.csv     month x distributor, euros, with a source column
  01_data/00_derived/warranty_cv_extension_overlap_check.json  the proof that the two sources tie

Euro rule is the audited one in build_warranty_commercial_datasets.py: EUR as is, GBP x 1.12, JPY / 163.7,
decided by the two-token CRNCY column. Parts only, lines with a real part number (8+ characters).
Duplicate rule is the master's: VIN17 + BILLYMD + PARTNBR + DOCNBR.
Nothing in the master files is touched; this adds a derived file beside them.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "01_data"
OUT_CSV = W / "00_derived" / "warranty_cv_monthly_202504_202608.csv"
OUT_JSON = W / "00_derived" / "warranty_cv_extension_overlap_check.json"
JPY, GBP = 163.7, 1.12
CRNCY = {"EUR EUR": 1.0, "EUR GBP": GBP, "JPY EUR": 1.0 / JPY}
KEY = ["VIN17", "BILLYMD", "PARTNBR", "DOCNBR"]


def prep(d: pd.DataFrame, src: str) -> pd.DataFrame:
    d = d.copy()
    d.columns = [str(c).strip().upper() for c in d.columns]
    for k in KEY:
        d[k] = d[k].astype(str).str.strip()
    d["src"] = src
    return d


master_files = [("Warranty_CV_2025.xlsx", "Sheet1"), ("Warranty_CV_2025.xlsx", "DATA WITHOUT MIDI"),
                ("CV Warranty.xlsx", "10_25-12_2025"), ("CV Warranty.xlsx", "2024"),
                ("CV warranty01_03_2026.xlsx", "Sheet1")]
master = pd.concat([prep(pd.read_excel(W / "06_Warranty" / f, sheet_name=s), "master") for f, s in master_files], ignore_index=True)
new = prep(pd.read_excel(W / "CV_Warranty_01-08_2026.xlsx"), "new_export")


def euros(d: pd.DataFrame) -> pd.DataFrame:
    d = d.drop_duplicates(subset=KEY).copy()
    tok = d.CRNCY.astype(str).str.strip().str.upper()
    d["fx"] = tok.map(CRNCY)
    d["pn"] = d.PARTNBR.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    d["has_pn"] = d.pn.str.len() >= 8
    d["parts_eur"] = pd.to_numeric(d.PARTAMT1, errors="coerce") * d.fx
    d["ym"] = d.BILLYMD.astype(str).str[:6]
    d["dist"] = d.DST_NAME.astype(str).str.strip().str.upper()
    d["market"] = d.CTY_NAME.astype(str).str.strip().str.upper()
    return d


# ---- overlap proof: does the new export contain everything the master holds for the shared months?
m, n = euros(master), euros(new)
shared = sorted(set(m.ym) & set(n.ym))
mk = set(map(tuple, m[KEY].values)); nk = set(map(tuple, n[KEY].values))
chk = {"shared_months": shared, "master_rows": len(mk), "new_rows": len(nk), "master_rows_not_in_new": len(mk - nk)}
by = {}
for ym in shared:
    a = m[(m.ym == ym) & m.has_pn].parts_eur.sum(); b = n[(n.ym == ym) & n.has_pn].parts_eur.sum()
    by[ym] = {"master_eur": round(a), "new_eur": round(b), "new_minus_master_eur": round(b - a),
              "master_lines": int(((m.ym == ym)).sum()), "new_lines": int(((n.ym == ym)).sum())}
chk["by_month"] = by
# lines in the new export for shared months that the master does not hold
extra = n[n.ym.isin(shared) & ~n.apply(lambda r: tuple(r[KEY]) in mk, axis=1)]
chk["lines_only_in_new_for_shared_months"] = int(len(extra))
chk["eur_only_in_new_for_shared_months"] = round(float(extra[extra.has_pn].parts_eur.sum()))
chk["unmapped_currency_lines_new"] = int(n.fx.isna().sum())
OUT_JSON.write_text(json.dumps(chk, indent=1), encoding="utf8")

# ---- union and output: master where it exists, new export for everything else
allr = pd.concat([m, n], ignore_index=True).drop_duplicates(subset=KEY, keep="first")
allr = euros(allr)  # recompute on the union
allr = allr[allr.ym >= "202504"]  # April 2025 onward, so April-August can be set against the year before
allr["source"] = np.where(allr.src.eq("master"), "master", "new_export_only")
g = (allr[allr.has_pn].groupby(["ym", "dist", "market", "source"], as_index=False)
     .agg(claim_lines=("parts_eur", "size"), parts_eur=("parts_eur", "sum")))
g["parts_eur"] = g.parts_eur.round(0)
g.to_csv(OUT_CSV, index=False)
print("wrote", OUT_CSV, len(g), "rows;", "check:", OUT_JSON)
print(json.dumps({k: v for k, v in chk.items() if k != "by_month"}, indent=1))
for ym, v in by.items():
    print(ym, v)
