# -*- coding: utf-8 -*-
"""Work package D, part 2 - supersession.

Does an old Isuzu number supersede into a current one, so a part that looks empty is
not empty after all? Two independent sources on disk:
  (a) 01_data/00_derived/pn_supersession_map.csv  (925 pairs, from PR00 IE40 newest_pn)
  (b) 01_data/00_derived/pricing_pr00_ie40.parquet  part_number -> newest_pn (90,823 pairs)
Plus the Eucon raw files' own supersession column, to test the reverse direction.
"""
import json
import re
from pathlib import Path

import pandas as pd

MAIN = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = Path(__file__).resolve().parent

WORKLIST = MAIN / "01_data" / "90_INBOX" / "MARKET_SCRAPE_WORKLIST_20261007.csv"
SUPMAP = MAIN / "01_data" / "00_derived" / "pn_supersession_map.csv"
PL = MAIN / "01_data" / "00_derived" / "pricing_pr00_ie40.parquet"
LEDGER = MAIN / "01_data" / "00_derived" / "price_observations.parquet"
F_ONL = MAIN / "01_data" / "Eucon_Online28072025.xlsx"
F_MAR = MAIN / "01_data" / "Eucon_March.xlsx"


def z(s):
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(10)


def find10(x):
    if pd.isna(x):
        return []
    return re.findall(r"\b\d{10}\b", str(x))


w = pd.read_csv(WORKLIST, dtype=str)
w["pn"] = z(w["part_number"])
wpn = set(w["pn"])
fam = w.drop_duplicates("pn").set_index("pn")["pms_category"].to_dict()

led = pd.read_parquet(LEDGER)
led["pn"] = z(led["part_no"])
led_raw_pns = set(led.pn)                    # every PN the ledger has a row for

# --- (a) the published map ------------------------------------------------
mp = pd.read_csv(SUPMAP, dtype=str)
mp["old_pn"] = z(mp["old_pn"])
mp["current_pn"] = z(mp["current_pn"])
print("pn_supersession_map.csv: %d pairs" % len(mp))

# --- (b) the price list's own chain ---------------------------------------
pl = pd.read_parquet(PL, columns=["part_number", "newest_pn", "description"])
pl["pn"] = z(pl["part_number"])
pl["newest"] = z(pl["newest_pn"])
chain = pl[pl.pn != pl.newest][["pn", "newest", "description"]].drop_duplicates("pn")
print("pricing_pr00_ie40.parquet: %d part numbers, %d supersession pairs" % (pl.pn.nunique(), len(chain)))
old2new = dict(zip(chain.pn, chain.newest))
desc = dict(zip(pl.pn, pl.description))

# --- (c) the raw files' own supersession column ----------------------------
onl = pd.read_excel(F_ONL, sheet_name="Fresh list_Export_28072025_0932", dtype=str)
onl["spn"] = z(onl["Searched Part Number"])
import re as _re
sup_col = [c for c in onl.columns if "supers" in c.lower()]
rrp = pd.read_excel(F_MAR, sheet_name="RRP MODE", dtype=str)
rrp["spn"] = z(rrp["Searched Part Number"])
sup_col += ["RRP MODE:" + c for c in rrp.columns if "supers" in c.lower()]
print("supersession columns found in the raw files:", sup_col)

# --- rows in the map that touch our 123 ------------------------------------
touch = mp[mp.old_pn.isin(wpn) | mp.current_pn.isin(wpn)].copy()
rows = []
for _, r in touch.iterrows():
    rows.append(dict(worklist_part_no=(r.old_pn if r.old_pn in wpn else r.current_pn),
                     relation="old" if r.old_pn in wpn else "current",
                     old_pn=r.old_pn, current_pn=r.current_pn,
                     source="pn_supersession_map.csv",
                     evidence="billed_on_old_pn_eur=%s" % r.get("billed_on_old_pn_eur"),
                     description=r.get("old_description", "")))

# --- rows in the price-list chain that touch our 123 -----------------------
for _, p in enumerate(sorted(wpn)):
    n = old2new.get(p)
    if n:
        rows.append(dict(worklist_part_no=p, relation="old", old_pn=p, current_pn=n,
                         source="pricing_pr00_ie40.parquet part_number->newest_pn",
                         evidence="successor exists in the price list",
                         description=str(desc.get(p, ""))))

# --- reverse: is a worklist PN itself a successor of an older number? ------
pred = chain[chain.newest.isin(wpn)]
for _, r in pred.iterrows():
    rows.append(dict(worklist_part_no=r.newest, relation="current", old_pn=r.pn,
                     current_pn=r.newest, source="pricing_pr00_ie40.parquet part_number->newest_pn",
                     evidence="predecessor %s exists in the price list" % r.pn,
                     description=str(desc.get(r.pn, ""))))

sm = pd.DataFrame(rows).drop_duplicates(subset=["worklist_part_no", "old_pn", "current_pn", "source"])
sm = sm.sort_values(["worklist_part_no", "relation"])
sm.to_csv(OUT / "supersession_map.csv", index=False, encoding="utf-8")
print("\nsupersession_map.csv rows: %d, distinct worklist PNs: %d" % (len(sm), sm.worklist_part_no.nunique()))
print("relation counts:", sm.relation.value_counts().to_dict())
print(sm.groupby("source").size().to_dict())

# --- does the successor carry a price the empty part does not? -------------
print("\n=== does a supersession unlock a number that is empty today? ===")
empty = sorted(p for p in wpn if p not in led_raw_pns)
print("worklist PNs with NO ledger row at all: %d" % len(empty))
gain = []
for p in sorted(wpn):
    n = old2new.get(p)
    if n and n in led_raw_pns:
        gain.append((p, n, "successor %s is in the ledger" % n))
    if p in led_raw_pns and not n:
        pass
for p in sorted(wpn):
    pr = list(pred[pred.newest == p].pn)
    for x in pr:
        if x in led_raw_pns:
            gain.append((p, x, "predecessor %s is in the ledger" % x))
g = pd.DataFrame(gain, columns=["worklist_pn", "related_pn", "why"])
g = g[g.worklist_pn.isin(empty)]
g.to_csv(OUT / "_supersession_gain.csv", index=False, encoding="utf-8")
print("empty worklist PNs whose old/new number IS in the ledger: %d" % len(g))
print(g.head(30).to_string(index=False))

json.dump(dict(map_pairs=len(mp), chain_pairs=len(chain),
               worklist_pns_in_map=int(sm.worklist_part_no.nunique()),
               empty_worklist_pns=len(empty),
               empty_unlocked_by_supersession=int(len(g)),
               raw_supersession_columns=sup_col),
          open(OUT / "_sup_counts.json", "w"), indent=2)
