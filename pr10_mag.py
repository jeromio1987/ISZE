"""Read-only: line-level change magnitude per side for conflicted files."""
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


def lines(txt):
    return [] if txt is None else txt.splitlines()


def delta(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    add = rem = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "delete"):
            rem += i2 - i1
        if tag in ("replace", "insert"):
            add += j2 - j1
    return add, rem


files = sys.argv[1].split(",")
print("%-58s %-8s %-8s %-8s %-16s %-16s" % ("FILE", "BASE", "OURS", "THEIRS", "OURS +add/-del", "THEIRS +add/-del"))
for f in files:
    b, o, t = lines(show(1, f)), lines(show(2, f)), lines(show(3, f))
    oa, od = delta(b, o)
    ta, td = delta(b, t)
    print("%-58s %-8d %-8d %-8d +%-6d -%-8d +%-6d -%-8d" % (
        f[-58:], len(b), len(o), len(t), oa, od, ta, td))
