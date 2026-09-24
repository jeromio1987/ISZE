"""Confirm the printed reading guide against the headings actually rendered in the PDF.

The guide's own page numbers are read out of the rendered guide table, not from a copy in this
script, so the check cannot go stale when the page count moves.
"""
import re
import sys

import fitz

sys.stdout.reconfigure(encoding="utf-8")

PDF = sys.argv[1] if len(sys.argv) > 1 else r"_build_30\_staged_final.pdf"
d = fitz.open(PDF)


def heads(pno, min_size=14.5):
    out = []
    for blk in d[pno - 1].get_text("dict")["blocks"]:
        for line in blk.get("lines", []):
            for sp in line["spans"]:
                if sp["size"] >= min_size and sp["bbox"][0] < 120 and sp["text"].strip():
                    out.append(sp["text"].strip())
    return out


# which page carries the guide table
guide_pg = None
for i in range(d.page_count):
    if "Chapter schedule" in d[i].get_text() and "Pages" in d[i].get_text():
        guide_pg = i + 1
        break
if guide_pg is None:
    print("no reading guide found")
    sys.exit(1)

# read the table rows: chapter title, then its page range, from the guide page itself
rows = []
t = "\n".join(d[guide_pg - 1].get_text().split("\n"))
for m in re.finditer(r"([0-9][0-9\-]*)\s*\n", t):
    rows.append(m.group(1))

# pair each guide line with the entry text that precedes it
entries = []
lines = [x.strip() for x in t.split("\n") if x.strip()]
for k, ln in enumerate(lines):
    if re.fullmatch(r"\d{1,2}(-\d{1,2})?", ln) and k:
        title = lines[k - 1]
        if re.fullmatch(r"\d{1,2}(-\d{1,2})?", title):
            continue
        entries.append((title, ln))

print(f"guide on page {guide_pg}; {len(entries)} entries read from the rendered table")
print()
bad = 0
for title, span in entries:
    where = [p for p in range(1, d.page_count + 1) if any(title in h for h in heads(p))]
    first = str(where[0]) if where else "NOT FOUND"
    ok = first == span.split("-")[0]
    bad += 0 if ok else 1
    print(f"  {'OK ' if ok else 'BAD'}  guide says {span:<6} heading rendered on {where}")
print(f"\nentries checked: {len(entries)}   mismatches: {bad}")
d.close()
sys.exit(1 if bad else 0)
