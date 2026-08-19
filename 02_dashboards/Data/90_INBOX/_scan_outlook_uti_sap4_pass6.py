"""Pass 6: different store / live window / subject-only / PST add. Never Send."""
from __future__ import annotations

import json
import os
import re
import time
import winreg
from datetime import datetime
from pathlib import Path

import pythoncom
import win32com.client

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_DIR = ISZE / r"01_data\90_INBOX\UTI_PartSales_mail_sap4_20260813"
META = ISZE / r"01_data\90_INBOX\outlook_uti_sap4_scan_pass6_20260813.json"
KEEP_EXT = (".xlsx", ".xls", ".xlsm", ".csv")
OL_MAIL = 43
EXACT = ("sap4@uti.co.il", "sap4u@uti.co.il", "sap4uti@uti.co.il")
SUBJ_TOKEN = "utipartsales was executed"

STORE_TYPE = {
    0: "olExchangeMailbox",
    1: "olExchangePublicFolder",
    2: "olNotExchange",
    3: "olExchangeManagedFolder",
}


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


def blob_of(mail) -> str:
    bits = []
    for attr in (
        "SenderEmailAddress",
        "SenderName",
        "SentOnBehalfOfName",
        "SenderEmailType",
    ):
        try:
            bits.append(str(getattr(mail, attr) or ""))
        except Exception:
            pass
    try:
        pa = mail.PropertyAccessor
        for tag in (
            "http://schemas.microsoft.com/mapi/proptag/0x0C1F001F",  # PR_SENDER_EMAIL_ADDRESS
            "http://schemas.microsoft.com/mapi/proptag/0x0065001F",  # PR_SENT_REPRESENTING_EMAIL
            "http://schemas.microsoft.com/mapi/proptag/0x0076001F",  # PR_RECEIVED_BY_EMAIL
            "http://schemas.microsoft.com/mapi/proptag/0x0078001F",  # PR_RECEIVED_BY_SMTP
            "http://schemas.microsoft.com/mapi/proptag/0x5D01001F",  # PR_SENDER_SMTP_ADDRESS
            "http://schemas.microsoft.com/mapi/proptag/0x5D02001F",  # PR_SENT_REPRESENTING_SMTP
        ):
            try:
                bits.append(str(pa.GetProperty(tag) or ""))
            except Exception:
                pass
    except Exception:
        pass
    return " ".join(b for b in bits if b).lower()


def is_keep(mail, subj: str) -> bool:
    fa = smtp_of(mail).lower()
    blob = blob_of(mail)
    sl = (subj or "").lower()
    if fa in EXACT:
        return True
    if "sap4" in fa and "uti.co.il" in fa:
        return True
    if "sap4" in blob and "uti" in blob:
        return True
    if SUBJ_TOKEN in sl and "sap4" in blob:
        return True
    if SUBJ_TOKEN in sl:
        rec = None
        try:
            rec = mail.ReceivedTime
        except Exception:
            pass
        if rec is not None:
            try:
                y = rec.year
                if 2020 <= y <= 2022:
                    return True
            except Exception:
                pass
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
    subj = ""
    try:
        subj = str(mail.Subject or "")
    except Exception:
        pass
    rec = None
    try:
        rec = str(mail.ReceivedTime)
    except Exception:
        pass
    fa = smtp_of(mail)
    hit = {
        "folder": fpath,
        "subject": subj,
        "received": rec,
        "from": fa,
        "sender_name": "",
        "entry_id": eid[:80],
        "attach_count": 0,
        "saved_files": [],
    }
    try:
        hit["sender_name"] = str(mail.SenderName or "")
    except Exception:
        pass
    try:
        hit["attach_count"] = int(mail.Attachments.Count)
    except Exception:
        pass
    hits.append(hit)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        atts = mail.Attachments
        n = int(atts.Count)
    except Exception:
        return
    for i in range(1, n + 1):
        try:
            att = atts.Item(i)
            name = str(att.FileName or "")
        except Exception:
            continue
        if not name.lower().endswith(KEEP_EXT):
            continue
        dest = unique_dest(OUT_DIR / re.sub(r"[^\w.\-]+", "_", name))
        try:
            att.SaveAsFile(str(dest))
        except Exception as e:
            hit["saved_files"].append({"err": str(e), "name": name})
            continue
        hit["saved_files"].append(str(dest))
        saved.append({"src": name, "dest": str(dest), "subject": subj, "received": rec, "from": fa})
        _p(f"SAVED {dest.name} from {fa} {subj[:60]}")


