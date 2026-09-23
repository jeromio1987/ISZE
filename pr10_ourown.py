"""Read-only: compare stage2 (ours) vs stage3 (theirs) for conflicted files."""
import difflib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def show(ref, path):
    r = subprocess.run(
        ["git", "show", "%s:%s" % (ref, path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return r.stdout if r.returncode == 0 else None


files = sys.argv[1].split(",")
maxdiff = int(sys.argv[2]) if len(sys.argv) > 2 else 4000
for f in files:
    o = show(":2", f)
    t = show(":3", f)
    print("=" * 90)
    print("FILE: %s" % f)
    if o is None or t is None:
        print("   ours=%s theirs=%s" % ("present" if o else "MISSING", "present" if t else "MISSING"))
        continue
    if o == t:
        print("   OURS == THEIRS (byte identical)")
        continue
    ol, tl = o.splitlines(), t.splitlines()
    sm = difflib.SequenceMatcher(None, ol, tl, autojunk=False)
    ops = [op for op in sm.get_opcodes() if op[0] != "equal"]
    print("   ours_lines=%d theirs_lines=%d  differing_blocks=%d" % (len(ol), len(tl), len(ops)))
    d = list(difflib.unified_diff(ol, tl, "OURS", "THEIRS", lineterm="", n=2))
    if len(d) > maxdiff:
        d = d[:maxdiff] + ["...[truncated]..."]
    print("\n".join(d))
