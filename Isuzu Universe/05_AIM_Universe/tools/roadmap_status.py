"""How much of the 96-task plan is finished, honestly.

A raw task count treats "reject an invalid quantity" and "choose a shared backend"
as equal work, which they are not. This reports the count AND the family breakdown,
so the number can be read against where the weight actually sits.

Usage:  python tools/roadmap_status.py
"""
import io
import json
import os
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROGRESS = os.path.join(ROOT, "progress", "progress.json")

FAMILY_LABEL = OrderedDict([
    ("BASE",    "Foundation, checks, build"),
    ("FIN",     "Financial engine (pricing arithmetic)"),
    ("DATA",    "Sources, imports, conservation"),
    ("REVIEW",  "The review workbench"),
    ("UX",      "One context across the views"),
    ("CASE",    "Durable case record"),
    ("MARKET",  "Competitor price evidence"),
    ("RANGE",   "Genuine/BVP range and migration"),
    ("CONNECT", "IDS / PRISM / tender connections"),
    ("SAFE",    "Access, permissions, exports"),
    ("RUN",     "Refresh, deployment, recovery"),
    ("ACCEPT",  "Independent acceptance"),
])

DONE = {"technically verified", "human accepted"}
PARTIAL = {"implemented", "in progress"}


def main():
    doc = json.load(io.open(PROGRESS, encoding="utf-8"))
    tasks = doc["tasks"]

    by_family = OrderedDict()
    for t in tasks:
        fam = t["id"].split("-")[0]
        by_family.setdefault(fam, []).append(t)

    total = len(tasks)
    done = sum(1 for t in tasks if t["state"] in DONE)
    partial = sum(1 for t in tasks if t["state"] in PARTIAL)

    print("OVERALL, by task count")
    print("  total planned           : %d" % total)
    print("  technically verified    : %d" % done)
    print("  partially done          : %d" % partial)
    print("  not started             : %d" % (total - done - partial))
    print("  done = %.0f%%   done+partial = %.0f%%" % (100.0 * done / total,
                                                        100.0 * (done + partial) / total))
    print()
    print("BY WORKSTREAM  (weighted by task count, which is itself a blunt measure)")
    print("  %-9s %-42s %5s %5s %5s %7s" % ("family", "what it covers",
                                             "done", "part", "left", "done%"))
    for fam, items in by_family.items():
        d = sum(1 for t in items if t["state"] in DONE)
        p = sum(1 for t in items if t["state"] in PARTIAL)
        n = len(items)
        print("  %-9s %-42s %5d %5d %5d %6.0f%%" % (
            fam, FAMILY_LABEL.get(fam, "")[:42], d, p, n - d - p, 100.0 * d / n))

    print()
    untouched = [f for f, i in by_family.items()
                 if not any(t["state"] in DONE or t["state"] in PARTIAL for t in i)]
    print("WORKSTREAMS WITH NOTHING STARTED: %s" % (", ".join(untouched) or "none"))
    print()
    print("This is R1 of a multi-release plan. It is not a percentage of a finished product.")


if __name__ == "__main__":
    main()
