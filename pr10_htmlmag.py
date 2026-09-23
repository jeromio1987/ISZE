"""Read-only: magnitude of change per side for all conflicted HTML files."""
import difflib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def show(stage, path):
    r = subprocess.run(
        ["git", "show", ":%d:%s" % (stage, path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return r.stdout if r.returncode == 0 else None


def delta(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    add = rem = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "delete"):
            rem += i2 - i1
        if tag in ("replace", "insert"):
            add += j2 - j1
    return add, rem


out = subprocess.run(
    ["git", "diff", "--name-only", "--diff-filter=U"],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
).stdout
files = [l.strip() for l in out.splitlines() if l.strip() and l.strip().endswith(".html")]

print("%-64s %-8s %-14s %-14s %s" % ("FILE", "BASE", "OURS delta", "THEIRS delta", "READ"))
for f in files:
    b, o, t = show(1, f), show(2, f), show(3, f)
    bl = b.splitlines() if b else []
    if o is None:
        print("%-64s %-8d %-14s %s" % (f[-64:], len(bl), "DELETED", "PR DELETED -> take deletion"))
        continue
    oa, od = delta(bl, o.splitlines())
    ta, td = delta(bl, t.splitlines()) if t else (0, 0)
    if oa <= 8 and od <= 8:
        read = "PR did NOT change content -> take MAIN"
    elif ta <= 8 and td <= 8:
        read = "MAIN did not change -> take OURS"
    else:
        read = "BOTH changed substantially -> MANUAL"
    print("%-64s %-8d +%-6d -%-7d +%-6d -%-7d %s" % (f[-64:], len(bl), oa, od, ta, td, read))
