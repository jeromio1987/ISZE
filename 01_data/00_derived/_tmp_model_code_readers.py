"""Ad-hoc: does any code READ model_code_to_tonnage.csv? List every occurrence with the
surrounding line, and separately list only the ones that look like an actual file read.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
TOKEN = "model_code_to_tonnage"
SKIP_DIRS = {".git", "node_modules", "__pycache__", "07_deploy", "history"}

READ_HINTS = ("read_csv", "read_parquet", "pd.read", "open(", "Path(", "read_text",
              "genfromtxt", "loadtxt", "load(")

hits = []
for p in ROOT.rglob("*"):
    if not p.is_file() or p.suffix.lower() not in (
            ".py", ".ps1", ".cmd", ".json", ".yaml", ".yml", ".html", ".js", ".mjs", ".md"):
        continue
    if any(s in p.parts for s in SKIP_DIRS):
        continue
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        continue
    if TOKEN not in text:
        continue
    for i, line in enumerate(text.splitlines(), 1):
        if TOKEN in line:
            hits.append((str(p.relative_to(ROOT)), i, line.strip()))

print(f"total occurrences: {len(hits)}\n")
print("--- every occurrence ---")
for f, i, line in hits:
    print(f"{f}:{i}\n    {line[:300]}")

print("\n--- occurrences that look like an actual file READ ---")
reads = [(f, i, l) for f, i, l in hits if any(h in l for h in READ_HINTS)]
if not reads:
    print("  none")
else:
    for f, i, line in reads:
        print(f"{f}:{i}\n    {line[:300]}")

print("\n--- occurrences inside built HTML (what a page embeds) ---")
for f, i, line in hits:
    if f.lower().endswith(".html"):
        print(f"{f}:{i}\n    {line[:400]}")
