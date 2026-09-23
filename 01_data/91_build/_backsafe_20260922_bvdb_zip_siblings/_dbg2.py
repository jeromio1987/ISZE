import collections
from pathlib import Path
for n in ("gps_spu_by_family.csv", "gps_spu_pms.csv", "aim_gps_matrix.csv", "gps_spu_by_distributor.csv"):
    raw = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived") .joinpath(n).read_bytes()
    c = collections.Counter(raw)
    print(n, "len", len(raw))
    print("   CR count", c[13], "LF count", c[10], "last 6 bytes", raw[-6:])
