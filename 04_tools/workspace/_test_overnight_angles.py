"""Run every overnight audit angle once and summarise what each found.

Read-only smoke test. Proves each angle executes without crashing and reports its findings
count, so the orchestrator is not wired to something that throws on the first tick.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANGLES_PY = HERE / "_overnight_angles.py"
OUT = HERE / "_angle_smoke_results.json"

listing = subprocess.run([sys.executable, str(ANGLES_PY), "--list"],
                         capture_output=True, text=True)
angles = json.loads(listing.stdout)

rows = []
for a in angles:
    name = a["angle"]
    p = subprocess.run([sys.executable, str(ANGLES_PY), "--angle", name, "--hours", "720"],
                       capture_output=True, text=True)
    try:
        j = json.loads(p.stdout)
    except Exception as e:  # noqa: BLE001
        rows.append({"angle": name, "ok": False, "error": f"unparseable: {e}",
                     "stderr": p.stderr[-400:]})
        print(f"  FAIL {name}: unparseable output")
        continue
    if "error" in j:
        rows.append({"angle": name, "ok": False, "error": j["error"]})
        print(f"  FAIL {name}: {j['error']}")
        continue
    by_sev = {}
    for f in j.get("findings", []):
        by_sev[f["severity"]] = by_sev.get(f["severity"], 0) + 1
    rows.append({"angle": name, "ok": True, "n_findings": len(j.get("findings", [])),
                 "by_severity": by_sev,
                 "sample": [f"{f['severity']}: {f['what'][:100]}"
                            for f in j.get("findings", [])[:3]]})
    sev = " ".join(f"{k}={v}" for k, v in sorted(by_sev.items())) or "clean"
    print(f"  OK   {name:34s} {len(j.get('findings', [])):3d} findings  ({sev})")

OUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")
print()
ok = sum(1 for r in rows if r["ok"])
print(f"angles={len(rows)} ok={ok} failed={len(rows) - ok}")
print(f"wrote {OUT.name}")
sys.exit(0 if ok == len(rows) else 1)
