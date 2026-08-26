"""Scan today's inbox for the newest self-sent mail and save its attachments."""
import re
from pathlib import Path

import win32com.client

OUT_DIR = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def clean(s: str) -> str:
    return re.sub(r"[^\w\-\. ]", "_", str(s))


def main() -> None:
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)
    items = inbox.Items
    items.Sort("[ReceivedTime]", True)
    rows = []
    saved = []
    n = 0
    for mail in items:
        n += 1
        if n > 40:
            break
        try:
            recv = str(mail.ReceivedTime)[:19]
            if recv < "2026-08-20":
                break
            subj = str(mail.Subject or "")
            sender = str(mail.SenderName or "")
            email = str(mail.SenderEmailAddress or "").lower()
            atts = []
            try:
                for a in range(1, mail.Attachments.Count + 1):
                    att = mail.Attachments.Item(a)
                    fn = str(att.FileName)
                    atts.append(fn)
                    if not re.search(r"\.(png|jpe?g|gif)$", fn, re.I):
                        dest = OUT_DIR / f"{recv[:10].replace('-', '')}_{clean(sender)[:20]}_{clean(fn)}"
                        try:
                            att.SaveAsFile(str(dest))
                            saved.append(str(dest))
                        except Exception as e:
                            saved.append(f"ERR {fn}: {e}")
            except Exception:
                pass
            rows.append({"received": recv, "from": sender, "email": email,
                         "subject": subj, "atts": atts})
        except Exception:
            pass

    for r in rows:
        print(r["received"], "|", r["from"], "|", r["subject"], "| atts:", r["atts"])
    print("SAVED:", saved)


if __name__ == "__main__":
    main()
