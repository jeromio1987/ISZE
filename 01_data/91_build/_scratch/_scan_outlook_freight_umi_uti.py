"""Freight/forwarder mail scan — UMI/UTI Zaventem->Tel Aviv logistics.

Goal: find any email about how Zaventem -> Tel Aviv air-freight parts shipments are
organised (forwarder, AWB consolidation, why UMI 1797 and UTI 1799 book separately).

Read-only Outlook COM (win32com). Never sends/modifies. Writes JSON only.
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import win32com.client
except ImportError:
    print("NO_WIN32COM", file=sys.stderr)
    sys.exit(2)

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ISZE / "01_data" / "90_INBOX" / "_freight_umi_uti_scan.json"
CHECKPOINT_EVERY = 100

SINCE = "01/01/2021 12:00 AM"
OL_MAIL = 43
MAX_BODY = 9000
MAX_PER_FOLDER = 60000

# Keyword groups: strong signals scored higher.
STRONG = [
    "air waybill", "waybill", "awb", "master awb", "house awb", "consolidat",
    "forwarder", "forwarding", "air freight", "freight forward", "zaventem",
    "brussels airport", "tel aviv", "universal trucks", "universal motors",
    "umi", "uti", "cut-off", "cut off", "cutoff", "booking", "cargo",
]
MED = [
    "freight", "shipment", "shipping", "flight", "courier", "dhl", "fedex",
    "ups", "expedite", "incoterm", "logistics", "transport", "forwarded",
    "dispatch", "etd", "eta", "pickup", "pick up", "collection",
]


def _key_re(word: str) -> re.Pattern:
    # word-boundary for short tokens; substring for multi-word
    if " " in word or len(word) >= 6:
        return re.compile(re.escape(word))
    return re.compile(rf"\b{re.escape(word)}\b")


STRONG_RE = [(w, _key_re(w)) for w in STRONG]
MED_RE = [(w, _key_re(w)) for w in MED]


def log(msg: str) -> None:
    print(msg.encode("ascii", "replace").decode(), flush=True)


def to_dt(rt):
    try:
        if hasattr(rt, "year"):
            return datetime(rt.year, rt.month, rt.day, rt.hour, rt.minute,
                            getattr(rt, "second", 0) or 0)
        return datetime.fromisoformat(str(rt)[:19])
    except Exception:
        return None


def smtp_of(mail) -> str:
    try:
        ae = mail.Sender
        if ae is not None:
            try:
                v = ae.PropertyAccessor.GetProperty(
                    "http://schemas.microsoft.com/mapi/proptag/0x39FE001E")
                if v:
                    return str(v).lower()
            except Exception:
                pass
        return str(getattr(mail, "SenderEmailAddress", "") or "").lower()
    except Exception:
        return str(getattr(mail, "SenderEmailAddress", "") or "").lower()


def match_keys(text_low: str):
    strong_hits = [w for w, rx in STRONG_RE if rx.search(text_low)]
    med_hits = [w for w, rx in MED_RE if rx.search(text_low)]
    return strong_hits, med_hits


def excerpt(text_low: str, keywords: list[str]) -> str:
    """Return a readable snippet around the first keyword hit."""
    pos = -1
    for w in keywords:
        i = text_low.find(w)
        if i != -1 and (pos == -1 or i < pos):
            pos = i
    if pos == -1:
        return text_low[:500]
    return text_low[max(0, pos - 200): pos + 500]


def scan_folder(folder, stats: dict, hits: list, seen: set) -> None:
    try:
        fpath = str(folder.FolderPath)
    except Exception:
        fpath = str(getattr(folder, "Name", "?"))

    try:
        items = folder.Items
        items.Sort("[ReceivedTime]", True)
        items = items.Restrict(f"[ReceivedTime] >= '{SINCE}'")
    except Exception as exc:
        log(f"  RESTRICT_FAIL {fpath}: {exc}")
        return

    scanned = 0
    for mail in items:
        scanned += 1
        if scanned > MAX_PER_FOLDER:
            break
        try:
            if int(mail.Class) != OL_MAIL:
                continue
        except Exception:
            continue

        try:
            eid = str(mail.EntryID or "")
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
            sender_name = str(mail.SenderName or "")
        except Exception:
            sender_name = ""
        from_smtp = smtp_of(mail)
        try:
            to = str(mail.To or "")
            cc = str(mail.CC or "")
        except Exception:
            to = cc = ""

        body = ""
        try:
            body = str(mail.Body or "")[:MAX_BODY]
        except Exception:
            body = ""

        text = f"{subj} {sender_name} {from_smtp} {to} {cc} {body}".lower()
        strong_hits, med_hits = match_keys(text)
        if not strong_hits and not med_hits:
            continue

        atts = []
        try:
            for ai in range(1, mail.Attachments.Count + 1):
                try:
                    atts.append(str(mail.Attachments.Item(ai).FileName))
                except Exception:
                    pass
        except Exception:
            pass

        rdt = to_dt(mail.ReceivedTime)
        hits.append({
            "received": rdt.isoformat(sep=" ") if rdt else "",
            "folder": fpath,
            "from_name": sender_name,
            "from_smtp": from_smtp,
            "to": to,
            "cc": cc,
            "subject": subj,
            "strong": strong_hits,
            "med": med_hits,
            "attachments": atts,
            "excerpt": excerpt(text, strong_hits + med_hits),
        })
        stats["hits"] += 1

    stats["scanned"] += scanned
    stats["folders"] += 1
    log(f"  {fpath}: scanned={scanned} total_hits={stats['hits']}")


def walk_folders(folder, acc: list, depth: int = 0) -> None:
    if depth > 20:
        return
    acc.append(folder)
    try:
        for sub in folder.Folders:
            walk_folders(sub, acc, depth + 1)
    except Exception:
        pass


def main() -> None:
    log(f"START {datetime.now().isoformat(sep=' ', timespec='seconds')}")
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")

    try:
        log(f"USER {ns.CurrentUser.Name}")
    except Exception:
        pass

    stats = {"scanned": 0, "folders": 0, "hits": 0}
    hits: list[dict] = []
    seen: set[str] = set()
    store_names = []

    def checkpoint() -> None:
        payload = {
            "scan_started": datetime.now().isoformat(sep=" ", timespec="seconds"),
            "note": "partial checkpoint",
            "stats": stats,
            "stores_seen": store_names,
            "hit_count": len(hits),
            "hits": hits,
        }
        OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    for si in range(1, ns.Stores.Count + 1):
        try:
            store = ns.Stores.Item(si)
            sname = str(store.DisplayName)
        except Exception as exc:
            log(f"STORE_ITEM_FAIL {si}: {exc}")
            continue
        store_names.append(sname)
        log(f"STORE {sname}")
        try:
            root = store.GetRootFolder()
        except Exception as exc:
            log(f"  ROOT_FAIL {sname}: {exc}")
            continue

        folders: list = []
        walk_folders(root, folders)

        for folder in folders:
            try:
                scan_folder(folder, stats, hits, seen)
            except Exception as exc:
                log(f"  FOLDER_FAIL {folder}: {exc}")

        checkpoint()

    hits.sort(key=lambda h: h["received"], reverse=True)
    payload = {
        "scan_started": datetime.now().isoformat(sep=" ", timespec="seconds"),
        "since": SINCE,
        "stats": stats,
        "stores_seen": store_names,
        "hit_count": len(hits),
        "hits": hits,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"DONE scanned={stats['scanned']} folders={stats['folders']} hits={len(hits)}")
    log(f"OUT {OUT}")


if __name__ == "__main__":
    main()
