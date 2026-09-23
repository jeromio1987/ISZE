import hashlib
import zipfile
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
Z = ROOT / "09_meetings"
for n in ("BVDB_PBI_Data_Upload_2026-09-23.zip",
          "BVDB_PBI_Data_Upload_2026-09-23.zip.bak_before_forecast_caveat_20260922",
          "BVDB_PBI_Data_Upload_2026-09-23_corrected_20260922.zip"):
    p = Z / n
    st = p.stat()
    with zipfile.ZipFile(p) as zf:
        members = len(zf.namelist())
    print(f"{n}")
    print(f"   bytes={st.st_size}  kb={st.st_size/1024:.1f}  members={members}")
    print(f"   mtime=2026-09-22 {__import__('datetime').datetime.fromtimestamp(st.st_mtime):%H:%M:%S}")
    print(f"   sha256={hashlib.sha256(p.read_bytes()).hexdigest()}")

print()
print("derived sibling files:")
for n in ("gps_spu_by_distributor.csv", "gps_spu_by_family.csv", "gps_spu_pms.csv",
          "aim_gps_matrix.csv"):
    p = ROOT / "01_data" / "00_derived" / n
    st = p.stat()
    print(f"   {n:32s} {st.st_size:>8} bytes  "
          f"{__import__('datetime').datetime.fromtimestamp(st.st_mtime):%Y-%m-%d %H:%M:%S}  "
          f"sha256={hashlib.sha256(p.read_bytes()).hexdigest()[:24]}")
