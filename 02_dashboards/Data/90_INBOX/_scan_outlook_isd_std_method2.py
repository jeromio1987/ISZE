"""Method 2: Outlook Instant Search + every store + German terms + Fabian/Technik.

Does not repeat Restrict on 'Sales to dealer'. Saves xlsx from ISD senders with
StD-ish names. Never Send.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import win32com.client

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_isd_std_mail_20260818")
ATT = OUT / "attachments"
ATT.mkdir(parents=True, exist_ok=True)
LOG = OUT / "scan_log_method2.txt"
JSON_OUT = OUT / "outlook_isd_method2.json"
OL_MAIL = 43
ATT_EXT = (".xlsx", ".xls", ".xlsm", ".csv")

log_lines: list[str] = []


def log(msg: str) -> None:
    print(msg)
    log_lines.append(msg)


def save_atts(mail, prefix: str) -> list[str]:
    saved = []
    for i in range(1, mail.Attachments.Count + 1):
        att = mail.Attachments.Item(i)
        name = str(att.FileName or "")
        if not name.lower().endswith(ATT_EXT):
            continue
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)[:120]
        dest = ATT / f"{prefix}_{safe}"
        n = 2
        while dest.exists():
            dest = ATT / f"{prefix}_{n}_{safe}"
            n += 1
        att.SaveAsFile(str(dest))
        saved.append(str(dest))
        log(f"SAVED {dest}")
    return saved


def mail_row(mail, how: str, saved: list[str]) -> dict:
    atts = [mail.Attachments.Item(i).FileName for i in range(1, mail.Attachments.Count + 1)]
    body = str(mail.Body or "")
    return {
        "how": how,
        "received": str(mail.ReceivedTime)[:19],
        "sender": str(mail.SenderName or ""),
        "sender_email": str(getattr(mail, "SenderEmailAddress", "") or ""),
        "to": str(mail.To or ""),
        "cc": str(mail.CC or ""),
        "subject": str(mail.Subject or ""),
        "attachments": atts,
        "saved": saved,
        "preview": " ".join(body.split())[:900],
    }


ol = win32com.client.Dispatch("Outlook.Application")
ns = ol.GetNamespace("MAPI")

stores = []
for i in range(1, ns.Stores.Count + 1):
    st = ns.Stores.Item(i)
    stores.append(str(st.DisplayName))
log(f"started {datetime.now().isoformat(timespec='seconds')}")
log(f"stores={stores}")

# Instant Search queries (DASL content indexer) — different mechanism from Restrict LIKE
queries = [
    ("is:isuzu-sales.de xlsx", 'isuzu-sales.de hasattachments:yes'),
    ("from:s.mueller", 'from:"s.mueller@isuzu-sales.de"'),
    ("from:sebastian.muller astara", 'from:"Sebastian.Muller@astara.com"'),
    ("from:fabian.thiel", 'from:"fabian.thiel"'),
    ("from:aftersales-technik", 'from:"aftersales-technik"'),
    ("haendlerabsatz", "Händlerabsatz"),
    ("verkauf_haendler", "Verkauf an Händler"),
    ("teileverkauf", "Teileverkauf"),
    ("partsales_isd", "ISD PartSales"),
    ("monthly demand germany", "Germany Monthly Demand"),
]

hits: list[dict] = []
seen = set()


def key_of(mail) -> str:
    try:
        return f"{mail.EntryID}"
    except Exception:
        return f"{mail.Subject}|{mail.ReceivedTime}|{mail.SenderName}"


def walk_search(scope_folder, qlabel: str, q: str, cap: int = 40) -> int:
    n = 0
    kept = 0
    try:
        items = scope_folder.Items
        # Instant Search: prefix with @SQL content class if AdvancedSearch not needed
        # Outlook COM Restrict on contents via ci_body / subject is still Restrict.
        # Use Application.AdvancedSearch on store.
    except Exception as e:
        log(f"walk_search fail {qlabel}: {e}")
        return 0
    return 0


# AdvancedSearch per store
for i in range(1, ns.Stores.Count + 1):
    st = ns.Stores.Item(i)
    sname = str(st.DisplayName)
    try:
        root = st.GetRootFolder()
        scope = root.FolderPath
    except Exception as e:
        log(f"store {sname} no root: {e}")
        continue
    for qlabel, q in queries:
        tag = f"isdstd_{i}_{qlabel}"
        try:
            s = ol.AdvancedSearch(scope, q, True, tag)
        except Exception as e:
            log(f"AdvancedSearch fail {sname}/{qlabel}: {e}")
            continue
        # Busy-wait briefly for indexer
        import time
        for _ in range(40):
            time.sleep(0.25)
            try:
                if s.Results.Count >= 0 and str(s.Status) in ("1", "2") or True:
                    pass
            except Exception:
                pass
            try:
                # 0=searching, 1=done in some versions; Results can populate while searching
                if s.Results.Count > 0:
                    break
            except Exception:
                break
        try:
            nres = s.Results.Count
        except Exception as e:
            log(f"results fail {sname}/{qlabel}: {e}")
            continue
        log(f"AdvancedSearch {sname}/{qlabel} count={nres}")
        for j in range(1, min(nres, 40) + 1):
            try:
                mail = s.Results.Item(j)
            except Exception:
                continue
            if getattr(mail, "Class", None) != OL_MAIL:
                continue
            k = key_of(mail)
            if k in seen:
                continue
            seen.add(k)
            rec = str(mail.ReceivedTime)[:10]
            prefix = f"{rec}_ISD_m2"
            saved = save_atts(mail, prefix)
            hits.append(mail_row(mail, f"adv:{sname}/{qlabel}", saved))

# Fallback: walk Inbox/Sent of each store, last 400, ISD people including Fabian/Technik
ISD_KEYS = (
    "müller", "muller", "spenlein", "thiel", "tomoe", "baumann",
    "isuzu-sales.de", "isuzu.de", "aftersales-technik", "affa",
    "groß", "gross", "björn", "bjorn",
)
STDISH = (
    "sales to dealer", "sell-out", "sellout", "partsales", "part sales",
    "händler", "haendler", "dealer data", "monthly demand", "teileverkauf",
    "verkauf", "kpi", "spi",
)

for i in range(1, ns.Stores.Count + 1):
    st = ns.Stores.Item(i)
    sname = str(st.DisplayName)
    try:
        root = st.GetRootFolder()
    except Exception:
        continue

    def walk(folder, depth=0):
        if depth > 3:
            return
        fname = str(folder.Name)
        # skip huge customer trees already scanned
        low = fname.lower()
        if any(x in low for x in ("ie customers", "ie suppliers", "deleted", "junk", "spam")):
            return
        try:
            items = folder.Items
            items.Sort("[ReceivedTime]", True)
        except Exception:
            items = None
        if items is not None and ("inbox" in low or "sent" in low or "inbox" in str(folder.FolderPath).lower() or "sent" in str(folder.FolderPath).lower()):
            c = 0
            n_isd = 0
            for mail in items:
                c += 1
                if c > 500:
                    break
                if getattr(mail, "Class", None) != OL_MAIL:
                    continue
                blob = " ".join([
                    str(mail.Subject or ""),
                    str(mail.SenderName or ""),
                    str(getattr(mail, "SenderEmailAddress", "") or ""),
                    str(mail.To or ""),
                    str(mail.CC or ""),
                ]).lower()
                if not any(k in blob for k in ISD_KEYS):
                    continue
                n_isd += 1
                k = key_of(mail)
                subj = str(mail.Subject or "").lower()
                atts = []
                try:
                    atts = [mail.Attachments.Item(i).FileName for i in range(1, mail.Attachments.Count + 1)]
                except Exception:
                    pass
                interesting = any(w in blob or w in " ".join(atts).lower() for w in STDISH)
                xls = [a for a in atts if a.lower().endswith(ATT_EXT)]
                if not interesting and not xls:
                    continue
                if k in seen and not xls:
                    continue
                seen.add(k)
                rec = str(mail.ReceivedTime)[:10]
                saved = save_atts(mail, f"{rec}_ISD_walk") if xls and interesting else []
                hits.append(mail_row(mail, f"walk:{sname}/{folder.FolderPath}", saved))
            log(f"walk {folder.FolderPath} scanned={c} isdish={n_isd}")
        try:
            for j in range(1, folder.Folders.Count + 1):
                walk(folder.Folders.Item(j), depth + 1)
        except Exception:
            pass

    walk(root)

JSON_OUT.write_text(json.dumps({"n": len(hits), "hits": hits}, indent=2, ensure_ascii=False), encoding="utf-8")
log(f"hits={len(hits)} wrote {JSON_OUT}")
LOG.write_text("\n".join(log_lines), encoding="utf-8")
print("done")
