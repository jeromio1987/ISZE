"""Build the single progress and integration record (BASE-08).

Reads the 96-task plan and merges progress/state_overlay.json, so the record
reflects evidence that actually exists rather than an optimistic hand count.
A task is never moved beyond 'technically verified' by a machine - 'human
accepted' requires a person.

Usage:  python tools/build_progress.py
"""
import io
import json
import os
import re
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PLAN = os.path.join(ROOT, "..", "TASKS_96.txt")
OVERLAY = os.path.join(ROOT, "progress", "state_overlay.json")
OUT = os.path.join(ROOT, "progress", "progress.json")

# The five states the brief requires, kept strictly apart.
STATES = ["not started", "in progress", "implemented", "technically verified", "human accepted"]

TASK_RE = re.compile(r'^([A-Z]+-\d+) \| (.+)$')
FIELD_RE = re.compile(r'^(Target|Roadmap|Acceptance|Existing finding|'
                      r'Can start after|Integrate after):\s*(.*)$')
OWNER_INLINE = re.compile(r'Proposed owner:\s*([^|]+)')


def parse_plan(path):
    txt = io.open(path, "rb").read().decode("utf-8", errors="replace")
    tasks = []
    cur = None
    for line in txt.split("\n"):
        m = TASK_RE.match(line)
        if m:
            cur = {"id": m.group(1), "title": m.group(2).strip()}
            tasks.append(cur)
            continue
        if cur is None:
            continue
        if "Proposed owner" in line:
            mo = OWNER_INLINE.search(line)
            if mo:
                cur["owner"] = mo.group(1).strip()
        mf = FIELD_RE.match(line)
        if mf:
            key = mf.group(1).strip().lower().replace(" ", "_")
            cur[key] = mf.group(2).strip()
    for t in tasks:
        t.setdefault("owner", "Integration owner")
        t.setdefault("target", "")
        t["state"] = "not started"
        t["evidence"] = []
        t["blockers"] = []
    return tasks


def main():
    tasks = parse_plan(os.path.abspath(PLAN))
    by_id = {t["id"]: t for t in tasks}

    overlay = {}
    if os.path.exists(OVERLAY):
        overlay = json.load(io.open(OVERLAY, encoding="utf-8"))

    applied, unknown = 0, []
    for tid, rec in (overlay.get("states") or {}).items():
        if tid not in by_id:
            unknown.append(tid)
            continue
        state = rec.get("state", "not started")
        if state not in STATES:
            unknown.append(tid + " (bad state " + state + ")")
            continue
        if state == "human accepted":
            state = "technically verified"
            rec.setdefault("evidence", []).append(
                "Clamped to technically verified: human acceptance is a person's decision.")
        by_id[tid]["state"] = state
        by_id[tid]["evidence"] = rec.get("evidence", [])
        applied += 1

    counts = {}
    for t in tasks:
        counts[t["state"]] = counts.get(t["state"], 0) + 1

    doc = {
        "record_version": 2,
        "plan_source": "TASKS_96.txt (2318 lines, 96 tasks)",
        "written_by": "integration owner (the only writer, so workers cannot overwrite it)",
        "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "state_vocabulary": STATES,
        "warning": (
            "A state of 'technically verified' means a named command was run and its "
            "actual output recorded. It does not mean human accepted, and it confers no "
            "business, technical, privacy or spending authority. Nothing here is deployed, "
            "published or sent."
        ),
        "counts": counts,
        "total_tasks": len(tasks),
        "overlay_applied": applied,
        "overlay_unknown_ids": unknown,
        "open_findings": overlay.get("open_findings", []),
        "tasks": tasks,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(doc, indent=2) + "\n")
    print("wrote", OUT)
    print("tasks:", len(tasks), " overlay applied:", applied)
    if unknown:
        print("WARNING unknown overlay ids:", unknown)
    print("by state:", json.dumps(counts))
    print("open findings:", len(doc["open_findings"]))
    for f in doc["open_findings"]:
        print("  -", f["id"], f["severity"], "|", f["title"])


if __name__ == "__main__":
    main()
