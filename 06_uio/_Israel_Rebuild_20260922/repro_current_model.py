"""Reproduce the current Israel model from the UTI registration bands + IML Emerging curve.

Goal: confirm exactly how the live workbook's Israel LD (6,059 @2025E, 6,101 @2026F)
and Israel MD (4,277 @2025E, 4,659 @2026F) rows are produced, so the rebuild can be
measured against them rather than guessed.
"""
from __future__ import annotations

import json
from pathlib import Path

import openpyxl

BASE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Israel_Rebuild_20260922")
SRC = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_imie_mail_20260730\UIO ISUZU 2025.xlsx"
)

# --- registration flow by band, as read from the xlsx -------------------------
wb = openpyxl.load_workbook(SRC, data_only=True)
ws = wb["גיליון1"]
bands = ["6.5 TON", "7.5 TON", "10TON", "11 TON", "12 TON"]
reg = {b: {} for b in bands}
for r in range(2, 34):
    y = ws.cell(row=r, column=1).value
    for j, b in enumerate(bands, start=2):
        v = ws.cell(row=r, column=j).value
        reg[b][int(y)] = int(v) if v else 0
REG_YEARS = sorted(reg["6.5 TON"])
print("reg years:", REG_YEARS[0], "->", REG_YEARS[-1])

# --- the IML Emerging curve, straight out of '3. UIO Calculation' Section A ---
# Sheet rows: age 1..20 = 1, .99, .98, .97, .96, .95, .9, .85, .8, .75, .7, .6, .5, .4, .3, .2, .15, .1, .05, 0
SHEET_AGE = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
SHEET_EMERGING = [1, .99, .98, .97, .96, .95, .9, .85, .8, .75, .7, .6, .5, .4, .3, .2, .15, .1, .05, 0]


def survive(ref_year: float, regs: dict[int, int], curve: list[float], age_offset: int) -> float:
    """age = ref - reg_year - age_offset, curve indexed from 0."""
    tot = 0.0
    for rgy, units in regs.items():
        if not units:
            continue
        age = ref_year - rgy - age_offset
        if age < 0 or age >= len(curve):
            continue
        tot += units * curve[int(age)]
    return tot


# Interpretation A: curve[age] with age = ref - reg ; curve[0]=1.0 and the sheet's
# "age 1" row is really age 0..1. i.e. shift the sheet list right by one.
CURVE_A = [1.0] + SHEET_EMERGING[:-1]          # index0=1.0, index1=.99 ... index19=.05
# Interpretation B: curve index = ref - reg, sheet row "age 1" is the first year index 0,
# and the 0 at sheet age 20 lands at index 19.
CURVE_B = SHEET_EMERGING[:-1]                   # index0=1, index1=.99 ... index19=.05
# Interpretation C: literal sheet, index = age, list as printed (index0=1 -> age 0)
CURVE_C = SHEET_EMERGING

print("\n--- reproduce LD (6.5+7.5) ---")
ld_regs = {y: reg["6.5 TON"][y] + reg["7.5 TON"][y] for y in REG_YEARS}
md_regs = {y: reg["10TON"][y] + reg["11 TON"][y] + reg["12 TON"][y] for y in REG_YEARS}

for name, curve in [("A", CURVE_A), ("B", CURVE_B), ("C", CURVE_C)]:
    t2025 = survive(2025, ld_regs, curve, 0)
    t2024 = survive(2024, ld_regs, curve, 0)
    m2025 = survive(2025, md_regs, curve, 0)
    m2024 = survive(2024, md_regs, curve, 0)
    print(f"  curve {name}: LD2024={t2024:9.0f} LD2025={t2025:9.0f} | MD2024={m2024:9.0f} MD2025={m2025:9.0f}")

print("\ntarget from live workbook: LD2024=6,071 LD2025E=6,059 | MD2024=3,978 MD2025E=4,277")

# --- survivorship of the 1999-2010 tail ---------------------------------------
old = {y: ld_regs[y] + md_regs[y] for y in range(1999, 2011)}
print("\nregistrations 1999-2010, all bands:", sum(old.values()), old)
for name, curve in [("A", CURVE_A), ("B", CURVE_B)]:
    tot = 0
    detail = {}
    for y, u in old.items():
        age = 2026 - y
        s = curve[age] if 0 <= age < len(curve) else 0.0
        detail[y] = round(u * s)
        tot += u * s
    print(f"  curve {name} retained at 2026: {tot:.0f}  {detail}")
print("  government (slide 14): 1,680 trucks first registered 1999-2010 still on the road")

# --- whole-fleet convolution for a few reference years -------------------------
all_regs = {y: ld_regs[y] + md_regs[y] for y in REG_YEARS}
print("\nfleet convolution (all bands) using curve A:")
for ref in (2020, 2022, 2024, 2025, 2026):
    print(f"  {ref}: LD={survive(ref, ld_regs, CURVE_A, 0):8.0f}  MD+12t={survive(ref, md_regs, CURVE_A, 0):8.0f}")

( BASE / "repro_current_model.json").write_text(json.dumps({
    "reg_by_band": reg,
    "ld_regs": ld_regs,
    "md_regs": md_regs,
    "old_tail_regs_1999_2010": old,
}, indent=2), encoding="utf-8")
print("\nwrote:", BASE / "repro_current_model.json")
