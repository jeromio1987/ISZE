from pathlib import Path
import re

# Read Nuno SOURCE fully
p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_nuno_kpi_portugal_20261001\SOURCE.md")
print(p.read_text(encoding="utf-8-sig"))

# Scan logs mentioning Nuno
for path in [
    Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_scan_nuno_machado_log.txt"),
    Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\nuno_machado_sales_to_dealer_20260903\SCAN_LOG.txt"),
]:
    if path.exists():
        print("====", path)
        print(path.read_text(encoding="utf-8", errors="ignore")[:4000])

# Search entire ISZE for filenames with IMOTORS/PORTUGAL + BO/BACKORDER/OVERVIEW
root = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
hits = []
for p in root.rglob("*"):
    try:
        if not p.is_file():
            continue
    except Exception:
        continue
    n = p.name.upper()
    if ("IMOTOR" in n or "PORTUGAL" in n or "ASTARA" in n) and any(x in n for x in ["BO ", "BO_", "_BO", "BACKORDER", "BACK ORDER", "BACK-ORDER", "OVERVIEW", "B/O"]):
        hits.append(p)
    # also generic Astara backorder reports
    if "BACKORDER" in n.replace(" ","") or "BACK ORDER" in n:
        if "PORTUGAL" in str(p).upper() or "ASTARA" in str(p).upper() or "IMOTOR" in str(p).upper() or "NUNO" in str(p).upper():
            hits.append(p)

print("\nSTRICT HITS", len(hits))
for h in sorted(set(hits), key=lambda x: str(x)):
    print(h)

# Visit brief mention of BO file?
brief = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Imotors_Portugal_IDS_2026\visit_3_dealers_Bart\VISIT_BRIEF_Jerome_IDS_test_case.md")
if brief.exists():
    t = brief.read_text(encoding="utf-8", errors="ignore")
    print("\n==== BRIEF lines with BO/Nuno/attach ====")
    for i,line in enumerate(t.splitlines()):
        if re.search(r"bo|nuno|back.?order|attach|kpi|fill", line, re.I):
            print(f"{i}: {line[:220]}")
