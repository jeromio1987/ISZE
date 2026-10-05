"""Read-only: targeted comparisons of the three merge stages for derived data files."""
import csv
import io
import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def show(stage, path):
    r = subprocess.run(
        ["git", "show", ":%d:%s" % (stage, path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return r.stdout if r.returncode == 0 else None


def rows(stage, path):
    txt = show(stage, path)
    if txt is None:
        return None
    return list(csv.reader(io.StringIO(txt)))


def label(stage):
    return {1: "BASE", 2: "OURS(PR)", 3: "THEIRS(main)"}[stage]


# ---- 1. pr00_classification.csv : empty fig_key count -----------------------
f = "01_data/00_derived/pr00_classification.csv"
print("#" * 90)
print("# %s" % f)
for st in (1, 2, 3):
    rr = rows(st, f)
    if rr is None:
        print("  %-12s MISSING" % label(st))
        continue
    hdr = rr[0]
    body = [r for r in rr[1:] if r]
    print("  %-12s rows=%-8d cols=%d header=%s" % (label(st), len(body), len(hdr), hdr))
    # count empty in each column
    for ci, name in enumerate(hdr):
        empty = sum(1 for r in body if ci < len(r) and r[ci].strip() == "")
        if empty:
            print("       empty %-14s %d" % (name, empty))
    # last 2 cols shown for a sample
    print("       sample: %s" % (body[0],))

# ---- 2. dealer_sellout files : what rows exist ------------------------------
for f in ("01_data/00_derived/dealer_sellout_aim_mix_2025.csv",
          "01_data/00_derived/dealer_sellout_gps_2025.csv"):
    print("#" * 90)
    print("# %s" % f)
    for st in (1, 2, 3):
        rr = rows(st, f)
        if rr is None:
            print("  %-12s MISSING" % label(st))
            continue
        hdr, body = rr[0], [r for r in rr[1:] if r]
        ents = sorted({r[-3] for r in body if len(r) > 3})
        print("  %-12s rows=%-5d entities=%s" % (label(st), len(body), ents))
        print("       first=%s" % (body[0][:4],))
        print("       last =%s" % (body[-1][:4],))

# ---- 3. dashboard json : compare parsed structure ---------------------------
f = "01_data/14_dashboards/dealer_sellout_aim_gps.json"
print("#" * 90)
print("# %s" % f)
for st in (1, 2, 3):
    txt = show(st, f)
    if txt is None:
        print("  %-12s MISSING" % label(st))
        continue
    try:
        obj = json.loads(txt)
    except Exception as exc:  # noqa: BLE001
        print("  %-12s NOT PARSEABLE: %s" % (label(st), exc))
        continue
    print("  %-12s top-level keys=%s" % (label(st), list(obj)[:12]))
    for k in list(obj):
        v = obj[k]
        if isinstance(v, list):
            print("       %-24s list len=%d" % (k, len(v)))
        elif isinstance(v, dict):
            print("       %-24s dict keys=%s" % (k, list(v)[:10]))
        else:
            print("       %-24s %r" % (k, v))
