"""Extract the figures for the UIO V19 vs V20 presentation into uio_v19_v20_data.json.

Sources (read-only):
  V19  06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx                                (18 Jun 2026)
  V20  06_uio/_CURRENT/ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22c.xlsx     (draft, 22 Sep 2026)
  Portugal registrations + plan: 06_uio/_Scripts/spec_20260924_pt_from_registrations.py
Sheet '1.UIO Overview': row 2 = Grand Total (MIDI included), row 5 = MIDI contribution,
rows 7-90 = market x class; col G = 1990 ... AP = 2025, AQ:AU = 2026-2030.
"""
import json, os, sys
import openpyxl

ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
V19 = ISZE + r"\06_uio\_CURRENT\ISUZU_UIO_Overview_2026.xlsx"
V20 = ISZE + r"\06_uio\_CURRENT\ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22c.xlsx"
OUT = os.path.join(os.path.dirname(__file__), "uio_v19_v20_data.json")
sys.path.insert(0, ISZE + r"\06_uio\_Scripts")
import spec_20260924_pt_from_registrations as pt  # noqa: E402

YEARS = list(range(1990, 2031))


def sheet(path):
    ws = openpyxl.load_workbook(path, data_only=True, read_only=True)["1.UIO Overview"]
    return {i + 1: row for i, row in enumerate(ws.iter_rows(min_row=1, max_row=90, values_only=True))}


def series(row):
    return {y: float(row[6 + (y - 1990)] or 0) for y in YEARS}


a, b = sheet(V19), sheet(V20)
data = {"years": YEARS,
        "total": {"v19": series(a[2]), "v20": series(b[2])},
        "midi": {"v19": series(a[5]), "v20": series(b[5])},
        "rows": []}
for r in range(7, 91):
    ra, rb = a[r], b[r]
    if ra[1] is None:
        continue
    s19, s20 = series(ra), series(rb)
    if not any(s19.values()) and not any(s20.values()):
        continue
    data["rows"].append({"row": r, "country": str(ra[1]).strip(), "cvlcv": ra[2], "model": ra[3],
                         "distributor": ra[5], "flag": rb[47], "v19": s19, "v20": s20})

# Portugal rebuilt from registrations (decided 24 Sep 2026, not yet in a workbook)
reg = pt.load_registrations()
yrs = list(range(2015, 2031))
pt_out = {}
for name, r, curve, pick in [("LD", 51, pt.CV, lambda v: v[1] + v[2]),
                             ("F-Series", 53, pt.CV, lambda v: v[3]),
                             ("Pickups", 54, pt.LCV, lambda v: v[0])]:
    R = {y: float(pick(v)) for y, v in reg.items()}
    for i, y in enumerate(range(2026, 2031)):
        R[y] = pt.load_plan(r)[i]
    pt_out[name] = dict(zip(yrs, pt.uio(R, curve, yrs)))
data["portugal_registrations"] = pt_out
data["portugal_regs_by_year"] = {y: {"pickups": v[0], "ld": v[1] + v[2], "f": v[3]} for y, v in reg.items()}

json.dump(data, open(OUT, "w", encoding="utf-8"), indent=1, default=str)
t19, t20 = data["total"]["v19"], data["total"]["v20"]
m19, m20 = data["midi"]["v19"], data["midi"]["v20"]
for y in (2025, 2026, 2030):
    print(y, "V19", round(t19[y]), "V20", round(t20[y]), "ex-MIDI", round(t19[y] - m19[y]), round(t20[y] - m20[y]))
print("rows", len(data["rows"]), "->", OUT)