def list_profiles() -> dict:
    out = {"default": None, "profiles": []}
    try:
        k = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Office\16.0\Outlook",
        )
        try:
            out["default"] = winreg.QueryValueEx(k, "DefaultProfile")[0]
        except OSError:
            pass
        winreg.CloseKey(k)
    except OSError as e:
        out["outlook16_err"] = str(e)
    try:
        pk = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Office\16.0\Outlook\Profiles",
        )
        i = 0
        while True:
            try:
                name = winreg.EnumKey(pk, i)
            except OSError:
                break
            i += 1
            rec = {"name": name, "keys": []}
            try:
                sk = winreg.OpenKey(pk, name)
                j = 0
                while True:
                    try:
                        rec["keys"].append(winreg.EnumKey(sk, j))
                    except OSError:
                        break
                    j += 1
                winreg.CloseKey(sk)
            except OSError:
                pass
            out["profiles"].append(rec)
        winreg.CloseKey(pk)
    except OSError as e:
        out["profiles_err"] = str(e)
    # New Outlook preference
    for path, label in (
        (r"Software\Microsoft\Office\16.0\Outlook\Preferences", "UseNewOutlook"),
        (r"Software\Microsoft\Office\16.0\Outlook\Options\General", "PreferNewOutlook"),
    ):
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path)
            try:
                out[label] = winreg.QueryValueEx(k, label)[0]
            except OSError:
                out[label] = None
            winreg.CloseKey(k)
        except OSError:
            out[label] = None
    return out


def dump_explorers(app, seen, hits, saved) -> list:
    rows = []
    try:
        explorers = app.Explorers
        n = int(explorers.Count)
    except Exception as e:
        return [{"err": str(e)}]
    _p(f"Explorers: {n}")
    for i in range(1, n + 1):
        rec = {"index": i}
        try:
            ex = explorers.Item(i)
        except Exception as e:
            rec["err"] = str(e)
            rows.append(rec)
            continue
        try:
            rec["caption"] = str(ex.Caption)
        except Exception as e:
            rec["caption_err"] = str(e)
        try:
            cf = ex.CurrentFolder
            rec["folder"] = str(cf.FolderPath)
            rec["folder_items"] = int(cf.Items.Count)
        except Exception as e:
            rec["folder_err"] = str(e)
        try:
            rec["view"] = str(ex.CurrentView.Name)
            rec["view_class"] = int(ex.CurrentView.Class)
        except Exception as e:
            rec["view_err"] = str(e)
        try:
            rec["search"] = str(ex.Search)
        except Exception:
            pass
        try:
            sel = ex.Selection
            rec["selection_count"] = int(sel.Count)
            rec["selection"] = []
            for j in range(1, min(int(sel.Count), 40) + 1):
                try:
                    it = sel.Item(j)
                    subj = str(it.Subject or "")
                    rec["selection"].append(
                        {
                            "subject": subj[:120],
                            "class": int(it.Class),
                            "from": smtp_of(it) if int(it.Class) == OL_MAIL else "",
                        }
                    )
                    if int(it.Class) == OL_MAIL and is_keep(it, subj):
                        save_mail(it, rec.get("folder", "SELECTION"), seen, hits, saved)
                    elif int(it.Class) == OL_MAIL and (
                        "utipartsales" in subj.lower() or "sap4" in blob_of(it)
                    ):
                        save_mail(it, rec.get("folder", "SELECTION"), seen, hits, saved)
                except Exception as e:
                    rec["selection"].append({"err": str(e)})
        except Exception as e:
            rec["selection_err"] = str(e)
        rows.append(rec)
        _p(f"  EX{i} {rec.get('caption')} folder={rec.get('folder')} sel={rec.get('selection_count')}")
    return rows


def dump_accounts(ns) -> list:
    rows = []
    try:
        accs = ns.Accounts
        n = int(accs.Count)
    except Exception as e:
        return [{"err": str(e)}]
    for i in range(1, n + 1):
        rec = {"index": i}
        try:
            a = accs.Item(i)
            rec["display"] = str(a.DisplayName)
            rec["smtp"] = str(a.SmtpAddress)
            rec["user"] = str(a.UserName)
            rec["type"] = int(a.AccountType)  # 0=exchange, 1=imap, 2=pop, 3=http, 4=eas, 5=other
            try:
                rec["delivery_store"] = str(a.DeliveryStore.DisplayName)
            except Exception as e:
                rec["delivery_store_err"] = str(e)
        except Exception as e:
            rec["err"] = str(e)
        rows.append(rec)
    return rows


