import pathlib
from pypdf import PdfReader

att = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull\attachments")
outdir = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull\pdf_text")
outdir.mkdir(parents=True, exist_ok=True)

for path in sorted(att.glob("*.pdf")):
    print("EXTRACT", path.name)
    try:
        reader = PdfReader(str(path))
        texts = []
        for i, page in enumerate(reader.pages):
            try:
                t = page.extract_text() or ""
            except Exception as ex:
                t = f"[page {i+1} extract error: {ex}]"
            texts.append(f"\n\n===== PAGE {i+1} =====\n{t}")
        out = outdir / (path.stem + ".txt")
        out.write_text("\n".join(texts), encoding="utf-8", errors="replace")
        print("  pages", len(reader.pages), "chars", sum(len(x) for x in texts), "->", out.name)
    except Exception as e:
        print("  FAIL", e)
