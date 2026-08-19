"""List Sales to dealer / dealer data threads and whether Ireland mentioned; save Ireland-related atts."""
from __future__ import annotations
import json, re
from pathlib import Path
import win32com.client

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_ireland_sales_mail_20260813")
ATT = OUT / "attachments_std_scan"
ATT.mkdir(exist_ok=True)
META = OUT / "outlook_sales_to_dealer_scan.json"

FILTERS = [
    ("sales_to_dealer", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Sales to dealer%'"),
    ("dealer_data", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%dealer data%'"),
    ("monthly_demand", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Monthly Demand%'"),
    ("partsales", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%PartSales%'"),
]

ATT_EXT=(".xlsx",".xls",".xlsm",".csv",".zip")
ol=win32com.client.Dispatch("Outlook.Application"); ns=ol.GetNamespace("MAPI")
rows=[]; seen=set()
for folder,fname in [(ns.GetDefaultFolder(6),"Inbox"),(ns.GetDefaultFolder(5),"Sent")]:
    items=folder.Items; items.Sort("[ReceivedTime]", True)
    for label,filt in FILTERS:
        try:
            sub=items.Restrict(filt)
            c=0
            for mail in sub:
                c+=1
                if c>40: break
                if mail.Class!=43: continue
                eid=str(mail.EntryID)
                if eid in seen: continue
                seen.add(eid)
                subj=str(mail.Subject or "")
                sender=str(getattr(mail,"SenderName","") or "")
                body=str(mail.Body or "")
                atts=[mail.Attachments.Item(i).FileName for i in range(1, mail.Attachments.Count+1)]
                blob=f"{subj} {sender} {body[:6000]} {' '.join(atts)}".lower()
                ie = any(x in blob for x in ("ireland","harris","cummins","isuzu.ie"))
                rows.append({
                    "folder":fname,"filter":label,"received":str(mail.ReceivedTime),
                    "subject":subj,"sender":sender,"attachments":atts,
                    "ireland_mention":ie,
                    "preview":" ".join(body.split())[:400],
                })
                if ie and any(a.lower().endswith(ATT_EXT) for a in atts):
                    stamp=str(mail.ReceivedTime)[:10]
                    for i in range(1, mail.Attachments.Count+1):
                        att=mail.Attachments.Item(i)
                        name=att.FileName
                        if not name.lower().endswith(ATT_EXT): continue
                        safe=re.sub(r"[^\w.\-]+","_", name)
                        path=ATT/f"{stamp}_STD_{safe}"
                        if not path.exists():
                            att.SaveAsFile(str(path))
                            print("SAVED", path)
            print(f"{fname}/{label} scanned={c}")
        except Exception as e:
            print("fail", fname, label, e)

META.write_text(json.dumps(rows, indent=2), encoding="utf-8")
print("=== Ireland mentions in StD-like threads ===")
for r in rows:
    if r["ireland_mention"]:
        print(f"{r['received'][:19]} | {r['folder']} | {r['sender'][:40]} | {r['subject'][:70]} | atts={r['attachments']}")
print("total rows", len(rows), "ireland", sum(1 for r in rows if r["ireland_mention"]))