def dump_stores(ns) -> list:
    rows = []
    try:
        stores = ns.Stores
        n = int(stores.Count)
    except Exception as e:
        return [{"err": str(e)}]
    for i in range(1, n + 1):
        rec = {"index": i}
        try:
            s = stores.Item(i)
            rec["name"] = str(s.DisplayName)
            rec["FilePath"] = str(s.FilePath or "")
            rec["IsOpen"] = str(s.IsOpen)
            rec["IsDataFileStore"] = str(s.IsDataFileStore)
            rec["ExchangeStoreType"] = int(s.ExchangeStoreType)
            rec["ExchangeStoreTypeName"] = STORE_TYPE.get(int(s.ExchangeStoreType), "?")
            try:
                rec["root"] = str(s.GetRootFolder().FolderPath)
            except Exception as e:
                rec["root_err"] = str(e)
            try:
                rec["cached"] = bool(s.IsCachedExchange)
            except Exception:
                rec["cached"] = None
        except Exception as e:
            rec["err"] = str(e)
        rows.append(rec)
        _p(f"STORE {rec.get('name')} type={rec.get('ExchangeStoreTypeName')} path={rec.get('FilePath')}")
    return rows


def table_restrict(folder, filt: str, cap: int = 80) -> list:
    rows = []
    try:
        tbl = folder.GetTable(filt)
    except Exception as e:
        return [{"_err": str(e), "_filt": filt[:120]}]
    try:
        tbl.Columns.Add("SenderEmailAddress")
        tbl.Columns.Add("SenderName")
        tbl.Columns.Add("ReceivedTime")
        tbl.Columns.Add("Subject")
        tbl.Columns.Add("EntryID")
    except Exception:
        pass
    n = 0
    while True:
        try:
            if tbl.EndOfTable:
                break
            r = tbl.GetNextRow()
        except Exception as e:
            rows.append({"_iter_err": str(e)})
            break
        n += 1
        if n > cap:
            rows.append({"_truncated": True, "_n": n})
            break
        rec = {}
        try:
            rec["Subject"] = str(r("Subject"))
        except Exception:
            pass
        try:
            rec["SenderEmailAddress"] = str(r("SenderEmailAddress"))
        except Exception:
            pass
        try:
            rec["SenderName"] = str(r("SenderName"))
        except Exception:
            pass
        try:
            rec["ReceivedTime"] = str(r("ReceivedTime"))
        except Exception:
            pass
        try:
            rec["EntryID"] = str(r("EntryID"))[:80]
        except Exception:
            pass
        rows.append(rec)
    return rows


def walk_named(folder, want: set[str], acc: dict, depth=0):
    if depth > 16:
        return
    try:
        name = str(folder.Name).lower()
        path = str(folder.FolderPath)
    except Exception:
        return
    for w in want:
        if w in name or w in path.lower():
            try:
                acc.setdefault(w, []).append(
                    {
                        "path": path,
                        "items": int(folder.Items.Count),
                    }
                )
            except Exception as e:
                acc.setdefault(w, []).append({"path": path, "err": str(e)})
    try:
        for sub in folder.Folders:
            walk_named(sub, want, acc, depth + 1)
    except Exception:
        pass


def force_search_table(app, ns, query: str, seen, hits, saved) -> dict:
    rec = {"q": query}
    try:
        inbox = ns.GetDefaultFolder(6)
        explorer = app.ActiveExplorer()
        if explorer is None:
            rec["err"] = "no ActiveExplorer"
            return rec
        explorer.CurrentFolder = inbox
    except Exception as e:
        rec["err"] = f"nav: {e}"
        return rec
    # Force a plain table view (not Compact / conversation)
    for vname in ("Single", "Preview", "Messages", "IMAP Messages"):
        try:
            explorer.CurrentView = vname
            rec["forced_view"] = vname
            break
        except Exception:
            continue
    try:
        explorer.Search(query, 1)  # olSearchScopeAllFolders
        rec["search_issued"] = True
    except Exception as e:
        rec["search_err"] = str(e)
        return rec
    time.sleep(12)
    try:
        rec["view"] = str(explorer.CurrentView.Name)
        rec["view_class"] = int(explorer.CurrentView.Class)
        rec["filter"] = str(explorer.CurrentView.Filter or "")
    except Exception as e:
        rec["view_err"] = str(e)
    try:
        tbl = explorer.CurrentView.GetTable()
        rec["table_rows"] = 0
        rec["rows"] = []
        while not tbl.EndOfTable:
            r = tbl.GetNextRow()
            rec["table_rows"] += 1
            if rec["table_rows"] <= 30:
                rec["rows"].append(
                    {
                        "Subject": str(r("Subject") or "")[:120],
                        "EntryID": str(r("EntryID") or "")[:80],
                    }
                )
            if rec["table_rows"] > 200:
                rec["truncated"] = True
                break
    except Exception as e:
        rec["table_err"] = str(e)
    # GetEntryID from table and hydrate
    for row in rec.get("rows") or []:
        eid = row.get("EntryID")
        if not eid:
            continue
        try:
            mail = ns.GetItemFromID(eid)
            save_mail(mail, "INSTANT_SEARCH", seen, hits, saved)
        except Exception as e:
            row["hydrate_err"] = str(e)
    _p(f"SEARCH {query!r} table_rows={rec.get('table_rows')} filter={rec.get('filter')!r} err={rec.get('table_err')}")
    return rec


