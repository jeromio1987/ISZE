"""Fast Restrict: Fabian Thiel + aftersales-technik + Isuzu Teile replies after 11 Aug."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import win32com.client

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_isd_std_mail_20260818")
JSON_OUT = OUT / "outlook_fabian_technik.json"
OL_MAIL = 43

ol = win32com.client.Dispatch("Outlook.Application")
ns = ol.GetNamespace("MAPI")

restricts = [
    "[SenderName] = 'Fabian Thiel'",
    "[SenderName] = 'Tomoe Baumann'",
    "[SenderName] = 'Tomoe.Baumann@isuzu.de'",
]
# subject DASL
subj = [
    ("technik", '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%aftersales-technik%\''),
    ("teile", '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%Isuzu Teile%\''),
    ("kpi_isd", '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%KPI%SPI%Check Sheet%\''),
]

rows = []
seen = set()

def dump(mail, how):
    eid = str(getattr(mail, "EntryID", "") or "")
    if eid in seen:
        return
    seen.add(eid)
    atts = [mail.Attachments.Item(i).FileName for i in range(1, mail.Attachments.Count + 1)]
    body = " ".join(str(mail.Body or "").split())[:700]
    rec = str(mail.ReceivedTime)[:19]
    rows.append({
        "how": how,
        "received": rec,
        "sender": str(mail.SenderName or ""),
        "email": str(getattr(mail, "SenderEmailAddress", "") or ""),
        "to": str(mail.To or "")[:200],
        "cc": str(mail.CC or "")[:200],
        "subject": str(mail.Subject or ""),
        "attachments": atts,
        "preview": body,
    })
    print(f"{rec} | {mail.SenderName} | {mail.Subject[:80]} | atts={atts}")

inbox = ns.GetDefaultFolder(6).Items
inbox.Sort("[ReceivedTime]", True)
sent = ns.GetDefaultFolder(5).Items
sent.Sort("[ReceivedTime]", True)

for folder, fname in ((inbox, "Inbox"), (sent, "Sent")):
    for r in restricts:
        try:
            sub = folder.Restrict(r)
        except Exception as e:
            print("restrict fail", fname, r, e)
            continue
        c = 0
        for mail in sub:
            c += 1
            if c > 25:
                break
            if mail.Class != OL_MAIL:
                continue
            dump(mail, f"{fname}:{r}")
        print(f"{fname} {r} scanned={c}")
    for label, filt in subj:
        try:
            sub = folder.Restrict(filt)
        except Exception as e:
            print("subj fail", label, e)
            continue
        c = 0
        for mail in sub:
            c += 1
            if c > 20:
                break
            if mail.Class != OL_MAIL:
                continue
            blob = " ".join([str(mail.SenderName or ""), str(mail.To or ""), str(mail.CC or ""), str(mail.Subject or "")]).lower()
            if not any(k in blob for k in ("thiel", "müller", "muller", "isuzu-sales", "isuzu.de", "isd", "teile", "technik", "tomoe")):
                continue
            dump(mail, f"{fname}:{label}")
        print(f"{fname} {label} scanned={c}")

JSON_OUT.write_text(json.dumps({"n": len(rows), "rows": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
print("wrote", JSON_OUT, "n=", len(rows))
