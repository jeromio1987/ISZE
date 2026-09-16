"""Scan Outlook for Isuzu Ireland / Harris sell-out / parts sales attachments."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import win32com.client

OUT_DIR = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_ireland_sales_mail_20260813")
META = OUT_DIR / "outlook_ireland_sales_scan.json"
ATT_DIR = OUT_DIR / "attachments"

KEYWORDS = [
    "ireland", "isuzu ireland", "harris", "cummins", "imie",
    "sales to dealer", "sell-out", "sellout", "sell out",
    "partsales", "part sales", "monthly demand", "parts sold",
    "dealer sales", "sales to dealers", "parts sold qt",
]
# Strong Ireland markers (must hit at least one of these OR subject has Ireland+sales-ish)
IRELAND_MARKERS = [
    "ireland", "isuzu ireland", "harris group", "harris@", "john cummins",
    "jcummins", "cummins@",
]
SALES_MARKERS = [
    "sales", "sell-out", "sellout", "sell out", "partsales", "part sales",
    "monthly demand", "parts sold", "dealer", "qty", "quantity", "stock",
    "kpi", "spi", "std", "sales to",
]
ATT_EXT = (".xlsx", ".xls", ".xlsm", ".csv", ".zip", ".7z", ".pdf")

FILTERS = [
    ("ireland", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Ireland%'"),
    ("isuzu_ireland", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Isuzu Ireland%'"),
    ("harris", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Harris%'"),
    ("cummins", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Cummins%'"),
    ("sellout", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%sell-out%'"),
    ("sellout2", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%sellout%'"),
    ("sales_to_dealer", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Sales to Dealer%'"),
    ("partsales", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%PartSales%'"),
    ("monthly_demand", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Monthly Demand%'"),
    ("parts_sold", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Parts Sold%'"),
]


def log(msg: str) -> None:
    print(msg, flush=True)


def blob_of(mail) -> str:
    atts = []
    try:
        for i in range(1, mail.Attachments.Count + 1):
            atts.append(mail.Attachments.Item(i).FileName)
    except Exception:
        pass
    parts = [
        str(mail.Subject or ""),
        str(getattr(mail, "SenderName", "") or ""),
        str(getattr(mail, "SenderEmailAddress", "") or ""),
        str(mail.Body or "")[:3000],
        " ".join(atts),
    ]
    return " ".join(parts).lower()


def is_ireland_sales(blob: str, subj: str, atts: list[str]) -> tuple[bool, list[str]]:
    tags = []
    has_ie = any(m in blob for m in IRELAND_MARKERS)
    has_sales = any(m in blob for m in SALES_MARKERS)
    att_blob = " ".join(atts).lower()
    # Prefer attachments that look like dealer/parts sales
    att_sales = any(
        any(k in att_blob for k in (
            "sales", "sell", "part", "demand", "qty", "dealer", "ireland", "harris", "kpi", "spi"
        ))
        for _ in [0]
    ) and any(a.lower().endswith(ATT_EXT) for a in atts)

    if has_ie and (has_sales or att_sales):
        tags.append("ireland_sales_candidate")
    # Attachment filename strongly Ireland+data
    if any(re.search(r"ireland|harris", a, re.I) and a.lower().endswith(ATT_EXT) for a in atts):
        tags.append("ireland_named_attachment")
    # Subject Ireland + spreadsheet attachment
    if "ireland" in subj.lower() and any(a.lower().endswith((".xlsx", ".xls", ".xlsm", ".csv", ".zip")) for a in atts):
        tags.append("ireland_subject_spreadsheet")
    # John Cummins / Harris with spreadsheet
    if (("cummins" in blob or "harris" in blob) and
            any(a.lower().endswith((".xlsx", ".xls", ".xlsm", ".csv", ".zip")) for a in atts)):
        tags.append("harris_cummins_spreadsheet")
    return bool(tags), tags


def save_atts(mail, tag: str) -> list[str]:
    ATT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = str(mail.ReceivedTime)[:10].replace("/", "-")
    saved = []
    for i in range(1, mail.Attachments.Count + 1):
        att = mail.Attachments.Item(i)
        name = att.FileName
        low = name.lower()
        if low.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff")):
            continue
        if not low.endswith(ATT_EXT):
            continue
        safe = re.sub(r"[^\w.\-]+", "_", name)
        path = ATT_DIR / f"{stamp}_{tag}_{safe}"
        # avoid overwrite
        if path.exists():
            n = 2
            while True:
                alt = ATT_DIR / f"{stamp}_{tag}_{n}_{safe}"
                if not alt.exists():
                    path = alt
                    break
                n += 1
        att.SaveAsFile(str(path))
        saved.append(str(path))
        log(f"SAVED {path}")
    return saved


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ATT_DIR.mkdir(parents=True, exist_ok=True)
    log("starting Outlook COM…")
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    log("MAPI ok")

    hits = []
    seen = set()
    folders = [
        (ns.GetDefaultFolder(6), "Inbox"),
        (ns.GetDefaultFolder(5), "Sent"),
    ]
    # Also try Search Folders / subfolders named with Ireland if present — skip deep walk for speed

    for folder, fname in folders:
        items = folder.Items
        items.Sort("[ReceivedTime]", True)
        for label, filt in FILTERS:
            try:
                sub = items.Restrict(filt)
                log(f"{fname}/{label} iterating…")
                c = 0
                for mail in sub:
                    c += 1
                    if c > 80:
                        break
                    try:
                        eid = str(mail.EntryID)
                        if eid in seen:
                            continue
                        if mail.Class != 43:
                            continue
                        subj = str(mail.Subject or "")
                        sender = str(getattr(mail, "SenderName", "") or "")
                        sender_email = str(getattr(mail, "SenderEmailAddress", "") or "")
                        atts = []
                        try:
                            for i in range(1, mail.Attachments.Count + 1):
                                atts.append(mail.Attachments.Item(i).FileName)
                        except Exception:
                            pass
                        blob = blob_of(mail)
                        ok, tags = is_ireland_sales(blob, subj, atts)
                        # For Ireland-subject filters keep spreadsheet/sales-ish; for sellout filters require Ireland marker
                        if label in ("sellout", "sellout2", "sales_to_dealer", "partsales", "monthly_demand", "parts_sold"):
                            if "ireland" not in blob and "harris" not in blob and "cummins" not in blob:
                                # still record if attachment name has ireland
                                if not any(re.search(r"ireland|harris", a, re.I) for a in atts):
                                    continue
                        if not ok and "ireland" in subj.lower() and atts:
                            ok, tags = True, ["ireland_subject_any_att"]
                        if not ok:
                            continue
                        seen.add(eid)
                        log(f"HIT {fname} {str(mail.ReceivedTime)[:19]} {tags} | {subj[:90]}")
                        saved = save_atts(mail, "IE") if any(a.lower().endswith(ATT_EXT) for a in atts) else []
                        body = str(mail.Body or "")
                        hits.append({
                            "folder": fname,
                            "filter": label,
                            "received": str(mail.ReceivedTime),
                            "subject": subj,
                            "sender": sender,
                            "sender_email": sender_email,
                            "tags": tags,
                            "attachments": atts,
                            "saved": saved,
                            "preview": " ".join(body.split())[:500],
                        })
                    except Exception as e:
                        log(f"mail err {e}")
                log(f"{fname}/{label} done scanned={c} unique_hits={len(hits)}")
            except Exception as e:
                log(f"restrict fail {fname}/{label}: {e}")

    # Secondary: AdvancedSearch-like iterate last N inbox with body containing Isuzu Ireland + xlsx
    # Already covered by Restrict on subject; also scan Inbox for sender domains
    log("sender-domain pass Inbox…")
    try:
        inbox = ns.GetDefaultFolder(6).Items
        inbox.Sort("[ReceivedTime]", True)
        c = 0
        for mail in inbox:
            c += 1
            if c > 400:
                break
            try:
                if mail.Class != 43:
                    continue
                eid = str(mail.EntryID)
                if eid in seen:
                    continue
                sender_email = str(getattr(mail, "SenderEmailAddress", "") or "").lower()
                sender = str(getattr(mail, "SenderName", "") or "").lower()
                subj = str(mail.Subject or "")
                atts = []
                try:
                    for i in range(1, mail.Attachments.Count + 1):
                        atts.append(mail.Attachments.Item(i).FileName)
                except Exception:
                    pass
                blob = f"{subj} {sender} {sender_email} {' '.join(atts)}".lower()
                if not any(x in blob for x in ("ireland", "harris", "cummins", "isuzu.ie", "harrisgroup")):
                    continue
                if not atts:
                    continue
                if not any(a.lower().endswith(ATT_EXT) for a in atts):
                    continue
                ok, tags = is_ireland_sales(blob_of(mail), subj, atts)
                if not ok:
                    tags = ["irelandish_sender_or_subj_with_att"]
                seen.add(eid)
                log(f"HIT Inbox/senderpass {str(mail.ReceivedTime)[:19]} {tags} | {subj[:90]}")
                saved = save_atts(mail, "IE")
                body = str(mail.Body or "")
                hits.append({
                    "folder": "Inbox",
                    "filter": "sender_domain_pass",
                    "received": str(mail.ReceivedTime),
                    "subject": subj,
                    "sender": str(getattr(mail, "SenderName", "") or ""),
                    "sender_email": str(getattr(mail, "SenderEmailAddress", "") or ""),
                    "tags": tags,
                    "attachments": atts,
                    "saved": saved,
                    "preview": " ".join(body.split())[:500],
                })
            except Exception as e:
                log(f"senderpass err {e}")
        log(f"sender-domain pass done scanned={c}")
    except Exception as e:
        log(f"sender-domain fail {e}")

    META.write_text(json.dumps({
        "hit_count": len(hits),
        "hits": hits,
        "attachment_dir": str(ATT_DIR),
    }, indent=2), encoding="utf-8")
    log(f"DONE hits={len(hits)} meta={META}")
    # summary
    with_xlsx = [h for h in hits if any(a.lower().endswith((".xlsx", ".xls", ".xlsm", ".csv", ".zip")) for a in h["attachments"])]
    log(f"with_data_atts={len(with_xlsx)}")
    for h in with_xlsx[:40]:
        log(f"  {h['received'][:19]} | {h['sender'][:40]} | {h['subject'][:70]} | {h['attachments']}")


if __name__ == "__main__":
    main()
