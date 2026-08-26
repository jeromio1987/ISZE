"""Freight/forwarder mail scan — fast subject + sender Restrict (no body index).

Subject and sender properties are cheap to substring-match server-side, so this
completes quickly even on large mailboxes. Skips non-mail system folders
(e.g. Legacy Archive Journals). Read-only. Writes JSON only.
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
OUT = ISZE / "01_data" / "90_INBOX" / "_freight_umi_uti_subject_scan.json"
SINCE_YEAR = 2021
MAX_BODY = 9000

SUBJECT_KEYS = [
    "freight", "forwarder", "forwarding", "awb", "waybill", "consolidat",
    "zaventem", "tel aviv", "shipment", "shipping", "booking", "cut-off",
    "cut off", "flight", "cargo", "courier", "dhl", "fedex", "ups", "expedite",
    "logistics", "transport", "air freight", "incoterm", "fca",
    "brussels airport", "universal trucks", "universal motors", "export",
    "customs", "delivery", "airwaybill", "air waybill",
]

SENDER_KEYS = [
    "dhl", "fedex", "ups", "tnt", "expeditors", "kuehne", "dsv", "ceva",
    "schenker", "geodis", "panalpina", "dachser", "cargo", "freight",
    "forwarding", "logistics", "airways", "courier", "expedite", "agility",
]

STRONG = [
    "air waybill", "waybill", "awb", "master awb", "house awb", "consolidat",
    "forwarder", "forwarding", "air freight", "freight forward", "zaventem",
    "brussels airport", "tel aviv", "universal trucks", "universal motors",
    "cut-off", "cut off", "cutoff", "cargo",
]
MED = [
    "freight", "shipment", "shipping", "flight", "courier", "dhl", "fedex",
    "ups", "expedite", "incoterm", "logistics", "transport", "dispatch",
    "etd", "pickup", "pick up", "collection", "booking", "fca", "umi", "uti",
]

SKIP_FOLDER_TOKENS = ("legacy archive", "sync issues", "yammer", "personmetadata",
                      "conversation history", "conversation action", "journal",
                      "deleted items", "junk email", "rss", "tasks", "notes",
                      "calendar", "contacts", "outbox", "drafts")


def _key_re(word: str) -> re.Pattern:
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


def excerpt(text_low: str, keywords: list[str]) -> str:
    pos = -1
    for w in keywords:
        i = text_low.find(w)
        if i != -1 and (pos == -1 or i < pos):
            pos = i
    if pos == -1:
        return text_low[:500]
    return text_low[max(0, pos - 200): pos + 500]


def dasl_like(prop, token):
    t = token.replace("'", "''")
    return f'"{prop}" LIKE \'%{t}%\''


def subject_filter():
    return "@SQL=(" + " OR ".join(
        dasl_like("urn:schemas:httpmail:subject", k) for k in SUBJECT_KEYS) + ")"


def sender_filter():
    props = ["urn:schemas:httpmail:fromemail", "urn:schemas:httpmail:from"]
    terms = [dasl_like(p, k) for p in props for k in SENDER_KEYS]
    return "@SQL=(" + " OR ".join(terms) + ")"


def folder_paths(store):
    paths = []

    def add(f, depth):
        try:
            n = str(f.Name or "").lower()
            if any(t in n for t in SKIP_FOLDER_TOKENS):
                return
            p = str(f.FolderPath)
        except Exception:
            return
        if p:
            paths.append(p)
        if depth <= 0:
            return
        try:
            for sub in f.Folders:
                add(sub, depth - 1)
        except Exception:
            pass

    for fid in (6, 5):
        try:
            add(store.GetDefaultFolder(fid), 3)
        except Exception:
            pass
    try:
        root = store.GetRootFolder()
        for i in range(1, root.Folders.Count + 1):
            try:
                f = root.Folders.Item(i)
                n = str(f.Name or "").lower()
                if "archive" in n or "archief" in n:
                    add(f, 2)
            except Exception:
                pass
    except Exception:
        pass
    return paths


def record(mail, strong: list[str], med: list[str]) -> dict:
    rdt = to_dt(mail.ReceivedTime)
    subj = ""
    body = ""
    try:
        subj = str(mail.Subject or "")
    except Exception:
        pass
    try:
        body = str(mail.Body or "")[:MAX_BODY]
    except Exception:
        body = ""
    to = cc = ""
    try:
        to = str(mail.To or "")
        cc = str(mail.CC or "")
    except Exception:
        pass
    atts = []
    try:
        for ai in range(1, mail.Attachments.Count + 1):
            try:
                atts.append(str(mail.Attachments.Item(ai).FileName))
            except Exception:
                pass
    except Exception:
        pass
    from_smtp = smtp_of(mail)
    try:
        folder = str(mail.Parent.FolderPath)
    except Exception:
        folder = ""
    text = f"{subj} {from_smtp} {to} {cc} {body}".lower()
    return {
        "received": rdt.isoformat(sep=" ") if rdt else "",
        "folder": folder,
        "from_name": str(getattr(mail, "SenderName", "") or ""),
        "from_smtp": from_smtp,
        "to": to,
        "cc": cc,
        "subject": subj,
        "strong": strong,
        "med": med,
        "attachments": atts,
        "excerpt": excerpt(text, strong + med),
    }


def main() -> None:
    log(f"START {datetime.now().isoformat(sep=' ', timespec='seconds')}")
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    try:
        log(f"USER {ns.CurrentUser.Name}")
    except Exception:
        pass

    sfilter = subject_filter()
    sndfilter = sender_filter()

    seen: set[str] = set()
    hits: list[dict] = []
    folders_searched = []

    for si in range(1, ns.Stores.Count + 1):
        try:
            store = ns.Stores.Item(si)
            sname = str(store.DisplayName)
        except Exception:
            continue
        for p in folder_paths(store):
            folders_searched.append(p)
            try:
                folder = ns.GetFolderFromID(store.GetDefaultFolder(6).Parent.EntryID)  # unused
            except Exception:
                pass
            # Resolve folder object from path via store default folders walk
            folder_obj = None
            try:
                # find folder by walking shallowly again
                folder_obj = _resolve(store, p)
            except Exception:
                pass
            if folder_obj is None:
                log(f"  SKIP (resolve fail) {p}")
                continue

            try:
                n_items = int(folder_obj.Items.Count)
            except Exception:
                n_items = -1

            for fltname, flt in (("subject", sfilter), ("sender", sndfilter)):
                try:
                    sub = folder_obj.Items.Restrict(flt)
                    n = int(sub.Count)
                except Exception as exc:
                    log(f"  RESTRICT_FAIL {p} {fltname}: {exc}")
                    continue
                if n == 0:
                    continue
                n = min(n, 3000)
                kept = 0
                for i in range(1, n + 1):
                    try:
                        mail = sub.Item(i)
                    except Exception:
                        continue
                    try:
                        if int(mail.Class) != 43:
                            continue
                    except Exception:
                        continue
                    eid = ""
                    try:
                        eid = str(mail.EntryID or "")
                    except Exception:
                        pass
                    if eid and eid in seen:
                        continue
                    if eid:
                        seen.add(eid)
                    try:
                        rdt = to_dt(mail.ReceivedTime)
                        if rdt and rdt.year < SINCE_YEAR:
                            continue
                    except Exception:
                        pass
                    strong, med = [], []
                    try:
                        subj = str(mail.Subject or "").lower()
                        body = str(mail.Body or "")[:MAX_BODY].lower()
                        text = f"{subj} {body}"
                        strong = [w for w, rx in STRONG_RE if rx.search(text)]
                        med = [w for w, rx in MED_RE if rx.search(text)]
                    except Exception:
                        pass
                    if eid:
                        seen.add(eid)
                    hits.append(record(mail, strong, med))
                    kept += 1
                if kept:
                    log(f"  {p} [{fltname}] {n} -> {kept} (total {len(hits)})")

        _dump(OUT, folders_searched, hits, partial=True)

    hits.sort(key=lambda h: h["received"], reverse=True)
    _dump(OUT, folders_searched, hits, partial=False)
    log(f"DONE hits={len(hits)}")
    log(f"OUT {OUT}")


def _resolve(store, path):
    """Resolve a folder path to a folder object without full-tree walk."""
    root = store.GetRootFolder()
    # path like \\Store\Inbox\Sub
    parts = path.split("\\")
    parts = [x for x in parts if x]
    # drop store name prefix
    if parts and parts[0].lower() == str(store.DisplayName).lower():
        parts = parts[1:]
    cur = root
    for name in parts:
        found = None
        try:
            for i in range(1, cur.Folders.Count + 1):
                f = cur.Folders.Item(i)
                if str(f.Name).lower() == name.lower():
                    found = f
                    break
        except Exception:
            return None
        if found is None:
            return None
        cur = found
    return cur


def _dump(out, folders_searched, hits, partial: bool) -> None:
    payload = {
        "scanned_at": datetime.now().isoformat(sep=" ", timespec="seconds"),
        "partial": partial,
        "since_year": SINCE_YEAR,
        "folders_searched": folders_searched,
        "hit_count": len(hits),
        "hits": hits,
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
