"""Outlook COM ingest for ITUK / GERMANY (ISD) / PORTUGAL (Imotors).

Same method as the UMI Bart pass: local win32com MAPI, Restrict + DASL,
customer-folder inventory, attachment names. Does NOT walk every item.

Hard splits:
  ITUK  = sold-to 2575, isuzutruck.co.uk, Duncan Young. NOT IUK 2574, NOT Ireland.
  GERMANY / ISD = sold-to 2516+601, Sebastian Müller / ISD folders. NOT Ireland Harris.
  PORTUGAL / Imotors = sold-to 519+92, Nuno Machado / Astara Portugal. NOT UMI.

Writes ISZE\\01_data\\90_INBOX\\_outlook_ituk_isd_imotors.json
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path

import win32com.client

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX")
JSON_OUT = OUT / "_outlook_ituk_isd_imotors.json"

PR_SMTP = "http://schemas.microsoft.com/mapi/proptag/0x39FE001E"
PR_SENDER_SMTP = "http://schemas.microsoft.com/mapi/proptag/0x5D01001F"

# --- positive keys per DB -------------------------------------------------
ITUK_POS = (
    "isuzutruck.co.uk",
    "isuzu truck uk",
    "isuzu truck (uk)",
    "sold-to 2575",
    "sold to 2575",
    "duncan young",
    "charlotte marston",
    "james.marsh@",
    "charlotte.marston@",
)
ITUK_PEOPLE_RESTRICT = [
    "[SenderName] = 'Duncan Young'",
    "[SenderName] = 'Charlotte Marston'",
    "[SenderName] = 'James Marsh'",
    "[SenderName] = 'Tim Hicks'",
    "[SenderName] = 'Stuart Beeton'",
]

ISD_POS = (
    "isuzu sales deutschland",
    "sold-to 2516",
    "sold to 2516",
    "sebastian müller",
    "sebastian muller",
    "sebastian.muller@astara",
    "thomas spenlein",
    "björn groß",
    "bjorn gross",
    "260805_isd",
)
ISD_PEOPLE_RESTRICT = [
    "[SenderName] = 'Sebastian Müller'",
    "[SenderName] = 'Sebastian Muller'",
    "[SenderName] = 'Thomas Spenlein'",
    "[SenderName] = 'Björn Groß'",
    "[SenderName] = 'Bjorn Gross'",
    "[SenderName] = 'Tomoe Baumann'",
]

PT_POS = (
    "imotors",
    "i-motors",
    "astara portugal",
    "sold-to 519",
    "sold to 519",
    "nuno machado",
    "nuno.machado",
)
PT_PEOPLE_RESTRICT = [
    "[SenderName] = 'Nuno Machado'",
]

# negatives — never classify into the three packs
IRELAND_NEG = (
    "harrisgroup.ie",
    "john cummins",
    "john.cummins",
    "isuzu ireland",
    "harris group",
    "sold-to 76",
    "sold to 76",
)
IUK_NEG = (
    "i.m. parts",
    "im parts",
    "sold-to 2574",
    "sold to 2574",
    "john lennon",
    "aaron singh",
)
UMI_NEG = (
    "umi.co.il",
    "shelly cohen",
    "netanel buchnik",
    "nadav libes",
    "sold-to 1797",
    "universal motors israel",
)
UTI_NEG = ("uti.co.il", "sold-to 1799", "shahaf rehani")

FOLDER_HINTS = (
    "ituk", "isd", "imotor", "portugal", "germany", "isuzu truck",
    "meeting minute", "astara",
)

DASL = [
    ("subj_ituk", '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%ITUK%\''),
    ("subj_isd", '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%ISD%\''),
    ("subj_imotors", '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%Imotors%\''),
    ("subj_portugal", '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%Portugal%\''),
    ("to_ituk", '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0E04001F" LIKE \'%isuzutruck.co.uk%\''),
    ("cc_ituk", '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0E03001F" LIKE \'%isuzutruck.co.uk%\''),
    ("to_nuno", '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0E04001F" LIKE \'%Nuno%\''),
    ("to_sebastian", '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0E04001F" LIKE \'%Sebastian%\''),
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
    if depth > 12:
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
        parts.append(str(mail.Body or "")[:4000])
    except Exception:
        pass
    return " ".join(parts).lower()


def has_any(blob: str, keys) -> bool:
    return any(k in blob for k in keys)


def classify(blob: str, fpath: str) -> str | None:
    """Return ITUK / GERMANY / PORTUGAL or None. Ireland/IUK/UMI never win."""
    pl = (fpath or "").lower()
    if has_any(blob, IRELAND_NEG) and not has_any(blob, ISD_POS) and "isd" not in pl:
        return None
    if has_any(blob, UMI_NEG) and not has_any(blob, PT_POS) and "portugal" not in pl and "imotor" not in pl:
        return None
    if has_any(blob, UTI_NEG):
        return None

    # Folder path is the strongest signal
    if re.search(r"[\\/](ituk|isuzu truck)([\\/]|$)", pl) or "isuzutruck" in pl:
        if not has_any(blob, IUK_NEG):
            return "ITUK"
    if re.search(r"[\\/]isd([\\/]|$)", pl) or "sales deutschland" in pl:
        return "GERMANY"
    if "portugal" in pl or "imotor" in pl:
        return "PORTUGAL"

    ituk = has_any(blob, ITUK_POS) or ("ituk" in blob and "iuk" not in blob.replace("ituk", ""))
    # IUK-only mail must not land in ITUK
    if has_any(blob, IUK_NEG) and not ituk:
        return None
    isd = has_any(blob, ISD_POS) or (re.search(r"\bisd\b", blob) and "ireland" not in blob)
    pt = has_any(blob, PT_POS) or ("portugal" in blob and "umi" not in blob)

    hits = []
    if ituk:
        hits.append("ITUK")
    if isd:
        hits.append("GERMANY")
    if pt:
        hits.append("PORTUGAL")
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        # Prefer person/domain over shared Astara parent
        if "isuzutruck.co.uk" in blob or "duncan young" in blob:
            return "ITUK"
        if "sebastian" in blob and "nuno" not in blob:
            return "GERMANY"
        if "nuno machado" in blob and "sebastian" not in blob:
            return "PORTUGAL"
        return None
    return None


def rec_of(mail, fpath: str, how: str, db: str) -> dict:
    body = ""
    try:
        body = str(mail.Body or "")[:5000]
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
    return {
        "db": db,
        "received": received,
        "from_name": str(getattr(mail, "SenderName", "") or ""),
        "from_smtp": smtp_of(mail),
        "to": str(getattr(mail, "To", "") or ""),
        "cc": str(getattr(mail, "CC", "") or ""),
        "subject": str(getattr(mail, "Subject", "") or ""),
        "folder": fpath,
        "how": how,
        "atts": atts,
        "preview": " ".join(body.split())[:1400],
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


def dasl_iter(folder, clause: str):
    try:
        items = folder.Items.Restrict(clause)
    except Exception:
        return
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
    folder_inventory = []
    target_folders = []  # (folder, path, n)
    inbox_sent = []

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
                pl = fpath.lower()
                if any(h in pl for h in FOLDER_HINTS):
                    folder_inventory.append({"path": fpath, "n": n})
                    target_folders.append((f, fpath, n))
                    log(f"  FOLDER {fpath} n={n}")
                leaf = pl.rsplit("\\", 1)[-1]
                if leaf in ("inbox", "sent items", "sent", "archive") or "inbox" in leaf:
                    inbox_sent.append((f, fpath, n))
        except Exception as e:
            log(f"STORE_FAIL {e}")

    log(f"hint_folders={len(target_folders)} inbox_sentish={len(inbox_sent)}")

    seen: set[str] = set()
    hits: list[dict] = []
    skipped = {"ireland": 0, "iuk": 0, "umi": 0, "unclassified": 0}

    def consider(mail, fpath: str, how: str) -> None:
        try:
            eid = str(getattr(mail, "EntryID", "") or "")
        except Exception:
            eid = ""
        if eid and eid in seen:
            return
        blob = blob_of(mail, extra=fpath)
        if has_any(blob, IRELAND_NEG) and not has_any(blob, ISD_POS):
            skipped["ireland"] += 1
            return
        if has_any(blob, UMI_NEG) and not has_any(blob, PT_POS):
            skipped["umi"] += 1
            return
        db = classify(blob, fpath)
        if db is None:
            skipped["unclassified"] += 1
            return
        if eid:
            seen.add(eid)
        hits.append(rec_of(mail, fpath, how, db))

    scan_folders = []
    seen_fp = set()
    for tup in target_folders + inbox_sent:
        fp = tup[1]
        if fp in seen_fp:
            continue
        seen_fp.add(fp)
        scan_folders.append(tup)

    restricts = ITUK_PEOPLE_RESTRICT + ISD_PEOPLE_RESTRICT + PT_PEOPLE_RESTRICT
    for f, fpath, n in scan_folders:
        log(f"SCAN {fpath} n={n}")
        for clause in restricts:
            for mail in restrict_iter(f, clause) or []:
                consider(mail, fpath, "restrict:" + clause)
        for tag, clause in DASL:
            for mail in dasl_iter(f, clause) or []:
                consider(mail, fpath, "dasl:" + tag)

    by_db = {"ITUK": [], "GERMANY": [], "PORTUGAL": []}
    for h in hits:
        by_db[h["db"]].append(h)
    for k in by_db:
        by_db[k].sort(key=lambda x: x.get("received") or "", reverse=True)

    minutes_atts = []
    for h in hits:
        for a in h.get("atts") or []:
            al = a.lower()
            if any(x in al for x in ("minute", "notes", "260805", "260806", "260729", "action")):
                minutes_atts.append({"db": h["db"], "file": a, "subject": h["subject"], "received": h["received"]})

    out = {
        "as_of": datetime.now().isoformat(timespec="seconds"),
        "elapsed_s": round(time.time() - t0, 1),
        "access": "local Outlook COM (win32com MAPI). Same method as UMI Bart pass.",
        "stores": stores,
        "folder_inventory": folder_inventory,
        "n_hits": len(hits),
        "n_by_db": {k: len(v) for k, v in by_db.items()},
        "skipped": skipped,
        "minutes_like_attachments": minutes_atts,
        "hits": hits,
        "hard_splits": {
            "ITUK": "sold_to 2575 · Isuzu Truck UK · not IUK 2574 · not Ireland 76",
            "GERMANY": "sold_to 2516+601 · gps_label ISD · not Ireland Harris",
            "PORTUGAL": "sold_to 519+92 · gps_label Imotors · not UMI 1797",
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    log(f"WROTE {JSON_OUT} hits={len(hits)} by_db={out['n_by_db']} skipped={skipped} {out['elapsed_s']}s")


if __name__ == "__main__":
    main()
