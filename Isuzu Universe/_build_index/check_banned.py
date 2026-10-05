# -*- coding: utf-8 -*-
r"""Search the finished index for anything that names build tooling.

Run with no argument for the current PDF, or with a path for another one. Read-only.
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(HERE), "UNIVERSE_FOLDER_INDEX_2026-09-23.pdf")

TERMS = ["_build", ".py", ".cmd", "SHIP_RECEIPT", "VERIFICATION", "_qa", "_probe",
         "build_", "figures", "docbuild", "check_", "receipt", "script", "_raw"]

d = fitz.open(PDF)
print("file:", PDF)
print("pages:", d.page_count)
text = ""
for i, p in enumerate(d):
    text += "\n<<<PAGE %d>>>\n" % (i + 1) + p.get_text()
d.close()

total = 0
for term in TERMS:
    hits = []
    for m in re.finditer(re.escape(term), text):
        start = max(0, m.start() - 60)
        end = min(len(text), m.end() + 60)
        ctx = " ".join(text[start:end].split())
        hits.append(ctx)
    total += len(hits)
    print()
    print("== %-14s hits: %d" % (term, len(hits)))
    for h in hits:
        print("     ...%s..." % h)

print()
print("TOTAL HITS:", total)
