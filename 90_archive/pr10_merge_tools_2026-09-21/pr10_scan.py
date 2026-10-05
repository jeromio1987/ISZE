"""Read-only conflict scanner for PR10 worktree. Prints conflict hunks per file.

Writes nothing except stdout. Reads only files listed by git as unmerged.
"""
import io
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

out = subprocess.run(
    ["git", "diff", "--name-only", "--diff-filter=U"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
)
files = [l.strip() for l in out.stdout.splitlines() if l.strip()]

mode = sys.argv[1] if len(sys.argv) > 1 else "all"
if mode == "nonhtml":
    files = [f for f in files if not f.endswith(".html")]
elif mode == "html":
    files = [f for f in files if f.endswith(".html")]

maxh = int(sys.argv[2]) if len(sys.argv) > 2 else 8
show = int(sys.argv[3]) if len(sys.argv) > 3 else 80

summary = []
for f in files:
    try:
        lines = io.open(f, encoding="utf-8", errors="replace").read().splitlines()
    except Exception as exc:  # noqa: BLE001
        print("ERR", f, exc)
        continue
    hunks = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("<<<<<<<"):
            start = i
            while i < len(lines) and not lines[i].startswith(">>>>>>>"):
                i += 1
            hunks.append((start, i))
        i += 1
    print("=" * 100)
    print("FILE: %s | hunks: %d | lines: %d" % (f, len(hunks), len(lines)))
    for n, (s, e) in enumerate(hunks[:maxh], 1):
        print("--- hunk %d (lines %d-%d) ---" % (n, s + 1, e + 1))
        for l in lines[max(0, s):min(len(lines), e + 1)][:show]:
            print(l)
    if len(hunks) > maxh:
        print("... %d more hunks suppressed" % (len(hunks) - maxh))
    summary.append((f, len(hunks)))

print()
print("### SUMMARY ###")
for f, n in summary:
    print("%4d  %s" % (n, f))
