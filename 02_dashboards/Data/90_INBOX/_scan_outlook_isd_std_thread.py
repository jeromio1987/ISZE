"""Second pass: original 'Sales to dealer data' blast + ISD replies after Sebastian returned (17 Aug)."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import win32com.client

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_isd_std_mail_20260818")
JSON_OUT = OUT / "thread_sales_to_dealer_data.json"
OL_MAIL = 43

ol = win32com.client.Dispatch("Outlook.Application")
ns = ol.GetNamespace("MAPI")
filt = '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%Sales to dealer data%\''

rows = []
for fid, name in ((6, "Inbox"), (5, "Sent")):
    items = ns.GetDefaultFolder(fid).Items
    items.Sort("[ReceivedTime]", True)
    sub = items.Restrict(filt)
    c = 0
    for mail in sub:
        c += 1
        if c > 40:
            break
        if mail.Class != OL_MAIL:
            continue
        atts = [mail.Attachments.Item(i).FileName for i in range(1, mail.Attachments.Count + 1)]
        body = str(mail.Body or "")
        rows.append({
            "folder": name,
            "received": str(mail.ReceivedTime)[:19],
            "sender": str(mail.SenderName or ""),
            "sender_email": str(getattr(mail, "SenderEmailAddress", "") or ""),
            "to": str(mail.To or ""),
            "cc": str(mail.CC or ""),
            "subject": str(mail.Subject or ""),
            "attachments": atts,
            "preview": " ".join(body.split())[:1200],
        })

# After 17 Aug: any mail from ISD domains / Sebastian / Fabian / aftersales-technik
print("thread_rows", len(rows))
for r in rows:
    print(f"{r['received']} | {r['folder']:5} | {r['sender'][:22]:22} | To:{r['to'][:80]} | atts={r['attachments']}")
    print(" ", r["subject"][:100])

JSON_OUT.write_text(json.dumps({"n": len(rows), "rows": rows}, indent=2, ensure_ascii=False), encoding="utf-8")

print("\n--- Inbox since 17 Aug from ISD people ---")
inbox = ns.GetDefaultFolder(6).Items
inbox.Sort("[ReceivedTime]", True)
c = 0
n_isd = 0
for mail in inbox:
    c += 1
    if c > 250:
        break
    if mail.Class != OL_MAIL:
        continue
    rec = mail.ReceivedTime
    if rec.year < 2026 or rec.month < 8 or rec.day < 17:
        # still in Aug 18..17 window if we break too early — only break when before Aug 17
        if rec.year < 2026 or rec.month < 8 or (rec.month == 8 and rec.day < 17):
            break
    blob = " ".join([
        str(mail.Subject or ""),
        str(mail.SenderName or ""),
        str(getattr(mail, "SenderEmailAddress", "") or ""),
        str(mail.To or ""),
        str(mail.CC or ""),
    ]).lower()
    keys = ("müller", "muller", "spenlein", "thiel", "isuzu-sales.de", "isuzu.de", "aftersales-technik", "isd")
    if not any(k in blob for k in keys):
        continue
    n_isd += 1
    atts = [mail.Attachments.Item(i).FileName for i in range(1, mail.Attachments.Count + 1)]
    print(f"{str(mail.ReceivedTime)[:19]} | {mail.SenderName} | {mail.Subject} | atts={atts}")

print("isd_since_17aug", n_isd)
print("wrote", JSON_OUT)
