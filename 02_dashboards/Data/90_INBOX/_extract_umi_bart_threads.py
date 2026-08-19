"""Save UMI minutes PDF + pull full Bart x UMI threads. Never Send."""
from __future__ import annotations

import json
import re
from pathlib import Path

import win32com.client

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_umi_bart_minutes")
OUT.mkdir(parents=True, exist_ok=True)
JSON_OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_umi_bart_threads_full.json")

PR_SMTP = "http://schemas.microsoft.com/mapi/proptag/0x39FE001E"

SUBJECTS = [
    "Meeting minutes 27/10 (ISZE - UMI)",
    "Parts training ISZE",
    "VIN number Israel",
    "israel UIO",
    "Service provider - Repair and maintenance",
]


def log(m):
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
    except Exception:
        pass
    return str(getattr(mail, "SenderEmailAddress", "") or "").lower()


def walk(folder, depth=0):
    yield folder
    if depth > 6:
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


def save_atts(mail, tag: str) -> list[str]:
    saved = []
    try:
        n = mail.Attachments.Count
    except Exception:
        return saved
    for i in range(1, n + 1):
        try:
            att = mail.Attachments.Item(i)
            name = str(att.FileName)
            low = name.lower()
            if low.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
                continue
            safe = re.sub(r"[^\w.\-]+", "_", name)
            path = OUT / f"{tag}_{safe}"
            if path.exists():
                continue
            att.SaveAsFile(str(path))
            saved.append(str(path))
            log(f"SAVED {path}")
        except Exception as e:
            log(f"att fail {e}")
    return saved


def main():
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    folders = []
    for fid in (6, 5):
        try:
            folders.append(ns.GetDefaultFolder(fid))
        except Exception:
            pass
    for s in ns.Stores:
        try:
            name = str(s.DisplayName)
            if name.lower() in ("sales", "parts") or "jerome" in name.lower():
                root = s.GetRootFolder()
                for f in walk(root):
                    try:
                        fp = str(f.FolderPath).lower()
                        n = int(f.Items.Count)
                    except Exception:
                        continue
                    if n <= 0:
                        continue
                    if any(x in fp for x in ("inbox", "sent", "archive", "veh customer")):
                        folders.append(f)
        except Exception:
            pass
    uniq = {}
    for f in folders:
        try:
            uniq[str(f.FolderPath)] = f
        except Exception:
            pass
    log(f"folders {len(uniq)}")

    seen = set()
    hits = []
    for fpath, folder in uniq.items():
        for subj in SUBJECTS:
            clause = f"@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001F\" LIKE '%{subj.replace(chr(39), '')}%'"
            try:
                items = folder.Items.Restrict(clause)
            except Exception as e:
                log(f"restrict fail {fpath} {subj}: {e}")
                continue
            n = 0
            for mail in items:
                try:
                    if int(mail.Class) != 43:
                        continue
                except Exception:
                    continue
                n += 1
                if n > 30:
                    break
                eid = str(getattr(mail, "EntryID", "") or "")
                if eid and eid in seen:
                    continue
                if eid:
                    seen.add(eid)
                body = ""
                try:
                    body = str(mail.Body or "")[:20000]
                except Exception:
                    body = ""
                stamp = str(getattr(mail, "ReceivedTime", "") or "")[:10]
                tag = re.sub(r"[^\w]+", "_", subj)[:40] + "_" + stamp
                saved = save_atts(mail, tag)
                rec = {
                    "received": str(getattr(mail, "ReceivedTime", "") or "")[:19],
                    "from_name": str(getattr(mail, "SenderName", "") or ""),
                    "from_smtp": smtp_of(mail),
                    "to": str(getattr(mail, "To", "") or ""),
                    "cc": str(getattr(mail, "CC", "") or ""),
                    "subject": str(getattr(mail, "Subject", "") or ""),
                    "folder": fpath,
                    "atts": [str(mail.Attachments.Item(i).FileName) for i in range(1, mail.Attachments.Count + 1)]
                    if mail.Attachments.Count
                    else [],
                    "saved": saved,
                    "body": body,
                }
                hits.append(rec)
                log(f"HIT {rec['received']} | {rec['subject'][:80]} | atts={rec['atts']}")
            if n:
                log(f"{fpath} / {subj}: {n}")

    JSON_OUT.write_text(json.dumps({"n": len(hits), "hits": hits}, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"DONE n={len(hits)} -> {JSON_OUT}")


if __name__ == "__main__":
    main()
