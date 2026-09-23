"""Build the rebuilt Israel rows on the government parc as the primary anchor.

Method (documented in the output):
  1. Level: the Israeli Ministry of Transport parc totals (UTI July 2026 deck, slide 14,
     "based on MOT data"), carried in V20_SPEC.md Problem 4. These are the primary anchor.
  2. Class split: the ministry's four weight bands at 30.06.2026.
  3. Back-cast / forward shape: the UTI registration flow table 1994-2025
     (UIO ISUZU 2025.xlsx, sheet 'גיליון1'), convolved with the IML Emerging CV curve,
     used ONLY as a shape index inside each class, rescaled to the government 2026 anchor.
  4. Old-tail floor: a survival floor for vehicles older than 15 years, calibrated
     against the ministry's 1999-2010 cohort (1,680 trucks still on the road).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import openpyxl

BASE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Israel_Rebuild_20260922")
OUT = BASE / "rebuild_outputs"
OUT.mkdir(parents=True, exist_ok=True)

REG_SRC = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_imie_mail_20260730\UIO ISUZU 2025.xlsx"
)

# ---------------------------------------------------------------- registration flow
wb = openpyxl.load_workbook(REG_SRC, data_only=True)
ws = wb["גיליון1"]
FLOW_BANDS = ["6.5 TON", "7.5 TON", "10TON", "11 TON", "12 TON"]
flow: dict[str, dict[int, int]] = {b: {} for b in FLOW_BANDS}
for r in range(2, 34):
    y = int(ws.cell(row=r, column=1).value)
    for j, b in enumerate(FLOW_BANDS, start=2):
        v = ws.cell(row=r, column=j).value
        flow[b][y] = int(v) if v else 0
FLOW_YEARS = sorted(flow["6.5 TON"])

# ---------------------------------------------------------------- our model's class map
# 6.5 + 7.5  -> the workbook's "CV LD" row (whole N-series NNR/NPR)
# 10         -> maps to the ministry's 7.6-10 t band
# 11 + 12    -> maps to the ministry's 10.1-12 t band
# (nothing)  -> the ministry's 12.1-16 t band has no registration flow at all
CLASSES = {
    "6.5-7.5 t": ["6.5 TON", "7.5 TON"],
    "7.6-10 t": ["10TON"],
    "10.1-12 t": ["11 TON", "12 TON"],
    "12.1-16 t": [],
}
GOV_2026 = {"6.5-7.5 t": 8610, "7.6-10 t": 2485, "10.1-12 t": 2697, "12.1-16 t": 227}
GOV_TOTAL_2026 = sum(GOV_2026.values())

# ---------------------------------------------------------------- government parc totals
# UTI July 2026 deck slide 14, as carried in V20_SPEC.md Problem 4.
GOV_TOTAL = {
    2020: 11514,
    2021: None,   # not quoted on the slide
    2022: 12557,
    2023: None,   # not quoted on the slide
    2024: 13323,
    2025: 13881,
    2026: 14019,
}
GOV_AVG_AGE = {"6.5-7.5 t": 9.4, "7.6-10 t": 6.2, "10.1-12 t": 5.9, "12.1-16 t": 5.6}
MKT_AVG_AGE = {"6.5-7.5 t": 9.8, "7.6-10 t": 10.7, "10.1-12 t": 7.3, "12.1-16 t": 9.1}

# ---------------------------------------------------------------- survival curves
SHEET_EMERGING = [1, .99, .98, .97, .96, .95, .9, .85, .8, .75, .7, .6, .5, .4, .3, .2, .15, .1, .05, 0]
CURVE = [1.0] + SHEET_EMERGING[:-1]      # index = ref - reg_year ; 0 from index 20

DEVELOPED = [1, .99, .98, .97, .96, .95, .9, .8, .7, .55, .4, .3, .2, .1, .05, 0]   # 0 from age 16


def floored(curve: list[float], floor: float | None, min_age: int) -> list[float]:
    c = list(curve)
    if floor is None:
        return c
    for age in range(min_age, len(c)):
        c[age] = max(c[age], floor)
    return c


def conv(ref: float, regs_by_band: dict[str, dict[int, int]], bands: list[str], curve: list[float]) -> float:
    tot = 0.0
    for b in bands:
        for rgy, units in regs_by_band[b].items():
            if not units:
                continue
            age = ref - rgy
            if age < 0 or age >= len(curve):
                continue
            tot += units * curve[int(age)]
    return tot


# ---------------------------------------------------------------- class-level flow curves
REF = 2026
flow_conv_2026 = {}
for cls, bands in CLASSES.items():
    flow_conv_2026[cls] = conv(REF, flow, bands, CURVE)
print("flow convolution at 2026-06-30, by ministry class:")
for cls in CLASSES:
    print(f"  {cls:<12} flow-conv={flow_conv_2026[cls]:>9.0f}   gov parc={GOV_2026[cls]:>7,}")

k = {}
for cls in CLASSES:
    k[cls] = (GOV_2026[cls] / flow_conv_2026[cls]) if flow_conv_2026[cls] else None
print("\nper-class anchor factor k = gov(2026) / flow-conv(2026):")
for cls in CLASSES:
    print(f"  {cls:<12} k={('n/a (no flow)' if k[cls] is None else round(k[cls], 4))}")

# ---------------------------------------------------------------- rebuilt parc by class
YEARS = list(range(1994, 2031))
rebuilt: dict[int, dict[str, float]] = {}
for y in YEARS:
    row = {}
    for cls, bands in CLASSES.items():
        if not bands:
            # 12.1-16 t has no registration flow. Hold the ministry anchor flat back to 2013,
            # then decay it on the developed-market curve for the earlier back-cast, and
            # carry it forward flat. Flagged as inferred.
            if y >= 2013:
                row[cls] = float(GOV_2026[cls])
            else:
                age = 2026 - 2013
                row[cls] = float(GOV_2026[cls]) * (DEVELOPED[min(age, len(DEVELOPED) - 1)])
            continue
        f = conv(y, flow, bands, CURVE)
        row[cls] = f * k[cls]
    rebuilt[y] = row

# ---------------------------------------------------------------- report table
print("\n" + "=" * 118)
print("REBUILT ISRAEL PARC BY MINISTRY WEIGHT CLASS  (government-anchored)")
print("=" * 118)
hdrs = ["year"] + list(CLASSES) + ["rebuilt total", "gov total", "delta"]
print(f"{hdrs[0]:>6}{hdrs[1]:>12}{hdrs[2]:>12}{hdrs[3]:>12}{hdrs[4]:>12}{hdrs[5]:>15}{hdrs[6]:>11}{hdrs[7]:>10}")
for y in YEARS:
    if y < 2005 and y not in (2020, 2022, 2024, 2025, 2026):
        continue
    row = rebuilt[y]
    tot = sum(row.values())
    gt = GOV_TOTAL.get(y)
    print(f"{y:>6}{row['6.5-7.5 t']:>12.0f}{row['7.6-10 t']:>12.0f}{row['10.1-12 t']:>12.0f}"
          f"{row['12.1-16 t']:>12.0f}{tot:>15.0f}"
          f"{(f'{gt:,}' if gt else '—'):>11}{(f'{tot - gt:+.0f}' if gt else '—'):>10}")

# ---------------------------------------------------------------- comparison at 2026-06-30
print("\n" + "=" * 118)
print("AT 30.06.2026 — government vs our model vs rebuilt")
print("=" * 118)
# Live workbook 2026F: LD 6,101 ; MD+F 4,659 (12 t folded into MD in V18).
WB_2026 = {"LD": 6101.0, "MD": 4659.0}
md_mix = {cls: flow_conv_2026[cls] for cls in ("7.6-10 t", "10.1-12 t")}
md_tot = sum(md_mix.values())
wb_split = {"7.6-10 t": WB_2026["MD"] * md_mix["7.6-10 t"] / md_tot,
            "10.1-12 t": WB_2026["MD"] * md_mix["10.1-12 t"] / md_tot,
            "12.1-16 t": 0.0}
OUR = {"6.5-7.5 t": WB_2026["LD"], **wb_split}

comp = []
print(f"{'class':<12}{'gov':>9}{'ours (workbook 2026F)':>24}{'rebuilt':>11}{'gap gov-ours':>15}{'gap gov-rebuilt':>17}")
for cls in CLASSES:
    g = GOV_2026[cls]
    o = OUR[cls]
    rb = rebuilt[2026][cls]
    comp.append({"class": cls, "gov": g, "ours_2026F": round(o), "rebuilt": round(rb),
                 "gap_gov_ours": round(g - o), "gap_gov_rebuilt": round(g - rb)})
    print(f"{cls:<12}{g:>9,}{o:>24,.0f}{rb:>11,.0f}{g - o:>+15,.0f}{g - rb:>+17,.0f}")
print(f"{'TOTAL':<12}{GOV_TOTAL_2026:>9,}{sum(OUR.values()):>24,.0f}{sum(rebuilt[2026].values()):>11,.0f}"
      f"{GOV_TOTAL_2026 - sum(OUR.values()):>+15,.0f}{GOV_TOTAL_2026 - sum(rebuilt[2026].values()):>+17,.0f}")

# ---------------------------------------------------------------- old tail / floor
print("\n" + "=" * 118)
print("OLD TAIL — cohorts first registered 1999-2010, still on the road at 30.06.2026")
print("=" * 118)
ALL_BANDS = FLOW_BANDS
old_regs = {y: sum(flow[b][y] for b in ALL_BANDS) for y in range(1999, 2011)}
print("  UTI flow registrations 1999-2010 (all bands):", sum(old_regs.values()))
print("  our IML Emerging curve retains at 2026     :", round(conv(2026, flow, ALL_BANDS, CURVE)))
print("  ministry: still on the road                : 1,680  (12% of 14,019)")
print("  implied survival of the recorded block     :",
      f"{1680 / sum(old_regs.values()) * 100:.1f}%")

print("\n  hard ceiling test — best case for ANY survival curve on the recorded flow:")
print("    every unit ever recorded, 1994-2025, all bands, still alive:",
      f"{sum(sum(flow[b].values()) for b in ALL_BANDS):,}")
print("    ministry parc at 30.06.2026: 14,019  ->",
      f"{14019 - sum(sum(flow[b].values()) for b in ALL_BANDS):+,} unreachable")

print("\n  floor scenarios on the recorded flow (target: 14,019):")
floor_rows = []
for min_age, floor in [(15, 0.5), (15, 0.8), (15, 0.9), (15, 1.0),
                       (16, 0.9), (16, 1.0), (19, 1.0)]:
    c = floored(CURVE, floor, min_age)
    t = conv(2026, flow, ALL_BANDS, c)
    t_old = conv(2026, {b: {y: flow[b][y] for y in range(1999, 2011)} for b in ALL_BANDS}, ALL_BANDS, c)
    floor_rows.append({"min_age": min_age, "floor": floor, "total_2026": round(t), "old_block_2026": round(t_old)})
    print(f"    floor={floor:>4} from age {min_age}: total={t:>8,.0f}  1999-2010 block={t_old:>6,.0f}  (gov 1,680)")

# ---------------------------------------------------------------- write csv outputs
with (OUT / "rebuilt_israel_parc_by_class.csv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["year"] + list(CLASSES) + ["rebuilt_total", "gov_total", "delta_vs_gov", "source"])
    for y in YEARS:
        row = rebuilt[y]
        tot = sum(row.values())
        gt = GOV_TOTAL.get(y)
        src = "government (MOT via UTI)" if gt else "flow shape x per-class anchor"
        w.writerow([y] + [round(row[c]) for c in CLASSES] + [round(tot), gt or "", (round(tot - gt) if gt else ""), src])

with (OUT / "per_class_table_2026-06-30.csv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["ministry_class", "gov_trucks", "gov_share", "avg_age", "mkt_avg_age",
                "ours_workbook_2026F", "gap_gov_ours", "rebuilt", "gap_gov_rebuilt"])
    for r in comp:
        w.writerow([r["class"], r["gov"], round(r["gov"] / GOV_TOTAL_2026, 4),
                    GOV_AVG_AGE[r["class"]], MKT_AVG_AGE[r["class"]],
                    r["ours_2026F"], r["gap_gov_ours"], r["rebuilt"], r["gap_gov_rebuilt"]])

(BASE / "rebuild_method.json").write_text(json.dumps({
    "gov_parc_2026_06_30_by_class": GOV_2026,
    "gov_parc_total_2026_06_30": GOV_TOTAL_2026,
    "gov_parc_totals_by_year": GOV_TOTAL,
    "flow_conv_2026_by_class": {c: round(v) for c, v in flow_conv_2026.items()},
    "anchor_factor_k": {c: (round(v, 4) if v else None) for c, v in k.items()},
    "workbook_2026F": WB_2026,
    "our_2026F_split_by_ministry_class": {c: round(v) for c, v in OUR.items()},
    "rebuilt_2026_by_class": {c: round(v) for c, v in rebuilt[2026].items()},
    "floor_scenarios": floor_rows,
}, indent=2), encoding="utf-8")

print("\nwrote:", OUT)
