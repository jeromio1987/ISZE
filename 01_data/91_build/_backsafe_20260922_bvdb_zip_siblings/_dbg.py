import io, csv
from pathlib import Path
p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_spu_by_family.csv")
raw = p.read_bytes()
text = raw.decode("utf-8-sig")
body = text[:-1] if text.endswith("\n") else text
lines = body.split("\n")
print("line0 repr:", repr(lines[0][:120]))
reader = list(csv.reader(io.StringIO(body)))
header = [c.strip() for c in reader[0]]
out = io.StringIO()
w = csv.writer(out, lineterminator="\n")
w.writerow(header + ["period_basis", "coverage_note"])
print("written repr:", repr(out.getvalue()[:120]))
print("equal:", out.getvalue().rstrip("\n") == lines[0])
