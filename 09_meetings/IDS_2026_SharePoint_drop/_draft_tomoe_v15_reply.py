"""ReplyAll draft on latest IDS Materials / Tomoe thread. Display only. Never Send."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import win32com.client  # type: ignore

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
LEDGER = ISZE / "09_meetings" / "_mail_delivery_ledger.jsonl"
OUT = ISZE / "09_meetings" / "IDS_2026_SharePoint_drop" / "_tomoe_v15_reply_draft.json"
OL_MAIL = 43

BODY = """Hello Tomoe,

Updated country dealer compare files are on SharePoint (v1.5). Incomplete dealers stay on the list but are out of the country average. The map works without a key.

https://isze.sharepoint.com/sites/ISZE-IMG/Shared%20Documents/Forms/AllItems.aspx?id=%2Fsites%2FISZE-IMG%2FShared%20Documents%2FIDS_DB_compare_v1.5

Kind regards,
"""


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _ledger(event: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    event = {"ts": _now(), **event}
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def _blob(mail) -> str:
    bits = []
    for attr in ("To", "CC", "SenderName", "SenderEmailAddress", "Subject"):
        try:
            bits.append(str(getattr(mail, attr, "") or ""))
        except Exception:
            pass
    return " ".join(bits).lower()


def _html_prefix(text: str) -> str:
    paras = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    chunks = []
    for p in paras:
        esc = (
            p.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )
        chunks.append(f"<p style=\"font-family:Calibri,sans-serif;font-size:11pt\">{esc}</p>")
    return "".join(chunks)


def main() -> int:
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)
    sent = ns.GetDefaultFolder(5)

    candidates = []
    for folder_name, folder in (("inbox", inbox), ("sent", sent)):
        items = folder.Items
        items.Sort("[ReceivedTime]" if folder_name == "inbox" else "[SentOn]", True)
        n = 0
        for item in items:
            n += 1
            if n > 250:
                break
            try:
                if item.Class != OL_MAIL:
                    continue
            except Exception:
                continue
            try:
                subj = item.Subject or ""
            except Exception:
                continue
            sl = subj.lower()
            if "ids materials" not in sl and "ids compare" not in sl:
                continue
            blob = _blob(item)
            if "tomoe" not in blob:
                continue
            try:
                when = item.ReceivedTime if folder_name == "inbox" else item.SentOn
            except Exception:
                when = None
            candidates.append(
                {
                    "folder": folder_name,
                    "when": when,
                    "subject": subj,
                    "to": getattr(item, "To", "") or "",
                    "cc": getattr(item, "CC", "") or "",
                    "sender": getattr(item, "SenderName", "") or "",
                    "entry_id": item.EntryID,
                    "item": item,
                    "has_hadi": ("hadi" in blob or "hadewijch" in blob),
                }
            )
            if len(candidates) >= 15:
                break

    if not candidates:
        payload = {"status": "NOT_FOUND", "note": "No IDS Materials / Tomoe thread in recent Inbox/Sent"}
        OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        print(json.dumps(payload, indent=2, default=str))
        return 4

    preferred = [c for c in candidates if c["has_hadi"]] or candidates
    preferred.sort(key=lambda c: c["when"] or datetime.min, reverse=True)
    pick = preferred[0]
    src = ns.GetItemFromID(pick["entry_id"])
    reply = src.ReplyAll()
    html_new = _html_prefix(BODY)
    try:
        reply.HTMLBody = html_new + (reply.HTMLBody or "")
    except Exception:
        reply.Body = BODY + "\n" + (reply.Body or "")
    reply.Save()
    reply.Display(False)

    payload = {
        "action": "draft",
        "mode": "replyall",
        "sent": False,
        "displayed": True,
        "source_folder": pick["folder"],
        "source_when": str(pick["when"]),
        "source_subject": pick["subject"],
        "source_to": pick["to"],
        "source_cc": pick["cc"],
        "source_sender": pick["sender"],
        "draft_to": getattr(reply, "To", "") or "",
        "draft_cc": getattr(reply, "CC", "") or "",
        "draft_subject": getattr(reply, "Subject", "") or "",
        "entry_id": reply.EntryID,
        "body": BODY,
        "candidates": [
            {
                "folder": c["folder"],
                "when": str(c["when"]),
                "subject": c["subject"],
                "to": c["to"],
                "cc": c["cc"],
                "sender": c["sender"],
                "has_hadi": c["has_hadi"],
            }
            for c in preferred[:8]
        ],
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    _ledger(
        {
            "action": "draft",
            "to": payload["draft_to"],
            "cc": payload["draft_cc"],
            "subject": payload["draft_subject"],
            "attachments": [],
            "entry_id": payload["entry_id"],
            "displayed": True,
            "sent": False,
            "thread": "IDS Materials for DB / Tomoe ReplyAll",
        }
    )
    print("STATUS=DRAFTED")
    print(json.dumps({k: payload[k] for k in payload if k != "candidates"}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
