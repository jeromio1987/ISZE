"""Pass 4: filtered TableView.GetTable after KQL + PR_CONTENT_COUNT. Never Send."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pythoncom
import win32com.client

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_DIR = ISZE / r"01_data\90_INBOX\UTI_PartSales_mail_sap4_20260813"
META = ISZE / r"01_data\90_INBOX\outlook_uti_sap4_scan_pass4_20260813.json"
KEEP_EXT = (".xlsx", ".xls", ".xlsm", ".csv")
OL_MAIL = 43
PR_CONTENT_COUNT = "http://schemas.microsoft.com/mapi/proptag/0x36020003"
PR_ASSOC_CONTENT_COUNT = "http://schemas.microsoft.com/mapi/proptag/0x36170003"
PR_FOLDER_CHILD_COUNT = "http://schemas.microsoft.com/mapi/proptag/0x36030003"


def _p(msg: str) -> None:
    print(msg.encode("ascii", "replace").decode(), flush=True)


def prop(obj, schema: str):
    try:
        return obj.PropertyAccessor.GetProperty(schema)
    except Exception as e:
        return f"ERR:{e}"


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
    atts = []
    saved_here = []
    blob = f"{from_addr} {sender} {subj}".lower()
    keep = (
        from_addr.lower() in {
            "sap4@uti.co.il",
            "sap4u@uti.co.il",
            "sap4uti@uti.co.il",
        }
        or ("sap4" in blob and "uti.co.il" in blob)
        or ("utipartsales" in blob and "sap4" in blob)
    )
    if not keep:
        return
    try:
        ac = mail.Attachments.Count
    except Exception:
        ac = 0
    for i in range(1, ac + 1):
        try:
            att = mail.Attachments.Item(i)
            an = str(att.FileName)
            atts.append(an)
            if not an.lower().endswith(KEEP_EXT):
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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    seen: set[str] = set()
    hits: list = []
    saved: list = []
    notes: dict = {}

    # Top-level Folders collection (may include Online Archive as a root).
    top = []
    try:
        for i in range(1, ns.Folders.Count + 1):
            f = ns.Folders.Item(i)
            try:
                n = int(f.Items.Count)
            except Exception:
                n = -1
            top.append(
                {
                    "name": str(f.Name),
                    "path": str(f.FolderPath),
                    "items": n,
                    "pr_content": str(prop(f, PR_CONTENT_COUNT)),
                }
            )
            _p(f"ROOT {f.FolderPath} items={n} pr={top[-1]['pr_content']}")
    except Exception as e:
        notes["folders_err"] = str(e)
    notes["top_folders"] = top

    folders = []
    for i in range(1, ns.Stores.Count + 1):
        try:
            walk_folders(ns.Stores.Item(i).GetRootFolder(), folders)
        except Exception:
            pass

    # PR_CONTENT_COUNT for Archive / UTI folders (server count vs local Items.Count).
    counts = []
    for folder in folders:
        try:
            fpath = str(folder.FolderPath)
        except Exception:
            continue
        fl = fpath.lower()
        if not ("archive" in fl or "uti" in fl or "search" in fl):
            continue
        try:
            n = int(folder.Items.Count)
        except Exception:
            n = -1
        pr = prop(folder, PR_CONTENT_COUNT)
        child = prop(folder, PR_FOLDER_CHILD_COUNT)
        rec = {
            "path": fpath,
            "items": n,
            "pr_content_count": str(pr),
            "pr_child": str(child),
        }
        counts.append(rec)
        interesting = False
        try:
            interesting = int(pr) > 0 and n == 0
        except Exception:
            interesting = "ERR" not in str(pr) and n == 0
        if interesting or (n > 0 and "archive" in fl and fpath.count("\\") <= 4) or "uti" in fl:
            _p(f"COUNT {fpath} items={n} pr={pr}")
    notes["folder_counts"] = counts

    # Search folders
    sf_notes = []
    for i in range(1, ns.Stores.Count + 1):
        store = ns.Stores.Item(i)
        try:
            sfs = store.GetSearchFolders()
            for j in range(1, sfs.Count + 1):
                sf = sfs.Item(j)
                try:
                    n = int(sf.Items.Count)
                except Exception:
                    n = -1
                name = str(sf.Name)
                sf_notes.append({"store": str(store.DisplayName), "name": name, "n": n})
                _p(f"SEARCHFOLDER {store.DisplayName} {name} n={n}")
                if n > 0 and n < 5000 and (
                    "sap4" in name.lower() or "uti" in name.lower() or "part" in name.lower()
                ):
                    for k in range(1, n + 1):
                        try:
                            save_mail(sf.Items.Item(k), f"SF:{name}", seen, hits, saved)
                        except Exception:
                            continue
        except Exception as e:
            sf_notes.append({"store": str(store.DisplayName), "err": str(e)})
    notes["search_folders"] = sf_notes

    # KQL + TableView.GetTable (respects Instant Search filter).
    kql_notes = []
    try:
        expl = ol.ActiveExplorer()
        if expl is None:
            ns.GetDefaultFolder(6).Display()
            expl = ol.ActiveExplorer()
        inbox = ns.GetDefaultFolder(6)
        expl.CurrentFolder = inbox
    except Exception as e:
        expl = None
        kql_notes.append({"err": str(e)})
        _p(f"NO EXPLORER {e}")

    kqls = [
        "from:sap4@uti.co.il",
        "from:sap4u@uti.co.il",
        "from:sap4uti@uti.co.il",
        "from:sap4",
        "from:(sap4@uti.co.il OR sap4u@uti.co.il OR sap4uti@uti.co.il)",
        "subject:UTIPartSales from:sap4",
        "received:01/01/2020..31/12/2022 subject:UTIPartSales",
    ]
    if expl is not None:
        for q in kqls:
            try:
                expl.Search(q, True)
            except Exception as e:
                kql_notes.append({"q": q, "search_err": str(e)})
                _p(f"KQL FAIL {q} {e}")
                continue
            pythoncom.PumpWaitingMessages()
            time.sleep(5)
            pythoncom.PumpWaitingMessages()
            rec = {"q": q}
            try:
                view = expl.CurrentView
                rec["view"] = str(view.Name)
                rec["view_class"] = int(view.Class)
                try:
                    rec["view_filter"] = str(view.Filter)
                except Exception as e:
                    rec["view_filter"] = str(e)
            except Exception as e:
                rec["view_err"] = str(e)
                view = None
            ntab = None
            if view is not None:
                try:
                    table = view.GetTable()
                    ntab = int(table.GetRowCount())
                    rec["table_rows"] = ntab
                    _p(f"KQL {q} table={ntab} view={rec.get('view')}")
                    # Pull EntryIDs from table then GetItemFromID
                    cols = []
                    try:
                        for c in range(1, table.Columns.Count + 1):
                            cols.append(str(table.Columns.Item(c).Name))
                    except Exception:
                        pass
                    rec["columns"] = cols
                    table.MoveToStart()
                    pulled = 0
                    while True:
                        try:
                            if table.EndOfTable:
                                break
                        except Exception:
                            break
                        try:
                            row = table.GetNextRow()
                        except Exception:
                            break
                        eid = None
                        for key in ("EntryID", "Entry ID", "PR_ENTRYID"):
                            try:
                                eid = row(key)
                                if eid:
                                    break
                            except Exception:
                                continue
                        if not eid:
                            try:
                                eid = row("EntryID")
                            except Exception:
                                eid = None
                        if eid:
                            try:
                                mail = ns.GetItemFromID(eid)
                                save_mail(mail, f"KQLTABLE:{q}", seen, hits, saved)
                                pulled += 1
                            except Exception as e:
                                rec.setdefault("get_err", []).append(str(e)[:120])
                    rec["pulled"] = pulled
                except Exception as e:
                    rec["table_err"] = str(e)
                    _p(f"KQL {q} table_err {e}")
            kql_notes.append(rec)

    notes["kql"] = kql_notes
    payload = {
        "scan_date": "2026-08-13",
        "never_send": True,
        "pass": 4,
        "hit_count": len(hits),
        "saved_count": len(saved),
        "saved": saved,
        "hits": hits,
        "notes": notes,
    }
    META.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    _p(f"DONE hits {len(hits)} saved {len(saved)} meta {META}")


if __name__ == "__main__":
    main()
