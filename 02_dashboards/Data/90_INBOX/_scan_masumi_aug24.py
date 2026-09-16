"""Scan Outlook for Masumi mail (Aug 22-25) + lubricants MoM drafts."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import win32com.client

OUT = Path(__file__).with_name("_scan_masumi_aug24.json")


def preview_body(mail) -> str:
    try:
        body = mail.Body or ""
    except Exception:
        body = ""
    return " ".join(str(body).replace("\r", " ").split())


def scan(folder, label, since, cap=600):
    items = folder.Items
    items.Sort("[ReceivedTime]", True)
    rows = []
    for n, mail in enumerate(items, 1):
        if n > cap:
            break
        try:
            recv = mail.ReceivedTime
            recv_naive = recv.replace(tzinfo=None) if recv is not None else None
            if recv_naive is None or recv_naive < since:
                break
            subj = str(mail.Subject or "")
            sender = str(getattr(mail, "SenderName", "") or "")
            try:
                sender_email = str(mail.SenderEmailAddress or "")
            except Exception:
                sender_email = ""
            body = preview_body(mail)
            atts = []
            try:
                for i in range(1, mail.Attachments.Count + 1):
                    atts.append(str(mail.Attachments.Item(i).FileName))
            except Exception:
                pass
            blob = f"{subj} {sender} {sender_email} {body}".lower()
            is_masumi = ("masumi" in sender.lower()) or ("hayakawa" in sender.lower()) or (
                "masumi.hayakawa" in sender_email.lower())
            is_lube_mom = any(k in blob for k in [
                "lubricant", "mom", "minutes", "ituk iml isze", "draft mom",
                "lubricants meeting", "moM_",
            ])
            if not (is_masumi or is_lube_mom):
                continue
            rows.append({
                "folder": label,
                "n": n,
                "received": str(recv)[:19],
                "from": sender,
                "email": sender_email,
                "subject": subj,
                "attachments": atts,
                "preview": body[:1500],
                "entry_id": str(mail.EntryID),
            })
        except Exception as exc:
            rows.append({"folder": label, "n": n, "error": str(exc)})
    return rows


def main() -> None:
    since = datetime(2026, 8, 22)
    print("starting Outlook COM", flush=True)
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)
    sent = ns.GetDefaultFolder(5)
    rows = scan(inbox, "Inbox", since) + scan(sent, "Sent", since)
    OUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"wrote {OUT} rows={len(rows)}", flush=True)
    for r in rows:
        print("=" * 80, flush=True)
        print(f"{r.get('folder')} #{r.get('n')} {r.get('received')} | {r.get('from')} <{r.get('email')}>", flush=True)
        print(f"SUBJ: {r.get('subject')}", flush=True)
        print(f"ATTS: {r.get('attachments')}", flush=True)
        print(f"BODY: {r.get('preview')}", flush=True)


if __name__ == "__main__":
    main()
