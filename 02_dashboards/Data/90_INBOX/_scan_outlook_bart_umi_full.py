"""Full Outlook pull: Bart Symons (from/to/cc) x UMI 1797. Not UTI 1799.

Local Outlook COM (win32com). Composio Outlook is not connected.
Walks every store + folder; Restrict by sender; UMI-domain senders; customer folders.
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import win32com.client

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX")
OUT.mkdir(parents=True, exist_ok=True)
JSON_OUT = OUT / "_umi_bart_outlook_full.json"
INDEX_OUT = OUT / "_umi_bart_outlook_full_index.json"

PR_SMTP = "http://schemas.microsoft.com/mapi/proptag/0x39FE001E"
PR_SENDER_SMTP = "http://schemas.microsoft.com/mapi/proptag/0x5D01001F"
PR_DISPLAY_TO = "http://schemas.microsoft.com/mapi/proptag/0x0E04001F"
PR_DISPLAY_CC = "http://schemas.microsoft.com/mapi/proptag/0x0E03001F"

BART_KEYS = (
    "bart.symons",
    "bart symons",
    "bart s ",
)
UMI_POS = (
    "umi.co.il",
    "universal motors israel",
    "universal motors",
    "sold-to 1797",
    "sold to 1797",
    "sold-to: 1797",
)
UMI_PEOPLE = (
    "shelly@umi",
    "netanelbuc@",
    "nadav@umi",
    "pnina@umi",
    "yaniv@umi",
    "henb@umi",
    "shelly cohen",
    "netanel buchnik",
    "nadav libes",
    "pnina swisa",
)
UTI_POS = (
    "uti.co.il",
    "sold-to 1799",
    "sold to 1799",
    "shahafr@",
    "shahaf rehani",
)

SENDER_RESTRICTS = [
    "[SenderName] = 'Bart Symons'",
    "[SenderName] = 'Bart SYMONS'",
    "[SenderName] = 'Bart S'",
]
UMI_SENDER_RESTRICTS = [
    "[SenderName] = 'Shelly Cohen'",
    "[SenderName] = 'Netanel Buchnik'",
    "[SenderName] = 'Nadav Libes'",
    "[SenderName] = 'Pnina Swisa'",
    "[SenderName] = 'Yaniv Nissim'",
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
    if depth > 14:
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


def blob_of(mail, extra: str = "") -> str:
    parts = [
        extra,
        str(getattr(mail, "Subject", "") or ""),
        str(getattr(mail, "SenderName", "") or ""),
        smtp_of(mail),
        str(getattr(mail, "To", "") or ""),
        str(getattr(mail, "CC", "") or ""),
    ]
    try:
        parts.append(str(mail.Body or "")[:8000])
    except Exception:
        pass
    return " ".join(parts).lower()


def bart_in(blob: str) -> bool:
    return any(k in blob for k in BART_KEYS)


def umi_in(blob: str) -> bool:
    if any(k in blob for k in UMI_POS):
        return True
    if any(k in blob for k in UMI_PEOPLE):
        return True
    # bare " umi " / subject UMI, but not UTI
    if re.search(r"\bumi\b", blob) and "uti.co.il" not in blob:
        return True
    return False


def uti_only(blob: str) -> bool:
    has_uti = any(k in blob for k in UTI_POS)
    has_umi = umi_in(blob)
    return has_uti and not has_umi


def rec_of(mail, fpath: str, how: str) -> dict:
    body = ""
    try:
        body = str(mail.Body or "")[:6000]
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
        rt = mail.ReceivedTime
        received = str(rt)[:19]
    except Exception:
        received = ""
    return {
        "received": received,
        "from_name": str(getattr(mail, "SenderName", "") or ""),
        "from_smtp": smtp_of(mail),
        "to": str(getattr(mail, "To", "") or ""),
        "cc": str(getattr(mail, "CC", "") or ""),
        "subject": str(getattr(mail, "Subject", "") or ""),
        "folder": fpath,
        "how": how,
        "atts": atts,
        "preview": " ".join(body.split())[:1200],
        "entry_id": str(getattr(mail, "EntryID", "") or "")[:80],
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
    try:
        log(f"USER {ns.CurrentUser.Name}")
    except Exception:
        pass

    stores = []
    umi_folder_inventory = []
    all_folders = []
    for s in ns.Stores:
        try:
            name = str(s.DisplayName)
            root = s.GetRootFolder()
            stores.append({"name": name, "path": str(getattr(s, "FilePath", "") or "")})
            log(f"STORE {name}")
            for f in walk_folders(root):
                try:
                    fpath = str(f.FolderPath)
                    n = int(f.Items.Count)
                except Exception:
                    continue
                all_folders.append((f, fpath, n))
                pl = fpath.lower()
                if any(x in pl for x in ("umi", "uti", "meeting minute", "israel")):
                    umi_folder_inventory.append({"path": fpath, "n": n})
                    log(f"  FOLDER {fpath} n={n}")
        except Exception as e:
            log(f"STORE_FAIL {e}")

    log(f"folders_total={len(all_folders)} umi_ish={len(umi_folder_inventory)}")

    seen: set[str] = set()
    hits: list[dict] = []
    bart_from_all = 0
    stats = {"restrict_bart": 0, "restrict_umi_sender": 0, "folder_walk_umi": 0, "skipped_uti": 0}

    def keep(mail, fpath: str, how: str, require_bart: bool) -> None:
        nonlocal bart_from_all
        eid = str(getattr(mail, "EntryID", "") or "")
        if eid and eid in seen:
            return
        blob = blob_of(mail)
        if uti_only(blob):
            stats["skipped_uti"] += 1
            return
        if not umi_in(blob):
            return
        if require_bart and not bart_in(blob):
            return
        if eid:
            seen.add(eid)
        rec = rec_of(mail, fpath, how)
        rec["bart"] = bart_in(blob)
        rec["umi"] = True
        rec["also_uti"] = any(k in blob for k in UTI_POS)
        hits.append(rec)
        if rec["bart"] and "bart.symons" in (rec["from_smtp"] or "") or "bart symons" in (rec["from_name"] or "").lower():
            bart_from_all += 1

    # Pass 1 — every folder: mail FROM Bart, keep if UMI
    for folder, fpath, n in all_folders:
        if n <= 0:
            continue
        for clause in SENDER_RESTRICTS:
            added = 0
            for mail in restrict_iter(folder, clause):
                keep(mail, fpath, f"from_bart:{clause}", require_bart=False)
                added += 1
            if added:
                stats["restrict_bart"] += added
                log(f"FROM BART {fpath}: {added}")

    # Pass 2 — UMI senders (Inbox/Sent/Archive + customer folders), keep if Bart in thread
    umi_targets = []
    for folder, fpath, n in all_folders:
        if n <= 0:
            continue
        pl = fpath.lower()
        if any(x in pl for x in ("inbox", "sent", "archive", "umi", "veh customer", "customers")):
            umi_targets.append((folder, fpath, n))

    for folder, fpath, n in umi_targets:
        for clause in UMI_SENDER_RESTRICTS:
            added = 0
            for mail in restrict_iter(folder, clause):
                keep(mail, fpath, f"umi_sender:{clause}", require_bart=True)
                added += 1
            if added:
                stats["restrict_umi_sender"] += added
                log(f"UMI SENDER {fpath} {clause}: {added}")

    # Pass 3 — dump every item in UMI customer / meeting-minutes folders
    for folder, fpath, n in all_folders:
        pl = fpath.lower()
        if n <= 0:
            continue
        if not any(x in pl for x in ("/umi", "\\umi", "customers/umi", "meeting minute")):
            continue
        if "uti" in pl and "umi" not in pl:
            continue
        log(f"WALK FOLDER {fpath} n={n}")
        scanned = 0
        try:
            items = folder.Items
            items.Sort("[ReceivedTime]", True)
        except Exception as e:
            log(f"  walk fail {e}")
            continue
        for mail in items:
            scanned += 1
            if scanned > 4000:
                break
            try:
                if int(mail.Class) != 43:
                    continue
            except Exception:
                continue
            keep(mail, fpath, "folder_walk", require_bart=False)
        stats["folder_walk_umi"] += scanned
        log(f"  scanned={scanned}")

    hits.sort(key=lambda h: h.get("received") or "", reverse=True)
    bart_hits = [h for h in hits if h.get("bart")]
    from_bart = [
        h
        for h in hits
        if "bart.symons" in (h.get("from_smtp") or "")
        or "bart symons" in (h.get("from_name") or "").lower()
    ]
    subjects = sorted({h["subject"] for h in bart_hits})

    summary = {
        "scanned_at": datetime.now().isoformat(timespec="seconds"),
        "elapsed_s": round(time.time() - t0, 1),
        "access": "local Outlook COM (win32com MAPI). Composio Outlook toolkit not connected.",
        "stores": stores,
        "folders_walked": len(all_folders),
        "umi_ish_folders": umi_folder_inventory,
        "stats": stats,
        "n_hits_umi": len(hits),
        "n_bart_involved": len(bart_hits),
        "n_from_bart": len(from_bart),
        "n_skipped_uti_only": stats["skipped_uti"],
        "subjects_bart": subjects,
    }
    payload = {**summary, "hits": hits}
    JSON_OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    INDEX_OUT.write_text(
        json.dumps(
            {
                **{k: summary[k] for k in summary if k != "stores"},
                "index": [
                    {
                        k: h[k]
                        for k in (
                            "received",
                            "from_name",
                            "from_smtp",
                            "subject",
                            "to",
                            "cc",
                            "folder",
                            "how",
                            "bart",
                            "also_uti",
                            "atts",
                        )
                    }
                    for h in hits
                ],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    log("SUMMARY " + json.dumps({k: summary[k] for k in summary if k not in ("stores", "umi_ish_folders", "subjects_bart")}))
    log(f"subjects_bart={len(subjects)}")
    for s in subjects:
        log(f"  SUBJ {s[:120]}")
    log(f"OUT {JSON_OUT}")


if __name__ == "__main__":
    main()
