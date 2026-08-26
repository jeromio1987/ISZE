"""List EVERY mail since 12:00 today across all stores/folders (to find the action plan)."""
import json
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


def walk(folder, depth=0):
    yield folder
    if depth > 12:
        return
    try:
        n = folder.Folders.Count
    except Exception:
        return
    for i in range(1, n + 1):
        try:
            yield from walk(folder.Folders.Item(i), depth + 1)
        except Exception:
            continue


def main():
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    hits = []
    saved = []
    seen = set()

    folders = [("Inbox", ns.GetDefaultFolder(6)), ("Sent", ns.GetDefaultFolder(5))]
    for s in ns.Stores:
        try:
            root = s.GetRootFolder()
            for f in walk(root):
                folders.append((str(f.FolderPath), f))
        except Exception:
            pass

    for label, folder in folders:
        try:
            items = folder.Items
            items.Sort("[ReceivedTime]", True)
        except Exception:
            continue
        n = 0
        for mail in items:
            n += 1
            if n > 60:
                break
            try:
                recv = str(mail.ReceivedTime)[:19]
                if recv < "2026-08-20 12:00":
                    break
            except Exception:
                continue
            try:
                if int(mail.Class) != 43:
                    continue
                subj = str(mail.Subject or "")
                sender = str(mail.SenderName or "")
                smtp = smtp_of(mail)
                eid = str(getattr(mail, "EntryID", "") or "")
                if eid and eid in seen:
                    continue
                seen.add(eid)
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
                hits.append({"received": recv, "from": sender, "smtp": smtp, "subject": subj, "folder": label, "atts": atts})
            except Exception:
                continue

    hits.sort(key=lambda h: h["received"], reverse=True)
    for h in hits:
        print(json.dumps(h, ensure_ascii=False))
    print("SAVED:")
    for s in saved:
        print(s)


if __name__ == "__main__":
    main()
