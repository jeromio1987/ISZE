"""Save chosen Duncan Rev2 pptx from Outlook, extract slides, dump mail body."""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import win32com.client  # type: ignore

DEST = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\IML_ITUK_Meeting_20260814")
CHOSEN = json.loads((DEST / "_chosen.json").read_text(encoding="utf-8"))
NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def _safe(name: str) -> str:
    return re.sub(r"[^\w.\-]+", "_", name)


def pptx_slides(path: Path) -> list[dict]:
    slides = []
    with zipfile.ZipFile(path) as z:
        names = sorted(
            n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")
        )
        # sort by slide number not lexicographic slide10 before slide2
        def key(n: str) -> int:
            m = re.search(r"slide(\d+)\.xml$", n)
            return int(m.group(1)) if m else 0

        names = sorted(names, key=key)
        for name in names:
            root = ET.fromstring(z.read(name))
            texts = [
                t.text.strip()
                for t in root.iter(NS + "t")
                if t.text and t.text.strip()
            ]
            slides.append({"file": name, "texts": texts, "joined": " | ".join(texts)})
    return slides


def dump_pptx(path: Path) -> Path:
    slides = pptx_slides(path)
    out = path.with_name(path.stem + "_slides.json")
    out.write_text(json.dumps(slides, indent=2, ensure_ascii=False), encoding="utf-8")
    md = path.with_name(path.stem + "_slides.md")
    lines = [f"# {path.name}", ""]
    for i, s in enumerate(slides, 1):
        lines.append(f"## Slide {i}")
        lines.append("")
        for t in s["texts"]:
            lines.append(f"- {t}")
        lines.append("")
    md.write_text("\n".join(lines), encoding="utf-8")
    print(f"{path.name}: {len(slides)} slides -> {md.name}", flush=True)
    return md


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    mail = ns.GetItemFromID(CHOSEN["entry_id"])
    meta = {
        "received": str(mail.ReceivedTime),
        "from": str(mail.SenderName or ""),
        "email": str(getattr(mail, "SenderEmailAddress", "") or ""),
        "subject": str(mail.Subject or ""),
        "to": str(mail.To or ""),
        "cc": str(mail.CC or ""),
        "attachments": [],
    }
    (DEST / "_mail_body.txt").write_text(str(mail.Body or ""), encoding="utf-8")
    html = str(getattr(mail, "HTMLBody", "") or "")
    if html:
        (DEST / "_mail_body.html").write_text(html, encoding="utf-8")
    saved_pptx = None
    for i in range(1, mail.Attachments.Count + 1):
        att = mail.Attachments.Item(i)
        name = str(att.FileName)
        low = name.lower()
        if low.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
            continue
        dest = DEST / _safe(name)
        att.SaveAsFile(str(dest))
        meta["attachments"].append({"name": name, "path": str(dest), "size": dest.stat().st_size})
        print(f"SAVED {dest} ({dest.stat().st_size} bytes)", flush=True)
        if low.endswith(".pptx"):
            saved_pptx = dest
    (DEST / "_mail_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    if saved_pptx:
        dump_pptx(saved_pptx)
    # also re-extract old with numeric slide sort for fair compare
    old = Path(
        r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\IML_ITUK_Meeting_20260813\PMS_Project_18_08_2026.pptx"
    )
    dump_pptx(old)


if __name__ == "__main__":
    main()
