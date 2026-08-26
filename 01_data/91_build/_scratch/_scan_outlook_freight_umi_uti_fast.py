"""Freight/forwarder mail scan (fast, DASL body/subject restrict) — UMI/UTI Zaventem->Tel Aviv.

Server-side substring search via Outlook Restrict on subject + plain-text body +
HTML body, across all stores. Read-only. Writes JSON only.
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
OL_MAIL = 43
SINCE_YEAR = 2021
MAX_BODY = 9000
PER_KEYWORD_CAP = 4000

# High-precision keywords for the server-side body/subject Restrict.
DASL_KEYS = [
    "awb", "waybill", "forwarder", "forwarding", "consolidat", "zaventem",
    "air freight", "tel aviv", "universal trucks", "universal motors",
    "air waybill", "house airway", "freight forward", "incoterm",
]

# Props searched server-side.
BODY_PROPS = [
    ("urn:schemas:httpmail:subject", "subject"),
    ("urn:schemas:httpmail:textdescription", "body"),
    ("urn:schemas:httpmail:htmldescription", "html"),
    ("urn:schemas:httpmail:fromemail", "from"),
    ("urn:schemas:httpmail:from", "fromname"),
]

# Full keyword list used client-side to label + keep a hit.
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


def dasl_like(prop: str, token: str) -> str:
    t = token.replace("'", "''")
    return f'"{prop}" LIKE \'%{t}%\''


def excerpt(text_low: str, keywords: list[str]) -> str:
    pos = -1
    for w in keywords:
        i = text_low.find(w)
        if i != -1 and (pos == -1 or i < pos):
            pos = i
    if pos == -1:
        return text_low[:500]
    return text_low[max(0, pos - 200): pos + 500]


def walk_folders(folder, acc: list, depth: int = 0) -> None:
    if depth > 20:
        return
    acc.append(folder)
    try:
        for sub in folder.Folders:
            walk_folders(sub, acc, depth + 1)
    except Exception:
        pass


def record(mail, fpath: str, strong: list[str], med: list[str]) -> dict:
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
    text = f"{subj} {from_smtp} {to} {cc} {body}".lower()
    return {
        "received": rdt.isoformat(sep=" ") if rdt else "",
        "folder": fpath,
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
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")

    try:
        log(f"USER {ns.CurrentUser.Name}")
    except Exception:
        pass

    seen: set[str] = set()
    hits: list[dict] = []
    store_names = []
    folder_inventory = []

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
        log(f"  folders: {len(folders)}")

        for folder in folders:
            try:
                fpath = str(folder.FolderPath)
            except Exception:
                fpath = str(getattr(folder, "Name", "?"))
            try:
                n_items = int(folder.Items.Count)
            except Exception:
                n_items = -1
            folder_inventory.append({"folder": fpath, "items": n_items})

            for key in DASL_KEYS:
                clause = " OR ".join(dasl_like(p, key) for p, _ in BODY_PROPS)
                filt = f"@SQL=({clause})"
                try:
                    sub = folder.Items.Restrict(filt)
                except Exception:
                    continue
                try:
                    n = int(sub.Count)
                except Exception:
                    n = 0
                if n == 0:
                    continue
                if n > PER_KEYWORD_CAP:
                    n = PER_KEYWORD_CAP
                for i in range(1, n + 1):
                    try:
                        mail = sub.Item(i)
                    except Exception:
                        continue
                    try:
                        if int(mail.Class) != OL_MAIL:
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
                    if not strong and not med:
                        continue
                    if eid:
                        seen.add(eid)
                    hits.append(record(mail, fpath, strong, med))

            log(f"  {fpath}: total_hits={len(hits)}")

        # checkpoint per store
        _dump(OUT, store_names, folder_inventory, hits, partial=True)

    hits.sort(key=lambda h: h["received"], reverse=True)
    _dump(OUT, store_names, folder_inventory, hits, partial=False)
    log(f"DONE hits={len(hits)}")
    log(f"OUT {OUT}")


def _dump(out, store_names, folder_inventory, hits, partial: bool) -> None:
    payload = {
        "scanned_at": datetime.now().isoformat(sep=" ", timespec="seconds"),
        "partial": partial,
        "since_year": SINCE_YEAR,
        "stores_seen": store_names,
        "folder_count": len(folder_inventory),
        "folders": folder_inventory,
        "hit_count": len(hits),
        "hits": hits,
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
