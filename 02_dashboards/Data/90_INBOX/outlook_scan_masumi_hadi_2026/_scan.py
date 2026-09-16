#!/usr/bin/env python3
"""Fast Outlook scan: Masumi + Hadi, calendar year 2026 (from + involving)."""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import win32com.client
except ImportError:
    print("NO_WIN32COM", file=sys.stderr)
    sys.exit(2)

OUT_DIR = Path(__file__).resolve().parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

CUTOFF = datetime(2026, 1, 1)
DATE_FILTER = "[ReceivedTime] >= '01/01/2026 12:00 AM'"

# Exact SenderName strings commonly used by Outlook + SMTP fragments
SENDER_QUERIES = [
    ("masumi", "[SenderName] = 'Masumi Hayakawa'"),
    ("hadi", "[SenderName] = 'Hadewijch Tibos'"),
]

NAME_KEYS = {
    "masumi": ["masumi.hayakawa", "masumi hayakawa"],
    "hadi": ["hadewijch.tibos", "hadewijch tibos"],
}


def log(msg: str) -> None:
    print(msg, flush=True)


def to_dt(rt) -> datetime | None:
    try:
        if hasattr(rt, "year"):
            return datetime(
                rt.year,
                rt.month,
                rt.day,
                rt.hour,
                rt.minute,
                getattr(rt, "second", 0) or 0,
            )
        return datetime.fromisoformat(str(rt)[:19])
    except Exception:
        return None


def smtp_of(mail) -> str:
    try:
        ae = mail.Sender
        if ae is not None:
            try:
                v = ae.PropertyAccessor.GetProperty(
                    "http://schemas.microsoft.com/mapi/proptag/0x39FE001E"
                )
                if v:
                    return str(v).lower()
            except Exception:
                pass
        return str(getattr(mail, "SenderEmailAddress", "") or "").lower()
    except Exception:
        return str(getattr(mail, "SenderEmailAddress", "") or "").lower()


def who_match(text: str) -> list[str]:
    t = (text or "").lower()
    return [pid for pid, keys in NAME_KEYS.items() if any(k in t for k in keys)]


def recipients_blob(mail) -> str:
    parts: list[str] = []
    try:
        parts.append(str(mail.To or ""))
        parts.append(str(mail.CC or ""))
    except Exception:
        pass
    return " ".join(parts).lower()


def mail_record(mail, fpath: str, from_people: list[str], to_people: list[str]) -> dict:
    rdt = to_dt(mail.ReceivedTime) or CUTOFF
    body = ""
    try:
        body = str(mail.Body or "")[:4000]
    except Exception:
        body = ""
    att_names = []
    try:
        for ai in range(1, mail.Attachments.Count + 1):
            try:
                att_names.append(str(mail.Attachments.Item(ai).FileName))
            except Exception:
                pass
    except Exception:
        pass
    entry_id = str(getattr(mail, "EntryID", "") or "")
    return {
        "received": rdt.isoformat(sep=" "),
        "folder": fpath,
        "from_name": str(getattr(mail, "SenderName", "") or ""),
        "from_smtp": smtp_of(mail),
        "to": str(getattr(mail, "To", "") or ""),
        "cc": str(getattr(mail, "CC", "") or ""),
        "subject": str(getattr(mail, "Subject", "") or ""),
        "from_people": from_people,
        "to_cc_people": to_people,
        "unread": bool(getattr(mail, "UnRead", False)),
        "flag": int(getattr(mail, "FlagStatus", 0) or 0),
        "importance": int(getattr(mail, "Importance", 1) or 1),
        "attachments": att_names,
        "body_preview": body,
        "entry_id": entry_id[:80],
    }


def default_folders(ns) -> list:
    """Inbox + Sent (+ Archive if present) on default store only."""
    out = []
    for fid, label in ((6, "Inbox"), (5, "Sent")):
        try:
            f = ns.GetDefaultFolder(fid)
            out.append(f)
            log(f"FOLDER {label}: {f.FolderPath}")
        except Exception as exc:
            log(f"FOLDER_MISS {label}: {exc}")
    # Common archive folder names under default store root
    try:
        root = ns.DefaultStore.GetRootFolder()
        for i in range(1, root.Folders.Count + 1):
            try:
                f = root.Folders.Item(i)
                name = (f.Name or "").lower()
                if any(x in name for x in ("archive", "archief", "online archive")):
                    out.append(f)
                    log(f"FOLDER Archive-ish: {f.FolderPath}")
            except Exception:
                pass
    except Exception as exc:
        log(f"ARCHIVE_WALK_SKIP: {exc}")
    return out


