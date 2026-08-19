"""Fresh pull: ALL mail FROM Shelly Cohen / shelly@umi.co.il (UMI 1797). Not UTI.

Also: Sent-item replies to Shelly after 2026-08-01 (did we already send the deck?).
Draft-only later — this script never Send.
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

import win32com.client

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX")
JSON_OUT = OUT / "_umi_shelly_outlook_20260817.json"
ATT_DIR = OUT / "_umi_shelly_atts"
ATT_DIR.mkdir(parents=True, exist_ok=True)

PR_SMTP = "http://schemas.microsoft.com/mapi/proptag/0x39FE001E"
PR_SENDER_SMTP = "http://schemas.microsoft.com/mapi/proptag/0x5D01001F"

SENDER_RESTRICTS = [
    "[SenderName] = 'Shelly Cohen'",
    "[SenderName] = 'Shelly'",
]
DASL = [
    ('from_smtp', '@SQL="http://schemas.microsoft.com/mapi/proptag/0x5D01001F" LIKE \'%shelly@umi.co.il%\''),
    ('from_smtp2', '@SQL="http://schemas.microsoft.com/mapi/proptag/0x39FE001E" LIKE \'%shelly@umi.co.il%\''),
    ('to_shelly', '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0E04001F" LIKE \'%shelly@umi%\''),
    ('cc_shelly', '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0E03001F" LIKE \'%shelly@umi%\''),
    ('subj_meeting', '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%Meeting%\''),
    ('subj_shell', '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%SHELL%\''),
]


def log(m: str) -> None:
    print(m, flush=True)


def smtp_of(mail) -> str:
    try:
        ae = mail.Sender
        if ae is not None:
            try:
                v = ae.PropertyAccessor.GetProperty(PR_SMTP)
                if v:
                    return str(v).lower()
            except Exception:
                pass
            try:
                v = ae.PropertyAccessor.GetProperty(PR_SENDER_SMTP)
                if v:
                    return str(v).lower()
            except Exception:
                pass
            try:
                eu = ae.GetExchangeUser()
                if eu is not None and eu.PrimarySmtpAddress:
                    return str(eu.PrimarySmtpAddress).lower()
            except Exception:
                pass
    except Exception:
        pass
    return str(getattr(mail, "SenderEmailAddress", "") or "").lower()


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


def rec_of(mail, fpath: str, how: str) -> dict:
    body = ""
    try:
        body = str(mail.Body or "")[:12000]
    except Exception:
        body = ""
    atts = []
    try:
        for i in range(1, mail.Attachments.Count + 1):
            try:
                atts.append(str(mail.Attachments.Item(i).FileName))
            except Exception:
                pass
    except Exception:
        pass
    received = ""
    try:
        received = str(mail.ReceivedTime)[:19]
    except Exception:
        received = ""
    smtp = smtp_of(mail)
    return {
        "received": received,
        "from_name": str(getattr(mail, "SenderName", "") or ""),
        "from_smtp": smtp,
        "to": str(getattr(mail, "To", "") or ""),
        "cc": str(getattr(mail, "CC", "") or ""),
        "subject": str(getattr(mail, "Subject", "") or ""),
        "folder": fpath,
        "how": how,
        "atts": atts,
        "body": body,
        "preview": " ".join(body.split())[:1800],
        "entry_id": str(getattr(mail, "EntryID", "") or ""),
        "from_shelly": "shelly@" in smtp or "shelly cohen" in str(getattr(mail, "SenderName", "") or "").lower(),
    }


def restrict_iter(folder, clause: str):
    try:
        items = folder.Items.Restrict(clause)
    except Exception:
        return
    try:
        _ = items.Count
    except Exception:
        pass
    try:
        for mail in items:
            try:
                if int(mail.Class) != 43:
                    continue
            except Exception:
                continue
            yield mail
    except Exception:
        return


def main() -> None:
    t0 = time.time()
    log(f"START {datetime.now().isoformat(timespec='seconds')}")
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")

    folders = []
    stores = []
    for s in ns.Stores:
        try:
            name = str(s.DisplayName)
            stores.append(name)
            log(f"STORE {name}")
            root = s.GetRootFolder()
            for f in walk_folders(root):
                try:
                    fpath = str(f.FolderPath)
                    n = int(f.Items.Count)
                except Exception:
                    continue
                if n <= 0:
                    continue
                pl = fpath.lower()
                if any(x in pl for x in ("inbox", "sent", "archive", "umi", "veh customer", "draft")):
                    folders.append((f, fpath, n))
        except Exception as e:
            log(f"STORE_FAIL {e}")

    log(f"folders={len(folders)}")
    seen: set[str] = set()
    hits: list[dict] = []

    def keep(mail, fpath: str, how: str) -> None:
        eid = str(getattr(mail, "EntryID", "") or "")
        if eid and eid in seen:
            return
        rec = rec_of(mail, fpath, how)
        blob = " ".join(
            [
                rec["from_name"],
                rec["from_smtp"],
                rec["to"],
                rec["cc"],
                rec["subject"],
                rec["body"][:2000],
            ]
        ).lower()
        if "uti.co.il" in blob and "umi.co.il" not in blob and "shelly@" not in blob:
            return
        is_from = rec["from_shelly"] or "shelly@umi" in rec["from_smtp"]
        is_thread = "shelly@umi" in blob or "shelly cohen" in blob
        if not (is_from or is_thread):
            return
        if eid:
            seen.add(eid)
        rec["lane"] = "from_shelly" if is_from else "thread"
        hits.append(rec)

    for folder, fpath, n in folders:
        for clause in SENDER_RESTRICTS:
            added = 0
            for mail in restrict_iter(folder, clause):
                keep(mail, fpath, f"sender:{clause}")
                added += 1
            if added:
                log(f"SENDER {fpath}: {added}")
        for tag, clause in DASL:
            added = 0
            for mail in restrict_iter(folder, clause):
                keep(mail, fpath, f"dasl:{tag}")
                added += 1
            if added and tag.startswith("from"):
                log(f"DASL {tag} {fpath}: {added}")

    hits.sort(key=lambda h: h.get("received") or "", reverse=True)
    from_shelly = [h for h in hits if h.get("lane") == "from_shelly"]
    sent_after = [
        h
        for h in hits
        if "sent" in (h.get("folder") or "").lower()
        and (h.get("received") or "") >= "2026-08-01"
        and "jerome" in (h.get("from_smtp") or "")
    ]

    summary = {
        "scanned_at": datetime.now().isoformat(timespec="seconds"),
        "elapsed_s": round(time.time() - t0, 1),
        "stores": stores,
        "folders": len(folders),
        "n_hits": len(hits),
        "n_from_shelly": len(from_shelly),
        "n_sent_to_shelly_thread_since_aug1": len(sent_after),
        "from_shelly_subjects": [
            {"received": h["received"], "subject": h["subject"], "folder": h["folder"]}
            for h in from_shelly
        ],
        "sent_since_aug1": [
            {"received": h["received"], "subject": h["subject"], "to": h["to"]}
            for h in sent_after
        ],
    }
    JSON_OUT.write_text(
        json.dumps({"summary": summary, "from_shelly": from_shelly, "all_hits": hits}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    log("SUMMARY " + json.dumps({k: summary[k] for k in summary if k not in ("from_shelly_subjects", "sent_since_aug1")}))
    log(f"FROM SHELLY n={len(from_shelly)}")
    for h in from_shelly[:40]:
        log(f"  {h['received']} | {h['subject'][:90]}")
    log(f"SENT since Aug1 n={len(sent_after)}")
    for h in sent_after[:20]:
        log(f"  {h['received']} | {h['subject'][:90]}")
    log(f"OUT {JSON_OUT}")


if __name__ == "__main__":
    main()
