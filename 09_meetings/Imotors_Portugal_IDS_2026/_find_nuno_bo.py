from pathlib import Path
import re

roots = [
    Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX"),
    Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Imotors_Portugal_IDS_2026"),
    Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\08_Distributor"),
]
# any file with nuno in path/name, or portugal kpi/bo nearby
cands = []
for root in roots:
    if not root.exists():
        continue
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        s = str(p).lower()
        n = p.name.lower()
        if "nuno" in s or "portugal" in n or "imotor" in n or "astara" in n:
            if any(x in n for x in [".xlsx",".xls",".csv",".pdf",".txt",".msg",".eml",".md"]):
                cands.append(p)

print("CANDIDATES", len(cands))
for p in sorted(cands, key=lambda x: x.stat().st_mtime, reverse=True)[:80]:
    print(f"{p.stat().st_mtime:.0f}\t{p.stat().st_size}\t{p}")

# deeper: filenames containing bo
print("\n=== NAME HAS BO / BACK ===")
for root in roots:
    if not root.exists(): continue
    for p in root.rglob("*"):
        if not p.is_file(): continue
        n = p.name.upper()
        if re.search(r"\bBO\b|BACK.?ORDER|B_O|B/O|BACKORDER", n) or "BO_" in n or "_BO" in n or " BO" in n:
            print(p)

# search text mentions of nuno + bo in SOURCE / md / txt under inbox
print("\n=== TEXT HITS nuno+bo ===")
for root in [Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_nuno_kpi_portugal_20261001"),
             Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_imotors_bo_compare_20261006")]:
    if not root.exists(): continue
    for p in root.rglob("*"):
        if p.suffix.lower() in {".md",".txt",".json"} and p.is_file():
            t = p.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"bo|back.?order|nuno", t, re.I):
                print("---", p)
                for i,line in enumerate(t.splitlines()):
                    if re.search(r"bo|back|nuno|attach|xlsx|overview", line, re.I):
                        print(f"{i}: {line[:200]}")
