"""Read-only: show conflict hunks for an explicit file list."""
import io
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

out = subprocess.run(
    ["git", "diff", "--name-only", "--diff-filter=U"],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
).stdout
avail = [l.strip() for l in out.splitlines() if l.strip()]

patterns = sys.argv[1].split(",")
files = [f for f in avail if any(p in f for p in patterns)]

maxlines = int(sys.argv[2]) if len(sys.argv) > 2 else 200

for f in files:
    lines = io.open(f, encoding="utf-8", errors="replace").read().splitlines()
    hunks = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("<<<<<<<"):
            s = i
            while i < len(lines) and not lines[i].startswith(">>>>>>>"):
                i += 1
            hunks.append((s, i))
        i += 1
    print("=" * 100)
    print("FILE: %s | hunks: %d | lines: %d" % (f, len(hunks), len(lines)))
    for n, (s, e) in enumerate(hunks[:12], 1):
        print("--- hunk %d (lines %d-%d, %d conflict lines) ---" % (n, s + 1, e + 1, e - s + 1))
        body = lines[max(0, s - 4):min(len(lines), e + 5)]
        for l in body[:maxlines]:
            print(l)
    if len(hunks) > 12:
        print("... %d more hunks suppressed" % (len(hunks) - 12))