def add_and_scan_pst(ns, pst_path: str, seen, hits, saved) -> dict:
    rec = {"path": pst_path}
    before = set()
    try:
        for s in ns.Stores:
            before.add(str(s.DisplayName))
    except Exception:
        pass
    try:
        ns.AddStore(pst_path)
        rec["added"] = True
    except Exception as e:
        rec["add_err"] = str(e)
        return rec
    added_store = None
    try:
        for s in ns.Stores:
            if str(s.DisplayName) not in before:
                added_store = s
                rec["store_name"] = str(s.DisplayName)
                break
        if added_store is None:
            # maybe already open
            rec["already_open"] = True
            return rec
        root = added_store.GetRootFolder()
        rec["root"] = str(root.FolderPath)
        rec["root_items"] = int(root.Items.Count)
        # subject GetTable on root + first-level folders only
        rec["tables"] = {}
        folders = [root]
        try:
            for sub in root.Folders:
                folders.append(sub)
        except Exception:
            pass
        for f in folders[:40]:
            try:
                path = str(f.FolderPath)
            except Exception:
                continue
            t = table_restrict(
                f,
                "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001F\" LIKE '%UTIPartSales%'",
                cap=40,
            )
            if t and not (len(t) == 1 and "_err" in t[0] and t[0].get("_err")):
                rec["tables"][path] = t[:15]
            # hydrate keepers
            for row in t:
                eid = row.get("EntryID")
                if not eid:
                    continue
                try:
                    mail = ns.GetItemFromID(eid)
                    subj = str(mail.Subject or "")
                    if is_keep(mail, subj) or "utipartsales" in subj.lower():
                        save_mail(mail, path, seen, hits, saved)
                except Exception:
                    pass
    except Exception as e:
        rec["scan_err"] = str(e)
    finally:
        if added_store is not None:
            try:
                ns.RemoveStore(added_store.GetRootFolder())
                rec["removed"] = True
            except Exception as e:
                rec["remove_err"] = str(e)
    return rec


