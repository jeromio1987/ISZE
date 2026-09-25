"""Verify the key claims of the release re-test."""
import io
import os
import re

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"

print("=" * 65)
print("1. the gate: what does it actually read?")
print("=" * 65)
g = os.path.join(ROOT, r"01_data\91_build\verify_aim_classification.py")
t = io.open(g, encoding="utf-8", errors="replace").read().splitlines()
for n in (29, 61, 201):
    if n <= len(t):
        print(f"  line {n}: {t[n-1].strip()[:130]}")

print()
print("=" * 65)
print("2. the leaf baseline file - does it say 177?")
print("=" * 65)
lb = os.path.join(ROOT, r"01_data\00_derived\aim_classification_leaf_baseline.json")
if os.path.exists(lb):
    print(io.open(lb, encoding="utf-8").read()[:400])
else:
    print("  not at that path; searching...")
    for dp, dn, fn in os.walk(ROOT):
        for f in fn:
            if "leaf_baseline" in f:
                print("   ", os.path.join(dp, f))

print()
print("=" * 65)
print("3. does the gate read the approved release anywhere?")
print("=" * 65)
print("  mentions of 'release' in the gate:", len(re.findall(r"release", io.open(g, encoding='utf-8', errors='replace').read(), re.I)))
print("  CLASS_V2 constant value:")
for line in t:
    if "CLASS_V2" in line and "=" in line:
        print("   ", line.strip()[:140])

print()
print("=" * 65)
print("4. is assert_release called anywhere?")
print("=" * 65)
hits = []
for dp, dn, fn in os.walk(ROOT):
    if any(s in dp for s in ["node_modules", ".git", "_archive", "__pycache__"]):
        continue
    for f in fn:
        if f.endswith((".py", ".ps1", ".bat")):
            p = os.path.join(dp, f)
            try:
                s = io.open(p, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            if "assert_release" in s:
                hits.append(os.path.relpath(p, ROOT))
print("  files calling assert_release:", len(hits))
for h in hits[:12]:
    print("   ", h)

print()
print("=" * 65)
print("5. the stale vs approved row counts")
print("=" * 65)
for rel in [r"01_data\00_derived\aim_pn_classification_v2.csv",
            r"01_data\00_derived\_releases\aim_pn_classification_release_2026-09-20.csv"]:
    p = os.path.join(ROOT, rel)
    if os.path.exists(p):
        with io.open(p, encoding="utf-8", errors="replace") as fh:
            n = sum(1 for _ in fh) - 1
        print(f"  {os.path.basename(p):58s} rows={n:7d}  mtime={os.path.getmtime(p):.0f}")
