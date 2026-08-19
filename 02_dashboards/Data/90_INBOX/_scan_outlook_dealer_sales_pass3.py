"""Pass 3: list Sales-to-Dealers / Petros hits; deep-scan Petros folder. Never Send."""
from __future__ import annotations

import json
from pathlib import Path

import win32com.client

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_DIR = ISZE / r"01_data\90_INBOX\dealer_sales_mail_20260813"
META = ISZE / r"01_data\90_INBOX\outlook_dealer_sales_scan_pass3_20260813.json"

TOKENS = [
    "Sales to Dealers",
    "Sales to Dealer",
    "Petros_Parts_Sold",
    "Petros Parts Sold",
    "Parts_Sold_Qties",
    "Parts Sold Qties",
    "sell-out",
    "sellout",
    "dealer sales",
    "sales-to-dealer",
]


def _p(msg: str) -> None:
    print(msg.encode("ascii", "replace").decode(), flush=True)


def _dasl_subject(token: str) -> str:
    t = token.replace("'", "''")
    return (
        '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001f" '
        f"LIKE '%{t}%'"
    )


def walk_folders(folder, acc: list, depth: int = 0) -> None:
    if depth > 16:
        return
    acc.append(folder)
    try:
        for sub in folder.Folders:
            walk_folders(sub, acc, depth + 1)
    except Exception:
        pass


def att_names(mail) -> list[str]:
    out = []
    try:
        n = mail.Attachments.Count
    except Exception:
        return out
    for i in range(1, n + 1):
        try:
            out.append(str(mail.Attachments.Item(i).FileName))
        except Exception:
            pass
    return out


def mail_rec(mail, fpath: str) -> dict | None:
    try:
        if int(mail.Class) != 43:
            return None
    except Exception:
        return None
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
    return {
        "folder": fpath,
        "received": recv,
        "subject": subj,
        "sender": sender,
        "from_addr": from_addr,
        "attachments": att_names(mail),
        "entry_id": str(getattr(mail, "EntryID", "") or ""),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    filters = [_dasl_subject(t) for t in TOKENS]
    seen: set[str] = set()
    hits: list[dict] = []
    petros_items: list[dict] = []

    for i in range(1, ns.Stores.Count + 1):
        store = ns.Stores.Item(i)
        name = str(store.DisplayName)
        _p(f"STORE {name}")
        folders = []
        try:
            walk_folders(store.GetRootFolder(), folders)
        except Exception as e:
            _p(f"  FAIL {e}")
            continue
        for folder in folders:
            try:
                fpath = str(folder.FolderPath)
            except Exception:
                fpath = "?"
            fl = fpath.lower()
            if "petros" in fl:
                _p(f"DEEP PETROS {fpath}")
                try:
                    items = folder.Items
                    n = items.Count
                    _p(f"  items={n}")
                    for j in range(1, n + 1):
                        try:
                            rec = mail_rec(items.Item(j), fpath)
                        except Exception:
                            continue
                        if rec:
                            petros_items.append(rec)
                            atts_l = " ".join(rec["attachments"]).lower()
                            subj_l = rec["subject"].lower()
                            if any(
                                h in atts_l or h in subj_l
                                for h in (
                                    "parts_sold",
                                    "parts sold",
                                    "sellout",
                                    "sell-out",
                                    "dealer",
                                    "qty",
                                    "qties",
                                )
                            ):
                                _p(
                                    f"  PETROS HIT {rec['received'][:19]} {rec['subject']} atts={rec['attachments']}"
                                )
                except Exception as e:
                    _p(f"  PETROS FAIL {e}")

            try:
                base = folder.Items
            except Exception:
                continue
            for filt in filters:
                try:
                    sub = base.Restrict(filt)
                    n = sub.Count
                except Exception:
                    continue
                for j in range(1, n + 1):
                    try:
                        rec = mail_rec(sub.Item(j), fpath)
                    except Exception:
                        continue
                    if not rec:
                        continue
                    eid = rec["entry_id"]
                    if eid and eid in seen:
                        continue
                    if eid:
                        seen.add(eid)
                    hits.append(rec)
                    _p(
                        f"HIT {fpath} | {rec['received'][:19]} | {rec['subject']} | {rec['attachments']}"
                    )

    payload = {
        "scan_date": "2026-08-13",
        "never_send": True,
        "pass": 3,
        "hit_count": len(hits),
        "petros_folder_item_count": len(petros_items),
        "hits": hits,
        "petros_folder_items": petros_items,
    }
    META.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    _p(f"DONE hits={len(hits)} petros_items={len(petros_items)} {META}")


if __name__ == "__main__":
    main()
