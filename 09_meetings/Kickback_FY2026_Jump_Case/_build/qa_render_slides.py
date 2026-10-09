"""Render every slide of the deck to PNG via LibreOffice (headless), for visual QA."""
from __future__ import annotations
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case")
PPTX = HERE / "ISZE_Kickback_FY2026_Year_End_Jump_Case.pptx"
QA = HERE / "_qa"
QA.mkdir(exist_ok=True)

soffice = None
for c in [r"C:\Program Files\LibreOffice\program\soffice.exe",
          r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"]:
    if Path(c).exists():
        soffice = c
        break
print("soffice:", soffice)
if not soffice:
    print("LIBREOFFICE_NOT_FOUND")
    sys.exit(2)

# pptx -> pdf
subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(QA), str(PPTX)],
               check=True, timeout=300)
pdf = QA / (PPTX.stem + ".pdf")
print("pdf:", pdf.exists(), pdf.stat().st_size if pdf.exists() else 0)

# pdf -> png per page
try:
    import fitz  # PyMuPDF
except ImportError:
    print("NO_PYMUPDF")
    sys.exit(3)
doc = fitz.open(pdf)
print("pages:", doc.page_count)
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=110)
    out = QA / f"slide_{i+1:02d}.png"
    pix.save(out)
    print("  ", out.name, pix.width, "x", pix.height)
doc.close()
