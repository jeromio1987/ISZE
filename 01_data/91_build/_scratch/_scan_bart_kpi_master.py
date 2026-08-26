"""Scan Outlook for Bart's KPI master file mail (today ~10:21) + who replied/updated it.

Local Outlook COM (win32com). Finds:
  - the KPI master file email from Bart (Bart Symons / Bart Van Den Bosch)
  - the same conversation thread: who else sent/replied (i.e. "who provided updates")
  - saves any real attachments to 90_INBOX.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import win32com.client

OUT_DIR = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX")
OUT_DIR.mkdir(parents=True, exist_ok=True)
JSON_OUT = OUT_DIR / "_bart_kpi_master_scan.json"

BART = ("bart.symons", "bart symons", "bart van den bosch", "bart van de bosch", "bart vdb")
KPI_KEYS = ("kpi", "targets", "fill rate", "days in stock", "master")


def clean(s: str) -> str:
    return re.sub(r"[^\w\-\. ]", "_", str(s))


def smtp_of(mail) -> str:
    try:
        ae = mail.Sender
        if ae is not None:
            for tag in (
                "http://schemas.microsoft.com/mapi/proptag/0x39FE001E",
                "http://schemas.microsoft.com/mapi/proptag/0x5D01001F",
            ):
                try:
                    v = ae.PropertyAccessor.GetProperty(tag)
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


def body_of(mail) -> str:
    try:
        return str(mail.Body or "")
    except Exception:
        return ""


def walk_folders(folder, depth=0):
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


def main() -> None:
    print("connecting Outlook COM", flush=True)
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    try:
        print("USER", ns.CurrentUser.Name, flush=True)
    except Exception:
        pass

    # gather folders of interest: inbox, sent, and any kpi/planning/archive folders
    targets = []
    inbox = ns.GetDefaultFolder(6)
    sent = ns.GetDefaultFolder(5)
    targets.append(("Inbox", inbox))
    targets.append(("Sent", sent))
    for s in ns.Stores:
        try:
            root = s.GetRootFolder()
            for f in walk_folders(root):
                pl = str(f.FolderPath).lower()
                if any(x in pl for x in ("kpi", "planning", "target", "archive", "inbox")):
                    targets.append((str(f.FolderPath), f))
        except Exception:
            pass
    # de-dup
    seen_folders = set()
    uniq = []
    for label, f in targets:
        if label in seen_folders:
            continue
        seen_folders.add(label)
        uniq.append((label, f))
    targets = uniq
    print(f"folders={len(targets)}", flush=True)

    seen = set()
    hits = []
    saved = []

    for label, folder in targets:
        try:
            items = folder.Items
            items.Sort("[ReceivedTime]", True)
        except Exception:
            continue
        n = 0
        for mail in items:
            n += 1
            if n > 500:
                break
            try:
                if int(mail.Class) != 43:
                    continue
                recv = str(mail.ReceivedTime)[:19]
                # only look at recent (last ~5 weeks) — KPI master is recent
                if recv < "2026-07-01":
                    break
            except Exception:
                continue
            try:
                sender = str(getattr(mail, "SenderName", "") or "")
                smtp = smtp_of(mail)
                subj = str(getattr(mail, "Subject", "") or "")
                body = body_of(mail)
                blob = f"{subj} {sender} {smtp} {body}".lower()
                is_bart = any(k in blob for k in BART)
                is_kpi = any(k in blob for k in KPI_KEYS)
                if not (is_bart or is_kpi):
                    continue
                eid = str(getattr(mail, "EntryID", "") or "")
                if eid and eid in seen:
                    continue
                seen.add(eid)
                atts = []
                try:
                    for a in range(1, mail.Attachments.Count + 1):
                        att = mail.Attachments.Item(a)
                        fn = str(att.FileName)
                        atts.append(fn)
                        if not re.search(r"\.(png|jpe?g|gif)$", fn, re.I) and is_bart and is_kpi:
                            dest = OUT_DIR / f"{recv[:10].replace('-', '')}_{clean(sender)[:20]}_{clean(fn)}"
                            try:
                                att.SaveAsFile(str(dest))
                                saved.append(str(dest))
                            except Exception as e:
                                saved.append(f"ERR {fn}: {e}")
                except Exception:
                    pass
                hits.append({
                    "received": recv,
                    "from_name": sender,
                    "from_smtp": smtp,
                    "subject": subj,
                    "folder": label,
                    "atts": atts,
                    "body_head": " ".join(body.split())[:500],
                    "is_bart": is_bart,
                    "is_kpi": is_kpi,
                })
            except Exception:
                continue

    hits.sort(key=lambda h: h.get("received") or "", reverse=True)
    JSON_OUT.write_text(json.dumps(hits, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"hits={len(hits)}", flush=True)
    for h in hits[:60]:
        print(
            f"{h['received']} | {h['from_name']} <{h['from_smtp']}> | {h['subject']} | atts={h['atts']} | bart={h['is_bart']}",
            flush=True,
        )
    print("SAVED:", saved, flush=True)
    print("OUT", JSON_OUT, flush=True)


if __name__ == "__main__":
    main()
