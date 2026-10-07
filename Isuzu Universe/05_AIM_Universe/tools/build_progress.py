"""Build the single progress and integration record (BASE-08).

Reads the 96-task plan and merges progress/state_overlay.json, so the record
reflects evidence that actually exists rather than an optimistic hand count.
A task is never moved beyond 'technically verified' by a machine - 'human
accepted' requires a person.

Usage:  python tools/build_progress.py
"""
import glob
import hashlib
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
TESTS = os.path.join(ROOT, "tests")
ARTIFACT = os.path.join(ROOT, "dist", "ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html")
RUN_SUMMARY = os.path.join(ROOT, "tests", "accept", "_out", "run_all_summary.json")

# A line that opens a test, a check or a recorded result. A task counts as
# named by a test only when its id appears on such a line - a comment or a
# header mentioning the id is not a test.
TEST_LINE = re.compile(r"\b(test|check|it)\s*\(|H\.test\(|record\(\s*['\"]")
SKIP_TEST_FILES = ("_diag", "_shape", "_probe")

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


def tested_by(task_ids):
    """Map each task id to the test lines that name it, as 'file:line'."""
    files = []
    for ext in ("*.mjs", "*.cjs", "*.py"):
        files += glob.glob(os.path.join(TESTS, "**", ext), recursive=True)
    out = {tid: [] for tid in task_ids}
    pats = {tid: re.compile(re.escape(tid) + r"(?!\d)") for tid in task_ids}
    for f in sorted(files):
        rel = os.path.relpath(f, ROOT).replace("\\", "/")
        if "/_out/" in rel or any(x in os.path.basename(f) for x in SKIP_TEST_FILES):
            continue
        with io.open(f, encoding="utf-8", errors="replace") as fh:
            for n, line in enumerate(fh, 1):
                if not TEST_LINE.search(line):
                    continue
                for tid, pat in pats.items():
                    if pat.search(line):
                        out[tid].append("%s:%d" % (rel, n))
    return out


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def acceptance_run(overlay):
    """The recorded run, with the artifact re-measured on disk now and the
    latest runner summary attached, so the record cannot name a file that is
    no longer there."""
    run = dict(overlay.get("_acceptance_run") or {})
    if run.get("artifact"):
        run["artifact_as_recorded"] = run["artifact"]
    if os.path.exists(ARTIFACT):
        run["artifact"] = "dist/%s (%d bytes, sha256 %s, measured %s)" % (
            os.path.basename(ARTIFACT), os.path.getsize(ARTIFACT), sha256_of(ARTIFACT),
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    else:
        run["artifact"] = "MISSING: dist/%s is not on disk" % os.path.basename(ARTIFACT)
    if os.path.exists(RUN_SUMMARY):
        summ = json.load(io.open(RUN_SUMMARY, encoding="utf-8-sig"))
        run["latest_runner_summary"] = {
            "file": os.path.relpath(RUN_SUMMARY, ROOT).replace("\\", "/"),
            "generated_at": summ.get("generated_at"),
            "failed_checks": summ.get("failed_checks"),
            "not_run": summ.get("not_run"),
            "known_findings_open_in": summ.get("known_findings_open_in"),
            "checks": [{"id": c.get("id"), "exit_code": c.get("exit_code"), "summary": c.get("summary")}
                       for c in (summ.get("checks") or [])],
        }
    return run


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

    # A task stays "technically verified" only when a test line names it. A
    # task with no such line is held at "implemented" and says why.
    named = tested_by([t["id"] for t in tasks])
    held = []
    for t in tasks:
        if t["state"] == "technically verified" and not named[t["id"]]:
            t["state"] = "implemented"
            t["blockers"].append(
                "Held at implemented: no test line names this task, so nothing would fail if "
                "the behaviour broke. It returns to technically verified when a named test exists.")
            held.append(t["id"])

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
        "held_without_named_test": held,
        "tested_by": named,
        "_acceptance_run": acceptance_run(overlay),
        "tasks": tasks,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(doc, indent=2) + "\n")
    print("wrote", OUT)
    print("tasks:", len(tasks), " overlay applied:", applied)
    if unknown:
        print("WARNING unknown overlay ids:", unknown)
    print("by state:", json.dumps(counts))
    print("held at implemented, no named test:", held)
    print("artifact:", doc["_acceptance_run"].get("artifact"))
    print("open findings:", len(doc["open_findings"]))
    for f in doc["open_findings"]:
        print("  -", f["id"], f["severity"], "|", f["title"])


if __name__ == "__main__":
    main()
