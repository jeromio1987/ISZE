"""Read-only: for each conflicted file show the last commit date on each side."""
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run(*args):
    return subprocess.run(
        list(args), capture_output=True, text=True, encoding="utf-8", errors="replace"
    ).stdout.strip()


out = run("git", "diff", "--name-only", "--diff-filter=U")
files = [l.strip() for l in out.splitlines() if l.strip()]

print("%-72s %-20s %-20s %s" % ("FILE", "PR-BRANCH-LAST", "MAIN-LAST", "HUNKS"))
for f in files:
    ours = run("git", "log", "-1", "--format=%ci", "HEAD", "--", f) or "n/a"
    theirs = run("git", "log", "-1", "--format=%ci", "origin/main", "--", f) or "n/a"
    ours = ours[:19]
    theirs = theirs[:19]
    print("%-72s %-20s %-20s" % (f, ours, theirs))
