"""Present a superseded figure as readable text only, with embedded JSON payloads stripped.

A bare "3.31" or "2.4751" also occurs as a price inside the big data arrays, which is how the first
sweep reported hits that were not findings. This strips the payload scripts and scans the prose, the
tables and the page script, and reports file and line.
"""
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")

RX = {
    "whole-book +1.7393% (superseded)": re.compile(r"1[.,]7393\s*%"),
    "Japan +5.7076% (superseded)": re.compile(r"5[.,]7076\s*%"),
    "Thailand -2.4751% (superseded)": re.compile(r"[-−]?\s*2[.,]4751\s*%"),
    "3.31% relief (measured from 172.6)": re.compile(r"3[.,]31\s*%"),
    "8.29% relief (measured from the list's own 163.7)": re.compile(r"8[.,]29\s*%"),
    "+7% base revision (fabricated, has no source)": re.compile(r"7\s*%\s*(?:base\s*)?revision", re.I),
}


def prose(path: Path) -> list[tuple[int, str]]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    # replace payload script bodies with a marker, keeping the line count
    out, lines = [], raw.split("\n")
    keep = True
    for ln in lines:
        if re.search(r'<script[^>]*type="application/json"', ln):
            keep = False
            out.append("/* PAUSED JSON PAYLOAD */")
            if "</script>" in ln:
                keep = True
            continue
        if not keep:
            if "</script>" in ln:
                keep = True
            out.append("")
            continue
        out.append(ln)
    for i, ln in enumerate(out, 1):
        if "/* PAUSED JSON PAYLOAD */" in ln:
            continue
        yield i, ln


FILES = sorted([p for p in (ROOT / "02_dashboards/pricing").glob("*.html")])
BUILDERS = sorted([p for p in (ROOT / "02_dashboards/pricing/_build").glob("*.py")])

print("=" * 96)
print("PUBLISHED PRICING PAGES — prose and page script, payloads stripped")
print("=" * 96)
for p in FILES:
    hits = []
    for i, ln in prose(p):
        for name, rx in RX.items():
            for m in rx.finditer(ln):
                a = max(0, m.start() - 130)
                b = min(len(ln), m.end() + 130)
                hits.append((i, name, ln[a:b].strip()))
    if not hits:
        continue
    print(f"\n  {p.name}")
    for i, name, ctx in hits:
        print(f"    L{i}  {name}")
        print(f"         ...{ctx}...")

print()
print("=" * 96)
print("PRICING BUILDERS — prose, comments and literals")
print("=" * 96)
for p in BUILDERS:
    if p.name.startswith("_sweep") or p.name.startswith("_qa"):
        continue
    hits = []
    for i, ln in enumerate(p.read_text(encoding="utf-8", errors="replace").split("\n"), 1):
        for name, rx in RX.items():
            for m in rx.finditer(ln):
                a = max(0, m.start() - 130)
                b = min(len(ln), m.end() + 130)
                hits.append((i, name, ln[a:b].strip()))
    if not hits:
        continue
    print(f"\n  {p.name}")
    for i, name, ctx in hits:
        print(f"    L{i}  {name}")
        print(f"         ...{ctx}...")
