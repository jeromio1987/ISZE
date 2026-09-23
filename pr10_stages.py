"""Read-only: classify each conflict by comparing the three merge stages.

stage 1 = merge base, stage 2 = ours (PR branch), stage 3 = theirs (main).
If only one side differs from base, the conflict is one-sided and mechanical.
If both differ from base, two sides genuinely changed the same region.
"""
import hashlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def blob_hash(stage, path):
    r = subprocess.run(
        ["git", "rev-parse", ":%d:%s" % (stage, path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if r.returncode != 0:
        return None
    return r.stdout.strip()


def blob(stage, path):
    r = subprocess.run(
        ["git", "show", ":%d:%s" % (stage, path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return r.stdout if r.returncode == 0 else None


def size(stage, path):
    r = subprocess.run(
        ["git", "cat-file", "-s", ":%d:%s" % (stage, path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return r.stdout.strip() if r.returncode == 0 else "MISSING"


out = subprocess.run(
    ["git", "diff", "--name-only", "--diff-filter=U"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
).stdout
files = [l.strip() for l in out.splitlines() if l.strip()]

print("%-70s %-9s %-9s %-9s %s" % ("FILE", "BASE", "OURS", "THEIRS", "VERDICT"))
counts = {}
for f in files:
    b, o, t = blob_hash(1, f), blob_hash(2, f), blob_hash(3, f)
    if b is None:
        verdict = "ADDED-BOTH (no base)"
    elif o is None:
        verdict = "OURS-DELETED, THEIRS-CHANGED"
    elif t is None:
        verdict = "THEIRS-DELETED, OURS-CHANGED"
    elif b == t and b != o:
        verdict = "OURS-ONLY (take ours)"
    elif b == o and b != t:
        verdict = "THEIRS-ONLY (take theirs)"
    elif o == t:
        verdict = "IDENTICAL (no real conflict)"
    else:
        verdict = "BOTH-CHANGED  <-- two-sided"
    counts[verdict.split(" ")[0]] = counts.get(verdict.split(" ")[0], 0) + 1
    print("%-70s %-9s %-9s %-9s %s" % (f, size(1, f), size(2, f), size(3, f), verdict))

print()
print("### COUNTS ###")
for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
    print("%4d  %s" % (v, k))

print()
print("### TWO-SIDED FILES IN DETAIL ###")
for f in files:
    b, o, t = blob_hash(1, f), blob_hash(2, f), blob_hash(3, f)
    if b and o and t and b != o and b != t and o != t:
        for stage, label in ((1, "BASE"), (2, "OURS/PR"), (3, "THEIRS/main")):
            pass
        print("~~ %s" % f)
