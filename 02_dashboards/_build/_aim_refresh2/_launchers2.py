"""Launcher audit: every OPEN_*.cmd near a rebuilt page must (a) name the file it opens,
(b) be CRLF, (c) start with @echo off. Read-only report; --fix rewrites only the
launchers whose NAME disagrees with their TARGET.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")

FOLDERS = ["02_dashboards/sales", "02_dashboards/pricing", "02_dashboards/hub", "02_dashboards/ops"]
TARGET_RE = re.compile(r'start\s+""\s+"%~dp0([^"]+)"')

problems = []
for folder in FOLDERS:
    for cmd in sorted((ISZE / folder).glob("OPEN_*.cmd")):
        raw = cmd.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        m = TARGET_RE.search(text)
        target = m.group(1) if m else None
        crlf = b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b"")
        echo = text.lstrip().lower().startswith("@echo off")
        name_stem = cmd.stem[len("OPEN_"):]
        target_stem = Path(target).stem if target else None
        name_matches = bool(target_stem) and (name_stem in target_stem or target_stem in name_stem)
        exists = bool(target) and (cmd.parent / target).is_file()
        rec = dict(cmd=str(cmd.relative_to(ISZE)), target=target, crlf=crlf, echo=echo,
                   name_matches=name_matches, target_exists=exists)
        bad = not (crlf and echo and name_matches and exists)
        if bad:
            problems.append(rec)
        print(("BAD  " if bad else "ok   ") + f"{rec['cmd']:<70} -> {target}  crlf={crlf} echo={echo} name_ok={name_matches} exists={exists}")

print("\nproblems:", len(problems))
for r in problems:
    print("  ", r)
