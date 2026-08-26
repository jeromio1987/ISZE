import csv
from pathlib import Path

rows = list(csv.DictReader(Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_spu_by_distributor.csv").open(encoding="utf-8-sig")))
rows = [r for r in rows if r["year"] == "2026" and (r.get("spend_per_unit_eur") or "").strip()]
for r in sorted(rows, key=lambda x: x["country"]):
    spu = float(r["spend_per_unit_eur"])
    mx = r.get("max_spend_eur") or "-"
    cap = r.get("gps_capture_vs_max") or "-"
    print(f"{r['country']:20s} code={r['distributor_code']:12s} spu={spu:8.1f} max={mx} capture={cap}")

# Kazakhstan any year
for r in rows if False else []:
    pass
kz = [r for r in list(csv.DictReader(Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_spu_by_distributor.csv").open(encoding="utf-8-sig"))) if "Kazakh" in (r.get("country") or "") or r.get("distributor_code") == "KTK"]
print("KAZ rows", len(kz))
for r in kz[:5]:
    print(r)