def pull_from_sender(folder, person: str, restrict_clause: str, seen: set, hits: list) -> int:
    try:
        fpath = folder.FolderPath
    except Exception:
        fpath = folder.Name
    t0 = time.time()
    try:
        # Combine date + sender for speed
        flt = f"{DATE_FILTER} AND {restrict_clause}"
        items = folder.Items.Restrict(flt)
    except Exception as exc:
        log(f"RESTRICT_FAIL {fpath} {person}: {exc}")
        return 0

    n = 0
    try:
        # Force Count evaluation (can be slow once, then iterate)
        _ = items.Count
    except Exception:
        pass

    for mail in items:
        try:
            if int(mail.Class) != 43:
                continue
        except Exception:
            continue
        entry_id = str(getattr(mail, "EntryID", "") or "")
        if entry_id and entry_id in seen:
            continue
        if entry_id:
            seen.add(entry_id)
        rec = mail_record(mail, fpath, [person], who_match(recipients_blob(mail)))
        hits.append(rec)
        n += 1
    log(f"FROM {person} @ {fpath}: {n} in {time.time()-t0:.1f}s")
    return n


def pull_involving_scan(folder, seen: set, hits: list, limit: int = 8000) -> int:
    """Date-restricted folder pass; keep if To/Cc mentions Masumi/Hadi (and not already kept as From)."""
    try:
        fpath = folder.FolderPath
    except Exception:
        fpath = folder.Name
    t0 = time.time()
    try:
        items = folder.Items
        items.Sort("[ReceivedTime]", True)
        items = items.Restrict(DATE_FILTER)
    except Exception as exc:
        log(f"INVOLVE_RESTRICT_FAIL {fpath}: {exc}")
        return 0

    added = 0
    scanned = 0
    for mail in items:
        scanned += 1
        if scanned > limit:
            break
        try:
            if int(mail.Class) != 43:
                continue
        except Exception:
            continue
        entry_id = str(getattr(mail, "EntryID", "") or "")
        if entry_id and entry_id in seen:
            continue

        sender_name = str(getattr(mail, "SenderName", "") or "")
        sender_smtp = smtp_of(mail)
        from_hits = who_match(f"{sender_name} {sender_smtp}")
        to_hits = who_match(recipients_blob(mail))
        if not from_hits and not to_hits:
            continue
        if entry_id:
            seen.add(entry_id)
        hits.append(mail_record(mail, fpath, from_hits, to_hits))
        added += 1
    log(f"INVOLVE {fpath}: scanned={scanned} added={added} in {time.time()-t0:.1f}s")
    return added


def main() -> None:
    log(f"START {datetime.now().isoformat(sep=' ', timespec='seconds')}")
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    try:
        log(f"USER {ns.CurrentUser.Name}")
    except Exception:
        pass

    folders = default_folders(ns)
    hits: list[dict] = []
    seen: set[str] = set()

    # Pass 1 — fast SenderName Restrict (From Masumi / From Hadi)
    for folder in folders:
        for person, clause in SENDER_QUERIES:
            pull_from_sender(folder, person, clause, seen, hits)

    # Pass 2 — Inbox (+ Sent lightly) for To/Cc involvement
    for folder in folders[:2]:
        pull_involving_scan(folder, seen, hits, limit=12000 if "Inbox" in (folder.Name or "") else 6000)

    hits.sort(key=lambda h: h["received"], reverse=True)

    summary = {
        "scanned_at": datetime.now().isoformat(sep=" ", timespec="seconds"),
        "year": 2026,
        "hit_count": len(hits),
        "from_masumi": sum(1 for h in hits if "masumi" in h["from_people"]),
        "from_hadi": sum(1 for h in hits if "hadi" in h["from_people"]),
        "involving_masumi": sum(
            1
            for h in hits
            if "masumi" in h["from_people"] or "masumi" in h["to_cc_people"]
        ),
        "involving_hadi": sum(
            1 for h in hits if "hadi" in h["from_people"] or "hadi" in h["to_cc_people"]
        ),
        "folders": [getattr(f, "FolderPath", str(f)) for f in folders],
    }

    (OUT_DIR / "_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT_DIR / "hits.json").write_text(
        json.dumps(hits, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    index = [
        {
            k: h[k]
            for k in (
                "received",
                "from_name",
                "from_smtp",
                "subject",
                "from_people",
                "to_cc_people",
                "folder",
                "attachments",
            )
        }
        for h in hits
    ]
    (OUT_DIR / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log("SUMMARY " + json.dumps(summary))
    log(f"OUT {OUT_DIR}")


if __name__ == "__main__":
    main()
