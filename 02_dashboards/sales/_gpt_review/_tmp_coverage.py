import csv
from pathlib import Path

root = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
gps = list(csv.DictReader((root / "01_data/00_derived/gps_spu_by_distributor.csv").open(encoding="utf-8-sig")))
gps25 = {r["distributor_code"]: float(r["total_sales_eur"]) for r in gps if r["year"] == "2025"}
total = sum(gps25.values())
print(f"18-market GPS billed CY2025: {total/1e6:.2f}M n={len(gps25)}")
print("all codes", sorted(gps25.keys()))
five = ["ITUK", "IUK", "IRELAND", "UTI", "GREECE"]
five_sum = sum(gps25.get(d, 0) for d in five)
print(f"five: {five_sum/1e6:.2f}M = {100*five_sum/total:.1f}%")
for d in ["GERMANY", "BELGIUM", "PORTUGAL", "ISUZU_DE", "ISUZU_BE", "ISUZU_PT"]:
    print(d, gps25.get(d))
# fuzzy
for d, v in sorted(gps25.items()):
    if any(x in d.upper() for x in ("GER", "BEL", "PORT", "DE", "BE", "PT")):
        print("hit", d, v / 1e6)
six = five + ["PORTUGAL"]
six_sum = sum(gps25.get(d, 0) for d in six if d in gps25)
print(f"six with PT: {six_sum/1e6:.2f}M = {100*six_sum/total:.1f}%")
derived = root / "01_data/00_derived"
longs = list(derived.glob("dealer_sellout_long_*_CY2025.csv"))
print("longs", [p.name for p in longs])
