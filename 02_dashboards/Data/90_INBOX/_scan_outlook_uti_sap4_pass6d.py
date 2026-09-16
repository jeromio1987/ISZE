"""Pass 6d: apply real Table view (no conversations), then Instant Search sap4. Never Send."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pythoncom
import win32com.client

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_DIR = ISZE / r"01_data\90_INBOX\UTI_PartSales_mail_sap4_20260813"
META = ISZE / r"01_data\90_INBOX\outlook_uti_sap4_scan_pass6d_20260813.json"
KEEP_EXT = (".xlsx", ".xls", ".xlsm", ".csv")


def _p(msg: str) -> None:
    print(msg.encode("ascii", "replace").decode(), flush=True)


def dump_table(explorer) -> dict:
    rec = {"n": 0, "rows": [], "view": None, "view_type": None, "err": None}
    try:
        v = explorer.CurrentView
        rec["view"] = str(v.Name)
        rec["view_class"] = int(v.Class)
        try:
            rec["view_type"] = int(v.ViewType)
        except Exception:
            pass
        try:
            rec["conv"] = bool(v.ShowAsConversations)
        except Exception as e:
            rec["conv_err"] = str(e)
    except Exception as e:
        rec["err"] = f"view:{e}"
        return rec
    try:
        tbl = v.GetTable()
    except Exception as e:
        rec["err"] = f"GetTable:{e}"
        return rec
    for col in ("SenderEmailAddress", "SenderName", "ReceivedTime", "MessageClass"):
        try:
            tbl.Columns.Add(col)
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
        if rec["n"] > 50:
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
        rec["subject"] = str(mail.Subject or "")
        rec["received"] = str(mail.ReceivedTime)
        rec["from"] = str(mail.SenderEmailAddress or "")
        rec["sender"] = str(mail.SenderName or "")
        rec["size"] = int(mail.Size)
        rec["class"] = int(mail.Class)
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
            k = 1
            cand = dest
            while cand.exists():
                k += 1
                cand = dest.with_name(f"{dest.stem}_{k}{dest.suffix}")
            att.SaveAsFile(str(cand))
            rec["saved"].append(str(cand))
            saved.append(str(cand))
            _p(f"SAVED {cand.name} {rec.get('from')} {rec.get('subject','')[:60]}")
        except Exception as e:
            rec["saved"].append({"err": str(e)})
            _p(f"SAVE_FAIL {e}")


def list_views(folder) -> list:
    rows = []
    try:
        vs = folder.Views
        n = int(vs.Count)
    except Exception as e:
        return [{"err": str(e)}]
    for i in range(1, n + 1):
        try:
            v = vs.Item(i)
            rec = {"name": str(v.Name), "class": int(v.Class)}
            try:
                rec["type"] = int(v.ViewType)
            except Exception:
                pass
            try:
                rec["std"] = bool(v.Standard)
            except Exception:
                pass
            rows.append(rec)
        except Exception as e:
            rows.append({"err": str(e)})
    return rows


def dump_recipient_cache(ns) -> dict:
    rec = {"hits": []}
    try:
        contacts = ns.GetDefaultFolder(10)  # olFolderContacts
        rec["contacts_path"] = str(contacts.FolderPath)
        rec["contacts_n"] = int(contacts.Items.Count)
        rec["sub"] = []
        for f in contacts.Folders:
            rec["sub"].append({"name": str(f.Name), "n": int(f.Items.Count)})
            name = str(f.Name).lower()
            if "recipient" in name or "cache" in name or "suggested" in name:
                rec["cache_folder"] = str(f.FolderPath)
                rec["cache_n"] = int(f.Items.Count)
                n = int(f.Items.Count)
                # scan for sap4 (cap 2000)
                cap = min(n, 2500)
                for i in range(1, cap + 1):
                    try:
                        it = f.Items.Item(i)
                        blob = " ".join(
                            str(getattr(it, a, "") or "")
                            for a in ("Email1Address", "Email2Address", "Email3Address", "FullName", "CompanyName", "Subject")
                        ).lower()
                        if "sap4" in blob:
                            rec["hits"].append(
                                {
                                    "i": i,
                                    "name": str(getattr(it, "FullName", "") or ""),
                                    "e1": str(getattr(it, "Email1Address", "") or ""),
                                    "class": int(it.Class),
                                }
                            )
                    except Exception:
                        continue
    except Exception as e:
        rec["err"] = str(e)
    return rec


def main() -> None:
    pythoncom.CoInitialize()
    app = win32com.client.Dispatch("Outlook.Application")
    ns = app.GetNamespace("MAPI")
    explorer = app.ActiveExplorer()
    inbox = ns.GetDefaultFolder(6)
    out = {"pass": "6d", "never_send": True, "views": [], "polls": [], "saved": []}
    out["views"] = list_views(inbox)
    _p("VIEWS " + ", ".join(f"{v.get('name')} t={v.get('type')}" for v in out["views"][:20]))

    # pick a table view (ViewType 0)
    table_names = [v["name"] for v in out["views"] if v.get("type") == 0]
    out["table_views"] = table_names
    applied = None
    for name in table_names:
        if name.lower() in ("compact",):
            continue
        try:
            explorer.CurrentView = name
            applied = name
            break
        except Exception as e:
            _p(f"view apply fail {name}: {e}")
    if applied is None:
        for name in ("Single", "Preview", "Messages", "IMAP Messages"):
            try:
                explorer.CurrentView = name
                applied = name
                break
            except Exception:
                continue
    out["applied"] = applied
    _p(f"APPLIED {applied}")
    try:
        v = explorer.CurrentView
        try:
            v.ShowAsConversations = False
            v.Apply()
            out["conv_off"] = True
        except Exception as e:
            out["conv_off_err"] = str(e)
    except Exception as e:
        out["view_err"] = str(e)

    out["cache"] = dump_recipient_cache(ns)
    _p(f"CACHE hits={len(out['cache'].get('hits') or [])} {out['cache'].get('cache_folder')} n={out['cache'].get('cache_n')}")

    try:
        explorer.ClearSearch()
    except Exception as e:
        out["clear_err"] = str(e)

    q = "from:sap4@uti.co.il"
    for scope in (2, 1):
        try:
            explorer.Search(q, scope)
            out["scope"] = scope
            _p(f"SEARCH {q} scope={scope}")
            break
        except Exception as e:
            out[f"scope{scope}_err"] = str(e)
            _p(f"scope {scope} fail {e}")

    saved: list = []
    elapsed = 0
    hit = None
    for step in (8, 12, 20):
        time.sleep(step)
        elapsed += step
        snap = dump_table(explorer)
        out["polls"].append({"elapsed": elapsed, "n": snap["n"], "view": snap.get("view"), "type": snap.get("view_type"), "err": snap.get("err"), "conv": snap.get("conv")})
        _p(f"POLL {elapsed}s n={snap['n']} view={snap.get('view')} type={snap.get('view_type')} err={snap.get('err')}")
        META.write_text(json.dumps({k: v for k, v in out.items() if k != "hit_table"}, indent=2, default=str), encoding="utf-8")
        if snap["n"] > 0:
            hit = snap
            break
    if hit is None:
        hit = dump_table(explorer)
    out["hit_table"] = hit

    for row in hit.get("rows") or []:
        eid = row.get("EntryID")
        if not eid:
            continue
        h = dict(row)
        try_save(ns, eid, h, saved)
        _p(
            f"  rec={h.get('ReceivedTime') or h.get('received')} from={h.get('SenderEmailAddress') or h.get('from')} "
            f"subj={str(h.get('Subject') or h.get('subject') or '')[:70]} got={h.get('got')} att={h.get('att')} err={h.get('get_err') or h.get('att_err')}"
        )
        row["hydrate"] = {k: v for k, v in h.items() if k not in ("EntryID",)}

    out["saved"] = saved
    out["saved_count"] = len(saved)
    META.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    _p(f"DONE n={hit.get('n')} saved={len(saved)} -> {META}")


if __name__ == "__main__":
    main()
