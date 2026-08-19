"""Outlook COM hunt for DB→DLR sell-out files. Draft/save only — never Send."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import win32com.client

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_DIR = ISZE / r"01_data\90_INBOX\dealer_sales_mail_20260813"
META = ISZE / r"01_data\90_INBOX\outlook_dealer_sales_scan_20260813.json"

SUBJECT_PATTERNS = [
    "Sales to Dealers",
    "UTIPartSales",
    "PartSales",
    "IUK Monthly Demand",
    "Monthly Demand",
    "Petros_Parts_Sold",
    "Petros Parts Sold",
    "Parts_Sold_Qties",
    "Parts Sold Qties",
    "sell-out",
    "sellout",
    "dealer sales",
    "Sales to Dealer",
    "sales-to-dealer",
]

SENDER_FRAGMENTS = [
    "uti.co.il",
    "noreply2@uti",
]

SAVE_NAME_HINTS = (
    "utipartsales",
    "partsales",
    "sales to dealers",
    "sales_to_dealers",
    "salestodealers",
    "monthly demand",
    "monthly_demand",
    "petros_parts_sold",
    "petros parts sold",
    "parts_sold_qties",
    "parts sold qties",
    "sell-out",
    "sellout",
    "dealer sales",
    "dealer_sales",
    "sales-to-dealer",
)

SKIP_NAME_HINTS = (
    "spa_uti",
    "spa-",
    "ids_-_dealer",
    "ids dealer",
    "recommended parts",
    "vk05",
    "vr05",
    "uio",
)

KEEP_EXT = (".xlsx", ".xls", ".xlsm", ".csv")
SKIP_EXT = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".eml")


def _safe(fn: str) -> str:
    return re.sub(r"[^\w.\-]+", "_", fn)


def _folder_safe(path: str) -> str:
    return re.sub(r"[^\w.\-]+", "_", path)[:60].strip("_")


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _dasl_subject(token: str) -> str:
    t = token.replace("'", "''")
    return (
        '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001f" '
        f"LIKE '%{t}%'"
    )


def _dasl_from(token: str) -> str:
    t = token.replace("'", "''")
    return (
        '@SQL="urn:schemas:httpmail:fromemail" '
        f"LIKE '%{t}%'"
    )


def _should_save(filename: str, subject: str) -> bool:
    low = filename.lower()
    subj = subject.lower()
    if low.endswith(SKIP_EXT):
        return False
    if not low.endswith(KEEP_EXT):
        return False
    if any(s in low for s in SKIP_NAME_HINTS):
        return False
    if any(h in low for h in SAVE_NAME_HINTS):
        return True
    if any(h in subj for h in SAVE_NAME_HINTS):
        return True
    return False


def walk_folders(folder, prefix: str, acc: list, depth: int = 0) -> None:
    if depth > 16:
        return
    try:
        path = str(folder.FolderPath)
    except Exception:
        path = prefix
    acc.append(folder)
    try:
        for sub in folder.Folders:
            walk_folders(sub, path, acc, depth + 1)
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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")

    filters = [_dasl_subject(t) for t in SUBJECT_PATTERNS]
    filters += [_dasl_from(t) for t in SENDER_FRAGMENTS]

    stores = []
    folders = []
    for i in range(1, ns.Stores.Count + 1):
        store = ns.Stores.Item(i)
        name = str(store.DisplayName)
        stores.append(name)
        print("STORE", name.encode("ascii", "replace").decode(), flush=True)
        try:
            walk_folders(store.GetRootFolder(), name, folders)
        except Exception as e:
            print("  STORE FAIL", name, e, flush=True)

    print(f"FOLDERS {len(folders)}", flush=True)

    seen: set[str] = set()
    hits: list[dict] = []
    saved: list[str] = []

    for folder in folders:
        try:
            fpath = str(folder.FolderPath)
        except Exception:
            fpath = "?"
        print("FOLDER", fpath.encode("ascii", "replace").decode(), flush=True)
        for mail in restrict_hits(folder, filters):
            try:
                if int(mail.Class) != 43:
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
            from_addr = ""
            try:
                sender = str(mail.SenderName or "")
            except Exception:
                pass
            try:
                from_addr = str(mail.SenderEmailAddress or "")
            except Exception:
                pass
            try:
                if mail.Sender:
                    eu = mail.Sender.GetExchangeUser()
                    if eu and eu.PrimarySmtpAddress:
                        from_addr = str(eu.PrimarySmtpAddress)
            except Exception:
                pass
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
                    if not _should_save(an, subj):
                        continue
                    stamp = recv[:10] if recv else "nodate"
                    dest = OUT_DIR / f"{stamp}_{_folder_safe(fpath)}_{_safe(an)}"
                    if dest.exists():
                        n = 2
                        while True:
                            dest2 = dest.with_name(f"{dest.stem}_{n}{dest.suffix}")
                            if not dest2.exists():
                                dest = dest2
                                break
                            n += 1
                    att.SaveAsFile(str(dest))
                    saved_here.append(str(dest))
                    saved.append(str(dest))
                    print("SAVED", dest, flush=True)
                except Exception as e:
                    saved_here.append(f"ERR:{e}")

            hits.append(
                {
                    "folder": fpath,
                    "received": recv,
                    "subject": subj,
                    "sender": sender,
                    "from_addr": from_addr,
                    "attachments": atts,
                    "saved": saved_here,
                }
            )

    payload = {
        "scan_date": "2026-08-13",
        "never_send": True,
        "stores": stores,
        "folder_count": len(folders),
        "hit_count": len(hits),
        "saved_count": len(saved),
        "saved": saved,
        "hits": hits,
    }
    META.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print("DONE hits", len(hits), "saved", len(saved), "meta", META, flush=True)


if __name__ == "__main__":
    main()