def main() -> None:
    pythoncom.CoInitialize()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    app = win32com.client.Dispatch("Outlook.Application")
    ns = app.GetNamespace("MAPI")
    seen: set[str] = set()
    hits: list = []
    saved: list = []
    notes: dict = {
        "never_send": True,
        "pass": 6,
        "scan_date": "2026-08-13",
        "method": "live explorers + profiles + subject GetTable + PST add + InstantSearch table view",
    }

    notes["current_user"] = None
    try:
        notes["current_user"] = str(ns.CurrentUser.Name)
        notes["current_smtp"] = str(ns.CurrentUser.Address)
    except Exception as e:
        notes["current_user_err"] = str(e)

    notes["profiles"] = list_profiles()
    notes["accounts"] = dump_accounts(ns)
    notes["stores"] = dump_stores(ns)
    notes["explorers"] = dump_explorers(app, seen, hits, saved)

    # Subject-only GetTable on default folders (no From filter)
    notes["subject_tables"] = {}
    default_ids = {
        "Inbox": 6,
        "Sent": 5,
        "Deleted": 3,
        "Drafts": 16,
        "Junk": 23,
        "Archive": 1,  # may fail
    }
    for label, fid in default_ids.items():
        try:
            f = ns.GetDefaultFolder(fid)
        except Exception as e:
            notes["subject_tables"][label] = {"err": str(e)}
            continue
        path = str(f.FolderPath)
        _p(f"GetTable subject {label} {path} items={f.Items.Count}")
        filt_subj = "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001F\" LIKE '%UTIPartSales%'"
        t1 = table_restrict(f, filt_subj, cap=60)
        filt_date = (
            "[ReceivedTime] >= '2020-01-01' AND [ReceivedTime] <= '2022-06-01'"
        )
        t2 = table_restrict(f, filt_date, cap=20)
        filt_from = "[SenderEmailAddress] = 'sap4@uti.co.il'"
        t3 = table_restrict(f, filt_from, cap=40)
        notes["subject_tables"][label] = {
            "path": path,
            "items": int(f.Items.Count),
            "uti_subj": t1[:25],
            "uti_subj_n": len([x for x in t1 if "Subject" in x]),
            "date_2020_2022_sample": t2[:8],
            "from_sap4": t3[:15],
            "from_sap4_n": len([x for x in t3 if "Subject" in x or "SenderEmailAddress" in x]),
        }
        for t in (t1, t3):
            for row in t:
                eid = row.get("EntryID")
                if not eid:
                    continue
                try:
                    mail = ns.GetItemFromID(eid)
                    subj = str(mail.Subject or "")
                    if is_keep(mail, subj):
                        save_mail(mail, path, seen, hits, saved)
                except Exception:
                    pass

    # Named folders that might be the screenshot (People / search / archive)
    notes["named_folders"] = {}
    want = {"archive", "uti", "umi", "online", "search", "journal"}
    try:
        for s in ns.Stores:
            walk_named(s.GetRootFolder(), want, notes["named_folders"])
    except Exception as e:
        notes["named_folders_err"] = str(e)

    # Instant Search with forced Table view — subject only, then from
    notes["instant"] = []
    for q in (
        "subject:\"UTIPartSales was executed\"",
        "UTIPartSales was executed",
        "from:sap4@uti.co.il",
        "sap4@uti.co.il",
    ):
        notes["instant"].append(force_search_table(app, ns, q, seen, hits, saved))

    # AdvancedSearch DASL subject-only (NOT @SQL — that was the pass2 bug)
    notes["advanced"] = []
    try:
        store_path = ns.GetDefaultFolder(6).Parent.FolderPath
        scope = f"'{store_path}'"
        filt = '"urn:schemas:httpmail:subject" like \'%UTIPartSales was executed%\''
        _p(f"AdvancedSearch scope={scope} filt={filt}")
        s = app.AdvancedSearch(scope, filt, True, "uti_pass6_subj")
        for _ in range(20):
            time.sleep(1)
            try:
                c = int(s.Results.Count)
            except Exception:
                c = -1
            if c > 0:
                break
        rec = {"scope": scope, "filt": filt, "count": int(s.Results.Count)}
        rec["sample"] = []
        for i in range(1, min(int(s.Results.Count), 25) + 1):
            try:
                mail = s.Results.Item(i)
                subj = str(mail.Subject or "")
                rec["sample"].append(
                    {
                        "subject": subj[:120],
                        "from": smtp_of(mail),
                        "received": str(mail.ReceivedTime),
                    }
                )
                if is_keep(mail, subj):
                    save_mail(mail, "ADVANCED_SUBJ", seen, hits, saved)
            except Exception as e:
                rec["sample"].append({"err": str(e)})
        notes["advanced"].append(rec)
        _p(f"AdvancedSearch count={rec['count']}")
    except Exception as e:
        notes["advanced"].append({"err": str(e)})

    # PST files passed in via env / notes file
    pst_list_path = ISZE / r"01_data\90_INBOX\_pst_ost_inventory_pass6.json"
    notes["pst_scan"] = []
    if pst_list_path.exists():
        inv = json.loads(pst_list_path.read_text(encoding="utf-8"))
        for pst in inv.get("pst", [])[:12]:
            p = pst.get("path") if isinstance(pst, dict) else pst
            if not p or not os.path.isfile(p):
                continue
            # skip tiny / obviously not mail
            try:
                sz = os.path.getsize(p)
            except OSError:
                continue
            if sz < 50_000:
                continue
            _p(f"AddStore PST {p}")
            notes["pst_scan"].append(add_and_scan_pst(ns, p, seen, hits, saved))

    notes["hit_count"] = len(hits)
    notes["saved_count"] = len(saved)
    notes["hits"] = hits
    notes["saved"] = saved
    META.write_text(json.dumps(notes, indent=2, default=str), encoding="utf-8")
    _p(f"DONE hits={len(hits)} saved={len(saved)} -> {META}")


if __name__ == "__main__":
    main()
