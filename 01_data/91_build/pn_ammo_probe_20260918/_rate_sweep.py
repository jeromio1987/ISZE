"""Scoped sweep: every file that states or computes a PMS service rate.

Walks only the workspace's own folders, skips caches and the deploy mirror, and reports what each
file claims so the disagreements are visible side by side.
"""

import os
import re

WORK = r"C:\Users\jerom\Desktop\claude\ISZE"
SKIP = {".claude", "__pycache__", "node_modules", ".git", "07_deploy", "90_archive",
        "91_legacy", ".venv", "site-packages", ".ipynb_checkpoints", "Data"}
EXT = {".py", ".md", ".yaml", ".yml", ".json", ".ps1", ".mjs", ".js", ".mdc", ".txt"}

PAT = {
    "services_per_year": re.compile(r"services_per_year"),
    "bucket_svc_year": re.compile(r"BUCKET_SERVICES_PER_YEAR"),
    "annual_km": re.compile(r"annual_km_yr|mileage_km_yr|km_per_yr|km_yr_"),
    "interval_km": re.compile(r"service_visit_interval_km|service_interval_km|interval_km"),
    "n35_rate": re.compile(r"N35_services_per_year"),
}

hits = {}
scanned = 0
for dirpath, dirnames, filenames in os.walk(WORK):
    dirnames[:] = [d for d in dirnames if d not in SKIP]
    for fn in filenames:
        ext = os.path.splitext(fn)[1].lower()
        if ext not in EXT:
            continue
        p = os.path.join(dirpath, fn)
        rel = os.path.relpath(p, WORK)
        try:
            if os.path.getsize(p) > 3_000_000 or os.path.getsize(p) < 50:
                continue
            with open(p, encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
            scanned += 1
        except Exception:
            continue
        found = {}
        for name, pat in PAT.items():
            for m in pat.finditer(text):
                ln = text.count("\n", 0, m.start()) + 1
                line = text.splitlines()[ln - 1].strip()[:140]
                found.setdefault(name, []).append(f"{ln}: {line}")
        if found:
            hits[rel] = found

print("=" * 112)
print(f"SWEEP RESULT — {len(hits)} files carry a service-rate constant (scanned {scanned} files)")
print("=" * 112)
for rel in sorted(hits):
    print(f"\n### {rel}")
    for key in ("services_per_year", "n35_rate", "bucket_svc_year", "annual_km", "interval_km"):
        for line in hits[rel].get(key, [])[:8]:
            print(f"   [{key:16s}] {line}")
