# -*- coding: utf-8 -*-
"""Add the observations the ledger's keys cannot express.

Two verified cases only:
  (c) a loaded row that carries a second-generation number in 'Additional Part
      Numbers' with its own RRP, while the ledger keeps only the searched number;
  (d) a raw export row whose own-number price (OE RRP) is complete but never loaded.

The raw text export was checked against the xlsx key by key (PN, brand, competitor
number, country, price): for the 123 worklist numbers both carry exactly the same 217
competitor-priced rows, so nothing was lost between them. That earlier claim was wrong
and is withdrawn here.
"""
import re
from pathlib import Path

import pandas as pd

MAIN = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = Path(__file__).resolve().parent

WORKLIST = MAIN / "01_data" / "90_INBOX" / "MARKET_SCRAPE_WORKLIST_20261007.csv"
LEDGER   = MAIN / "01_data" / "00_derived" / "price_observations.parquet"
F_ONL    = MAIN / "01_data" / "Eucon_Online28072025.xlsx"


def z(s):
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(10)


def num(s):
    return pd.to_numeric(s.astype(str).str.replace(",", ".", regex=False), errors="coerce")


w = pd.read_csv(WORKLIST, dtype=str)
w["pn"] = z(w["part_number"])
wpn = set(w["pn"])
fam = w.drop_duplicates("pn").set_index("pn")["pms_category"].to_dict()

led = pd.read_parquet(LEDGER)
led["pn"] = z(led["part_no"])
led_all_pns = set(led.pn)

onl = pd.read_excel(F_ONL, sheet_name="Fresh list_Export_28072025_0932", dtype=str)
onl["pn"] = z(onl["Searched Part Number"])
onl["rrp"] = num(onl["RRP"])
onl["oerrp"] = num(onl["OE RRP"])
onl["addpn"] = onl["Additional Part Numbers"].fillna("").str.strip()
onl["oepn"] = onl["OE Part Number"].fillna("").str.strip()

rows = []
gen2 = onl[(onl.addpn != "") & onl.pn.isin(wpn)]
for _, r in gen2.iterrows():
    alts = [x for x in re.findall(r"[A-Za-z0-9\-\.]+", r.addpn) if x]
    rows.append(dict(part_no=r.pn, family=fam.get(r.pn, ""), raw_file=F_ONL.name,
                     sheet="Fresh list_Export_28072025_0932",
                     competitor_brand=r["Brand"], competitor_pn=r["Part Number"],
                     price=(("%.2f" % r.rrp) if pd.notna(r.rrp) else ""),
                     currency=r["Currency (RRP)"],
                     why_missing="SECOND_GENERATION_NUMBER_NOT_A_LEDGER_KEY",
                     evidence=("the row the ledger already holds under %s also carries the "
                               "second-generation number(s) %s in 'Additional Part Numbers', with its own "
                               "RRP %s %s. The ledger keys the row on %s alone, so nothing in the ledger "
                               "answers a search on %s."
                               % (r.pn, ", ".join(alts), ("%.2f" % r.rrp) if pd.notna(r.rrp) else "blank",
                                  r["Currency (RRP)"], r.pn, alts[0] if alts else "?")),
                     expected_loader="eucon_online_2025"))

# (d) own-number price complete but never loaded
oer = onl[onl.oerrp.notna() & (onl.oerrp > 2.34) & onl.pn.isin(wpn)]
for _, r in oer.iterrows():
    rows.append(dict(part_no=r.pn, family=fam.get(r.pn, ""), raw_file=F_ONL.name,
                     sheet="Fresh list_Export_28072025_0932",
                     competitor_brand=r["Brand"], competitor_pn=r["Part Number"],
                     price="", currency="",
                     why_missing="OWN_NUMBER_PRICE_NOT_LOADED",
                     evidence=("OE RRP %.2f %s is stated for our own number %s in this row; "
                               "build_price_ledger.py loads RRP only and never OE RRP"
                               % (r.oerrp, r["OE Currency"], r.pn)),
                     expected_loader="(none)"))

add = pd.DataFrame(rows).drop_duplicates(
    subset=["part_no", "raw_file", "sheet", "competitor_brand", "competitor_pn", "why_missing"])

mo = pd.read_csv(OUT / "missing_observations.csv", dtype=str)
# withdraw the withdrawn code if it is in the file already
mo = mo[mo.why_missing != "XLSX_LOST_ROWS_PRESENT_IN_RAW_TEXT_EXPORT"]
mo = pd.concat([mo, add], ignore_index=True)
mo.to_csv(OUT / "missing_observations.csv", index=False, encoding="utf-8")
print("added:", len(add), add.why_missing.value_counts().to_dict())
print()
print(mo.why_missing.value_counts().to_dict())
print("distinct PNs:", mo.part_no.nunique(), " total rows:", len(mo))
