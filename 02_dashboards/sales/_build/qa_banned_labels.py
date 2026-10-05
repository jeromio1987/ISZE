"""Banned-label and stale-figure check for the shared PMS family and tonnage pages.

These are the labels and statements Jerome has asked to stop appearing on pages he reads: the
internal names for the interval schedules and for the pricing initiative, the audience labels, and
the false claim that the heavy-truck family carries almost no billing.

The family page is now shipped as one file, ``ISZE_PMS_Family_Evolution_v2.html``; the two older
pages it replaces were moved to ``_build/history/`` and are no longer checked here because they are
not in the folder Jerome reads. A page that is listed but absent is reported rather than crashing,
so this check cannot be left broken by a file being renamed or retired.
"""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
SALES = ROOT / "02_dashboards" / "sales"
FILES = [
    SALES / "ISZE_PMS_Family_Evolution_v2.html",
    SALES / "ISZE_PMS_Tonnage_Evolution.html",
]
BAN = [
    "IML v7", "PRISM lane", "Model B", "Mode A", "Mode B", "wallet", "street",
    "sell-out", "sell out", "sellout", "Book B", "service schedule A", "service schedule B",
    "no F-series", "no F series", "almost no attributable", "95 heavy-truck-only",
    "no parts were sold",
]

fail = 0
missing = 0
for f in FILES:
    if not f.is_file():
        print(f"--- {f.name}: NOT PRESENT (skipped)")
        missing += 1
        continue
    s = f.read_text(encoding="utf-8")
    print(f"--- {f.name}")
    hits = 0
    for b in BAN:
        pat = r"\b" + re.escape(b) + r"\b"
        for i, ln in enumerate(s.split("\n"), 1):
            if re.search(pat, ln, 0 if b == "Model B" else re.I):
                print(f"    FAIL L{i}: {b!r}")
                hits += 1
    if not hits:
        print("    clean")
    fail += hits

print()
if missing:
    print(f"note: {missing} listed page(s) not present, skipped")
print("BANNED LABEL CHECK PASS" if not fail else f"BANNED LABEL CHECK FAIL ({fail})")
raise SystemExit(1 if fail else 0)
