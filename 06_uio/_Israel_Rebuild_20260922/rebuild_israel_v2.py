"""Build the rebuilt Israel rows on the government parc as the primary anchor (v2).

Method
------
1. LEVEL — the Israeli Ministry of Transport parc for Isuzu trucks, quoted in the UTI
   July 2026 deck (slide 14, "based on MOT data") and carried in V20_SPEC.md Problem 4.
   Those government totals are used directly for every year the source quotes.
2. CLASS SPLIT at 30.06.2026 — the ministry's four weight bands
   (6.5-7.5 t 8,610 | 7.6-10 t 2,485 | 10.1-12 t 2,697 | 12.1-16 t 227), which sum to
   exactly the quoted 14,019.
3. SHAPE — the UTI registration flow table 1994-2025 (UIO ISUZU 2025.xlsx, sheet
   'גיליון1') convolved with the IML Emerging CV curve, used ONLY as a shape index for
   (a) the mix between the ministry's classes and (b) the years the ministry does not
   quote. It never sets the level where a government number exists.
4. OLD TAIL — an age floor for trucks over 15 years, calibrated against the ministry's
   1999-2010 cohort (1,680 trucks, 12% of the fleet, still on the road).
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

CLASSES = ["6.5-7.5 t", "7.6-10 t", "10.1-12 t", "12.1-16 t"]
CLASS_BANDS = {
    "6.5-7.5 t": ["6.5 TON", "7.5 TON"],
    "7.6-10 t": ["10TON"],
    "10.1-12 t": ["11 TON", "12 TON"],
    "12.1-16 t": [],
}
GOV_2026 = {"6.5-7.5 t": 8610, "7.6-10 t": 2485, "10.1-12 t": 2697, "12.1-16 t": 227}
GOV_TOTAL_2026 = sum(GOV_2026.values())

# Ministry / UTI parc totals quoted per year (V20_SPEC.md Problem 4 table).
GOV_TOTAL = {2020: 11514, 2022: 12557, 2024: 13323, 2025: 13881, 2026: 14019}
GOV_AVG_AGE = {"6.5-7.5 t": 9.4, "7.6-10 t": 6.2, "10.1-12 t": 5.9, "12.1-16 t": 5.6}
MKT_AVG_AGE = {"6.5-7.5 t": 9.8, "7.6-10 t": 10.7, "10.1-12 t": 7.3, "12.1-16 t": 9.1}

SHEET_EMERGING = [1, .99, .98, .97, .96, .95, .9, .85, .8, .75, .7, .6, .5, .4, .3, .2, .15, .1, .05, 0]
CURVE = [1.0] + SHEET_EMERGING[:-1]
DEVELOPED = [1, .99, .98, .97, .96, .95, .9, .8, .7, .55, .4, .3, .2, .1, .05, 0]


def floored(curve: list[float], floor: float | None, min_age: int) -> list[float]:
    c = list(curve)
    if floor is None:
        return c
    for age in range(min_age, len(c)):
        c[age] = max(c[age], floor)
    return c


def cohort_units(ref: float, bands: list[str], curve: list[float]) -> list[tuple[int, float]]:
    """(registration year, surviving units) for the named bands at reference year ref."""
    out = []
    for b in bands:
        for rgy, units in flow[b].items():
            if not units:
                continue
            age = ref - rgy
            if age < 0 or age >= len(curve):
                continue
            out.append((rgy, units * curve[int(age)]))
    return out


def conv(ref: float, bands: list[str], curve: list[float]) -> float:
    return sum(u for _, u in cohort_units(ref, bands, curve))


REF = 2026
flow_conv_2026 = {c: conv(REF, CLASS_BANDS[c], CURVE) for c in CLASSES}
k = {c: (GOV_2026[c] / flow_conv_2026[c]) if flow_conv_2026[c] else None for c in CLASSES}

# 12.1-16 t has no registration flow to shape it: hold the ministry anchor flat for
# 2013+ and decay it on the developed curve for the earlier back-cast. Flagged.
def c1216(y: float) -> float:
    if y >= 2013:
        return float(GOV_2026["12.1-16 t"])
    age = 2026 - 2013
    return float(GOV_2026["12.1-16 t"]) * DEVELOPED[min(int(age), len(DEVELOPED) - 1)]


def shaped(y: float) -> dict[str, float]:
    """Flow-shape × per-class anchor, before the level adjustment."""
    row = {}
    for c in CLASSES:
        if not CLASS_BANDS[c]:
            row[c] = c1216(y)
        else:
            row[c] = conv(y, CLASS_BANDS[c], CURVE) * k[c]
    return row


# ---------------------------------------------------------------- level adjustment
gov_years = sorted(GOV_TOTAL)
adj: dict[int, float] = {}
for y in gov_years:
    adj[y] = GOV_TOTAL[y] / sum(shaped(y).values())
# interpolate the adjustment for the unquoted government years between anchors
for y in range(gov_years[0], gov_years[-1] + 1):
    if y in adj:
        continue
    lo = max(a for a in gov_years if a < y)
    hi = min(a for a in gov_years if a > y)
    t = (y - lo) / (hi - lo)
    adj[y] = adj[lo] + t * (adj[hi] - adj[lo])

print("per-class anchor k = gov(2026) / flow-conv(2026):")
for c in CLASSES:
    print(f"  {c:<12} {'n/a (no flow)' if k[c] is None else round(k[c], 4)}")
print("\nlevel adjustment by year (gov total / flow-shaped total):")
for y in sorted(adj):
    tag = "government" if y in GOV_TOTAL else "interpolated"
    print(f"  {y}: {adj[y]:.4f}   [{tag}]")

PRE_ADJ = adj[gov_years[0]]
POST_ADJ = 1.0

YEARS = list(range(1994, 2031))
rebuilt: dict[int, dict[str, float]] = {}
for y in YEARS:
    if y < gov_years[0]:
        a = PRE_ADJ
        tag = "flow shape (no government anchor before 2020)"
    elif y in adj:
        a = adj[y]
        tag = "government" if y in GOV_TOTAL else "government-interpolated"
    else:
        a = POST_ADJ
        tag = "flow shape carried forward (no government data)"
    row = shaped(y)
    row = {c: v * a for c, v in row.items()}
    rebuilt[y] = row
    rebuilt[y]["_tag"] = tag  # type: ignore[assignment]

# ---------------------------------------------------------------- report
print("\n" + "=" * 122)
print("REBUILT ISRAEL PARC BY MINISTRY WEIGHT CLASS  (government-anchored, whole trucks)")
print("=" * 122)
print(f"{'year':>6}{'6.5-7.5 t':>12}{'7.6-10 t':>12}{'10.1-12 t':>12}{'12.1-16 t':>12}"
      f"{'rebuilt total':>15}{'gov total':>11}{'delta':>9}  source")
for y in YEARS:
    if y < 2008 and y not in (2020, 2026):
        continue
    row = rebuilt[y]
    tot = sum(row[c] for c in CLASSES)
    gt = GOV_TOTAL.get(y)
    print(f"{y:>6}{row['6.5-7.5 t']:>12,.0f}{row['7.6-10 t']:>12,.0f}{row['10.1-12 t']:>12,.0f}"
          f"{row['12.1-16 t']:>12,.0f}{tot:>15,.0f}{(f'{gt:,}' if gt else '—'):>11}"
          f"{(f'{tot - gt:+,.0f}' if gt else '—'):>9}  {row['_tag']}")

# ---------------------------------------------------------------- 2026 comparison
WB_2026 = {"LD": 6101.0, "MD": 4659.0}
md_mix = {c: flow_conv_2026[c] for c in ("7.6-10 t", "10.1-12 t")}
md_tot = sum(md_mix.values())
OUR = {
    "6.5-7.5 t": WB_2026["LD"],
    "7.6-10 t": WB_2026["MD"] * md_mix["7.6-10 t"] / md_tot,
    "10.1-12 t": WB_2026["MD"] * md_mix["10.1-12 t"] / md_tot,
    "12.1-16 t": 0.0,
}

print("\n" + "=" * 122)
print("AT 30.06.2026 — government vs our workbook vs rebuilt")
print("=" * 122)
comp = []
print(f"{'class':<12}{'gov':>8}{'share':>8}{'avg age':>9}{'ours 2026F':>12}{'gap gov-ours':>14}{'rebuilt':>10}")
for c in CLASSES:
    g, o, rb = GOV_2026[c], OUR[c], rebuilt[2026][c]
    comp.append({"class": c, "gov": g, "ours_2026F": round(o), "rebuilt": round(rb),
                 "gap_gov_ours": round(g - o), "gap_gov_rebuilt": round(g - rb)})
    print(f"{c:<12}{g:>8,}{g / GOV_TOTAL_2026:>8.1%}{GOV_AVG_AGE[c]:>9.1f}{o:>12,.0f}"
          f"{g - o:>+14,.0f}{rb:>10,.0f}")
print(f"{'TOTAL':<12}{GOV_TOTAL_2026:>8,}{1:>8.1%}{'':>9}{sum(OUR.values()):>12,.0f}"
      f"{GOV_TOTAL_2026 - sum(OUR.values()):>+14,.0f}{sum(rebuilt[2026][c] for c in CLASSES):>10,.0f}")

# ---------------------------------------------------------------- gap decomposition
print("\n" + "=" * 122)
print("GAP DECOMPOSITION at 30.06.2026  (our total 10,760 vs government 14,019 = -3,259)")
print("=" * 122)
gap = GOV_TOTAL_2026 - sum(OUR.values())
blocks = [
    ("12.1-16 t class has no row in our model at all", GOV_2026["12.1-16 t"], 0.0,
     "measured — a whole class is missing"),
    ("7.6-10 t under-counted (our 10 t column against the ministry's band)",
     GOV_2026["7.6-10 t"], OUR["7.6-10 t"], "measured, accrual cause"),
    ("10.1-12 t under-counted (our 11+12 t columns against the ministry's band)",
     GOV_2026["10.1-12 t"], OUR["10.1-12 t"], "measured, accrual cause"),
    ("6.5-7.5 t under-counted (our whole LD row)",
     GOV_2026["6.5-7.5 t"], OUR["6.5-7.5 t"], "measured, accrual cause"),
]
print(f"{'block':<72}{'gov':>8}{'ours':>9}{'gap':>9}{'% of 3,259':>11}  basis")
sum_gap = 0.0
for label, g, o, basis in blocks:
    d = g - o
    sum_gap += d
    print(f"{label:<72}{g:>8,.0f}{o:>9,.0f}{d:>+9,.0f}{d / gap * 100:>10.1f}%  {basis}")
print(f"{'sum':<72}{'':>8}{'':>9}{sum_gap:>+9,.0f}{sum_gap / gap * 100:>10.1f}%")

# ---------------------------------------------------------------- old tail / floor
print("\n" + "=" * 122)
print("OLD TAIL — vehicles first registered 1999-2010, still on the road at 30.06.2026")
print("=" * 122)
ALL_BANDS = FLOW_BANDS
old_flow = {b: {y: flow[b][y] for y in range(1999, 2011)} for b in ALL_BANDS}
saved_flow = flow
flow = old_flow  # noqa: F841  (rebind for the helper)
old_registered = sum(sum(flow[b].values()) for b in ALL_BANDS)
old_our = conv(2026, ALL_BANDS, CURVE)
flow = saved_flow

print(f"  UTI flow registrations 1999-2010 (all bands) : {old_registered:,}")
print(f"  our IML Emerging curve retains at 2026       : {old_our:,.0f}")
print(f"  ministry: still on the road                  : 1,680  (12% of 14,019)")
print(f"  implied survival of the recorded block       : {1680 / old_registered * 100:.1f}%"
      f"   vs our curve's {old_our / old_registered * 100:.1f}%")
print(f"  shortfall our curve creates on that tail     : {1680 - old_our:+,.0f}")

print("\n  HARD CEILING — the best any survival curve could do on the recorded flow:")
cum = sum(sum(flow[b].values()) for b in ALL_BANDS)
print(f"    every unit UTI ever recorded 1994-2025, all bands, still alive : {cum:,}")
print(f"    ministry parc at 30.06.2026                                    : {14_019:,}")
print(f"    unreachable                                                      : {14_019 - cum:+,}")

print("\n  floor scenarios on the recorded flow alone (never enough on its own):")
floor_rows = []
for min_age, floor in [(15, 0.5), (15, 0.8), (15, 0.9), (15, 0.95), (15, 1.0),
                       (16, 1.0), (19, 1.0)]:
    c = floored(CURVE, floor, min_age)
    tot = conv(2026, ALL_BANDS, c)
    flow = old_flow
    old_c = conv(2026, ALL_BANDS, c)
    flow = saved_flow
    floor_rows.append({"min_age": min_age, "floor": floor,
                       "total_2026": round(tot), "old_block_1999_2010_2026": round(old_c)})
    print(f"    floor={floor:<5} from age {min_age:>2}: fleet {tot:>8,.0f}   1999-2010 block {old_c:>6,.0f}"
          f"   (ministry 1,680)")

# ---------------------------------------------------------------- implied age check
print("\n" + "=" * 122)
print("VALIDATION — implied average age per class from the rebuilt parc vs the ministry's own")
print("=" * 122)
print(f"{'class':<12}{'our implied avg age':>21}{'ministry states':>17}{'market avg':>12}")
for c in CLASSES:
    if not CLASS_BANDS[c]:
        print(f"{c:<12}{'n/a (no cohort detail)':>21}{GOV_AVG_AGE[c]:>17.1f}{MKT_AVG_AGE[c]:>12.1f}")
        continue
    cohorts = cohort_units(2026, CLASS_BANDS[c], CURVE)
    units = sum(u for _, u in cohorts)
    wa = sum((2026 - rgy) * u for rgy, u in cohorts) / units if units else 0
    print(f"{c:<12}{wa:>21.1f}{GOV_AVG_AGE[c]:>17.1f}{MKT_AVG_AGE[c]:>12.1f}")

# ---------------------------------------------------------------- write outputs
with (OUT / "rebuilt_israel_parc_by_class.csv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["year"] + CLASSES + ["rebuilt_total", "gov_total", "delta_vs_gov", "basis"])
    for y in YEARS:
        row = rebuilt[y]
        tot = sum(row[c] for c in CLASSES)
        gt = GOV_TOTAL.get(y)
        w.writerow([y] + [round(row[c]) for c in CLASSES] + [round(tot), gt or "",
                    (round(tot - gt) if gt else ""), row["_tag"]])

with (OUT / "per_class_table_2026-06-30.csv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["ministry_class", "gov_trucks", "gov_share", "ministry_avg_age", "market_avg_age",
                "ours_2026F", "gap_gov_ours", "rebuilt_2026", "gap_gov_rebuilt"])
    for r in comp:
        w.writerow([r["class"], r["gov"], round(r["gov"] / GOV_TOTAL_2026, 4),
                    GOV_AVG_AGE[r["class"]], MKT_AVG_AGE[r["class"]], r["ours_2026F"],
                    r["gap_gov_ours"], r["rebuilt"], r["gap_gov_rebuilt"]])

(BASE / "rebuild_method.json").write_text(json.dumps({
    "gov_parc_2026_06_30_by_class": GOV_2026,
    "gov_parc_total_2026_06_30": GOV_TOTAL_2026,
    "gov_parc_totals_by_year": GOV_TOTAL,
    "flow_conv_2026_by_class": {c: round(v) for c, v in flow_conv_2026.items()},
    "anchor_factor_k": {c: (round(v, 4) if v else None) for c, v in k.items()},
    "level_adjustment": {str(y): round(v, 4) for y, v in sorted(adj.items())},
    "workbook_2026F": WB_2026,
    "our_2026F_split_by_ministry_class": {c: round(v) for c, v in OUR.items()},
    "rebuilt_2026_by_class": {c: round(rebuilt[2026][c]) for c in CLASSES},
    "old_tail": {"registrations_1999_2010": old_registered, "our_curve_2026": round(old_our),
                 "ministry_2026": 1680},
    "cumulative_flow_all_bands": cum,
    "floor_scenarios": floor_rows,
}, indent=2), encoding="utf-8")

print("\nwrote:", OUT)
