# -*- coding: utf-8 -*-
"""Work package D, part 3 - supersession, the direction that matters.

For every worklist number that is still empty, find whether an OLD number supersedes
into it (or it into a current one), then check whether the Eucon raw files carry a
competitor price under that related number. That is the case the brief asks about:
a part that looks empty only because it is searched under a stale number.
"""
import json
import re
from pathlib import Path

import pandas as pd

MAIN = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = Path(__file__).resolve().parent

WORKLIST = MAIN / "01_data" / "90_INBOX" / "MARKET_SCRAPE_WORKLIST_20261007.csv"
SUPMAP   = MAIN / "01_data" / "00_derived" / "pn_supersession_map.csv"
PL       = MAIN / "01_data" / "00_derived" / "pricing_pr00_ie40.parquet"
LEDGER   = MAIN / "01_data" / "00_derived" / "price_observations.parquet"
GRADED   = MAIN / "04_tools" / "aftermarket_intelligence" / "state" / "crossref_graded.csv"
F_ONL    = MAIN / "01_data" / "Eucon_Online28072025.xlsx"
F_MAR    = MAIN / "01_data" / "Eucon_March.xlsx"
F_PP     = MAIN / "01_data" / "01_Pricing" / "_raw" / "eucon_pricing_partspool_20260329.xlsx"


def z(s):
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(10)


def find10(x):
    if pd.isna(x):
        return []
    return re.findall(r"\b\d{10}\b", str(x))


w = pd.read_csv(WORKLIST, dtype=str)
w["pn"] = z(w["part_number"])
wpn = sorted(set(w["pn"]))
fam = w.drop_duplicates("pn").set_index("pn")["pms_category"].to_dict()

led = pd.read_parquet(LEDGER)
led["pn"] = z(led["part_no"])
led_pns = set(led.pn)
empty = [p for p in wpn if p not in led_pns]

pl = pd.read_parquet(PL, columns=["part_number", "newest_pn", "description"])
pl["pn"] = z(pl["part_number"])
pl["newest"] = z(pl["newest_pn"])
chain = pl[pl.pn != pl.newest][["pn", "newest"]].drop_duplicates("pn")
fwd = dict(zip(chain.pn, chain.newest))
# reverse index: successor -> [predecessors]
rev = {}
for a, b in fwd.items():
    rev.setdefault(b, []).append(a)


def resolve(p, depth=6):
    """Follow the chain forward to its terminal number, with the path."""
    path = [p]
    cur = p
    for _ in range(depth):
        nxt = fwd.get(cur)
        if not nxt or nxt in path:
            break
        path.append(nxt)
        cur = nxt
    return cur, path


# --- competitor prices available under any related number -----------------
def raw_index():
    idx = {}
    pp = pd.read_excel(F_PP, sheet_name="Eucon_Pricing_Clean", dtype=str)
    for _, r in pp.iterrows():
        p = "".join(ch for ch in str(r["Searched_PN_Isuzu"]) if ch.isdigit()).zfill(10)
        idx.setdefault(p, []).append(("Eucon PartsPool 2026-03-29", "Eucon_Pricing_Clean",
                                      r["Competitor_Brand"], r["Competitor_PN"], r["Online_Price_EUR"]))
    onl = pd.read_excel(F_ONL, sheet_name="Fresh list_Export_28072025_0932", dtype=str)
    for _, r in onl.iterrows():
        for p in find10(r["OE Part Number"]):
            idx.setdefault(p, []).append(("Eucon Online 2025-07-28", "Fresh list",
                                          r["Brand"], r["Part Number"], r["RRP"]))
    rr = pd.read_excel(F_MAR, sheet_name="RRP MODE", dtype=str)
    for _, r in rr.iterrows():
        for p in find10(r["OE Part Number"]):
            idx.setdefault(p, []).append(("Eucon March RRP MODE", "RRP MODE",
                                          r["Brand"], r["Part Number"], r["RRP"]))
    mo = pd.read_excel(F_MAR, sheet_name="Online 15032024", dtype=str)
    for _, r in mo.iterrows():
        p = "".join(ch for ch in str(r["Searched Part Number"]) if ch.isdigit()).zfill(10)
        idx.setdefault(p, []).append(("Eucon March online 2024", "Online 15032024",
                                      r["Brand"], r["Part Number"], r["Online Price"]))
    return idx


idx = raw_index()
print("raw index: %d distinct Isuzu numbers carry at least one raw observation" % len(idx))

rows = []
for p in empty:
    term, path = resolve(p)
    preds = rev.get(p, [])
    related = {}
    if term != p:
        related[term] = "superseded by (forward chain)"
    for x in preds:
        related[x] = "predecessor of this number (reverse)"
    # also predecessors of the terminal
    for x in rev.get(term, []):
        related.setdefault(x, "predecessor of the terminal number")
    for rel, why in related.items():
        obs = idx.get(rel, [])
        inled = rel in led_pns
        if obs or inled:
            rows.append(dict(worklist_pn=p, family=fam.get(p, ""), related_pn=rel, relation=why,
                             related_in_ledger=inled,
                             raw_observations=len(obs),
                             sample=[str(o) for o in obs[:3]],
                             chain=" -> ".join(path)))

sm2 = pd.DataFrame(rows)
sm2.to_csv(OUT / "_supersession_reach.csv", index=False, encoding="utf-8")
print("\nempty PNs (%d) that reach a related number with raw observations or a ledger row: %d"
      % (len(empty), sm2.worklist_pn.nunique() if len(sm2) else 0))
print(sm2.to_string(index=False) if len(sm2) else "(none)")

json.dump(dict(empty_pns=len(empty), empty_unlocked=int(sm2.worklist_pn.nunique()) if len(sm2) else 0),
          open(OUT / "_sup_counts2.json", "w"), indent=2)
