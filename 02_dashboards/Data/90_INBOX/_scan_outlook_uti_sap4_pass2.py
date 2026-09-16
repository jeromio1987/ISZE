"""Pass 2: AdvancedSearch + brute Archive + Jet Restrict. Never Send."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pythoncom
import win32com.client

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_DIR = ISZE / r"01_data\90_INBOX\UTI_PartSales_mail_sap4_20260813"
META = ISZE / r"01_data\90_INBOX\outlook_uti_sap4_scan_pass2_20260813.json"
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


def blob_of(mail, from_addr: str, sender: str) -> str:
    bits = [from_addr, sender]
    try:
        bits.append(str(mail.SentOnBehalfOfName or ""))
    except Exception:
        pass
    return " ".join(b for b in bits if b).lower()


def is_keep(from_addr: str, blob: str, subj: str) -> bool:
    fa = (from_addr or "").lower()
    if fa in EXACT:
        return True
    if "sap4" in fa and "@uti.co.il" in fa:
        return True
    if "sap4" in blob and "uti.co.il" in blob:
        return True
    if "utipartsales" in (subj or "").lower() and "sap4" in blob:
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
    blob = blob_of(mail, from_addr, sender)
    if not is_keep(from_addr, blob, subj):
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
            if "partsales" not in low and "utipartsales" not in (subj or "").lower():
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
    _p(f"HIT {recv[:19]} {from_addr} {subj[:80]}")


def walk_folders(folder, acc: list, depth: int = 0) -> None:
    if depth > 18:
        return
    acc.append(folder)
    try:
        for sub in folder.Folders:
            walk_folders(sub, acc, depth + 1)
    except Exception:
        pass


def brute_folder(folder, seen, hits, saved, label: str) -> int:
    try:
        items = folder.Items
        n = int(items.Count)
    except Exception as e:
        _p(f"BRUTE FAIL {label} {e}")
        return 0
    _p(f"BRUTE {label} n={n}")
    kept = 0
    for i in range(1, n + 1):
        try:
            mail = items.Item(i)
        except Exception:
            continue
        before = len(hits)
        save_mail(mail, label, seen, hits, saved)
        if len(hits) > before:
            kept += 1
    return kept


def jet_restrict(folder, filt: str):
    try:
        return folder.Items.Restrict(filt)
    except Exception:
        return None


def dasl_restrict(folder, token: str, prop: str):
    t = token.replace("'", "''")
    filt = f'@SQL="{prop}" LIKE \'%{t}%\''
    try:
        return folder.Items.Restrict(filt)
    except Exception:
        return None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")

    store_meta = []
    folders = []
    for i in range(1, ns.Stores.Count + 1):
        store = ns.Stores.Item(i)
        name = str(store.DisplayName)
        meta = {"name": name}
        for attr in ("FilePath", "IsOpen", "ExchangeStoreType", "IsDataFileStore"):
            try:
                meta[attr] = str(getattr(store, attr))
            except Exception as e:
                meta[attr] = f"ERR:{e}"
        store_meta.append(meta)
        _p(f"STORE {meta}")
        try:
            walk_folders(store.GetRootFolder(), folders)
        except Exception as e:
            _p(f"  ROOT FAIL {e}")

    seen: set[str] = set()
    hits: list[dict] = []
    saved: list[str] = []

    # 1) Jet Restrict on high-value folders (Inbox/Sent/Deleted/Archive + Sales/Parts).
    jet_filters = [
        "[SenderEmailAddress] = 'sap4@uti.co.il'",
        "[SenderEmailAddress] = 'sap4u@uti.co.il'",
        "[SenderEmailAddress] = 'sap4uti@uti.co.il'",
        "[SenderName] = 'sap4'",
        "[SenderName] = 'sap4u'",
        "[SenderName] = 'sap4uti'",
        "[Subject] = 'UTIPartSales was executed at 01/11/2020 08:05:00'",
    ]
    dasl_tokens = ["sap4@uti.co.il", "sap4u@uti.co.il", "sap4uti@uti.co.il", "sap4"]
    dasl_props = [
        "urn:schemas:httpmail:fromemail",
        "http://schemas.microsoft.com/mapi/proptag/0x5D01001F",
        "http://schemas.microsoft.com/mapi/proptag/0x0C1A001F",
    ]
    high = []
    for folder in folders:
        try:
            fpath = str(folder.FolderPath)
        except Exception:
            continue
        fl = fpath.lower()
        try:
            n = int(folder.Items.Count)
        except Exception:
            n = -1
        if n <= 0:
            continue
        if any(
            k in fl
            for k in (
                "inbox",
                "sent",
                "deleted",
                "archive",
                "junk",
                "draft",
            )
        ) or fl.endswith("\\sales") or fl.endswith("\\parts"):
            high.append((folder, fpath, n))

    _p(f"HIGH FOLDERS {len(high)}")
    for folder, fpath, n in high:
        _p(f"JET {fpath} n={n}")
        for jf in jet_filters:
            sub = jet_restrict(folder, jf)
            if sub is None:
                continue
            try:
                c = int(sub.Count)
            except Exception:
                c = 0
            if c:
                _p(f"  JET HIT {c} {jf}")
            for i in range(1, c + 1):
                try:
                    save_mail(sub.Item(i), fpath, seen, hits, saved)
                except Exception:
                    continue
        for prop in dasl_props:
            for tok in dasl_tokens:
                sub = dasl_restrict(folder, tok, prop)
                if sub is None:
                    continue
                try:
                    c = int(sub.Count)
                except Exception:
                    c = 0
                if c:
                    _p(f"  DASL HIT {c} {tok} {prop[-12:]}")
                for i in range(1, c + 1):
                    try:
                        save_mail(sub.Item(i), fpath, seen, hits, saved)
                    except Exception:
                        continue

    # 2) Brute-force cached Archive folders (and any UTI-named folder with items).
    for folder in folders:
        try:
            fpath = str(folder.FolderPath)
        except Exception:
            continue
        fl = fpath.lower()
        try:
            n = int(folder.Items.Count)
        except Exception:
            continue
        if n <= 0:
            continue
        if "archive" in fl or "uti" in fl:
            brute_folder(folder, seen, hits, saved, fpath)

    # 3) AdvancedSearch per store root (server-side / indexer).
    adv_notes = []
    dasl_adv = [
        '@SQL="urn:schemas:httpmail:fromemail" LIKE \'%sap4%\'',
        '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%UTIPartSales%\'',
        '@SQL="urn:schemas:httpmail:from" LIKE \'%sap4%\'',
    ]
    for i in range(1, ns.Stores.Count + 1):
        store = ns.Stores.Item(i)
        try:
            root = store.GetRootFolder()
            scope = str(root.FolderPath)
        except Exception as e:
            adv_notes.append({"store": str(store.DisplayName), "err": str(e)})
            continue
        for filt in dasl_adv:
            tag = f"sap4_{i}_{abs(hash(filt)) % 99999}"
            try:
                search = ol.AdvancedSearch(scope, filt, True, tag)
            except Exception as e:
                adv_notes.append({"scope": scope, "filt": filt, "err": str(e)})
                continue
            _p(f"ADV start {scope} {filt[:60]}")
            deadline = time.time() + 45
            last = -1
            while time.time() < deadline:
                pythoncom.PumpWaitingMessages()
                time.sleep(1.5)
                try:
                    c = int(search.Results.Count)
                except Exception:
                    c = -1
                if c != last:
                    _p(f"  ADV count={c}")
                    last = c
            try:
                results = search.Results
                c = int(results.Count)
            except Exception as e:
                adv_notes.append({"scope": scope, "filt": filt, "wait_err": str(e)})
                continue
            adv_notes.append({"scope": scope, "filt": filt, "count": c})
            _p(f"ADV done {scope} count={c}")
            for j in range(1, c + 1):
                try:
                    save_mail(results.Item(j), f"ADV:{scope}", seen, hits, saved)
                except Exception:
                    continue

    payload = {
        "scan_date": "2026-08-13",
        "never_send": True,
        "pass": 2,
        "stores": store_meta,
        "hit_count": len(hits),
        "saved_count": len(saved),
        "saved": saved,
        "hits": hits,
        "advanced_search": adv_notes,
    }
    META.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    _p(f"DONE hits {len(hits)} saved {len(saved)} meta {META}")


if __name__ == "__main__":
    main()
