"""Scan recent Outlook inbox/sent for IML/PMS mail (Tue 18 Aug meeting)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import win32com.client

OUT = Path(__file__).with_name("_scan_recent_iml_mail.json")
KEYWORDS = [
    "iml",
    "pms",
    "ituk",
    "teams",
    "tuesday",
    "masumi",
    "duncan",
    "suzuki",
    "hayakawa",
    "periodical",
    "maintenance",
    "gidss",
    "isze mtg",
]


def preview_body(mail) -> str:
    try:
        body = mail.Body or ""
    except Exception:
        body = ""
    return " ".join(str(body).replace("\r", " ").split())[:800]


def scan_folder(folder, label: str, cap: int = 80) -> list[dict]:
    items = folder.Items
    items.Sort("[ReceivedTime]", True)
    rows = []
    n = 0
    for mail in items:
        n += 1
        if n > cap:
            break
        try:
            subj = str(mail.Subject or "")
            sender = str(getattr(mail, "SenderName", "") or "")
            try:
                sender_email = str(mail.SenderEmailAddress or "")
            except Exception:
                sender_email = ""
            atts = []
            try:
                for i in range(1, mail.Attachments.Count + 1):
                    atts.append(str(mail.Attachments.Item(i).FileName))
            except Exception:
                pass
            blob = f"{subj} {sender} {sender_email} {preview_body(mail)}".lower()
            keep = n <= 20 or any(k in blob for k in KEYWORDS)
            if not keep:
                continue
            rows.append(
                {
                    "folder": label,
                    "n": n,
                    "received": str(mail.ReceivedTime)[:19],
                    "from": sender,
                    "email": sender_email,
                    "subject": subj,
                    "attachments": atts,
                    "preview": preview_body(mail)[:500],
                    "entry_id": str(mail.EntryID),
                }
            )
        except Exception as exc:
            rows.append({"folder": label, "n": n, "error": str(exc)})
    return rows


def main() -> None:
    print("starting Outlook COM", flush=True)
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)
    sent = ns.GetDefaultFolder(5)
    rows = scan_folder(inbox, "Inbox", 100) + scan_folder(sent, "Sent", 40)
    OUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"wrote {OUT} rows={len(rows)}", flush=True)
    for r in rows[:25]:
        print(
            f"{r.get('folder')} #{r.get('n')} {r.get('received')} | {r.get('from')} | atts={len(r.get('attachments') or [])}",
            flush=True,
        )
        print(f"  SUBJ: {r.get('subject')}", flush=True)


if __name__ == "__main__":
    main()
