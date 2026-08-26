"""Pull full details of Bart's KPI Master File email (2026-08-20 10:21) + thread replies."""
import json
import re
from pathlib import Path

import win32com.client

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_bart_kpi_master_email_detail.json")


def strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", '"')
    return " ".join(s.split())


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

    # find the KPI Master File mail
    target = None
    for mail in items:
        try:
            subj = str(mail.Subject or "")
            recv = str(mail.ReceivedTime)[:19]
            if recv < "2026-08-20":
                break
            if "KPI Master" in subj:
                target = mail
                break
        except Exception:
            continue

    if target is None:
        print("NOT FOUND")
        return

    def detail(m):
        return {
            "subject": str(m.Subject or ""),
            "from_name": str(getattr(m, "SenderName", "") or ""),
            "from_smtp": smtp_of(m),
            "to": str(getattr(m, "To", "") or ""),
            "cc": str(getattr(m, "CC", "") or ""),
            "received": str(m.ReceivedTime)[:19],
            "sent": str(getattr(m, "SentOn", "") or ""),
            "conversation_id": str(getattr(m, "ConversationID", "") or ""),
            "conversation_index": str(getattr(m, "ConversationIndex", "") or "")[:120],
            "body_text": strip_html(str(getattr(m, "Body", "") or ""))[:3000],
        }

    target_d = detail(target)
    print("=== TARGET EMAIL ===")
    print(json.dumps(target_d, ensure_ascii=False, indent=1))

    # now find replies in the same conversation (walk inbox + sent, match conversation topic or subject)
    conv_topic = ""
    try:
        conv_topic = str(target.ConversationTopic or "")
    except Exception:
        conv_topic = str(target.Subject or "")
    conv_topic = conv_topic.replace("RE: ", "").replace("FW: ", "").strip()

    replies = []
    for folder, label in ((inbox, "Inbox"), (ns.GetDefaultFolder(5), "Sent")):
        try:
            it = folder.Items
            it.Sort("[ReceivedTime]", True)
        except Exception:
            continue
        for mail in it:
            try:
                subj = str(mail.Subject or "").replace("RE: ", "").replace("FW: ", "").replace("Re: ", "").replace("Fw: ", "").strip()
                if subj == conv_topic or conv_topic in subj or subj in conv_topic:
                    recv = str(mail.ReceivedTime)[:19]
                    if recv < "2026-08-19":
                        break
                    replies.append(detail(mail))
            except Exception:
                continue

    print("=== THREAD (same subject, since 19 Aug) ===")
    for r in replies:
        print(r["received"], "|", r["from_name"], "<" + r["from_smtp"] + ">", "|", r["subject"])

    OUT.write_text(json.dumps({"target": target_d, "thread": replies}, indent=2, ensure_ascii=False), encoding="utf-8")
    print("OUT", OUT)


if __name__ == "__main__":
    main()
