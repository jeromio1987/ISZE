"""Read-only: compare common rows (by first column) between OURS and THEIRS."""
import csv
import io
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def rows(ref, path):
    r = subprocess.run(
        ["git", "show", "%s:%s" % (ref, path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if r.returncode != 0:
        return None
    return list(csv.reader(io.StringIO(r.stdout)))


files = sys.argv[1].split(",")
keycol = int(sys.argv[2]) if len(sys.argv) > 2 else 0

for f in files:
    ro, rt = rows(":2", f), rows(":3", f)
    print("=" * 88)
    print("FILE: %s" % f)
    if not ro or not rt:
        print("   missing on one side")
        continue
    ho, ht = ro[0], rt[0]
    print("   header ours  : %s" % ho)
    print("   header theirs: %s" % ht)
    if ho != ht:
        print("   ** HEADER DIFFERS **")
    do = {r[keycol]: r for r in ro[1:] if len(r) > keycol}
    dt = {r[keycol]: r for r in rt[1:] if len(r) > keycol}
    common = sorted(set(do) & set(dt))
    only_o = sorted(set(do) - set(dt))
    only_t = sorted(set(dt) - set(do))
    print("   rows ours=%d theirs=%d  common=%d  ours-only=%d  theirs-only=%d" % (
        len(do), len(dt), len(common), len(only_o), len(only_t)))
    diffs = [k for k in common if do[k] != dt[k]]
    print("   common rows with DIFFERENT VALUES: %d" % len(diffs))
    for k in diffs[:6]:
        print("      key=%s" % k)
        print("        ours  : %s" % do[k])
        print("        theirs: %s" % dt[k])
    if only_t:
        print("   theirs-only sample: %s" % [dt[k] for k in only_t[:3]])
    if only_o:
        print("   ours-only sample  : %s" % [do[k] for k in only_o[:3]])
