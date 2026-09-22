"""Sweep files for restricted supplier cost values.

The exclusion scheme keeps the payload, the frozen reference and the assembled
HTML out of version control. It does not stop a restricted VALUE being quoted in
a document, which is how a four-decimal supplier cost ended up in
progress/progress.json beside a part number.

This reads the real cost values out of the restricted payload, then searches for
them. Two scopes:

    python tools/restricted_value_sweep.py                 # git-tracked files
    python tools/restricted_value_sweep.py <folder>        # any folder, tracked or not

The second scope matters and was missing. The tracked-file scan is blind to
build-script folders and handover packs, and a real payload cost figure was found
in an UNTRACKED build script (06_Working/_aim_pack_20260922/validate_v03.py)
precisely because nothing was looking there. A scan that only sees what version
control already vets does not answer the question a reader is asking.

Usage:  python tools/restricted_value_sweep.py [folder]
Exit 0 when clean, 1 when a scanned file carries a restricted value.
"""
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=ROOT,
                      capture_output=True, text=True).stdout.strip()
PAYLOAD = os.path.join(ROOT, "payload", "aim_payload_20260922.json")

TEXT_EXT = (".js", ".mjs", ".cjs", ".py", ".json", ".md", ".txt", ".ps1", ".html", ".css")

# Folders that hold the restricted material itself, and must never be scanned as
# if they were suspicious - they are the source of truth this sweep reads.
SKIP_DIRS = ("\\.git", "node_modules", "_qa", "\\dist", "\\reference", "\\payload")


def tracked_files():
    out = subprocess.run(["git", "ls-files", "--", "Isuzu Universe/05_AIM_Universe"],
                         cwd=REPO, capture_output=True, text=True).stdout
    return [os.path.join(REPO, f.strip()) for f in out.split("\n") if f.strip()]


def walk_files(folder):
    out = []
    for base, dirs, files in os.walk(folder):
        if any(s.strip("\\") in base for s in SKIP_DIRS):
            continue
        dirs[:] = [d for d in dirs
                   if d not in (".git", "node_modules", "_qa", "dist", "reference", "payload")]
        for f in files:
            if f.lower().endswith(TEXT_EXT):
                out.append(os.path.join(base, f))
    return out


def sensitive_values():
    """Every cost figure and part number the payload carries, as strings."""
    if not os.path.exists(PAYLOAD):
        print("note: the restricted payload is not present, so this sweep cannot read the")
        print("      values it should be looking for. Run it where the payload lives.\n")
        return set(), set()
    d = json.load(io.open(PAYLOAD, encoding="utf-8"))
    costs, parts = set(), set()
    for row in d.get("verifiedCosts", []):
        parts.add(str(row.get("part_number")))
        for basis, cell in (row.get("cost_bases") or {}).items():
            v = cell.get("cost_eur")
            if isinstance(v, (int, float)) and abs(v) > 0.01:
                costs.add("%.4f" % v)
                costs.add("%.2f" % v)
        for key in ("default_forward_cost_eur", "historical_cost_eur"):
            v = row.get(key)
            if isinstance(v, (int, float)) and abs(v) > 0.01:
                costs.add("%.4f" % v)
                costs.add("%.2f" % v)
    return costs, parts


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    costs, parts = sensitive_values()
    files = walk_files(target) if target else tracked_files()
    scope = ("folder " + target) if target else "git-tracked files under 05_AIM_Universe"

    # Four decimals is precise enough to be a copied figure; two decimals alone is
    # too common to be evidence, so the scan requires a part number on the line.
    four_dp = {c for c in costs if len(c.split(".")[-1]) == 4}

    print("scope                  : %s" % scope)
    print("files scanned          : %d" % len(files))
    print("restricted cost figures: %d distinct (of which %d are four-decimal)"
          % (len(costs), len(four_dp)))
    print("part numbers           : %d" % len(parts))
    print("")

    findings = []
    for path in files:
        try:
            text = io.open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        rel = os.path.relpath(path, REPO).replace("\\", "/")
        for n, line in enumerate(text.split("\n"), 1):
            hit_cost = [c for c in four_dp if c in line]
            hit_part = [p for p in parts if p and p in line]
            if hit_cost and hit_part:
                findings.append((rel, n, "a restricted cost figure and a part number on one line",
                                 ", ".join(hit_part)))
            elif hit_cost and re.search(r"cost|price|fob|eur", line, re.I):
                findings.append((rel, n, "a restricted cost figure in a cost context",
                                 ", ".join(hit_cost)))

    if not findings:
        print("CLEAN: no scanned file carries a restricted cost figure.")
        return 0
    print("FINDINGS: %d line(s) carry a restricted cost figure.\n" % len(findings))
    for rel, n, what, detail in findings:
        print("  %s:%d" % (rel, n))
        print("     %s" % what)
        print("     matched: %s" % detail)
        print("")
    print("Fix by citing the FIELD NAME instead of the figure, or by banding it.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
