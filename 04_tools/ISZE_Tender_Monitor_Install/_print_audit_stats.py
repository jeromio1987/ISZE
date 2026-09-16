# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

r = json.loads(Path(r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_audit_analyze_v3_results.json").read_text(encoding="utf-8"))
print("generated", r["meta_generated_at"])
print("notices", r["notice_count"], "opps", r["opportunity_count"])
print("SOURCES", r["notice_source_counts"])
print()
print("FIELD COMPLETENESS (ranked by emptiness):")
for row in r["field_completeness"]:
    print(f"  {row['pct_empty']:5.1f}% empty | {row['populated']:4d}/{r['notice_count']} | {row['field']}")
print()
print("MARKETS:")
for m in r["markets_returning"]:
    print(f"  {m['code']:4s} {m['name']:20s} notices={m['notices']:4d} opps={m['opportunities']:4d} action={m['action_tier']:3d} sources={m['sources']}")
print()
print("ZERO:", r["zero_notice_isze_markets"])
print("TED missing named:", r["ted_filter_missing_named_markets"])

# deadline specifically
d = json.loads(Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\tender_data.json").read_text(encoding="utf-8"))
notices = d["notices"]
opps = d["opportunities"]
dl = sum(1 for n in notices if n.get("Deadline") or n.get("Deadline Date"))
rm = sum(1 for n in notices if n.get("rm_contract") is True)
print()
print("Deadline populated (Deadline or Deadline Date):", dl, f"({100*dl/len(notices):.1f}%)")
print("rm_contract True:", rm)
print("action-tier opps (attack+selective):", sum(1 for o in opps if (o.get('decision') or '').lower() in ('attack','selective')))
print("decisions:", json.dumps({k: sum(1 for o in opps if o.get('decision')==k) for k in sorted({o.get('decision') for o in opps})}))
