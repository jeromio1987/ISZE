# -*- coding: utf-8 -*-
"""B2: verify the single isuzu.pt apparent price (competitor 'P 34 013')."""
from __future__ import annotations
import io, re, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\01_data\90_INBOX\scrape_targets\_probe\_u26\B2")
p = HERE / "pages" / "www.isuzu.pt__P 34 013.html"
print("exists:", p.exists())
if p.exists():
    b = p.read_text(encoding="utf-8", errors="replace")
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b))
    print("len:", len(b))
    for m in re.finditer(r"\u20ac\s*\d[\d.,]*|\d[\d.,]*\s*\u20ac", txt):
        print("  ...", txt[max(0,m.start()-110):m.start()+60])
    m = re.search(r"(Nada encontrado|Nothing found|Sem resultados|Não foi possível encontrar|resultados)", txt, re.I)
    print("marker:", txt[max(0,m.start()-60):m.start()+120] if m else "none")
