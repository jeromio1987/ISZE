"""Targeted Outlook: John Cummins / Harris / Sales to dealer Ireland / StD."""
from __future__ import annotations
import json, re
from pathlib import Path
import win32com.client

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_ireland_sales_mail_20260813")
ATT = OUT / "attachments_targeted"
ATT.mkdir(parents=True, exist_ok=True)
META = OUT / "outlook_ireland_targeted.json"

FILTERS = [
    ("cummins_subj", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Cummins%'"),
    ("john_cummins", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%John Cummins%'"),
    ("business_review", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Business review%'"),
    ("std", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%StD%'"),
    ("sales_to_dealer", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Sales to dealer%'"),
    ("sales_to_dealers", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Sales to Dealers%'"),
    ("dealer_data", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%dealer data%'"),
    ("harris_group", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Harris Group%'"),
    ("parts_sales_ireland", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Ireland%parts%'"),
]

ATT_EXT = (".xlsx", ".xls", ".xlsm", ".csv", ".zip", ".7z")

def log(m): print(m, flush=True)

def save_atts(mail, tag):
    stamp = str(mail.ReceivedTime)[:10]
    saved=[]
    for i in range(1, mail.Attachments.Count+1):
        att=mail.Attachments.Item(i)
        name=att.FileName
        low=name.lower()
        if not low.endswith(ATT_EXT):
            continue
        safe=re.sub(r"[^\w.\-]+","_", name)
        path=ATT/f"{stamp}_{tag}_{safe}"
        if path.exists():
            n=2
            while True:
                alt=ATT/f"{stamp}_{tag}_{n}_{safe}"
                if not alt.exists():
                    path=alt; break
                n+=1
        att.SaveAsFile(str(path))
        saved.append(str(path))
        log(f"SAVED {path}")
    return saved

ol=win32com.client.Dispatch("Outlook.Application")
ns=ol.GetNamespace("MAPI")
hits=[]; seen=set()
for folder,fname in [(ns.GetDefaultFolder(6),"Inbox"), (ns.GetDefaultFolder(5),"Sent")]:
    items=folder.Items; items.Sort("[ReceivedTime]", True)
    for label,filt in FILTERS:
        try:
            sub=items.Restrict(filt)
            log(f"{fname}/{label}…")
            c=0
            for mail in sub:
                c+=1
                if c>60: break
                if mail.Class!=43: continue
                eid=str(mail.EntryID)
                if eid in seen: continue
                subj=str(mail.Subject or "")
                sender=str(getattr(mail,"SenderName","") or "")
                sender_email=str(getattr(mail,"SenderEmailAddress","") or "")
                body=str(mail.Body or "")
                atts=[mail.Attachments.Item(i).FileName for i in range(1, mail.Attachments.Count+1)]
                blob=f"{subj} {sender} {sender_email} {body[:4000]} {' '.join(atts)}".lower()
                # keep if Ireland/Harris/Cummins OR (sales to dealer AND ireland-ish in body) OR business review with ireland
                keep=False
                reason=[]
                if any(x in blob for x in ("ireland","harris","cummins","isuzu.ie","harrisgroup")):
                    keep=True; reason.append("irelandish")
                if label in ("sales_to_dealer","sales_to_dealers","dealer_data","std") and any(x in blob for x in ("ireland","harris","cummins")):
                    keep=True; reason.append("std_ireland")
                if label=="business_review" and any(x in blob for x in ("ireland","harris","cummins","john")):
                    keep=True; reason.append("biz_review_ie")
                if not keep:
                    continue
                seen.add(eid)
                log(f"HIT {fname} {str(mail.ReceivedTime)[:19]} {reason} | {subj[:90]} | atts={atts}")
                saved=save_atts(mail, "TGT") if any(a.lower().endswith(ATT_EXT) for a in atts) else []
                hits.append({
                    "folder":fname,"filter":label,"received":str(mail.ReceivedTime),
                    "subject":subj,"sender":sender,"sender_email":sender_email,
                    "to": str(getattr(mail,"To","") or ""),
                    "reasons":reason,"attachments":atts,"saved":saved,
                    "preview":" ".join(body.split())[:800],
                })
            log(f"{fname}/{label} scanned={c}")
        except Exception as e:
            log(f"fail {fname}/{label}: {e}")

# Also Instant Search via AdvancedSearch is flaky; try Windows Search mailbox? skip.
# Body search: iterate recent Sent for 'sales to dealer' to Ireland
log("sent body pass for Ireland StD…")
sent=ns.GetDefaultFolder(5).Items; sent.Sort("[ReceivedTime]", True)
c=0
for mail in sent:
    c+=1
    if c>500: break
    try:
        if mail.Class!=43: continue
        eid=str(mail.EntryID)
        if eid in seen: continue
        subj=str(mail.Subject or "")
        body=str(mail.Body or "")
        blob=f"{subj} {body[:5000]}".lower()
        if "ireland" not in blob and "cummins" not in blob and "harris" not in blob:
            continue
        if not any(k in blob for k in ("sales to dealer","sell-out","sellout","monthly demand","partsales","part sales","dealer sales","std ")):
            continue
        atts=[mail.Attachments.Item(i).FileName for i in range(1, mail.Attachments.Count+1)]
        seen.add(eid)
        log(f"HIT Sent/body {str(mail.SentOn)[:19]} | {subj[:90]} | atts={atts}")
        saved=save_atts(mail,"BODY") if any(a.lower().endswith(ATT_EXT) for a in atts) else []
        hits.append({
            "folder":"Sent","filter":"body_std_ireland","received":str(getattr(mail,"SentOn",mail.ReceivedTime)),
            "subject":subj,"sender":"me","sender_email":"",
            "to":str(getattr(mail,"To","") or ""),
            "reasons":["sent_body_std_ireland"],"attachments":atts,"saved":saved,
            "preview":" ".join(body.split())[:800],
        })
    except Exception as e:
        log(f"body err {e}")

META.write_text(json.dumps({"hit_count":len(hits),"hits":hits}, indent=2), encoding="utf-8")
log(f"DONE targeted hits={len(hits)} -> {META}")
for h in hits:
    if h["attachments"]:
        print(f"{h['received'][:19]} | {h['subject'][:70]} | {h['attachments']}")
