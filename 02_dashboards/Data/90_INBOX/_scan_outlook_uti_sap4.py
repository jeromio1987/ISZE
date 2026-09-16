"""Outlook COM hunt: old UTI PartSales senders sap4*@uti.co.il. Never Send."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import win32com.client

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_DIR = ISZE / r"01_data\90_INBOX\UTI_PartSales_mail_sap4_20260813"
META = ISZE / r"01_data\90_INBOX\outlook_uti_sap4_scan_20260813.json"
UTI_DIR = ISZE / r"01_data\12_raw\dealer_sales\UTI"

EXACT_SENDERS = {
    "sap4@uti.co.il",
    "sap4u@uti.co.il",
    "sap4uti@uti.co.il",
}
KEEP_EXT = (".xlsx", ".xls", ".xlsm", ".csv")
OL_MAIL = 43

# Do not overwrite these newer files.
PROTECTED_STEMS = {
    "UTIPartSales_2025-01",
    "UTIPartSales_2025-08",
    "UTIPartSales_2025-09",
    "UTIPartSales_2025-10",
    "UTIPartSales_2025-11",
    "UTIPartSales_2025-12_YTD",
    "UTIPartSales_2026-01",
    "UTIPartSales_2026-02",
    "UTIPartSales_2026-03",
    "UTIPartSales_2026-04",
    "UTIPartSales_2026-05",
    "UTIPartSales_2026-06",
}


def _p(msg: str) -> None:
    print(msg.encode("ascii", "replace").decode(), flush=True)


def _safe(fn: str) -> str:
    return re.sub(r"[^\w.\-]+", "_", fn)


def _folder_safe(path: str) -> str:
    return re.sub(r"[^\w.\-]+", "_", path)[:60].strip("_")


def _dasl_like(prop: str, token: str) -> str:
    t = token.replace("'", "''")
    return f'@SQL="{prop}" LIKE \'%{t}%\''


def walk_folders(folder, acc: list, depth: int = 0) -> None:
    if depth > 18:
        return
    acc.append(folder)
    try:
        for sub in folder.Folders:
            walk_folders(sub, acc, depth + 1)
    except Exception:
        pass


def restrict_hits(folder, filters: list[str]) -> list:
    items_out = []
    try:
        base = folder.Items
    except Exception:
        return items_out
    for filt in filters:
        try:
            sub = base.Restrict(filt)
        except Exception:
            continue
        try:
            n = sub.Count
        except Exception:
            n = 0
        for i in range(1, n + 1):
            try:
                items_out.append(sub.Item(i))
            except Exception:
                continue
    return items_out


def smtp_of(mail) -> str:
    addr = ""
    try:
        addr = str(mail.SenderEmailAddress or "")
    except Exception:
        pass
    try:
        sender = mail.Sender
        if sender:
            try:
                eu = sender.GetExchangeUser()
                if eu and eu.PrimarySmtpAddress:
                    addr = str(eu.PrimarySmtpAddress)
            except Exception:
                pass
            try:
                pa = str(sender.PropertyAccessor.GetProperty(
                    "http://schemas.microsoft.com/mapi/proptag/0x39FE001E"
                ) or "")
                if "@" in pa:
                    addr = pa
            except Exception:
                pass
    except Exception:
        pass
    return addr.strip()


def sender_blob(mail, from_addr: str, sender_name: str) -> str:
    bits = [from_addr, sender_name]
    try:
        bits.append(str(mail.SenderName or ""))
    except Exception:
        pass
    try:
        bits.append(str(mail.SentOnBehalfOfName or ""))
    except Exception:
        pass
    return " ".join(b for b in bits if b).lower()


def is_sap4_uti(from_addr: str, blob: str) -> bool:
    fa = (from_addr or "").lower()
    if fa in EXACT_SENDERS:
        return True
    if "sap4" in fa and "@uti.co.il" in fa:
        return True
    if "sap4" in blob and "uti.co.il" in blob:
        return True
    if "sap4" in blob and "@uti.co.il" in blob:
        return True
    return False


def parse_exec_date(subject: str):
    m = re.search(
        r"executed at\s+(\d{1,2})/(\d{1,2})/(\d{4})",
        subject or "",
        re.I,
    )
    if not m:
        return None
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        return datetime(y, mo, d)
    except ValueError:
        return None


def prev_month(dt: datetime) -> tuple[int, int]:
    if dt.month == 1:
        return 12, dt.year - 1
    return dt.month - 1, dt.year


def build_filters() -> list[str]:
    props = [
        "urn:schemas:httpmail:fromemail",
        "urn:schemas:httpmail:from",
        "http://schemas.microsoft.com/mapi/proptag/0x0C1F001F",  # PR_SENDER_EMAIL_ADDRESS
        "http://schemas.microsoft.com/mapi/proptag/0x0065001F",  # PR_SENT_REPRESENTING_EMAIL_ADDRESS
        "http://schemas.microsoft.com/mapi/proptag/0x5D01001F",  # PR_SENDER_SMTP_ADDRESS
        "http://schemas.microsoft.com/mapi/proptag/0x5D02001F",  # PR_SENT_REPRESENTING_SMTP_ADDRESS
        "http://schemas.microsoft.com/mapi/proptag/0x0C1A001F",  # PR_SENDER_NAME
    ]
    tokens = [
        "sap4@uti.co.il",
        "sap4u@uti.co.il",
        "sap4uti@uti.co.il",
        "sap4",
    ]
    filters = [_dasl_like(p, t) for p in props for t in tokens]
    filters.append(
        _dasl_like("http://schemas.microsoft.com/mapi/proptag/0x0037001F", "UTIPartSales")
    )
    return filters


def unique_dest(path: Path) -> Path:
    if not path.exists():
        return path
    n = 2
    while True:
        cand = path.with_name(f"{path.stem}_{n}{path.suffix}")
        if not cand.exists():
            return cand
        n += 1


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    filters = build_filters()

    stores = []
    folders = []
    for i in range(1, ns.Stores.Count + 1):
        store = ns.Stores.Item(i)
        name = str(store.DisplayName)
        stores.append(name)
        _p(f"STORE {name}")
        try:
            walk_folders(store.GetRootFolder(), folders)
        except Exception as e:
            _p(f"  STORE FAIL {name} {e}")

    _p(f"FOLDERS {len(folders)}")

    seen: set[str] = set()
    hits: list[dict] = []
    saved: list[str] = []
    folder_stats: list[dict] = []
    sap4_aliases: set[str] = set()

    for folder in folders:
        try:
            fpath = str(folder.FolderPath)
        except Exception:
            fpath = "?"
        try:
            n_items = int(folder.Items.Count)
        except Exception:
            n_items = -1
        folder_stats.append({"folder": fpath, "items": n_items})
        _p(f"FOLDER {fpath} items={n_items}")

        for mail in restrict_hits(folder, filters):
            try:
                if int(mail.Class) != OL_MAIL:
                    continue
            except Exception:
                continue
            try:
                eid = str(mail.EntryID)
            except Exception:
                eid = ""
            if eid and eid in seen:
                continue
            if eid:
                seen.add(eid)

            try:
                subj = str(mail.Subject or "")
            except Exception:
                subj = ""
            try:
                recv = str(mail.ReceivedTime)
            except Exception:
                recv = ""
            sender = ""
            try:
                sender = str(mail.SenderName or "")
            except Exception:
                pass
            from_addr = smtp_of(mail)
            blob = sender_blob(mail, from_addr, sender)
            sap4 = is_sap4_uti(from_addr, blob)
            subj_hit = "utipartsales" in subj.lower()

            # Keep: exact/alias sap4@uti, or (sap4-like AND UTIPartSales).
            if not sap4 and not (subj_hit and "sap4" in blob):
                continue
            if sap4 and from_addr:
                sap4_aliases.add(from_addr.lower())

            atts: list[str] = []
            saved_here: list[str] = []
            try:
                ac = mail.Attachments.Count
            except Exception:
                ac = 0
            for i in range(1, ac + 1):
                try:
                    att = mail.Attachments.Item(i)
                    an = str(att.FileName)
                    atts.append(an)
                    low = an.lower()
                    if not low.endswith(KEEP_EXT):
                        continue
                    if "utipartsales" not in low and "partsales" not in low and not subj_hit:
                        continue
                    stamp = recv[:10] if recv else "nodate"
                    dest = unique_dest(
                        OUT_DIR / f"{stamp}_{_folder_safe(fpath)}_{_safe(an)}"
                    )
                    att.SaveAsFile(str(dest))
                    saved_here.append(str(dest))
                    saved.append(str(dest))
                    _p(f"SAVED {dest}")
                except Exception as e:
                    saved_here.append(f"ERR:{e}")

            hits.append(
                {
                    "folder": fpath,
                    "received": recv,
                    "subject": subj,
                    "sender": sender,
                    "from_addr": from_addr,
                    "sap4_match": sap4,
                    "attachments": atts,
                    "saved": saved_here,
                }
            )

    payload = {
        "scan_date": "2026-08-13",
        "never_send": True,
        "uti_sap_sold_to": 1799,
        "not_umi": 1797,
        "stores": stores,
        "folder_count": len(folders),
        "sap4_aliases_seen": sorted(sap4_aliases),
        "hit_count": len(hits),
        "saved_count": len(saved),
        "saved": saved,
        "hits": hits,
        "archive_zero_item_folders": [
            s for s in folder_stats if s["items"] == 0 and "archive" in s["folder"].lower()
        ][:80],
    }
    META.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    _p(f"DONE hits {len(hits)} saved {len(saved)} aliases {sorted(sap4_aliases)} meta {META}")


if __name__ == "__main__":
    main()
