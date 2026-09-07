"""Find latest Outlook item involving Tomoe AND Hadi/Hadewijch. Read-only."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import win32com.client  # type: ignore

OUT = Path(__file__).resolve().parent / "_latest_tomoe_hadi_thread.json"
OL_MAIL = 43


def _recips(mail) -> dict:
    to, cc, sender = "", "", ""
    try:
        to = mail.To or ""
    except Exception:
        pass
    try:
        cc = mail.CC or ""
    except Exception:
        pass
    try:
        sender = mail.SenderEmailAddress or mail.SenderName or ""
    except Exception:
        try:
            sender = mail.SenderName or ""
        except Exception:
            sender = ""
    return {"to": to, "cc": cc, "sender": sender}


def _blob(mail) -> str:
    r = _recips(mail)
    subj = ""
    try:
        subj = mail.Subject or ""
    except Exception:
        pass
    return " ".join([r["to"], r["cc"], r["sender"], subj]).lower()


def main() -> int:
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)
    sent = ns.GetDefaultFolder(5)
    hits = []
    cutoff = datetime.now() - timedelta(days=21)

    for folder_name, folder in (("inbox", inbox), ("sent", sent)):
        items = folder.Items
        items.Sort("[ReceivedTime]" if folder_name == "inbox" else "[SentOn]", True)
        n = 0
        for item in items:
            n += 1
            if n > 400:
                break
            try:
                if item.Class != OL_MAIL:
                    continue
            except Exception:
                continue
            try:
                when = item.ReceivedTime if folder_name == "inbox" else item.SentOn
            except Exception:
                when = None
            if when and when.replace(tzinfo=None) < cutoff:
                # still allow a few more then stop this folder
                if n > 80:
                    break
            blob = _blob(item)
            if "tomoe" not in blob:
                continue
            if "hadi" not in blob and "hadewijch" not in blob:
                continue
            rec = _recips(item)
            try:
                body = (item.Body or "")[:800]
            except Exception:
                body = ""
            hits.append(
                {
                    "folder": folder_name,
                    "when": str(when),
                    "subject": item.Subject,
                    "to": rec["to"],
                    "cc": rec["cc"],
                    "sender": rec["sender"],
                    "entry_id": item.EntryID,
                    "conversation": getattr(item, "ConversationTopic", "") or "",
                    "body_preview": body.replace("\r", "\n")[:600],
                }
            )
            if len(hits) >= 12:
                break

    OUT.write_text(json.dumps({"hits": hits, "count": len(hits)}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"count": len(hits), "top": hits[:3]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
