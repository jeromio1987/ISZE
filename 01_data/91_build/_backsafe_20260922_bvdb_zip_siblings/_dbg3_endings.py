import collections
import tempfile
from pathlib import Path

live = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\pms_opportunity_matrix.csv")
tmp = Path(tempfile.gettempdir()) / "pms_opp_rebuild_preview.csv"
pack = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\BVDB_PBI_Data_Upload_2026-09-23\03_PMS\pms_opportunity_matrix.csv")

for label, p in (("live", live), ("builder output", tmp), ("pack copy", pack)):
    raw = p.read_bytes()
    c = collections.Counter(raw)
    print(f"{label:16s} {len(raw):>9} bytes  CR={c[13]:>5} LF={c[10]:>5} "
          f"BOM={raw[:3] == b'\\xef\\xbb\\xbf'}  ends={raw[-10:]!r}")
