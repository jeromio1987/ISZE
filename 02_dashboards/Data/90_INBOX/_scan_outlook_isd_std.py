"""Hunt ISD (Germany) sales-to-dealer Excel in local Outlook.

Own Inbox + Sent, plus every MAPI store (Sales/Parts included — same as
scan_outlook_three_dbs.py). Subject Restrict first, then a short recent-Inbox
body pass. Saves .xlsx/.xls/.csv/.xlsm into this folder's attachments/.
Never Send / move / delete.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import win32com.client

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_isd_std_mail_20260818")
ATT = OUT / "attachments"
ATT.mkdir(parents=True, exist_ok=True)
META = OUT / "outlook_isd_std.json"
LOG = OUT / "scan_log.txt"

ATT_EXT = (".xlsx", ".xls", ".xlsm", ".csv")
OL_MAIL = 43

ISD_PEOPLE = (
    "sebastian müller",
    "sebastian muller",
    "thomas spenlein",
    "björn groß",
    "bjorn gross",
    "tomoe baumann",
    "christian affa",
)
ISD_DOMAINS = (
    "isuzu-sales.de",
    "isuzu.de",
    "astara.com",
)
ISD_WORDS = (
    "isd",
    "isuzu sales deutschland",
    "sold-to 2516",
    "sold to 2516",
)
STD_WORDS = (
    "sales to dealer",
    "sales-to-dealer",
    "sales to dealers",
    "sell-out",
    "sellout",
    "sell out",
    "dealer data",
    "partsales",
    "part sales",
    "monthly demand",
)
NEG = (
    "harrisgroup",
    "john cummins",
    "isuzutruck.co.uk",
    "duncan young",
    "uti.co.il",
    "umi.co.il",
    "petropoulos",
)

SUBJECT_FILTERS = [
    ("sales_to_dealer", '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%Sales to dealer%\''),
    ("sales_to_dealers", '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%Sales to Dealers%\''),
    ("dealer_data", '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%dealer data%\''),
    ("std", '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%StD%\''),
    ("sellout", '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%sell-out%\''),
    ("sellout2", '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%sellout%\''),
    ("isd", '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%ISD%\''),
    ("germany", '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%Germany%\''),
]
SENDER_RESTRICTS = [
    "[SenderName] = 'Sebastian Müller'",
    "[SenderName] = 'Sebastian Muller'",
    "[SenderName] = 'Thomas Spenlein'",
    "[SenderName] = 'Tomoe Baumann'",
    "[SenderName] = 'Björn Groß'",
    "[SenderName] = 'Bjorn Gross'",
    "[SenderName] = 'Christian Affa'",
]

lines: list[str] = []
hits: list[dict] = []
seen: set[str] = set()


def log(m: str) -> None:
    print(m, flush=True)
    lines.append(m)


def save_atts(mail, tag: str) -> list[str]:
    stamp = str(mail.ReceivedTime)[:10]
    saved: list[str] = []
    try:
        n = mail.Attachments.Count
    except Exception:
        return saved
    for i in range(1, n + 1):
        att = mail.Attachments.Item(i)
        name = str(att.FileName or "")
        if not name.lower().endswith(ATT_EXT):
            continue
        safe = re.sub(r"[^\w.\-]+", "_", name)
        path = ATT / f"{stamp}_{tag}_{safe}"
        n2 = 2
        while path.exists():
            path = ATT / f"{stamp}_{tag}_{n2}_{safe}"
            n2 += 1
        att.SaveAsFile(str(path))
        saved.append(str(path))
        log(f"SAVED {path}")
    return saved


def blob_of(mail, extra: str = "") -> str:
    parts = [
        extra,
        str(getattr(mail, "Subject", "") or ""),
        str(getattr(mail, "SenderName", "") or ""),
        str(getattr(mail, "SenderEmailAddress", "") or ""),
        str(getattr(mail, "To", "") or ""),
        str(getattr(mail, "CC", "") or ""),
    ]
    try:
        parts.append(str(mail.Body or "")[:4000])
    except Exception:
        pass
    try:
        atts = [mail.Attachments.Item(i).FileName for i in range(1, mail.Attachments.Count + 1)]
        parts.extend(atts)
    except Exception:
        atts = []
    return " ".join(parts).lower(), atts


def is_ireland_iuk_uti(blob: str) -> bool:
    return any(n in blob for n in NEG)


def is_isd(blob: str) -> bool:
    if any(p in blob for p in ISD_PEOPLE):
        return True
    if any(d in blob for d in ISD_DOMAINS):
        return True
    if any(w in blob for w in ISD_WORDS):
        return True
    return False


def is_std(blob: str) -> bool:
    return any(w in blob for w in STD_WORDS)


def keep_mail(mail, folder_path: str, how: str) -> None:
    if mail.Class != OL_MAIL:
        return
    eid = str(mail.EntryID)
    if eid in seen:
        return
    blob, atts = blob_of(mail, folder_path)
    if is_ireland_iuk_uti(blob) and not is_isd(blob):
        return
    # Keep if ISD + (StD language OR spreadsheet attached from ISD people after the ask)
    std = is_std(blob)
    isd = is_isd(blob)
    has_sheet = any(a.lower().endswith(ATT_EXT) for a in atts)
    auto = "automatische antwort" in blob or "automatic reply" in blob
    if not isd:
        return
    if not (std or (has_sheet and how.startswith("sender"))):
        # ISD + StD subject filter already implies std via subject; for ISD subject
        # filter, require std or sheet
        if how.startswith("subj_isd") or how.startswith("subj_germany"):
            if not (std or has_sheet):
                return
        elif not std:
            return
    seen.add(eid)
    subj = str(mail.Subject or "")
    rec = str(getattr(mail, "ReceivedTime", "") or "")[:19]
    sender = str(getattr(mail, "SenderName", "") or "")
    log(f"HIT {rec} | {sender[:24]} | {subj[:90]} | atts={[a for a in atts if not a.lower().startswith('image')]}")
    tag = "STD" if std else "ISD"
    saved = save_atts(mail, tag) if has_sheet else []
    hits.append({
        "received": rec,
        "sender": sender,
        "sender_email": str(getattr(mail, "SenderEmailAddress", "") or ""),
        "to": str(getattr(mail, "To", "") or ""),
        "subject": subj,
        "folder": folder_path,
        "how": how,
        "attachments": atts,
        "saved": saved,
        "auto_reply": auto,
        "std": std,
        "preview": " ".join(str(getattr(mail, "Body", "") or "").split())[:600],
    })


def walk_folders(folder, depth: int = 0):
    yield folder
    if depth > 10:
        return
    try:
        n = folder.Folders.Count
    except Exception:
        return
    for i in range(1, n + 1):
        try:
            yield from walk_folders(folder.Folders.Item(i), depth + 1)
        except Exception:
            continue


def restrict_folder(folder, folder_path: str) -> None:
    items = folder.Items
    try:
        items.Sort("[ReceivedTime]", True)
    except Exception:
        pass
    for label, filt in SUBJECT_FILTERS + [(f"sender_{i}", r) for i, r in enumerate(SENDER_RESTRICTS)]:
        try:
            sub = items.Restrict(filt)
        except Exception as e:
            log(f"fail Restrict {folder_path}/{label}: {e}")
            continue
        c = 0
        try:
            for mail in sub:
                c += 1
                if c > 80:
                    break
                try:
                    keep_mail(mail, folder_path, label)
                except Exception as e:
                    log(f"item err {e}")
        except Exception as e:
            log(f"iter err {folder_path}/{label}: {e}")
        if c:
            log(f"{folder_path}/{label} scanned={c}")


def recent_inbox_body(folder, folder_path: str, limit: int = 400) -> None:
    """Catch 'see attached' replies whose subject is AW:/RE: without StD words."""
    items = folder.Items
    try:
        items.Sort("[ReceivedTime]", True)
    except Exception:
        return
    c = 0
    for mail in items:
        c += 1
        if c > limit:
            break
        try:
            if mail.Class != OL_MAIL:
                continue
            rec = mail.ReceivedTime
            if rec.year < 2026 or (rec.year == 2026 and rec.month < 7):
                break
            blob, atts = blob_of(mail)
            if not is_isd(blob):
                continue
            if not (is_std(blob) or any(a.lower().endswith(ATT_EXT) for a in atts)):
                continue
            keep_mail(mail, folder_path, "recent_body")
        except Exception:
            continue


def main() -> None:
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    log(f"started {datetime.now().isoformat(timespec='seconds')}")
    stores = []
    for i in range(1, ns.Folders.Count + 1):
        try:
            root = ns.Folders.Item(i)
            stores.append(str(root.Name))
        except Exception:
            continue
    log(f"stores={stores}")

    # Default Inbox + Sent first (own mailbox)
    for fid, name in ((6, "Inbox"), (5, "Sent")):
        f = ns.GetDefaultFolder(fid)
        restrict_folder(f, f"default/{name}")
        if name == "Inbox":
            recent_inbox_body(f, "default/Inbox", 500)
        if name == "Sent":
            recent_inbox_body(f, "default/Sent", 300)

    # Other stores: only folders whose path hints ISD/Germany/customers
    hints = ("isd", "germany", "deutschland", "astara", "inbox", "sent")
    for i in range(1, ns.Folders.Count + 1):
        try:
            root = ns.Folders.Item(i)
        except Exception:
            continue
        rname = str(root.Name)
        if "jerome.van.der.pluym" in rname.lower() and "archive" not in rname.lower():
            continue  # already did default folders
        n_f = 0
        for folder in walk_folders(root):
            n_f += 1
            if n_f > 80:
                break
            try:
                fpath = str(folder.FolderPath)
            except Exception:
                continue
            pl = fpath.lower()
            if not any(h in pl for h in hints):
                continue
            log(f"store-folder {fpath}")
            restrict_folder(folder, fpath)

    META.write_text(
        json.dumps(
            {
                "as_of": datetime.now().isoformat(timespec="seconds"),
                "stores": stores,
                "hit_count": len(hits),
                "xlsx_saved": sum(len(h["saved"]) for h in hits),
                "hits": hits,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    LOG.write_text("\n".join(lines), encoding="utf-8")
    log(f"DONE hits={len(hits)} saved_xlsx={sum(len(h['saved']) for h in hits)} -> {META}")


if __name__ == "__main__":
    main()
