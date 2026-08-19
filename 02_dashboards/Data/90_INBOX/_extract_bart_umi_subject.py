"""Pull Bart mail 260812_UMI and any other subject containing _UMI. Save atts."""
from __future__ import annotations

import json
import re
from pathlib import Path

import win32com.client

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_umi_bart_minutes")
JSON_OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_umi_bart_260812.json")
PR_SMTP = "http://schemas.microsoft.com/mapi/proptag/0x39FE001E"


def smtp_of(mail) -> str:
    try:
        ae = mail.Sender
        if ae is not None:
            v = ae.PropertyAccessor.GetProperty(PR_SMTP)
            if v:
                return str(v).lower()
    except Exception:
        pass
    return str(getattr(mail, "SenderEmailAddress", "") or "").lower()


def main():
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)
    sent = ns.GetDefaultFolder(5)
    hits = []
    seen = set()
    for folder, label in ((inbox, "Inbox"), (sent, "Sent")):
        for clause in (
            "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001F\" LIKE '%_UMI%'",
            "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001F\" LIKE '%260812%'",
            "[SenderName] = 'Bart Symons'",
        ):
            try:
                items = folder.Items.Restrict(clause)
            except Exception as e:
                print("fail", label, clause, e, flush=True)
                continue
            n = 0
            for mail in items:
                try:
                    if int(mail.Class) != 43:
                        continue
                except Exception:
                    continue
                n += 1
                subj = str(mail.Subject or "")
                if clause.endswith("'Bart Symons'"):
                    if not re.search(r"(?<![A-Za-z])UMI(?![A-Za-z])", subj) and "umi.co.il" not in (
                        str(mail.To or "") + str(mail.CC or "")
                    ).lower():
                        continue
                eid = str(getattr(mail, "EntryID", "") or "")
                if eid in seen:
                    continue
                seen.add(eid)
                saved = []
                for i in range(1, mail.Attachments.Count + 1):
                    att = mail.Attachments.Item(i)
                    name = str(att.FileName)
                    if name.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
                        continue
                    safe = re.sub(r"[^\w.\-]+", "_", name)
                    stamp = str(mail.ReceivedTime)[:10]
                    path = OUT / f"{stamp}_{safe}"
                    if not path.exists():
                        att.SaveAsFile(str(path))
                    saved.append(str(path))
                    print("SAVED", path, flush=True)
                body = str(mail.Body or "")[:25000]
                hits.append(
                    {
                        "received": str(mail.ReceivedTime)[:19],
                        "from_name": str(mail.SenderName or ""),
                        "from_smtp": smtp_of(mail),
                        "to": str(mail.To or ""),
                        "cc": str(mail.CC or ""),
                        "subject": subj,
                        "folder": label,
                        "saved": saved,
                        "atts": [
                            str(mail.Attachments.Item(i).FileName)
                            for i in range(1, mail.Attachments.Count + 1)
                        ],
                        "body": body,
                    }
                )
                print("HIT", str(mail.ReceivedTime)[:19], subj[:90], flush=True)
            print(label, clause[:40], "n=", n, flush=True)
    JSON_OUT.write_text(json.dumps({"n": len(hits), "hits": hits}, indent=2, ensure_ascii=False), encoding="utf-8")
    print("DONE", len(hits), JSON_OUT)


if __name__ == "__main__":
    main()
