"""Read-only: who reads pricing_aim_source_lines / cube, and who reads aim_gps_matrix."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
SKIP = re.compile(r"(_backsafe|_archive|_qa|_gpt_review|_composable|_design|_working|_audit|"
                  r"_recover|history|pn_ammo_probe|91_build/_tmp|90_INBOX|_INBOX)")

NEEDLES = ["pricing_aim_source_lines", "pricing_aim_source_cube", "aim_gps_matrix"]
for needle in NEEDLES:
    print("==", needle)
    for p in ROOT.rglob("*.py"):
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        if SKIP.search(rel):
            continue
        s = p.read_text(encoding="utf-8", errors="replace")
        if needle in s:
            where = "WRITES" if re.search(r"to_(?:csv|parquet|json)\([^\n]*" + needle, s) else "reads"
            print(f"   {where}: {rel}")
