"""Probe the UTI July 2026 parts presentation PDF: page count, text layer, render pages 13-18."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import fitz  # PyMuPDF

SRC = Path(r"C:\Users\jerom\Downloads\מצגת לחלפים בלגיה - אפריל 2026.pdf")
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Israel_Rebuild_20260922\_pdf")
OUT.mkdir(parents=True, exist_ok=True)

print("pdf:", SRC.name)
print("exists:", SRC.exists())
st = SRC.stat()
print("bytes:", st.st_size, "mtime:", datetime.fromtimestamp(st.st_mtime).isoformat())

doc = fitz.open(SRC)
print("pages:", doc.page_count)
print("metadata:", json.dumps({k: str(v) for k, v in (doc.metadata or {}).items()}, ensure_ascii=False))

meta = {
    "source_file": str(SRC),
    "source_mtime": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
    "read_utc": datetime.now(timezone.utc).isoformat(),
    "page_count": doc.page_count,
    "pages": {},
}

for i in range(doc.page_count):
    page = doc[i]
    txt = page.get_text("text")
    meta["pages"][str(i + 1)] = {"chars": len(txt)}
    print(f"\n{'=' * 90}\nPAGE {i + 1}  chars={len(txt)}\n{'=' * 90}")
    print(txt.strip()[:4000])

# Render selected pages for visual QA of the charts / tables.
targets = [13, 14, 15, 16, 17, 18, 19, 20]
for p in targets:
    if p < 1 or p > doc.page_count:
        continue
    pix = doc[p - 1].get_pixmap(dpi=170)
    f = OUT / f"uti_p{p:02d}.png"
    pix.save(f)
    print("rendered:", f, pix.width, "x", pix.height)

(OUT / "pdf_probe.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nwrote:", OUT / "pdf_probe.json")
