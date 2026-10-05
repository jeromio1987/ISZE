"""Read-only: commit history per side for conflicted files."""
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

base = sys.argv[1]
files = sys.argv[2].split(",")
maxc = int(sys.argv[3]) if len(sys.argv) > 3 else 6

for f in files:
    print("=" * 92)
    print("FILE: %s" % f)
    for label, rng in (("PR-BRANCH (base..HEAD)", "%s..HEAD" % base),
                       ("MAIN (base..origin/main)", "%s..origin/main" % base)):
        r = subprocess.run(
            ["git", "log", "--oneline", "--no-merges", rng, "--", f],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        print("  %s  (%d commits)" % (label, len(lines)))
        for l in lines[:maxc]:
            print("      %s" % l)
