"""Freight/forwarder mail search via Outlook AdvancedSearch (indexed full-text).

Scopes each store's Inbox + Sent (+subfolders) + Archive by folder path.
Read-only. Checkpoints JSON per store. Writes JSON only.
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
    import pythoncom
except ImportError:
    print("NO_WIN32COM", file=sys.stderr)
    sys.exit(2)

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ISZE / "01_data" / "90_INBOX" / "_freight_umi_uti_scan.json"
SINCE_YEAR = 2021
MAX_BODY = 9000
SUB_DEPTH = 2
STORE_TIMEOUT = 300

DASL_KEYS = [
    "awb", "waybill", "forwarder", "forwarding", "consolidat", "zaventem",
    "air freight", "tel aviv", "universal trucks", "universal motors",
    "air waybill", "freight forward", "incoterm", "fca",
]
PROPS = [
    "urn:schemas:httpmail:subject",
    "urn:schemas:httpmail:textdescription",
    "urn:schemas:httpmail:htmldescription",
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


def build_filter() -> str:
    terms = []
    for kw in DASL_KEYS:
        k = kw.replace("'", "''")
        for p in PROPS:
            terms.append(f'{p} LIKE \'%{k}%\'')
    return " OR ".join(terms)


def folder_paths(store):
    """Inbox + Sent + Archive (+ bounded subfolders) as full folder paths."""
    paths = []

    def add(f, depth):
        try:
            p = str(f.FolderPath)
        except Exception:
            p = ""
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
            add(store.GetDefaultFolder(fid), SUB_DEPTH)
        except Exception:
            pass
    try:
        root = store.GetRootFolder()
        for i in range(1, root.Folders.Count + 1):
            try:
                f = root.Folders.Item(i)
                n = str(f.Name or "").lower()
                if "archive" in n or "archief" in n:
                    add(f, 1)
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


class SearchEvents:
    def __init__(self):
        self.done = {}

    def OnAdvancedSearchComplete(self, s):
        try:
            self.done[s.Tag] = s
            log(f"  COMPLETE {s.Tag}")
        except Exception as e:
            log(f"  COMPLETE_ERR {e}")

    def OnAdvancedSearchStopped(self, s):
        try:
            self.done.setdefault(s.Tag, s)
            log(f"  STOPPED {s.Tag}")
        except Exception as e:
            log(f"  STOPPED_ERR {e}")


def main() -> None:
    log(f"START {datetime.now().isoformat(sep=' ', timespec='seconds')}")
    ol = win32com.client.Dispatch("Outlook.Application")
    handler = win32com.client.WithEvents(ol, SearchEvents)
    ns = ol.GetNamespace("MAPI")
    try:
        log(f"USER {ns.CurrentUser.Name}")
    except Exception:
        pass

    filt = build_filter()
    log(f"FILTER terms={len(DASL_KEYS) * len(PROPS)}")

    seen: set[str] = set()
    hits: list[dict] = []
    store_names = []
    per_store = {}

    for si in range(1, ns.Stores.Count + 1):
        try:
            store = ns.Stores.Item(si)
            sname = str(store.DisplayName)
        except Exception as exc:
            log(f"STORE_ITEM_FAIL {si}: {exc}")
            continue
        store_names.append(sname)

        paths = folder_paths(store)
        log(f"STORE {sname}: {len(paths)} folder(s)")

        # run AdvancedSearch per folder (chunked) so a single slow folder doesn't block all
        store_hits_before = len(hits)
        for pi in range(0, len(paths), 5):
            chunk = paths[pi:pi + 5]
            scope = ", ".join("'" + p + "'" for p in chunk)
            tag = f"fs_{si}_{pi}"
            try:
                ol.AdvancedSearch(scope, filt, True, tag)
            except Exception as exc:
                log(f"  LAUNCH_FAIL {sname} chunk {pi}: {exc}")
                continue

            deadline = time.time() + STORE_TIMEOUT
            while time.time() < deadline and tag not in handler.done:
                pythoncom.PumpWaitingMessages()
                time.sleep(0.3)

            if tag not in handler.done:
                log(f"  TIMEOUT {sname} chunk {pi}")
                continue

            try:
                results = handler.done[tag].Results
                n = int(results.Count)
            except Exception as exc:
                log(f"  RESULTS_FAIL {sname} chunk {pi}: {exc}")
                continue

            kept = 0
            for r in results:
                try:
                    if int(r.Class) != 43:
                        continue
                except Exception:
                    continue
                eid = ""
                try:
                    eid = str(r.EntryID or "")
                except Exception:
                    pass
                if eid and eid in seen:
                    continue
                if eid:
                    seen.add(eid)
                try:
                    rdt = to_dt(r.ReceivedTime)
                    if rdt and rdt.year < SINCE_YEAR:
                        continue
                except Exception:
                    pass
                strong, med = [], []
                try:
                    subj = str(r.Subject or "").lower()
                    body = str(r.Body or "")[:MAX_BODY].lower()
                    text = f"{subj} {body}"
                    strong = [w for w, rx in STRONG_RE if rx.search(text)]
                    med = [w for w, rx in MED_RE if rx.search(text)]
                except Exception:
                    pass
                if not strong and not med:
                    continue
                if eid:
                    seen.add(eid)
                hits.append(record(r, strong, med))
                kept += 1
            log(f"  {sname} chunk {pi}: {n} raw -> {kept} kept (total {len(hits)})")

        per_store[sname] = len(hits) - store_hits_before
        _dump(OUT, store_names, per_store, hits, partial=True)

    hits.sort(key=lambda h: h["received"], reverse=True)
    _dump(OUT, store_names, per_store, hits, partial=False)
    log(f"DONE hits={len(hits)}")
    log(f"OUT {OUT}")


def _dump(out, store_names, per_store, hits, partial: bool) -> None:
    payload = {
        "scanned_at": datetime.now().isoformat(sep=" ", timespec="seconds"),
        "partial": partial,
        "since_year": SINCE_YEAR,
        "stores_seen": store_names,
        "per_store_kept": per_store,
        "hit_count": len(hits),
        "hits": hits,
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
