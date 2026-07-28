import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

import openpyxl
import yaml

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SPA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\03_PMS\PMS SPA study_ISZE (1).xlsx")
AIM = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_pn_classification.csv")
ITUK = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\ituk_pms_pn_audit.csv")
TAX = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\data\fig_key_taxonomy.yaml")
SALES_FIG = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\sales_by_db_fig_key_year.csv")
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\suzuki_pms_mail_pull\spa_ituk_fig_audit.txt")

wb = openpyxl.load_workbook(SPA, data_only=True, read_only=True)
ws = wb["PMS SPA study"]
rows = list(ws.iter_rows(values_only=True))
wb.close()

packs = []
cur = None
for r in rows:
    vals = [v for v in r if v is not None]
    if not vals:
        continue
    first = str(vals[0])
    if any(k in first for k in ("campaign", "pack", "NPR", "N35", "N75", "4HK", "4JJ", "4JZ")) or first.endswith("pack"):
        # header-ish rows for packs
        if "PMS category" in first:
            continue
        cur = first
        packs.append([cur, []])
        continue
    if cur is None:
        # first pack title may be row1
        if "NPR" in first or "campaign" in first.lower():
            cur = first
            packs.append([cur, []])
            continue
    if cur and len(vals) >= 2:
        pn = str(vals[1]).strip()
        if pn.isdigit() and len(pn) >= 7:
            packs[-1][1].append(
                {
                    "cat": str(vals[0]),
                    "pn": pn,
                    "hof": str(vals[2]).strip() if len(vals) > 2 and vals[2] is not None else "",
                    "desc": str(vals[3]) if len(vals) > 3 else "",
                }
            )

# If no packs detected, treat whole sheet as one pack after header
if not packs or sum(len(p[1]) for p in packs) == 0:
    packs = [["PMS SPA study (all)", []]]
    for r in rows[2:]:
        if not r or r[1] is None:
            continue
        pn = str(r[1]).strip()
        if pn.isdigit() and len(pn) >= 7:
            packs[0][1].append(
                {
                    "cat": str(r[0]) if r[0] else "",
                    "pn": pn,
                    "hof": str(r[2]).strip() if r[2] is not None else "",
                    "desc": str(r[3]) if len(r) > 3 and r[3] else "",
                }
            )

aim = {}
with AIM.open(encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        aim[r["part_number"]] = (r.get("fig_key") or "", r.get("description_norm") or "")

ituk_qty = defaultdict(float)
ituk_rev = defaultdict(float)
ituk_years = defaultdict(set)
with ITUK.open(encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        pn = r["part_number"]
        ituk_qty[pn] += float(r.get("actual_qty") or 0)
        ituk_rev[pn] += float(r.get("actual_rev_eur") or 0)
        ituk_years[pn].add(r.get("year"))

tax = yaml.safe_load(TAX.read_text(encoding="utf-8"))
pms_figs = set((tax.get("pms_fig_keys") or {}).keys())
# also category defaults
for v in (tax.get("category_default_fig_key") or {}).values():
    if v:
        pms_figs.add(v)

# sales by db fig 2025 for all DBs
db_figs_2025 = defaultdict(set)
with SALES_FIG.open(encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        if r.get("year") != "2025":
            continue
        fk = (r.get("fig_key") or "").strip()
        db = r.get("distributor_code") or ""
        if fk:
            db_figs_2025[db].add(fk)

lines = []
def w(s=""):
    lines.append(s)
    print(s)

w("=== SPA campaign packs ===")
all_items = []
for name, items in packs:
    w(f"{name}: {len(items)} PNs")
    all_items.extend(items)
uniq = {i["pn"]: i for i in all_items}
w(f"Unique PNs: {len(uniq)}")

w("\n=== PN vs AIM / ITUK audit ===")
w("pn\tcat\tfig\tin_aim\tituk_qty\tituk_rev\tyears")
zero = []
for pn, i in sorted(uniq.items()):
    fk, desc = aim.get(pn, ("", ""))
    qty = ituk_qty.get(pn, 0.0)
    rev = ituk_rev.get(pn, 0.0)
    yrs = ",".join(sorted(ituk_years.get(pn, [])))
    w(f"{pn}\t{i['cat']}\t{fk}\t{pn in aim}\t{qty}\t{rev:.1f}\t{yrs}")
    if qty == 0:
        zero.append((pn, i["cat"], fk))

w(f"\nCampaign PNs with ZERO ITUK PMS-audit sales: {len(zero)} / {len(uniq)}")
for pn, cat, fk in zero:
    w(f"  {pn} | {cat} | fig={fk}")

spa_figs = sorted({aim[pn][0] for pn in uniq if pn in aim and aim[pn][0]})
w(f"\nSPA campaign fig keys ({len(spa_figs)}): {spa_figs}")
w(f"Taxonomy PMS fig keys ({len(pms_figs)}): {sorted(pms_figs)}")
missing_tax = sorted(set(spa_figs) - pms_figs)
extra_needed = sorted(pms_figs - set(spa_figs))
w(f"SPA figs NOT in taxonomy PMS set: {missing_tax}")
w(f"Taxonomy PMS figs NOT in SPA campaign: {extra_needed}")

w("\n=== Fig-key coverage by distributor (CY2025 sales present?) for SPA figs ===")
dbs = sorted(db_figs_2025.keys())
# focus main EU DBs
focus = [d for d in dbs if d in {"ITUK", "IUK", "UTI", "IRELAND", "GERMANY", "BELGIUM", "PORTUGAL", "ITALY", "SPAIN", "FRANCE", "NETHERLANDS", "POLAND", "HUNGARY", "ROMANIA", "GREECE", "CYPRUS", "MALTA", "ICELAND", "DENMARK", "NORWAY", "SWEDEN", "FINLAND"} or True]
# summarize: for each SPA fig, which DBs have sales
w("fig\t#DBs_with_2025_sales\tITUK\tUTI\tIRELAND\tGERMANY\tBELGIUM")
for fk in spa_figs:
    dbs_hit = [d for d, s in db_figs_2025.items() if fk in s]
    def has(d):
        return "Y" if fk in db_figs_2025.get(d, set()) else "N"
    w(f"{fk}\t{len(dbs_hit)}\t{has('ITUK')}\t{has('UTI')}\t{has('IRELAND')}\t{has('GERMANY')}\t{has('BELGIUM')}")

w("\n=== Taxonomy PMS fig keys: ITUK / network presence CY2025 ===")
for fk in sorted(pms_figs):
    def has(d):
        return "Y" if fk in db_figs_2025.get(d, set()) else "N"
    n = sum(1 for s in db_figs_2025.values() if fk in s)
    w(f"{fk}\tn={n}\tITUK={has('ITUK')}\tUTI={has('UTI')}\tIRELAND={has('IRELAND')}")

# Target
w("\n=== Target 5876102500 ===")
pn = "5876102500"
w(f"in SPA campaign: {pn in uniq}")
w(f"AIM: {aim.get(pn)}")
w(f"ITUK qty/rev: {ituk_qty.get(pn)} / {ituk_rev.get(pn)}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nWrote {OUT}")
