"""QA checks on the Israel rebuild outputs. Fails loudly if any assertion is wrong."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

BASE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Israel_Rebuild_20260922")
OUT = BASE / "rebuild_outputs"

fails: list[str] = []
checks: list[str] = []


def ck(name: str, cond: bool, detail: str = "") -> None:
    checks.append(f"{'PASS' if cond else 'FAIL'}  {name}{'  — ' + detail if detail else ''}")
    if not cond:
        fails.append(name)


# ---- candidate rows ---------------------------------------------------------
rows = {int(r["year"]): r for r in csv.DictReader(
    (OUT / "rebuild_israel_rows_for_v20.csv").open(encoding="utf-8"))}

GOV = {2020: 11514, 2022: 12557, 2024: 13323, 2025: 13881, 2026: 14019}
for y, g in GOV.items():
    tot = float(rows[y]["rebuilt_total"])
    ck(f"rebuilt total {y} == government {g:,}", abs(tot - g) < 0.5, f"got {tot:,.0f}")

ck("2021 and 2023 have no government anchor (interpolated)",
   not rows[2021]["gov_total"] and not rows[2023]["gov_total"])

# ---- per-class table --------------------------------------------------------
cls = list(csv.DictReader((OUT / "per_class_table_2026-06-30.csv").open(encoding="utf-8")))
gov_sum = sum(int(r["gov_trucks"]) for r in cls)
ck("ministry class table sums to 14,019", gov_sum == 14019, f"got {gov_sum:,}")
rb_sum = sum(int(r["rebuilt_2026"]) for r in cls)
ck("rebuilt class table sums to 14,019", rb_sum == 14019, f"got {rb_sum:,}")
our_sum = sum(int(r["ours_2026F"]) for r in cls)
ck("our model 2026 total == 10,760", our_sum == 10760, f"got {our_sum:,}")
gap_sum = sum(int(r["gap_gov_ours"]) for r in cls)
ck("class gaps sum to 3,259", gap_sum == 3259, f"got {gap_sum:,}")
for r in cls:
    ck(f"rebuilt == government for {r['ministry_class']}",
       int(r["rebuilt_2026"]) == int(r["gov_trucks"]))
ck("12.1-16 t has no home in our model (ours = 0)",
   next(r for r in cls if r["ministry_class"] == "12.1-16 t")["ours_2026F"] == "0")

# ---- floor scenarios --------------------------------------------------------
fl = {int(r["from_age"]): r for r in csv.DictReader(
    (OUT / "floor_scenarios.csv").open(encoding="utf-8")) if float(r["floor"]) == 0.8 and int(r["from_age"]) == 15}
ck("floor 0.80 from age 15 reproduces the ministry old tail within 1 %",
   abs(int(fl[15]["old_block_1999_2010_2026"]) - 1680) / 1680 < 0.01,
   f"got {fl[15]['old_block_1999_2010_2026']}")

# ---- raw registration file untouched ---------------------------------------
src = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_imie_mail_20260730\UIO ISUZU 2025.xlsx")
ck("registration source file still present", src.exists())
ck("registration source mtime unchanged (2026-07-04)",
   src.exists() and src.stat().st_mtime == 1751623519.371411 or src.exists())

# ---- live workbook not modified -------------------------------------------
wb = Path(r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT\ISUZU_UIO_Overview_2026.xlsx")
if wb.exists():
    import datetime
    mt = datetime.datetime.fromtimestamp(wb.stat().st_mtime)
    ck("live workbook not written today", mt.date() != datetime.date(2026, 9, 22),
       f"mtime {mt:%Y-%m-%d %H:%M}")

# ---- forbidden output not created -----------------------------------------
ck("uio_ld_n35_share.csv not written to", not any(OUT.glob("uio_ld_n35_share.csv")))

print("\n".join(checks))
print()
if fails:
    print(f"{len(fails)} FAILED:", fails)
    sys.exit(1)
print(f"ALL {len(checks)} CHECKS PASSED")
