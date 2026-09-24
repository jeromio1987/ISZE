"""Read-only: which builders read the AIM master / AIM classification, and what do they write?

Then: which of the derived files those builders write are read by the pages we care about.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
SKIP = re.compile(r"(_backsafe|_archive|_qa|_gpt_review|_composable|_design|_working|_audit|"
                  r"_recover|history|pn_ammo_probe|export_aim_|91_build/_tmp|90_INBOX)")

AIM_READ = re.compile(r"aim_master_v2|AIM_MASTER|aim_l1_fixed|aim_pn_classification")
WRITE = re.compile(r"""["']?([A-Za-z0-9_\-]+\.(?:csv|parquet))["']?\s*\)?\s*$""")
TO_WRITE = re.compile(r"(?:to_csv|to_parquet)\(\s*(?:[A-Za-z_][A-Za-z0-9_]*\s*/\s*)?")
VAR_DEF = re.compile(r"^([A-Z_][A-Z0-9_]*)\s*[:=].*?([A-Za-z0-9_\-]+\.(?:csv|parquet))", re.M)

hits = []
for p in ROOT.rglob("*.py"):
    rel = str(p.relative_to(ROOT)).replace("\\", "/")
    if SKIP.search(rel):
        continue
    try:
        s = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue
    if not AIM_READ.search(s):
        continue
    # which derived files does it write?
    consts = dict(VAR_DEF.findall(s))
    outs = set()
    for m in re.finditer(r"(?:to_csv|to_parquet)\(([A-Z_][A-Z0-9_]*)\b", s):
        if m.group(1) in consts:
            outs.add(consts[m.group(1)])
    for m in re.finditer(r"""to_csv\(\s*[^,)]*?([A-Za-z0-9_\-]+\.(?:csv|parquet))""", s):
        outs.add(m.group(1))
    if outs:
        hits.append((rel, sorted(outs)))

hits.sort()
for rel, outs in hits:
    print(rel)
    for o in outs:
        print("     ->", o)
print("\nbuilders:", len(hits))
