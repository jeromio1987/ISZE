# -*- coding: utf-8 -*-
"""supersession_map.csv - the old->current mapping that matters for the worklist.

For every one of the 123 numbers: the number it supersedes into (forward chain), the
older numbers that supersede INTO it, and whether that related number already carries a
ledger row or a raw observation. Source of the mapping is named per row.
"""
from pathlib import Path

import pandas as pd

MAIN = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = Path(__file__).resolve().parent

WORKLIST = MAIN / "01_data" / "90_INBOX" / "MARKET_SCRAPE_WORKLIST_20261007.csv"
SUPMAP   = MAIN / "01_data" / "00_derived" / "pn_supersession_map.csv"
PL       = MAIN / "01_data" / "00_derived" / "pricing_pr00_ie40.parquet"
LEDGER   = MAIN / "01_data" / "00_derived" / "price_observations.parquet"
F_TXT    = MAIN / "01_data" / "Fresh list_Export_28072025_0932.txt"
F_ONL    = MAIN / "01_data" / "Eucon_Online28072025.xlsx"
F_MAR    = MAIN / "01_data" / "Eucon_March.xlsx"
F_PP     = MAIN / "01_data" / "01_Pricing" / "_raw" / "eucon_pricing_partspool_20260329.xlsx"


def z(s):
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(10)


def find10(x):
    import re
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
led_by_pn = led.groupby("pn").size().to_dict()

# published map
mp = pd.read_csv(SUPMAP, dtype=str)
mp["old_pn"] = z(mp["old_pn"])
mp["current_pn"] = z(mp["current_pn"])

# price list chain
pl = pd.read_parquet(PL, columns=["part_number", "newest_pn", "description"])
pl["pn"] = z(pl["part_number"])
pl["newest"] = z(pl["newest_pn"])
chain = pl[pl.pn != pl.newest][["pn", "newest"]].drop_duplicates("pn")
fwd = dict(zip(chain.pn, chain.newest))
rev = {}
for a, b in fwd.items():
    rev.setdefault(b, []).append(a)
desc = dict(zip(pl.pn, pl.description))

# raw files: which numbers carry an observation at all
raw_pns = {}
pp = pd.read_excel(F_PP, sheet_name="Eucon_Pricing_Clean", dtype=str)
for _, r in pp.iterrows():
    p = "".join(ch for ch in str(r["Searched_PN_Isuzu"]) if ch.isdigit()).zfill(10)
    raw_pns.setdefault(p, set()).add("Eucon PartsPool 2026-03-29")
onl = pd.read_excel(F_ONL, sheet_name="Fresh list_Export_28072025_0932", dtype=str)
for _, r in onl.iterrows():
    for p in find10(r["OE Part Number"]):
        raw_pns.setdefault(p, set()).add("Eucon online 2025-07-28")
rr = pd.read_excel(F_MAR, sheet_name="RRP MODE", dtype=str)
for _, r in rr.iterrows():
    for p in find10(r["OE Part Number"]):
        raw_pns.setdefault(p, set()).add("Eucon March RRP MODE")
mo = pd.read_excel(F_MAR, sheet_name="Online 15032024", dtype=str)
for _, r in mo.iterrows():
    p = "".join(ch for ch in str(r["Searched Part Number"]) if ch.isdigit()).zfill(10)
    raw_pns.setdefault(p, set()).add("Eucon March online 2024-03-15")


def resolve(p, depth=8):
    path = [p]
    cur = p
    for _ in range(depth):
        n = fwd.get(cur)
        if not n or n in path:
            break
        path.append(n)
        cur = n
    return cur, path


rows = []
for p in wpn:
    term, path = resolve(p)
    if term != p:
        rows.append(dict(worklist_part_no=p, family=fam.get(p, ""), old_pn=p, current_pn=term,
                         direction="superseded into a current number",
                         source_file="01_data/00_derived/pricing_pr00_ie40.parquet (part_number -> newest_pn)",
                         chain=" -> ".join(path),
                         related_in_ledger=(term in led_pns),
                         related_ledger_rows=led_by_pn.get(term, 0),
                         related_raw_sources="; ".join(sorted(raw_pns.get(term, []))),
                         old_description=str(desc.get(p, ""))))
    for x in rev.get(p, []):
        rows.append(dict(worklist_part_no=p, family=fam.get(p, ""), old_pn=x, current_pn=p,
                         direction="an older number supersedes into this one",
                         source_file="01_data/00_derived/pricing_pr00_ie40.parquet (part_number -> newest_pn)",
                         chain="%s -> %s" % (x, p),
                         related_in_ledger=(x in led_pns),
                         related_ledger_rows=led_by_pn.get(x, 0),
                         related_raw_sources="; ".join(sorted(raw_pns.get(x, []))),
                         old_description=str(desc.get(x, ""))))
    h = mp[(mp.old_pn == p) | (mp.current_pn == p)]
    for _, r in h.iterrows():
        rows.append(dict(worklist_part_no=p, family=fam.get(p, ""), old_pn=r.old_pn,
                         current_pn=r.current_pn,
                         direction=("listed in the published map (old)" if r.old_pn == p
                                    else "listed in the published map (current)"),
                         source_file="01_data/00_derived/pn_supersession_map.csv (925 pairs, from PR00 IE40 newest_pn)",
                         chain="%s -> %s" % (r.old_pn, r.current_pn),
                         related_in_ledger=(r.current_pn in led_pns or r.old_pn in led_pns),
                         related_ledger_rows=led_by_pn.get(r.current_pn, 0) + led_by_pn.get(r.old_pn, 0),
                         related_raw_sources="; ".join(sorted(raw_pns.get(r.current_pn, set()) | raw_pns.get(r.old_pn, set()))),
                         old_description=str(r.get("old_description", ""))))

sm = pd.DataFrame(rows).drop_duplicates(subset=["worklist_part_no", "old_pn", "current_pn", "source_file"])
sm = sm.sort_values(["worklist_part_no", "direction"])
sm.to_csv(OUT / "supersession_map.csv", index=False, encoding="utf-8")
print("supersession_map.csv rows:", len(sm), " distinct worklist PNs:", sm.worklist_part_no.nunique())
print(sm.direction.value_counts().to_dict())
print()
print("rows where a related number already carries a ledger row:")
g = sm[sm.related_in_ledger]
print(g[["worklist_part_no", "old_pn", "current_pn", "direction", "related_ledger_rows", "source_file"]].to_string(index=False))
