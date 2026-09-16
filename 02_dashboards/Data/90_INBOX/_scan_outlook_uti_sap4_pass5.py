"""Pass 5: single KQL + TableView.GetTable. Never Send."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pythoncom
import win32com.client

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_DIR = ISZE / r"01_data\90_INBOX\UTI_PartSales_mail_sap4_20260813"
META = ISZE / r"01_data\90_INBOX\outlook_uti_sap4_scan_pass5_20260813.json"
KEEP_EXT = (".xlsx", ".xls", ".xlsm", ".csv")


def _p(msg: str) -> None:
    print(msg.encode("ascii", "replace").decode(), flush=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)
    expl = ol.ActiveExplorer()
    if expl is None:
        inbox.Display()
        expl = ol.ActiveExplorer()
    expl.CurrentFolder = inbox
    pythoncom.PumpWaitingMessages()

    q = "from:sap4@uti.co.il OR from:sap4u@uti.co.il OR from:sap4uti@uti.co.il"
    _p(f"SEARCH {q}")
    expl.Search(q, True)
    for _ in range(12):
        pythoncom.PumpWaitingMessages()
        time.sleep(1)
    rec = {"q": q}
    try:
        cf = expl.CurrentFolder
        rec["folder"] = str(cf.FolderPath)
        rec["items"] = int(cf.Items.Count)
    except Exception as e:
        rec["folder_err"] = str(e)
        cf = None
    _p(f"FOLDER {rec}")

    view = None
    try:
        view = expl.CurrentView
        rec["view"] = str(view.Name)
        rec["view_class"] = int(view.Class)
        try:
            rec["filter"] = str(view.Filter)
        except Exception as e:
            rec["filter"] = str(e)
        try:
            rec["xml"] = str(view.XML)[:2000]
        except Exception as e:
            rec["xml_err"] = str(e)
    except Exception as e:
        rec["view_err"] = str(e)
    _p(f"VIEW {rec.get('view')} class={rec.get('view_class')} filter={rec.get('filter')}")

    saved = []
    hits = []
    if view is not None:
        try:
            table = view.GetTable()
            n = int(table.GetRowCount())
            rec["table_rows"] = n
            _p(f"TABLE {n}")
            cols = []
            for c in range(1, table.Columns.Count + 1):
                cols.append(str(table.Columns.Item(c).Name))
            rec["columns"] = cols
            table.MoveToStart()
            while not table.EndOfTable:
                row = table.GetNextRow()
                eid = None
                for key in cols:
                    if "entry" in key.lower():
                        try:
                            eid = row(key)
                        except Exception:
                            continue
                if not eid:
                    try:
                        eid = row("EntryID")
                    except Exception:
                        eid = None
                subj = None
                try:
                    subj = row("Subject")
                except Exception:
                    pass
                fromn = None
                try:
                    fromn = row("From")
                except Exception:
                    pass
                rec.setdefault("rows_preview", []).append(
                    {"subject": str(subj)[:80] if subj else None, "from": str(fromn) if fromn else None, "eid": bool(eid)}
                )
                if not eid:
                    continue
                mail = ns.GetItemFromID(eid)
                recv = str(getattr(mail, "ReceivedTime", ""))
                sender = str(getattr(mail, "SenderEmailAddress", ""))
                subj2 = str(getattr(mail, "Subject", ""))
                atts = []
                saved_here = []
                for i in range(1, mail.Attachments.Count + 1):
                    att = mail.Attachments.Item(i)
                    an = str(att.FileName)
                    atts.append(an)
                    if not an.lower().endswith(KEEP_EXT):
                        continue
                    dest = OUT_DIR / f"{recv[:10]}_{an}"
                    nuniq = 2
                    while dest.exists():
                        dest = OUT_DIR / f"{recv[:10]}_{dest.stem}_{nuniq}{dest.suffix}"
                        nuniq += 1
                    att.SaveAsFile(str(dest))
                    saved_here.append(str(dest))
                    saved.append(str(dest))
                    _p(f"SAVED {dest}")
                hits.append(
                    {
                        "received": recv,
                        "from": sender,
                        "subject": subj2,
                        "attachments": atts,
                        "saved": saved_here,
                    }
                )
                _p(f"HIT {recv[:19]} {sender} {subj2[:80]}")
        except Exception as e:
            rec["table_err"] = str(e)
            _p(f"TABLE ERR {e}")

    payload = {
        "scan_date": "2026-08-13",
        "never_send": True,
        "pass": 5,
        "rec": rec,
        "hit_count": len(hits),
        "saved_count": len(saved),
        "hits": hits,
        "saved": saved,
    }
    META.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    _p(f"DONE hits {len(hits)} saved {len(saved)}")


if __name__ == "__main__":
    main()
