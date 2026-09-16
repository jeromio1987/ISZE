"""Pass 6c: poll Instant Search until rows appear; persist EntryIDs immediately. Never Send."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pythoncom
import win32com.client

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_DIR = ISZE / r"01_data\90_INBOX\UTI_PartSales_mail_sap4_20260813"
META = ISZE / r"01_data\90_INBOX\outlook_uti_sap4_scan_pass6c_20260813.json"
KEEP_EXT = (".xlsx", ".xls", ".xlsm", ".csv")
OL_MAIL = 43


def _p(msg: str) -> None:
    print(msg.encode("ascii", "replace").decode(), flush=True)


def dump_table(explorer) -> dict:
    rec = {"rows": [], "n": 0, "view": None, "view_class": None, "filter": None, "err": None}
    try:
        v = explorer.CurrentView
        rec["view"] = str(v.Name)
        rec["view_class"] = int(v.Class)
        try:
            rec["filter"] = str(v.Filter or "")
        except Exception:
            rec["filter"] = None
        try:
            rec["xml"] = str(v.XML or "")[:500]
        except Exception:
            pass
    except Exception as e:
        rec["err"] = f"view:{e}"
        return rec
    try:
        tbl = v.GetTable()
    except Exception as e:
        rec["err"] = f"GetTable:{e}"
        return rec
    try:
        tbl.Columns.Add("SenderEmailAddress")
        tbl.Columns.Add("SenderName")
        tbl.Columns.Add("ReceivedTime")
        tbl.Columns.Add("MessageClass")
    except Exception:
        pass
    while not tbl.EndOfTable:
        r = tbl.GetNextRow()
        rec["n"] += 1
        row = {}
        for col in ("Subject", "EntryID", "SenderEmailAddress", "SenderName", "ReceivedTime", "MessageClass"):
            try:
                val = r(col)
                row[col] = str(val) if val is not None else None
            except Exception:
                pass
        rec["rows"].append(row)
        if rec["n"] > 60:
            rec["truncated"] = True
            break
    return rec


def try_save(ns, eid: str, rec: dict, saved: list) -> None:
    try:
        mail = ns.GetItemFromID(eid)
    except Exception as e:
        rec["get_err"] = str(e)
        return
    rec["got"] = True
    try:
        rec["class"] = int(mail.Class)
        rec["subject"] = str(mail.Subject or "")
        rec["received"] = str(mail.ReceivedTime)
        rec["from"] = str(mail.SenderEmailAddress or "")
        rec["sender"] = str(mail.SenderName or "")
        rec["size"] = int(mail.Size)
    except Exception as e:
        rec["meta_err"] = str(e)
    try:
        insp = mail.GetInspector
        rec["inspector"] = True
        try:
            insp.Close(1)
        except Exception:
            pass
    except Exception as e:
        rec["inspector_err"] = str(e)
    try:
        n = int(mail.Attachments.Count)
        rec["att"] = n
    except Exception as e:
        rec["att_err"] = str(e)
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rec["saved"] = []
    for i in range(1, n + 1):
        try:
            att = mail.Attachments.Item(i)
            name = str(att.FileName or f"att{i}")
            rec.setdefault("names", []).append(name)
            if not name.lower().endswith(KEEP_EXT):
                continue
            dest = OUT_DIR / "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
            if dest.exists():
                k = 2
                while dest.with_name(f"{dest.stem}_{k}{dest.suffix}").exists():
                    k += 1
                dest = dest.with_name(f"{dest.stem}_{k}{dest.suffix}")
            att.SaveAsFile(str(dest))
            rec["saved"].append(str(dest))
            saved.append(str(dest))
            _p(f"SAVED {dest.name}")
        except Exception as e:
            rec["saved"].append({"err": str(e)})
            _p(f"SAVE_FAIL {e}")


def main() -> None:
    pythoncom.CoInitialize()
    app = win32com.client.Dispatch("Outlook.Application")
    ns = app.GetNamespace("MAPI")
    explorer = app.ActiveExplorer()
    out = {
        "pass": "6c",
        "never_send": True,
        "before": None,
        "polls": [],
        "saved": [],
    }
    out["before"] = {
        "caption": str(explorer.Caption),
        "folder": str(explorer.CurrentFolder.FolderPath),
        "sel": int(explorer.Selection.Count),
    }
    _p(f"BEFORE {out['before']}")
    out["before"]["table"] = dump_table(explorer)
    _p(f"  existing table n={out['before']['table'].get('n')} view={out['before']['table'].get('view')} err={out['before']['table'].get('err')}")

    try:
        explorer.ClearSearch()
        out["cleared"] = True
    except Exception as e:
        out["clear_err"] = str(e)

    for vname in ("Single", "Preview", "Messages"):
        try:
            explorer.CurrentView = vname
            out["forced_view"] = vname
            break
        except Exception:
            continue

    q = "from:sap4@uti.co.il"
    # 2 = olSearchScopeAllOutlookItems
    try:
        explorer.Search(q, 2)
        out["scope"] = 2
        out["q"] = q
    except Exception as e:
        _p(f"scope2 fail {e}, fallback 1")
        explorer.Search(q, 1)
        out["scope"] = 1
        out["q"] = q
        out["scope2_err"] = str(e)

    saved: list = []
    found = False
    for wait in (5, 10, 15, 25, 40):
        time.sleep(5 if wait == 5 else wait - (out["polls"][-1]["wait"] if out["polls"] else 0))
        snap = dump_table(explorer)
        snap["wait"] = wait
        out["polls"].append({"wait": wait, "n": snap["n"], "view": snap.get("view"), "err": snap.get("err"), "filter": snap.get("filter")})
        _p(f"POLL {wait}s n={snap['n']} view={snap.get('view')} err={snap.get('err')}")
        META.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
        if snap["n"] > 0:
            out["hit_table"] = snap
            found = True
            break

    if not found:
        # last dump
        out["hit_table"] = dump_table(explorer)

    for row in (out.get("hit_table") or {}).get("rows") or []:
        eid = row.get("EntryID")
        if not eid:
            continue
        h = dict(row)
        try_save(ns, eid, h, saved)
        _p(
            f"  rec={h.get('ReceivedTime') or h.get('received')} from={h.get('SenderEmailAddress') or h.get('from')} "
            f"subj={str(h.get('Subject') or h.get('subject') or '')[:70]} got={h.get('got')} att={h.get('att')} "
            f"get_err={h.get('get_err')}"
        )
        row.update({k: v for k, v in h.items() if k not in row})

    out["saved"] = saved
    out["saved_count"] = len(saved)
    META.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    _p(f"DONE n={out.get('hit_table',{}).get('n')} saved={len(saved)} -> {META}")


if __name__ == "__main__":
    main()
