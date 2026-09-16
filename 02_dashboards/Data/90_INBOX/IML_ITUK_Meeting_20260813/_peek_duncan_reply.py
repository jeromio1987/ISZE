"""Peek Inbox/Sent for Duncan Young mail today. Print metadata only, then body of latest."""
from __future__ import annotations

from pathlib import Path

import win32com.client  # type: ignore

OUT = Path(__file__).with_name("_duncan_reply_today.txt")


def main() -> None:
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)
    sent = ns.GetDefaultFolder(5)
    lines: list[str] = []

    lines.append("=== SENT (recent, Duncan/PMS/Tuesday) ===")
    items = sent.Items
    items.Sort("[ReceivedTime]", True)
    n = 0
    for it in items:
        n += 1
        if n > 80:
            break
        try:
            t = it.SentOn
            to = str(getattr(it, "To", "") or "")
            subj = str(getattr(it, "Subject", "") or "")
            blob = (to + " " + subj).lower()
            if t.year == 2026 and t.month == 8 and t.day >= 13:
                if any(k in blob for k in ("duncan", "young", "pms", "tuesday", "materials", "ituk")):
                    lines.append(f"{t} | To={to} | {subj}")
        except Exception as e:  # noqa: BLE001
            lines.append(f"sent err {e}")

    lines.append("")
    lines.append("=== INBOX from Duncan (scan 300) ===")
    items = inbox.Items
    items.Sort("[ReceivedTime]", True)
    hits = []
    n = 0
    for it in items:
        n += 1
        if n > 300:
            break
        try:
            sender = str(getattr(it, "SenderName", "") or "")
            addr = str(getattr(it, "SenderEmailAddress", "") or "")
            subj = str(getattr(it, "Subject", "") or "")
            t = it.ReceivedTime
            sl = (sender + " " + addr).lower()
            if "duncan" in sl or "young" in sl:
                hits.append(it)
                lines.append(f"{t} | {sender} <{addr}> | {subj}")
                if len(hits) >= 12:
                    break
        except Exception:
            continue

    lines.append("")
    if hits:
        it = hits[0]
        lines.append("=== LATEST DUNCAN BODY ===")
        lines.append(f"Subject: {it.Subject}")
        lines.append(f"From: {it.SenderName}")
        lines.append(f"Received: {it.ReceivedTime}")
        body = str(getattr(it, "Body", "") or "")
        lines.append(body[:8000])
    else:
        lines.append("No Duncan mail in first 300 inbox items.")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT} lines={len(lines)}")


if __name__ == "__main__":
    main()
