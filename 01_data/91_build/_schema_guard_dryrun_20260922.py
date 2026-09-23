"""Dry-run the schema guard against the live files and print one line per file."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
sys.path.insert(0, str(REPO / "03_analytics" / "Isuzu" / "prism"))

import yaml  # noqa: E402

from modules import schema_guard  # noqa: E402

fx = yaml.safe_load((REPO / "03_analytics/Isuzu/prism/data/verification_fixtures.yaml")
                    .read_text(encoding="utf-8"))
dd = REPO / "01_data" / "00_derived"
res = schema_guard.evaluate(fx["schema_required"]["files"], dd, REPO)

print(f"{'file':34} {'status':14} {'present':>7}  missing")
print("-" * 100)
for e in res["files"]:
    print(f"{e['file']:34} {e['status']:14} {e['present']:>7}  {e['missing']}"
          f"   lost_vs_git={e.get('lost_vs_git_head')}")
print()
print("git_lost aggregate:", res["git_lost"])
