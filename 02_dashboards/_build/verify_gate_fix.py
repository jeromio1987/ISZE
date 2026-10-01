"""Verify the gate fix: second-run stability, honest handling, and nothing else moved."""
import hashlib
import io
import json
import os
import subprocess

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
GATE = os.path.join(ROOT, r"01_data\91_build\verify_aim_classification.py")

print("=" * 68)
print("1. second run - is the per-file drift baseline stable?")
print("=" * 68)
r2 = subprocess.run(["python", GATE], cwd=ROOT, capture_output=True, text=True, timeout=300)
out = r2.stdout + r2.stderr
line = [l for l in out.splitlines() if "drift_vs_previous_run" in l]
print("  exit code:", r2.returncode)
print("  ", line[0].strip() if line else "drift line not found")
print("  verdict line:", [l.strip() for l in out.splitlines() if "PASS" in l or "FAIL" in l][:1])

print()
print("=" * 68)
print("2. does it still refuse to invent the copy-integrity figure?")
print("=" * 68)
for l in out.splitlines():
    if "pr00_copy_integrity" in l or "UNAVAILABLE" in l:
        print("  ", l.strip()[:200])

print()
print("=" * 68)
print("3. the release file and leaf baseline - unchanged?")
print("=" * 68)
rel = os.path.join(ROOT, r"01_data\00_derived\_releases\aim_pn_classification_release_2026-09-20.csv")
h = hashlib.sha256(open(rel, "rb").read()).hexdigest()
print("  release sha256:", h)
print("  matches approved :", h == "60111c104ddeb466e6c15f084039639d35172056b0fd2ea10225a3c50da610e0")
lb = os.path.join(ROOT, r"01_data\00_derived\aim_classification_leaf_baseline.json")
print("  leaf baseline mtime:", os.path.getmtime(lb), "| L3 approved:",
      json.load(io.open(lb, encoding="utf-8")).get("axis_a_l3_approved"))

print()
print("=" * 68)
print("4. per-file gate reports written")
print("=" * 68)
d = os.path.join(ROOT, r"01_data\00_derived\_releases")
for f in sorted(os.listdir(d)):
    if f.endswith(".gate.json"):
        print("  ", f, os.path.getsize(os.path.join(d, f)), "bytes")

print()
print("=" * 68)
print("5. the board still reads the old run - does it now show a stale verdict?")
print("=" * 68)
b = io.open(os.path.join(ROOT, r"02_dashboards\hub\ISZE_UNIVERSE_BOARD.html"),
            encoding="utf-8", errors="replace").read()
i = b.find("safety")
print("  board mentions of the gate failing:")
for probe in ["18 of 18", "17 of 18", "FAIL", "safety checks"]:
    print(f"    '{probe}': {b.count(probe)}")
# the live report the board reads
rep = os.path.join(ROOT, r"01_data\00_derived\aim_classification_gate.json")
print("  live report verdict:", json.load(io.open(rep, encoding="utf-8")).get("verdict"),
      "| passed:", json.load(io.open(rep, encoding="utf-8")).get("passed"))
