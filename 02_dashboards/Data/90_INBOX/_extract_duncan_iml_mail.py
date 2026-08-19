"""Extract Duncan Young ITUK/IML meeting mail + attachments."""
from __future__ import annotations

import json
import re
from pathlib import Path

import win32com.client

DEST = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\IML_ITUK_Meeting_20260813")
META = DEST / "_mail_meta.json"


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)
    items = inbox.Items
    items.Sort("[ReceivedTime]", True)
    found = None
    n = 0
    for mail in items:
        n += 1
        if n > 30:
            break
        subj = str(mail.Subject or "")
        sender = str(getattr(mail, "SenderName", "") or "")
        if "Duncan" in sender and "Meeting Material" in subj:
            found = mail
            break
    if found is None:
        raise SystemExit("mail not found")

    body = found.Body or ""
    (DEST / "_mail_body.txt").write_text(str(body), encoding="utf-8")
    html = ""
    try:
        html = found.HTMLBody or ""
        (DEST / "_mail_body.html").write_text(str(html), encoding="utf-8")
    except Exception:
        pass

    saved = []
    for i in range(1, found.Attachments.Count + 1):
        att = found.Attachments.Item(i)
        name = str(att.FileName)
        safe = re.sub(r"[^\w.\-]+", "_", name)
        path = DEST / safe
        att.SaveAsFile(str(path))
        saved.append({"name": name, "path": str(path), "size": path.stat().st_size})
        print(f"SAVED {path} ({path.stat().st_size})", flush=True)

    meta = {
        "received": str(found.ReceivedTime)[:19],
        "from": str(found.SenderName),
        "email": str(found.SenderEmailAddress),
        "subject": str(found.Subject),
        "to": str(found.To),
        "cc": str(found.CC),
        "attachments": saved,
    }
    META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("META", META, flush=True)
    print("--- BODY START ---", flush=True)
    print(str(body)[:8000], flush=True)


if __name__ == "__main__":
    main()
