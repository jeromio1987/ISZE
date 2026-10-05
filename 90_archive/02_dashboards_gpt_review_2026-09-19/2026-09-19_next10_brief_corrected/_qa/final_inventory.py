"""Final verification-statement inventory across the ten files, post-edit, with line numbers,
and a check that no '143' / '116' / 'Pass 116' verification statement survives in visible text.
"""
import os, re

BASE = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected"
FILES = sorted(f for f in os.listdir(BASE) if f.endswith(".html"))
BAD = re.compile(r"143 pass|143/0/0|Pass 116|116 \u00b7 fail|143 passed|data verification 143|verification 143")

for fn in FILES:
    t = open(os.path.join(BASE, fn), encoding="utf-8", newline="").read()
    lines = t.split("\n")
    vis_idx = []
    # line numbers that are outside script/style
    in_script = in_style = False
    for i, ln in enumerate(lines, start=1):
        low = ln.lower()
        if "<script" in low: in_script = True
        if "</script>" in low: in_script = False; continue
        if "<style" in low: in_style = True
        if "</style>" in low: in_style = False; continue
        if in_script or in_style: continue
        vis_idx.append(i)
    vis = "\n".join(lines[i - 1] for i in vis_idx)
    def lines_with(pat):
        return [i for i in vis_idx if re.search(pat, lines[i - 1])]
    print("=" * 90)
    print(fn)
    for label, pat in [
        ("basis-strip / Data status", r"Data status"),
        ("footer .pf data verification", r"data verification"),
        ("sources-page verdict", r"pass / \d+ warn"),
        ("verify-stamp card", r"Verify stamp"),
    ]:
        hits = lines_with(pat)
        for h in hits:
            s = lines[h - 1].strip()
            s = re.sub(r"<[^>]+>", "", s)
            print(f"   L{h:>5}  {label:<28} {s[:150]}")
    bad = lines_with(BAD.pattern)
    print(f"   -> surviving stale verification statements in visible text: {bad if bad else 'NONE'}")
