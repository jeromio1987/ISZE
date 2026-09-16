"""Pass 3: quoted AdvancedSearch + Instant Search + open UTI archive. Never Send."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pythoncom
import win32com.client

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_DIR = ISZE / r"01_data\90_INBOX\UTI_PartSales_mail_sap4_20260813"
META = ISZE / r"01_data\90_INBOX\outlook_uti_sap4_scan_pass3_20260813.json"
KEEP_EXT = (".xlsx", ".xls", ".xlsm", ".csv")
OL_MAIL = 43
EXACT = ("sap4@uti.co.il", "sap4u@uti.co.il", "sap4uti@uti.co.il")


def _p(msg: str) -> None:
    print(msg.encode("ascii", "replace").decode(), flush=True)


def smtp_of(mail) -> str:
    addr = ""
    try:
        addr = str(mail.SenderEmailAddress or "")
    except Exception:
        pass
    try:
        sender = mail.Sender
        if sender:
            try:
                eu = sender.GetExchangeUser()
                if eu and eu.PrimarySmtpAddress:
                    addr = str(eu.PrimarySmtpAddress)
            except Exception:
                pass
    except Exception:
        pass
    return (addr or "").strip()


def is_keep(from_addr: str, sender: str, subj: str) -> bool:
    blob = f"{from_addr} {sender} {subj}".lower()
    fa = (from_addr or "").lower()
    if fa in EXACT:
        return True
    if "sap4" in fa and "@uti.co.il" in fa:
        return True
    if "sap4" in blob and "uti.co.il" in blob:
        return True
    return False


def unique_dest(path: Path) -> Path:
    if not path.exists():
        return path
    n = 2
    while True:
        cand = path.with_name(f"{path.stem}_{n}{path.suffix}")
        if not cand.exists():
            return cand
        n += 1


def save_mail(mail, fpath: str, seen: set[str], hits: list, saved: list) -> None:
    try:
        if int(mail.Class) != OL_MAIL:
            return
    except Exception:
        return
    try:
        eid = str(mail.EntryID)
    except Exception:
        eid = ""
    if eid and eid in seen:
        return
    if eid:
        seen.add(eid)
    try:
        subj = str(mail.Subject or "")
    except Exception:
        subj = ""
    try:
        recv = str(mail.ReceivedTime)
    except Exception:
        recv = ""
    sender = ""
    try:
        sender = str(mail.SenderName or "")
    except Exception:
        pass
    from_addr = smtp_of(mail)
    if not is_keep(from_addr, sender, subj):
        return
    atts = []
    saved_here = []
    try:
        ac = mail.Attachments.Count
    except Exception:
        ac = 0
    for i in range(1, ac + 1):
        try:
            att = mail.Attachments.Item(i)
            an = str(att.FileName)
            atts.append(an)
            low = an.lower()
            if not low.endswith(KEEP_EXT):
                continue
            if "partsales" not in low and "utipartsales" not in subj.lower():
                continue
            stamp = recv[:10] if recv else "nodate"
            dest = unique_dest(OUT_DIR / f"{stamp}_{an}")
            att.SaveAsFile(str(dest))
            saved_here.append(str(dest))
            saved.append(str(dest))
            _p(f"SAVED {dest}")
        except Exception as e:
            saved_here.append(f"ERR:{e}")
    hits.append(
        {
            "folder": fpath,
            "received": recv,
            "subject": subj,
            "sender": sender,
            "from_addr": from_addr,
            "attachments": atts,
            "saved": saved_here,
        }
    )
    _p(f"HIT {recv[:19]} | {from_addr} | {subj[:90]}")


def walk_folders(folder, acc: list, depth: int = 0) -> None:
    if depth > 18:
        return
    acc.append(folder)
    try:
        for sub in folder.Folders:
            walk_folders(sub, acc, depth + 1)
    except Exception:
        pass


def wait_search(search, seconds: int = 40) -> int:
    deadline = time.time() + seconds
    last = -1
    while time.time() < deadline:
        pythoncom.PumpWaitingMessages()
        time.sleep(1)
        try:
            c = int(search.Results.Count)
        except Exception:
            c = -1
        if c != last:
            _p(f"  results={c}")
            last = c
        # Instant Search often fills in the first few seconds then stalls.
        if c > 0 and time.time() > deadline - seconds + 8:
            # keep draining a bit after first hits
            if time.time() > deadline - seconds + 15:
                break
    try:
        return int(search.Results.Count)
    except Exception:
        return last if last >= 0 else 0


def adv(ol, scope: str, filt: str, tag: str, seen, hits, saved, notes: list) -> None:
    try:
        search = ol.AdvancedSearch(scope, filt, True, tag)
    except Exception as e:
        notes.append({"scope": scope, "filt": filt, "err": str(e)})
        _p(f"ADV FAIL {scope} {e}")
        return
    _p(f"ADV {scope} {filt[:70]}")
    c = wait_search(search, 35)
    notes.append({"scope": scope, "filt": filt, "count": c})
    _p(f"ADV done count={c}")
    try:
        results = search.Results
        n = int(results.Count)
    except Exception as e:
        notes.append({"scope": scope, "filt": filt, "read_err": str(e)})
        return
    for j in range(1, n + 1):
        try:
            save_mail(results.Item(j), f"ADV:{scope}", seen, hits, saved)
        except Exception as e:
            _p(f"  result {j} err {e}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    seen: set[str] = set()
    hits: list = []
    saved: list = []
    notes: list = []

    folders = []
    for i in range(1, ns.Stores.Count + 1):
        try:
            walk_folders(ns.Stores.Item(i).GetRootFolder(), folders)
        except Exception:
            pass

    # Open online-stub UTI archive folders in Explorer so cached mode may hydrate.
    hydrate = []
    for folder in folders:
        try:
            fpath = str(folder.FolderPath)
        except Exception:
            continue
        fl = fpath.lower()
        if "archive" in fl and ("uti" in fl or "umi" in fl):
            hydrate.append(folder)
    _p(f"HYDRATE folders {len(hydrate)}")
    try:
        expl = ol.ActiveExplorer()
        if expl is None:
            ns.GetDefaultFolder(6).Display()
            expl = ol.ActiveExplorer()
    except Exception as e:
        expl = None
        _p(f"NO EXPLORER {e}")
    for folder in hydrate:
        try:
            fpath = str(folder.FolderPath)
            n0 = int(folder.Items.Count)
        except Exception:
            continue
        _p(f"OPEN {fpath} before={n0}")
        if expl is not None:
            try:
                expl.CurrentFolder = folder
            except Exception as e:
                _p(f"  set folder fail {e}")
        pythoncom.PumpWaitingMessages()
        time.sleep(3)
        pythoncom.PumpWaitingMessages()
        try:
            n1 = int(folder.Items.Count)
        except Exception:
            n1 = -1
        _p(f"  after={n1}")
        notes.append({"hydrate": fpath, "before": n0, "after": n1})
        if n1 > 0:
            items = folder.Items
            for i in range(1, n1 + 1):
                try:
                    save_mail(items.Item(i), fpath, seen, hits, saved)
                except Exception:
                    continue

    # Quoted AdvancedSearch scopes (Inbox / Sent / Deleted / Archive).
    scopes = []
    inbox = ns.GetDefaultFolder(6)
    sent = ns.GetDefaultFolder(5)
    deleted = ns.GetDefaultFolder(3)
    for fld in (inbox, sent, deleted):
        scopes.append("'" + str(fld.FolderPath) + "'")
    for folder in folders:
        try:
            fpath = str(folder.FolderPath)
        except Exception:
            continue
        if fpath.lower().endswith("\\archive") and fpath.count("\\") <= 3:
            scopes.append("'" + fpath + "'")
    # Whole mailbox (quoted store root).
    try:
        scopes.append("'" + str(inbox.Parent.FolderPath) + "'")
    except Exception:
        pass
    # Unique preserve order
    seen_scope = []
    for s in scopes:
        if s not in seen_scope:
            seen_scope.append(s)
    scopes = seen_scope
    _p(f"SCOPES {scopes}")

    filters = [
        '"urn:schemas:httpmail:fromemail" like \'%sap4@uti.co.il%\'',
        '"urn:schemas:httpmail:fromemail" like \'%sap4%\'',
        '"urn:schemas:httpmail:from" like \'%sap4%\'',
        '"urn:schemas:httpmail:fromemail" ci_phrasematch \'sap4@uti.co.il\'',
        '"http://schemas.microsoft.com/mapi/proptag/0x0C1A001F" like \'%sap4%\'',
        '"urn:schemas:httpmail:subject" like \'%UTIPartSales%\' AND "urn:schemas:httpmail:fromemail" like \'%sap4%\'',
    ]

    tag_i = 0
    # First try Inbox-only with each filter (fastest signal), then mailbox root.
    inbox_scope = "'" + str(inbox.FolderPath) + "'"
    mailbox_scope = "'" + str(inbox.Parent.FolderPath) + "'"
    for filt in filters:
        tag_i += 1
        adv(ol, inbox_scope, filt, f"sap4in{tag_i}", seen, hits, saved, notes)
        tag_i += 1
        adv(ol, mailbox_scope, filt, f"sap4mb{tag_i}", seen, hits, saved, notes)

    # Explorer KQL search (same engine as the UI From grouping).
    kql_notes = []
    kqls = [
        "from:sap4@uti.co.il",
        "from:sap4u@uti.co.il",
        "from:sap4uti@uti.co.il",
        "from:sap4@uti.co.il OR from:sap4u@uti.co.il OR from:sap4uti@uti.co.il",
        "from:(sap4) received:01/01/2020..12/31/2022",
    ]
    if expl is not None:
        try:
            expl.CurrentFolder = inbox
        except Exception:
            pass
        for q in kqls:
            try:
                expl.Search(q, True)
            except Exception as e:
                kql_notes.append({"q": q, "err": str(e)})
                _p(f"KQL FAIL {q} {e}")
                continue
            _p(f"KQL {q}")
            pythoncom.PumpWaitingMessages()
            time.sleep(6)
            pythoncom.PumpWaitingMessages()
            try:
                cf = expl.CurrentFolder
                fpath = str(cf.FolderPath)
                n = int(cf.Items.Count)
            except Exception as e:
                kql_notes.append({"q": q, "after_err": str(e)})
                continue
            _p(f"  current={fpath} n={n}")
            kql_notes.append({"q": q, "folder": fpath, "n": n})
            # Search view may not change CurrentFolder; still scan Inbox Restrict after.
            if n and n < 5000:
                items = cf.Items
                for i in range(1, min(n, 400) + 1):
                    try:
                        save_mail(items.Item(i), f"KQL:{q}", seen, hits, saved)
                    except Exception:
                        continue

    payload = {
        "scan_date": "2026-08-13",
        "never_send": True,
        "pass": 3,
        "hit_count": len(hits),
        "saved_count": len(saved),
        "saved": saved,
        "hits": hits,
        "advanced_search": notes,
        "kql": kql_notes,
    }
    META.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    _p(f"DONE hits {len(hits)} saved {len(saved)} meta {META}")


if __name__ == "__main__":
    main()
