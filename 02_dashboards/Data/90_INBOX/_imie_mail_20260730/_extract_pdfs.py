import fitz
import re
from pathlib import Path

out = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_imie_mail_20260730")
keywords = re.compile(
    r"UK|IUK|ITUK|ZEV|BIK|P700|stock|SPA|order|share|mandate|ICE|BEV|EV|"
    r"fleet|car.?park|UIO|regist|soft|market|compet|Maxus|Ford|Foton|"
    r"changeover|MY|26MY|penalty|demand|target|FY27|FY26|IMIE|IMIT|"
    r"Nikola|Lucas|Lukas|Israel|UMI|Portugal|Ireland|Germany|Turkey|"
    r"Norway|Belgium|SPA|P700|N75|N35",
    re.I,
)
focus = re.compile(
    r"UK:|ZEV|BIK|P700|IUK|ICE|BEV|share|mandate|stock|soft|"
    r"changeover|26MY|Maxus|penalty|Order Summary|TTL|YTD|"
    r"registrations are low|BIK tax|Foton|Ford|Israel|UMI|skipped|"
    r"SPA|P700|model",
    re.I,
)

for name in [
    "260629_3 Party Meeting English.pdf",
    "260724_3 Party Meeting English.pdf",
]:
    pdf = out / name
    if not pdf.exists():
        print("MISSING", name)
        continue
    doc = fitz.open(pdf)
    stem = pdf.stem.replace(" ", "_")
    text_path = out / f"{stem}_fulltext.txt"
    hits_path = out / f"{stem}_hits.txt"
    pages_out = []
    hits = []
    for i, page in enumerate(doc):
        t = page.get_text("text")
        pages_out.append(f"\n===== PAGE {i+1} =====\n{t}")
        for ln in t.splitlines():
            ln = ln.strip()
            if ln and keywords.search(ln):
                hits.append(f"P{i+1}: {ln}")
    text_path.write_text("\n".join(pages_out), encoding="utf-8")
    hits_path.write_text("\n".join(hits), encoding="utf-8")
    print(f"{name}: {len(doc)} pages, {len(hits)} hit lines")
    print("--- KEY SNIPPETS ---")
    for h in hits:
        if focus.search(h):
            print(h[:300])
    print()
