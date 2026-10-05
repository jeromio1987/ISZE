# -*- coding: utf-8 -*-
r"""Read-only probe 9: the feed's own scores, the outcome field, and the Romania frame agreement."""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ISZE = os.path.dirname(ROOT)
T = os.path.join(ISZE, "01_data", "14_dashboards", "tender_data.json")

d = json.load(open(T, encoding="utf-8"))
opps = d["opportunities"]
key = "opportunity_score"
scored = [o for o in opps if isinstance(o.get(key), (int, float))]
scored.sort(key=lambda o: -o[key])
print("scored %d of %d, range %s..%s" % (len(scored), len(opps),
                                         scored[-1][key], scored[0][key]))
print("\ntop 3 by opportunity score:")
for o in scored[:3]:
    print("  %s | %s | %s | pub %s | deadline %s | value %r %s | decision %s" % (
        o[key], o["country"], (o["title"] or "")[:64], o["published_first"],
        o["deadline_date"], o["value_amount"], o["currency"], o["decision"]))
    print("      drivers %s | aftersales %s | owner %s | next %s" % (
        o["score_drivers"][:5], (o["aftersales_tags"] or [])[:4],
        o["owner_suggested"], o["next_action_suggested"]))

print("\noutcome values:", {str(o.get("outcome")) for o in opps})
print("value_amount non-empty: %d of %d" % (
    sum(1 for o in opps if o.get("value_amount")), len(opps)))
print("decision counts:", d["meta"]["decision_counts"])
print("aftersales_tagged:", d["meta"]["stats"]["aftersales_tagged"])

print("\nRomania frame agreement:")
for o in opps:
    blob = json.dumps(o, ensure_ascii=False).lower()
    if "acord cadru" in blob and ("reparatii" in blob or "intretinere" in blob):
        print("  score %s | %s | %s | %s" % (o[key], o["country"], o["buyer"], o["title"][:80]))
        print("      pub %s  deadline %s  days %s  value %r  framework_hits %s" % (
            o["published_first"], o["deadline_date"], o["days_to_deadline"],
            o["value_amount"], o["framework_hits"]))
        print("      service_hits %s  parts_signal %s  drivers %s" % (
            o["service_hits"], o["parts_signal"], o["score_drivers"]))
        print("      owner %s  next %s  url %s" % (
            o["owner_suggested"], o["next_action_suggested"], (o["url"] or "")[:80]))
