"""Restore the PR's banned-word cleanup on the 41 resolved IDS pages.

Replaces the 'Mode A' audience label with the approved 'shared' wording in one
identical comment line. Writes only inside the PR worktree.
"""
import glob
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OLD = "Workspace aliases \u2192 Mode A country labels"
NEW = "Workspace aliases \u2192 shared country labels"

changed = 0
scanned = 0
for path in glob.glob("02_dashboards/ids/**/*.html", recursive=True):
    scanned += 1
    txt = io.open(path, encoding="utf-8", errors="surrogateescape").read()
    if OLD in txt:
        io.open(path, "w", encoding="utf-8", errors="surrogateescape", newline="").write(
            txt.replace(OLD, NEW)
        )
        changed += 1

print("scanned %d html files under 02_dashboards/ids" % scanned)
print("changed %d" % changed)

leftover = 0
for path in glob.glob("02_dashboards/ids/**/*.html", recursive=True):
    txt = io.open(path, encoding="utf-8", errors="surrogateescape").read()
    if "Mode A" in txt or "Mode B" in txt:
        leftover += 1
print("files still containing Mode A/B: %d" % leftover)
