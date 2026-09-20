import sys

sys.path.insert(0, r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism")
from modules.pms_capture_config import (  # noqa: E402
    BUCKET_SERVICES_PER_YEAR,
    BUCKET_SERVICES_PER_YEAR_OVERRIDES,
    N35_SHARE,
)

base = BUCKET_SERVICES_PER_YEAR["cv_std"]
print("cv_std base (N75 basis):", base)
print()
print("market        n35_share   cv_std now")
for db, s in sorted(N35_SHARE.items(), key=lambda kv: -kv[1]):
    rate = BUCKET_SERVICES_PER_YEAR_OVERRIDES.get(db, {}).get("cv_std", base)
    print(f"  {db:12s} {s:8.4f}   {rate:.4f}")
print()
print("markets with no measured N35 fleet (must be unchanged at", base, "):")
for db in ("UTI", "GREECE", "BELGIUM", "GERMANY", "IRELAND", "MALTA", "CYPRUS", "PORTUGAL",
           "SWEDEN", "NORWAY", "DENMARK", "FINLAND", "ICELAND", "UMI", "IUK", "HUNGARY",
           "ROMANIA"):
    r = BUCKET_SERVICES_PER_YEAR_OVERRIDES.get(db, {}).get("cv_std", base)
    flag = "  <-- MOVED" if abs(r - base) > 1e-9 else ""
    print(f"  {db:12s} {r:.4f}{flag}")
