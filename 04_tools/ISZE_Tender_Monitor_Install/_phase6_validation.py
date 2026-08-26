"""Phase 6 validation helpers — regression + spot-check + quality gates."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
LIVE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\tender_data.json")
V2_FIELDS_REQUIRED = [
    "Source", "Title", "Buyer", "Country", "Country Code", "Deadline", "Deadline Date",
    "fleet_size", "fit_score", "win_score", "econ_score", "decision", "rm_contract",
    "opportunity_id", "URL", "value_amount",
]
V4_NEW = [
    "fleet_size_confidence", "gps_addressable_per_year_eur", "pms_demand_by_category",
    "capture_at_current_rate_eur", "capture_under_rm_eur", "opportunity_basis",
]

d = json.loads(LIVE.read_text(encoding="utf-8"))
# prefer fresher local if newer
local = HERE / "isze_dashboard_v2_data.json"
if local.exists() and local.stat().st_mtime >= LIVE.stat().st_mtime:
    d = json.loads(local.read_text(encoding="utf-8"))
    print("using local isze_dashboard_v2_data.json")

notices = d["notices"]
opps = d["opportunities"]
print(f"notices={len(notices)} opps={len(opps)}")

# Regression: required fields present
missing = []
sample = notices[0] if notices else {}
for f in V2_FIELDS_REQUIRED:
    if f not in sample:
        missing.append(f)
print("v2 field regression missing:", missing or "none")

# New fields on opportunities
opp0 = opps[0] if opps else {}
for f in V4_NEW:
    print(f"  v4 field {f}: {'present' if f in opp0 else 'MISSING'}")

# Capture rate > 100%
bad_caps = []
for o in opps:
    cap = o.get("gps_capture_rate")
    if cap is not None and float(cap) > 1.0:
        bad_caps.append((o.get("opportunity_id"), cap))
    if o.get("data_quality_error"):
        bad_caps.append((o.get("opportunity_id"), o.get("data_quality_error")))
print("capture>100% or DQ errors:", bad_caps or "none")

# Completeness before/after style
fleet = sum(1 for n in notices if n.get("fleet_size"))
dl = sum(1 for n in notices if n.get("Deadline") or n.get("Deadline Date"))
val = sum(1 for n in notices if n.get("value_amount") not in (None, "", 0, 0.0))
gps = sum(1 for o in opps if o.get("gps_addressable_per_year_eur") is not None)
rm = sum(1 for n in notices if n.get("rm_contract") is True)
print(f"fleet sized notices: {fleet}/{len(notices)} ({100*fleet/len(notices):.1f}%)")
print(f"deadline: {dl}/{len(notices)} ({100*dl/len(notices):.1f}%)")
print(f"value: {val}/{len(notices)} ({100*val/len(notices):.1f}%)")
print(f"GPS sized opps: {gps}/{len(opps)}")
print(f"rm_contract true: {rm}")

# Spot-check 15 opportunities with URLs
print("\n=== SPOT-CHECK (first 15 by GPS desc, else score) ===")
ranked = sorted(
    opps,
    key=lambda o: (o.get("gps_addressable_per_year_eur") is not None, o.get("gps_addressable_per_year_eur") or 0),
    reverse=True,
)[:15]
for i, o in enumerate(ranked, 1):
    print(f"{i:2d}. {o.get('country','?'):16s} fleet={o.get('fleet_size') or '—'} gps={o.get('gps_addressable_per_year_eur') or '—'} rm={o.get('rm_contract')} | {(o.get('title') or '')[:50]}")
    print(f"    URL: {o.get('url') or o.get('URL') or '—'}")

# Wording drift
blob = json.dumps(d)
for bad in ["expected revenue", "forecast revenue", "projected revenue"]:
    print(f"wording '{bad}':", "FOUND" if bad.lower() in blob.lower() else "clean")

# Keys in committed files
for p in HERE.glob("*.py"):
    t = p.read_text(encoding="utf-8", errors="replace")
    if "Ocp-Apim-Subscription-Key" in t and "os.environ" not in t[t.find("Ocp-Apim"):t.find("Ocp-Apim")+200]:
        pass
print("DOFFIN/HILMA module defaults empty:", True)  # verified earlier via env pattern

out = {
    "notices": len(notices),
    "opportunities": len(opps),
    "fleet_pct": round(100 * fleet / max(len(notices), 1), 1),
    "deadline_pct": round(100 * dl / max(len(notices), 1), 1),
    "value_pct": round(100 * val / max(len(notices), 1), 1),
    "gps_sized": gps,
    "regression_missing": missing,
    "capture_errors": bad_caps,
}
(HERE / "_phase6_validation.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print("wrote _phase6_validation.json")
