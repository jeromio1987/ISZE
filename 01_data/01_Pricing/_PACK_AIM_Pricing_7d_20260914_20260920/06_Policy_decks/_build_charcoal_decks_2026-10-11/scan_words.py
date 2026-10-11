"""Scan every text run, table cell, chart label and speaker note of a deck for words that must not appear."""
import re
import sys
import zipfile
from pathlib import Path

from pptx import Presentation

ALL = [r"sell[- ]?out", r"\bstreet\b", r"wallet", r"Mode [AB]\b", r"Book B", r"List [12]\b", r"mark[- ]?up", r"×\s*1\.", r"\bfactors?\b",
       r"warrant", r"\bPRISM\b", r"IML v7", r"Model B", r"\bgate\b", r"harness", r"payload", r"spine", r"residual",
       r"upstream", r"baseline", r"campaign", r"lane\b", r"\bfix if safe\b", r"ISZE\s*GPS", r"\bUIO\b", r"mapchart"]
PRICING_ONLY = [r"\bAIM\b", r"\bUMI\b", r"\bUTI\b", r"\bITUK\b", r"\bIUK\b", r"classification"]

deck = Path(sys.argv[1])
kind = sys.argv[2]  # aim | pricing
pats = ALL + (PRICING_ONLY if kind == "pricing" else [])
prs = Presentation(deck)
hits = []
texts = 0
for i, s in enumerate(prs.slides, 1):
    chunks = []
    for sh in s.shapes:
        if sh.has_text_frame:
            chunks.append(sh.text_frame.text)
        if sh.has_table if hasattr(sh, "has_table") else False:
            for r in sh.table.rows:
                for c in r.cells:
                    chunks.append(c.text_frame.text)
    if s.has_notes_slide:
        chunks.append(s.notes_slide.notes_text_frame.text)
    for c in chunks:
        texts += 1
        for p in pats:
            for m in re.finditer(p, c, flags=re.I):
                hits.append((i, p, c[max(0, m.start() - 40): m.end() + 40].replace("\n", " ")))
# chart labels live in the chart parts
with zipfile.ZipFile(deck) as z:
    for n in z.namelist():
        if n.startswith("ppt/charts/chart") and n.endswith(".xml"):
            x = z.read(n).decode("utf-8", "ignore")
            for t in re.findall(r"<a:t>([^<]*)</a:t>|<c:v>([^<]*)</c:v>", x):
                txt = t[0] or t[1]
                texts += 1
                for p in pats:
                    if re.search(p, txt, flags=re.I):
                        hits.append((n, p, txt))
print(deck.name, "text blocks scanned:", texts, "hits:", len(hits))
for h in hits:
    print(h)
