import csv
import sys
from pathlib import Path

import openpyxl
import yaml

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
SPA = ROOT / r"01_data\03_PMS\PMS SPA study_ISZE (1).xlsx"
DIM = ROOT / r"01_data\00_derived\bvp_pn_dimension.csv"
XREF = ROOT / r"01_data\00_derived\genuine_bvp_crossref.csv"
SUPP = ROOT / r"03_analytics\Isuzu\prism\data\pms_capture_supplement.csv"
AIM = ROOT / r"01_data\00_derived\aim_pn_classification.csv"
OVERRIDES = ROOT / r"03_analytics\Isuzu\prism\data\fig_key_pn_overrides.csv"
TAX = ROOT / r"03_analytics\Isuzu\prism\data\fig_key_taxonomy.yaml"

wb = openpyxl.load_workbook(SPA, data_only=True, read_only=True)
ws = wb["PMS SPA study"]
spa: dict[str, dict] = {}
for r in list(ws.iter_rows(values_only=True))[2:]:
    if not r or r[1] is None:
        continue
    pn = str(r[1]).strip()
    if pn.isdigit() and len(pn) >= 7:
        spa[pn] = {
            "cat": str(r[0]) if r[0] else "",
            "hof": str(r[2]).strip() if r[2] is not None else "",
            "desc": str(r[3]) if len(r) > 3 and r[3] else "",
        }
wb.close()

dim: dict[str, dict] = {}
with DIM.open(encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        pn = (r.get("part_number") or r.get("pn") or "").strip()
        if pn:
            dim[pn] = r
print("bvp_pn_dimension", len(dim), "cols", list(next(iter(dim.values())).keys()))

xref_pns: set[str] = set()
with XREF.open(encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
    print("crossref cols", list(rows[0].keys()) if rows else None)
    for r in rows:
        for k, v in r.items():
            s = str(v or "").strip()
            if s.isdigit() and len(s) >= 7:
                xref_pns.add(s)

supp: set[str] = set()
with SUPP.open(encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        pn = (r.get("part_number") or "").strip()
        if pn:
            supp.add(pn)

overrides: set[str] = set()
with OVERRIDES.open(encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        pn = (r.get("part_number") or "").strip()
        if pn:
            overrides.add(pn)

tax = yaml.safe_load(TAX.read_text(encoding="utf-8"))
pms_figs = set((tax.get("pms_fig_keys") or {}).keys()) | {
    "130-001",
    "145-001",
    "145-002",
    "145-057",
}

aim_fig: dict[str, str] = {}
aim_all: set[str] = set()
with AIM.open(encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        pn = r["part_number"]
        aim_all.add(pn)
        fk = (r.get("fig_key") or "").strip()
        if fk in pms_figs:
            aim_fig[pn] = fk

global_list = set(dim) | supp | overrides | xref_pns

print("supplement", len(supp))
print("overrides", len(overrides))
print("xref pns", len(xref_pns))
print("global union", len(global_list))
print("SPA", len(spa))

missing = []
present = []
for pn, meta in sorted(spa.items()):
    row = {
        "pn": pn,
        "spa_cat": meta["cat"],
        "desc": meta["desc"][:50],
        "dim": pn in dim,
        "supp": pn in supp,
        "xref": pn in xref_pns,
        "override": pn in overrides,
        "aim": pn in aim_all,
        "aim_fig": aim_fig.get(pn, ""),
        "in_global": pn in global_list,
    }
    if dim.get(pn):
        # useful flags if present
        for k in ("pms_flag", "pms_category", "line_type", "pms_registry", "pms_capture_eligible"):
            if k in dim[pn]:
                row[k] = dim[pn].get(k)
    if row["in_global"]:
        present.append(row)
    else:
        missing.append(row)

print(f"\nIN global list: {len(present)} / {len(spa)}")
print(f"MISSING from global list: {len(missing)} / {len(spa)}")
print("\npn\tspa_cat\tin_aim\taim_fig\dim\tsupp\txref\toverride\tdesc")
for r in missing:
    print(
        f"{r['pn']}\t{r['spa_cat']}\t{r['aim']}\t{r['aim_fig']}\t{r['dim']}\t{r['supp']}\t{r['xref']}\t{r['override']}\t{r['desc']}"
    )

# Also: in AIM via fig but not in dim (catalog-known PMS-ish but not on capture dimension)
print("\n=== SPA PNs in AIM/catalog but NOT in bvp_pn_dimension ===")
n = 0
for pn, meta in sorted(spa.items()):
    if pn in aim_all and pn not in dim:
        n += 1
        print(f"{pn}\t{meta['cat']}\tfig={aim_fig.get(pn,'')}\tin_global={pn in global_list}\t{meta['desc'][:40]}")
print("count", n)

# Dim membership detail for all SPA
print("\n=== All SPA vs dim/global ===")
for pn, meta in sorted(spa.items()):
    flag = "OK" if pn in global_list else "MISSING"
    print(f"{flag}\t{pn}\t{meta['cat']}\tdim={pn in dim}\tfig={aim_fig.get(pn,'')}")
