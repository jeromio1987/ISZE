"""Pass 6e: brute folders that actually have items + resolve sap4 recipient. Never Send."""
from __future__ import annotations

import json
from pathlib import Path

import pythoncom
import win32com.client

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_DIR = ISZE / r"01_data\90_INBOX\UTI_PartSales_mail_sap4_20260813"
META = ISZE / r"01_data\90_INBOX\outlook_uti_sap4_scan_pass6e_20260813.json"
KEEP_EXT = (".xlsx", ".xls", ".xlsm", ".csv")
OL_MAIL = 43
WANT = ("sap4@uti.co.il", "sap4u@uti.co.il", "sap4uti@uti.co.il")


def _p(msg: str) -> None:
    print(msg.encode("ascii", "replace").decode(), flush=True)


def smtp_blob(mail) -> str:
    bits = []
    for attr in ("SenderEmailAddress", "SenderName", "SentOnBehalfOfName", "SenderEmailType"):
        try:
            bits.append(str(getattr(mail, attr) or ""))
        except Exception:
            pass
    try:
        pa = mail.PropertyAccessor
        for tag in (
            "http://schemas.microsoft.com/mapi/proptag/0x5D01001F",
            "http://schemas.microsoft.com/mapi/proptag/0x5D02001F",
            "http://schemas.microsoft.com/mapi/proptag/0x0C1F001F",
        ):
            try:
                bits.append(str(pa.GetProperty(tag) or ""))
            except Exception:
                pass
    except Exception:
        pass
    return " ".join(bits).lower()


def unique(path: Path) -> Path:
    if not path.exists():
        return path
    n = 2
    while True:
        c = path.with_name(f"{path.stem}_{n}{path.suffix}")
        if not c.exists():
            return c
        n += 1


def save_atts(mail, rec, saved):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        n = int(mail.Attachments.Count)
    except Exception as e:
        rec["att_err"] = str(e)
        return
    rec["att"] = n
    rec["saved"] = []
    for i in range(1, n + 1):
        try:
            att = mail.Attachments.Item(i)
            name = str(att.FileName or f"att{i}")
            rec.setdefault("names", []).append(name)
            if not name.lower().endswith(KEEP_EXT):
                continue
            dest = unique(OUT_DIR / "".join(c if c.isalnum() or c in "._-" else "_" for c in name))
            att.SaveAsFile(str(dest))
            rec["saved"].append(str(dest))
            saved.append(str(dest))
            _p(f"SAVED {dest.name}")
        except Exception as e:
            rec["saved"].append({"err": str(e)})


def find_folder(root, pred, acc, depth=0):
    if depth > 12:
        return
    try:
        path = str(root.FolderPath)
        n = int(root.Items.Count)
    except Exception:
        return
    if pred(path, n, root):
        acc.append(root)
    try:
        for sub in root.Folders:
            find_folder(sub, pred, acc, depth + 1)
    except Exception:
        pass


def brute_folder(folder, saved) -> dict:
    rec = {"path": str(folder.FolderPath), "items": 0, "scanned": 0, "hits": [], "errors": 0}
    try:
        items = folder.Items
        rec["items"] = int(items.Count)
    except Exception as e:
        rec["err"] = str(e)
        return rec
    n = rec["items"]
    _p(f"BRUTE {rec['path']} n={n}")
    # Sort by received to make date filter cheaper? still must visit all for sap4
    for i in range(1, n + 1):
        try:
            it = items.Item(i)
        except Exception:
            rec["errors"] += 1
            continue
        rec["scanned"] += 1
        try:
            cls = int(it.Class)
        except Exception:
            continue
        if cls != OL_MAIL:
            continue
        try:
            subj = str(it.Subject or "")
        except Exception:
            subj = ""
        blob = smtp_blob(it)
        sl = subj.lower()
        keep = False
        reason = ""
        if any(w in blob for w in WANT) or ("sap4" in blob and "uti" in blob):
            keep = True
            reason = "from_sap4"
        else:
            recvd = None
            try:
                recvd = it.ReceivedTime
            except Exception:
                pass
            if "utipartsales" in sl and recvd is not None:
                try:
                    y = recvd.year
                    if 2020 <= y <= 2022:
                        keep = True
                        reason = "subj_2020_2022"
                except Exception:
                    pass
        if keep:
            hit = {
                "i": i,
                "subject": subj[:160],
                "reason": reason,
                "blob": blob[:200],
            }
            try:
                hit["received"] = str(it.ReceivedTime)
            except Exception:
                pass
            save_atts(it, hit, saved)
            rec["hits"].append(hit)
            _p(f"  HIT {reason} {hit.get('received')} {subj[:70]}")
        if i % 500 == 0:
            _p(f"  ... {i}/{n}")
    return rec


