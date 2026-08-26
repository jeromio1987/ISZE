"""Search mailbox for meeting minutes (any meeting) — recent, all folders."""
import json
import re
from pathlib import Path

import win32com.client

OUT_DIR = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX")
OUT_DIR.mkdir(parents=True, exist_ok=True)

KEYS = ("minute", "minutes", "notulen", "meeting", "verslag", "mom ", "notes")


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
            if n > 200:
                break
            try:
                recv = str(mail.ReceivedTime)[:19]
                if recv < "2026-08-01":
                    break
            except Exception:
                continue
            try:
                if int(mail.Class) != 43:
                    continue
                subj = str(mail.Subject or "")
                sender = str(mail.SenderName or "")
                if not any(k in subj.lower() for k in KEYS):
                    continue
                eid = str(getattr(mail, "EntryID", "") or "")
                if eid and eid in seen:
                    continue
                seen.add(eid)
                atts = []
                try:
                    for a in range(1, mail.Attachments.Count + 1):
                        atts.append(str(mail.Attachments.Item(a).FileName))
                except Exception:
                    pass
                hits.append({"received": recv, "from": sender, "subject": subj, "folder": label, "atts": atts})
            except Exception:
                continue

    for h in hits:
        print(json.dumps(h, ensure_ascii=False))


if __name__ == "__main__":
    main()
