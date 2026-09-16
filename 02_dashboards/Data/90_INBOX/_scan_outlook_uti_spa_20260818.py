"""Find UTI SPA mails/attachments. Never Send."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import win32com.client

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX")
JSON_OUT = OUT / "_uti_spa_outlook_20260818.json"
ATT_DIR = OUT / "_uti_spa_atts_20260818"
ATT_DIR.mkdir(parents=True, exist_ok=True)

KEEP_EXT = (".xlsx", ".xls", ".xlsm", ".csv")
SUBJ_DASL = [
    '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%SPA%\'',
    '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%spa2%\'',
    '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%spa new request%\'',
]
FROM_DASL = [
    '@SQL="http://schemas.microsoft.com/mapi/proptag/0x5D01001F" LIKE \'%@uti.co.il%\'',
    '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0C1F001F" LIKE \'%@uti.co.il%\'',
]


def walk(folder, depth=0):
    yield folder
    if depth > 12:
        return
    try:
        n = folder.Folders.Count
    except Exception:
        return
    for i in range(1, n + 1):
        try:
            yield from walk(folder.Folders.Item(i), depth + 1)
        except Exception:
            continue


def rec(mail, folder: str, how: str) -> dict:
    atts = []
    try:
        for i in range(1, mail.Attachments.Count + 1):
            try:
                atts.append(str(mail.Attachments.Item(i).FileName))
            except Exception:
                pass
    except Exception:
        pass
    body = ""
    try:
        body = str(mail.Body or "")[:2500]
    except Exception:
        body = ""
    received = ""
    try:
        received = str(mail.ReceivedTime)[:19]
    except Exception:
        pass
    sender = str(getattr(mail, "SenderEmailAddress", "") or "")
    name = str(getattr(mail, "SenderName", "") or "")
    subj = str(getattr(mail, "Subject", "") or "")
    return {
        "received": received,
        "from_name": name,
        "from_addr": sender,
        "to": str(getattr(mail, "To", "") or ""),
        "subject": subj,
        "folder": folder,
        "how": how,
        "atts": atts,
        "preview": " ".join(body.split())[:900],
        "entry_id": str(getattr(mail, "EntryID", "") or ""),
    }


def is_uti(r: dict) -> bool:
    blob = " ".join(
        [
            r["from_addr"],
            r["from_name"],
            r["to"],
            r["subject"],
            r["preview"],
            " ".join(r["atts"]),
        ]
    ).lower()
    return "uti.co.il" in blob or "uti " in blob or blob.startswith("uti") or " 1799" in blob


def is_spa(r: dict) -> bool:
    blob = " ".join([r["subject"], " ".join(r["atts"]), r["preview"]]).lower()
    return "spa" in blob or "spa2" in blob


def main() -> None:
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    hits: dict[str, dict] = {}
    stores = []
    for i in range(1, ns.Folders.Count + 1):
        store = ns.Folders.Item(i)
        stores.append(str(store.Name))
        print("STORE", store.Name, flush=True)
        for folder in walk(store):
            try:
                fpath = str(folder.FolderPath)
            except Exception:
                continue
            try:
                items = folder.Items
            except Exception:
                continue
            for filt in SUBJ_DASL + FROM_DASL:
                try:
                    sub = items.Restrict(filt)
                except Exception:
                    continue
                try:
                    n = sub.Count
                except Exception:
                    continue
                for j in range(1, min(n, 400) + 1):
                    try:
                        mail = sub.Item(j)
                    except Exception:
                        continue
                    if int(getattr(mail, "Class", 0) or 0) != 43:
                        continue
                    r = rec(mail, fpath, filt[:40])
                    if not (is_uti(r) and is_spa(r)):
                        continue
                    eid = r["entry_id"] or f"{r['received']}|{r['subject']}"
                    prev = hits.get(eid)
                    if prev is None or len(r["atts"]) > len(prev["atts"]):
                        hits[eid] = r

    rows = sorted(hits.values(), key=lambda x: x.get("received") or "", reverse=True)
    saved = []
    for r in rows[:12]:
        recvd = r.get("received") or ""
        if recvd < "2026-07-01":
            continue
        # Re-open by EntryID to save xlsx
        try:
            mail = ns.GetItemFromID(r["entry_id"])
        except Exception:
            continue
        stamp = recvd[:10].replace(":", "")
        try:
            for i in range(1, mail.Attachments.Count + 1):
                att = mail.Attachments.Item(i)
                name = str(att.FileName)
                if not name.lower().endswith(KEEP_EXT):
                    continue
                safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name)
                dest = ATT_DIR / f"{stamp}_{safe}"
                if not dest.exists():
                    att.SaveAsFile(str(dest))
                saved.append(str(dest))
                print("SAVED", dest, flush=True)
        except Exception as e:
            print("SAVE_ERR", e, flush=True)

    payload = {
        "scanned_at": datetime.now().isoformat(timespec="seconds"),
        "stores": stores,
        "n_hits": len(rows),
        "hits": rows[:40],
        "saved_atts": saved,
    }
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("HITS", len(rows), "OUT", JSON_OUT, flush=True)
    for r in rows[:15]:
        print(r["received"], "|", r["from_name"], "|", r["subject"], "|", r["atts"], flush=True)


if __name__ == "__main__":
    main()