def resolve_sap4(ns, app) -> list:
    rows = []
    for addr in WANT:
        rec = {"addr": addr}
        try:
            r = ns.CreateRecipient(addr)
            rec["resolve"] = bool(r.Resolve())
            rec["name"] = str(r.Name)
            try:
                ae = r.AddressEntry
                rec["ae_type"] = str(ae.Type)
                rec["ae_addr"] = str(ae.Address)
                rec["ae_name"] = str(ae.Name)
                try:
                    rec["smtp"] = str(ae.GetExchangeUser().PrimarySmtpAddress)
                except Exception as e:
                    rec["ex_user_err"] = str(e)
            except Exception as e:
                rec["ae_err"] = str(e)
        except Exception as e:
            rec["err"] = str(e)
        rows.append(rec)
        _p(f"RESOLVE {addr} {rec}")
    return rows


def try_named_stores(ns) -> list:
    names = [
        "Online Archive - jerome.van.der.pluym@isuzu-e.com",
        "Online Archive - Jerome Van Der Pluym",
        "In-Place Archive - jerome.van.der.pluym@isuzu-e.com",
        "Archive",
        "info@vdpj-ventures.be",
    ]
    rows = []
    for name in names:
        rec = {"name": name}
        try:
            s = ns.Stores.Item(name)
            rec["ok"] = str(s.DisplayName)
            rec["path"] = str(s.FilePath or "")
            rec["type"] = int(s.ExchangeStoreType)
        except Exception as e:
            rec["err"] = str(e)
        rows.append(rec)
    return rows


def main() -> None:
    pythoncom.CoInitialize()
    app = win32com.client.Dispatch("Outlook.Application")
    ns = app.GetNamespace("MAPI")
    saved: list = []
    out = {"pass": "6e", "never_send": True, "brutes": [], "saved": []}
    out["resolve"] = resolve_sap4(ns, app)
    out["named_stores"] = try_named_stores(ns)
    _p("named_stores " + json.dumps(out["named_stores"], default=str)[:400])

    targets = []
    def pred(path, n, folder):
        pl = path.lower()
        if n <= 0:
            return False
        # real-count archive-ish folders only (skip huge Inbox/Sent)
        if "inbox" in pl and "archive" not in pl:
            return False
        if "sent" in pl:
            return False
        if n > 8000:
            return False
        if "archive" in pl or "journal" in pl:
            return n >= 1
        return False

    for s in ns.Stores:
        try:
            find_folder(s.GetRootFolder(), pred, targets)
        except Exception as e:
            _p(f"walk fail {s.DisplayName}: {e}")

    # always include the three known archives even if pred missed
    extras = []
    try:
        extras.append(("primary_archive", ns.Stores.Item(1).GetRootFolder().Folders["Archive"]))
    except Exception:
        pass
    seen_paths = set()
    folders = []
    for f in targets:
        p = str(f.FolderPath)
        if p in seen_paths:
            continue
        seen_paths.add(p)
        folders.append(f)
    _p(f"TARGET FOLDERS {len(folders)}")
    for f in folders:
        try:
            _p(f"  {f.FolderPath} {f.Items.Count}")
        except Exception:
            pass

    for f in folders:
        out["brutes"].append(brute_folder(f, saved))
        META.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")

    out["saved"] = saved
    out["saved_count"] = len(saved)
    out["hit_total"] = sum(len(b.get("hits") or []) for b in out["brutes"])
    META.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    _p(f"DONE hits={out['hit_total']} saved={len(saved)} -> {META}")


if __name__ == "__main__":
    main()
