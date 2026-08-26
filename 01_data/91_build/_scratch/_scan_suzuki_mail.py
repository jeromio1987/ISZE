"""Find Suzuki's most recent mail and save any real attachment to 90_INBOX."""
import json
import re
from pathlib import Path

import win32com.client

OUT_DIR = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = OUT_DIR / "_suzuki_mail.json"

SUZUKI = "takayoshi_suzuki@isuzu.com"


def safe(s):
    return re.sub(r"[^\w\-\. ]", "_", str(s))


def scan():
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    rows = []
    saved = []
    # default inbox (6), sent (5), plus walk any top-level stores' inboxes
    folders = []
    for i in (6, 5):
        try:
            folders.append((f"default-{i}", ns.GetDefaultFolder(i)))
        except Exception:
            pass
    # shared mailboxes (Sales etc.)
    try:
        for store in ns.Stores:
            try:
                root = store.GetRootFolder()
                for f in root.Folders:
                    if "Inbox" in str(f.Name):
                        folders.append((str(store.DisplayName) + "/" + str(f.Name), f))
            except Exception:
                pass
    except Exception:
        pass

    seen = set()
    for label, folder in folders:
        items = folder.Items
        items.Sort("[ReceivedTime]", True)
        n = 0
        for mail in items:
            n += 1
            if n > 60:
                break
            try:
                email = str(getattr(mail, "SenderEmailAddress", "") or "").lower()
                sender = str(getattr(mail, "SenderName", "") or "")
                subj = str(mail.Subject or "")
                recv = str(mail.ReceivedTime)[:19]
                if SUZUKI not in email and "suzuki" not in sender.lower():
                    continue
                key = str(mail.EntryID)
                if key in seen:
                    continue
                seen.add(key)
                atts = []
                try:
                    for a in range(1, mail.Attachments.Count + 1):
                        att = mail.Attachments.Item(a)
                        fn = str(att.FileName)
                        atts.append(fn)
                        # save non-image attachments to disk
                        if not re.search(r"\.(png|jpe?g|gif)$", fn, re.I):
                            dest = OUT_DIR / f"{recv[:10].replace('-','')}_{safe(sender)[:20]}_{safe(fn)}"
                            try:
                                att.SaveAsFile(str(dest))
                                saved.append(str(dest))
                            except Exception as e:
                                saved.append(f"ERR {fn}: {e}")
                except Exception:
                    pass
                rows.append({
                    "folder": label, "received": recv, "from": sender,
                    "subject": subj, "attachments": atts,
                })
            except Exception:
                pass
    OUT_JSON.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print("rows:", len(rows))
    for r in rows:
        print(r["received"], "|", r["from"], "|", r["subject"], "| atts:", r["attachments"])
    print("SAVED:", saved)


if __name__ == "__main__":
    scan()
