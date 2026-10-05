"""Read-only: set-based comparison of OURS vs THEIRS for conflicted data files.

Reports whether one side is a strict superset (all their rows present in ours, or
vice versa) with no row content changed, or whether both sides carry different
values for overlapping rows.
"""
import csv
import io
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def raw(ref, path):
    r = subprocess.run(
        ["git", "show", "%s:%s" % (ref, path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return r.stdout if r.returncode == 0 else None


def rowset(ref, path):
    txt = raw(ref, path)
    if txt is None:
        return None, None
    rdr = list(csv.reader(io.StringIO(txt)))
    return set(tuple(r) for r in rdr[1:] if r), rdr[0] if rdr else []


files = [f.strip() for f in sys.argv[1].split(",")]
print("%-58s %-7s %-7s %-7s %-7s %-9s %s" % (
    "FILE", "OURS", "THEIRS", "O-ONLY", "T-ONLY", "HDR-SAME", "VERDICT"))
for f in files:
    o, ho = rowset(":2", f)
    t, ht = rowset(":3", f)
    if o is None or t is None:
        print("%-58s one side missing" % f[-58:])
        continue
    oo, tt = len(o - t), len(t - o)
    hdr = "yes" if ho == ht else "NO"
    if o == t:
        v = "IDENTICAL CONTENT"
    elif not tt:
        v = "OURS STRICT SUPERSET"
    elif not oo:
        v = "THEIRS STRICT SUPERSET"
    else:
        v = "BOTH DIVERGE (both carry rows the other lacks)"
    print("%-58s %-7d %-7d %-7d %-7d %-9s %s" % (f[-58:], len(o), len(t), oo, tt, hdr, v))
