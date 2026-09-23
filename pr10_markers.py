"""Read-only: check which markers each side's version of a conflicted file contains."""
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def show(stage, path):
    r = subprocess.run(
        ["git", "show", ":%d:%s" % (stage, path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return r.stdout if r.returncode == 0 else None


path = sys.argv[1]
markers = sys.argv[2].split("|")

for stage, label in ((1, "BASE"), (2, "OURS(PR)"), (3, "THEIRS(main)")):
    txt = show(stage, path)
    print("=" * 70)
    print("%s  (%s)" % (label, "MISSING" if txt is None else "%d bytes" % len(txt)))
    if txt is None:
        continue
    low = txt.lower()
    for m in markers:
        print("   %-42s %s" % (m, "YES" if m.lower() in low else "no"))
