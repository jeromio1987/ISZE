"""Pass 6b: hydrate Instant Search from:sap4@uti.co.il (19 rows). Never Send."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pythoncom
import win32com.client

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_DIR = ISZE / r"01_data\90_INBOX\UTI_PartSales_mail_sap4_20260813"
META = ISZE / r"01_data\90_INBOX\outlook_uti_sap4_scan_pass6b_20260813.json"
KEEP_EXT = (".xlsx", ".xls", ".xlsm", ".csv")
OL_MAIL = 43


def _p(msg: str) -> None:
    print(msg.encode("ascii", "replace").decode(), flush=True)


def smtp_of(mail) -> str:
    bits = []
    for attr in ("SenderEmailAddress", "SenderName", "SentOnBehalfOfName"):
        try:
            bits.append(f"{attr}={getattr(mail, attr)}")
        except Exception as e:
            bits.append(f"{attr}=ERR:{e}")
    try:
        pa = mail.PropertyAccessor
        for name, tag in (
            ("PR_SENDER_SMTP", "http://schemas.microsoft.com/mapi/proptag/0x5D01001F"),
            ("PR_SENT_REPR_SMTP", "http://schemas.microsoft.com/mapi/proptag/0x5D02001F"),
            ("PR_SENDER_EMAIL", "http://schemas.microsoft.com/mapi/proptag/0x0C1F001F"),
        ):
            try:
                bits.append(f"{name}={pa.GetProperty(tag)}")
            except Exception:
                pass
    except Exception:
        pass
    return " | ".join(bits)


def unique_dest(path: Path) -> Path:
    if not path.exists():
        return path
    n = 2
    while True:
        cand = path.with_name(f"{path.stem}_{n}{path.suffix}")
        if not cand.exists():
            return cand
        n += 1


def try_save(mail, rec: dict, saved: list) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        rec["class"] = int(mail.Class)
        rec["subject"] = str(mail.Subject or "")
        rec["received"] = str(mail.ReceivedTime)
        rec["size"] = int(mail.Size)
        rec["unread"] = bool(mail.UnRead)
        rec["smtp"] = smtp_of(mail)
    except Exception as e:
        rec["meta_err"] = str(e)
    # Force download via inspector (online stub)
    try:
        insp = mail.GetInspector
        rec["inspector"] = str(insp.Caption)[:80] if insp else None
        try:
            insp.Close(1)  # olDiscard
        except Exception:
            pass
    except Exception as e:
        rec["inspector_err"] = str(e)
    try:
        rec["download_state"] = int(mail.PropertyAccessor.GetProperty(
            "http://schemas.microsoft.com/mapi/proptag/0x0E230003"  # PR_MESSAGE_FLAGS-ish; try PR_NATIVE_BODY
        ))
    except Exception:
        pass
    try:
        rec["msg_flags"] = hex(int(mail.PropertyAccessor.GetProperty(
            "http://schemas.microsoft.com/mapi/proptag/0x0E070003"  # PR_MESSAGE_FLAGS
        )))
    except Exception as e:
        rec["msg_flags_err"] = str(e)
    try:
        n = int(mail.Attachments.Count)
        rec["attach_count"] = n
    except Exception as e:
        rec["attach_err"] = str(e)
        n = 0
    rec["saved_files"] = []
    for i in range(1, n + 1):
        try:
            att = mail.Attachments.Item(i)
            name = str(att.FileName or f"att{i}")
            rec.setdefault("att_names", []).append(name)
            if not name.lower().endswith(KEEP_EXT):
                continue
            dest = unique_dest(OUT_DIR / "".join(c if c.isalnum() or c in "._-" else "_" for c in name))
            att.SaveAsFile(str(dest))
            rec["saved_files"].append(str(dest))
            saved.append({"dest": str(dest), "subject": rec.get("subject"), "received": rec.get("received")})
            _p(f"SAVED {dest.name} :: {rec.get('subject','')[:70]}")
        except Exception as e:
            rec["saved_files"].append({"err": str(e), "i": i})
            _p(f"SAVE_FAIL i={i} {e}")


def run_search(app, ns, query: str) -> dict:
    inbox = ns.GetDefaultFolder(6)
    explorer = app.ActiveExplorer()
    explorer.CurrentFolder = inbox
    for vname in ("Single", "Preview", "Messages"):
        try:
            explorer.CurrentView = vname
            break
        except Exception:
            continue
    explorer.Search(query, 1)
    time.sleep(15)
    rec = {"q": query, "view": None, "table_rows": 0, "rows": []}
    try:
        rec["view"] = str(explorer.CurrentView.Name)
        rec["view_class"] = int(explorer.CurrentView.Class)
    except Exception as e:
        rec["view_err"] = str(e)
    try:
        tbl = explorer.CurrentView.GetTable()
    except Exception as e:
        rec["table_err"] = str(e)
        return rec
    try:
        tbl.Columns.Add("SenderEmailAddress")
        tbl.Columns.Add("SenderName")
        tbl.Columns.Add("ReceivedTime")
        tbl.Columns.Add("MessageClass")
        tbl.Columns.Add("Size")
    except Exception:
        pass
    while not tbl.EndOfTable:
        r = tbl.GetNextRow()
        rec["table_rows"] += 1
        row = {"i": rec["table_rows"]}
        for col in ("Subject", "EntryID", "SenderEmailAddress", "SenderName", "ReceivedTime", "MessageClass", "Size", "CreationTime", "LastModificationTime"):
            try:
                val = r(col)
                row[col] = str(val) if val is not None else None
            except Exception:
                pass
        rec["rows"].append(row)
        if rec["table_rows"] > 80:
            rec["truncated"] = True
            break
    return rec


def hydrate(ns, row: dict, saved: list) -> dict:
    rec = dict(row)
    eid = row.get("EntryID")
    if not eid:
        rec["hydrate"] = "no_entryid"
        return rec
    mail = None
    try:
        mail = ns.GetItemFromID(eid)
        rec["hydrate"] = "GetItemFromID_ok"
    except Exception as e:
        rec["hydrate"] = f"GetItemFromID_fail:{e}"
        mail = None
    if mail is None:
        return rec
    try_save(mail, rec, saved)
    return rec


def main() -> None:
    pythoncom.CoInitialize()
    app = win32com.client.Dispatch("Outlook.Application")
    ns = app.GetNamespace("MAPI")
    saved: list = []
    out = {
        "pass": "6b",
        "never_send": True,
        "scan_date": "2026-08-13",
        "note": "Instant Search TableView hydrate of sap4 hits (19 expected)",
    }
    queries = [
        "from:sap4@uti.co.il",
        "from:sap4u@uti.co.il",
        "from:sap4uti@uti.co.il",
    ]
    out["searches"] = []
    for q in queries:
        _p(f"SEARCH {q}")
        srec = run_search(app, ns, q)
        _p(f"  table_rows={srec.get('table_rows')}")
        hydrated = []
        for row in srec.get("rows") or []:
            h = hydrate(ns, row, saved)
            hydrated.append(h)
            _p(
                f"  [{h.get('i')}] rec={h.get('ReceivedTime')} from={h.get('SenderEmailAddress') or h.get('smtp','')[:60]} "
                f"subj={str(h.get('Subject') or h.get('subject') or '')[:70]} hyd={h.get('hydrate')} "
                f"att={h.get('attach_count')} saved={h.get('saved_files')}"
            )
        srec["hydrated"] = hydrated
        # drop raw rows duplicate
        out["searches"].append(srec)

    out["saved_count"] = len(saved)
    out["saved"] = saved
    META.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    _p(f"DONE saved={len(saved)} -> {META}")


if __name__ == "__main__":
    main()
