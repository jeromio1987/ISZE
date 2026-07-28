"""Extract text from GIDSS PDFs via PyMuPDF; also render pages to PNG for OCR."""
import pathlib
import fitz

att = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull\attachments")
outdir = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull\pdf_text")
imgdir = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull\pdf_pages")
outdir.mkdir(parents=True, exist_ok=True)
imgdir.mkdir(parents=True, exist_ok=True)

targets = [
    "20260716_Rene_Paul_isuzu_de_GIDSS_maint_N_MY24.pdf",
    "20260716_Rene_Paul_isuzu_de_GIDSS_maint_N_MY14.pdf",
    "20260716_Rene_Paul_isuzu_de_GIDSS_maint_F_MY24.pdf",
    "20260716_Rene_Paul_isuzu_de_GIDSS_maint_F_MY14.pdf",
    "20260723_Duncan_Young_Parts_Business_Service_product.pdf",
]

for name in targets:
    path = att / name
    if not path.exists():
        print("MISSING", name)
        continue
    doc = fitz.open(path)
    print(f"\n=== {name} pages={doc.page_count} ===")
    texts = []
    for i, page in enumerate(doc):
        # try multiple extractors
        t1 = page.get_text("text") or ""
        t2 = page.get_text("blocks")
        block_text = []
        if isinstance(t2, list):
            for b in t2:
                if len(b) >= 5 and isinstance(b[4], str):
                    block_text.append(b[4])
        t_blocks = "\n".join(block_text)
        # prefer longer
        chosen = t1 if len(t1) >= len(t_blocks) else t_blocks
        texts.append(f"\n\n===== PAGE {i+1} =====\n{chosen}")
        # render page image at 200 dpi for OCR
        if name.startswith("20260716_Rene"):
            zoom = 200 / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            out_img = imgdir / f"{path.stem}_p{i+1:02d}.png"
            pix.save(str(out_img))
            print(f"  p{i+1}: text_chars={len(chosen)} img={out_img.name} {pix.width}x{pix.height}")
        else:
            print(f"  p{i+1}: text_chars={len(chosen)}")
    out = outdir / (path.stem + "_pymupdf.txt")
    out.write_text("\n".join(texts), encoding="utf-8", errors="replace")
    print("WROTE", out.name, "total", sum(len(x) for x in texts))
