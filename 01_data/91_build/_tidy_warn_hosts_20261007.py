"""Tidy the builder after the defensive-layer edits: de-duplicate warning hosts only.

Deliberately narrow: it removes an immediately repeated identical <div id="warn-p-X"></div> and
nothing else. Every other edit in this pass is made by hand and reviewed.
"""
import re
from pathlib import Path

P = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ops\_build_backlog_iml_wk41.py")
s = P.read_text(encoding="utf-8")

pat = re.compile(r'(<div id="warn-p-[a-z]+"></div>)\1+')
before = len(pat.findall(s))
s = pat.sub(r"\1", s)
after = len(re.findall(r'<div id="warn-p-[a-z]+"></div>', s))

P.write_text(s, encoding="utf-8")
print("doubled groups fixed:", before)
print("warning hosts now:", after)
for m in re.finditer(r'<div id="warn-p-[a-z]+"></div>', s):
    print("  ", m.group(0))
