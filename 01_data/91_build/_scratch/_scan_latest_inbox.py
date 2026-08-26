"""Scan today's inbox for the newest mail (action plan) + save any real attachments."""
import re
from pathlib import Path

import win32com.client

OUT_DIR = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def clean(s: str) -> str:
    return re.sub(r"[^\w\-\. ]", "_", str(s))


def smtp_of(mail) -> str:
    try:
        ae = mail.Sender
        if ae is not None:
            for tag in ("http://schemas.microsoft.com/mapi/proptag/0x39FE001E", "http://schemas.microsoft.com/mapi/proptag/0x5D01001F"):
                try:
                    v = ae.PropertyAccessor.GetProperty(tag)
                    if v:
                        return str(v).lower()
                except Exception:
                    pass
            try:
                eu = ae.GetExchangeUser()
                if eu is not None and eu.PrimarySmtpAddress:
                    return str(eu.PrimarySmtpAddress).lower()
            except Exception:
                pass
    except Exception:
        pass
    return str(getattr(mail, "SenderEmailAddress", "") or "").lower()


def main():
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
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
            if recv < "2026-08-20 12:00":
                break
            subj = str(mail.Subject or "")
            sender = str(mail.SenderName or "")
            email = smtp_of(mail)
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
            rows.append({"received": recv, "from": sender, "email": email, "subject": subj, "atts": atts})
        except Exception:
            pass

    import json
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))
    print("SAVED:")
    for s in saved:
        print(s)


if __name__ == "__main__":
    main()
