"""Pass 2: DASL To/CC/body umi.co.il + all Bart Inbox/Sent headers. Not UTI-only."""
from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path

import win32com.client

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX")
JSON_OUT = OUT / "_umi_bart_outlook_pass2.json"
BART_HDR = OUT / "_bart_symons_headers.json"

PR_SMTP = "http://schemas.microsoft.com/mapi/proptag/0x39FE001E"

UMI_POS = (
    "umi.co.il",
    "universal motors",
    "sold-to 1797",
    "sold to 1797",
    "shelly@umi",
    "netanelbuc@",
    "nadav@umi",
    "pnina@umi",
    "yaniv@umi",
    "henb@umi",
    "shelly cohen",
    "netanel buchnik",
    "nadav libes",
    "pnina swisa",
)
UTI_POS = ("uti.co.il", "sold-to 1799", "sold to 1799", "shahafr@", "shahaf rehani")
BART_KEYS = ("bart.symons", "bart symons")

DASL = [
    ('to_umi', '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0E04001F" LIKE \'%umi.co.il%\''),
    ('cc_umi', '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0E03001F" LIKE \'%umi.co.il%\''),
    ('to_umi2', '@SQL="urn:schemas:httpmail:to" LIKE \'%umi.co.il%\''),
    ('cc_umi2', '@SQL="urn:schemas:httpmail:cc" LIKE \'%umi.co.il%\''),
    ('subj_umi', '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%UMI%\''),
    ('subj_israel', '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%Israel%\''),
    ('subj_shelly', '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%Shelly%\''),
    ('subj_netanel', '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%Netanel%\''),
    ('subj_nadav', '@SQL="http://schemas.microsoft.com/mapi/proptag/0x0037001F" LIKE \'%Nadav%\''),
]


def log(m):
    print(m, flush=True)


def smtp_of(mail) -> str:
    try:
        ae = mail.Sender
        if ae is not None:
            try:
                v = ae.PropertyAccessor.GetProperty(PR_SMTP)
                if v:
                    return str(v).lower()
            except Exception:
                pass
            try:
                eu = ae.GetExchangeUser()
                if eu and eu.PrimarySmtpAddress:
                    return str(eu.PrimarySmtpAddress).lower()
            except Exception:
                pass
    except Exception:
        pass
    return str(getattr(mail, "SenderEmailAddress", "") or "").lower()


def walk(folder, depth=0):
    yield folder
    if depth > 8:
        return
    try:
        n = folder.Folders.Count
    except Exception:
        return
    for i in range(1, n + 1):
        try:
            yield from walk(folder.Folders.Item(i), depth + 1)
        except Exception:
            continue


def rec(mail, fpath, how, body_n=2500):
    body = ""
    try:
        body = str(mail.Body or "")[:body_n]
    except Exception:
        body = ""
    atts = []
    try:
        for i in range(1, mail.Attachments.Count + 1):
            try:
                atts.append(str(mail.Attachments.Item(i).FileName))
            except Exception:
                pass
    except Exception:
        pass
    return {
        "received": str(getattr(mail, "ReceivedTime", "") or "")[:19],
        "from_name": str(getattr(mail, "SenderName", "") or ""),
        "from_smtp": smtp_of(mail),
        "to": str(getattr(mail, "To", "") or ""),
        "cc": str(getattr(mail, "CC", "") or ""),
        "subject": str(getattr(mail, "Subject", "") or ""),
        "folder": fpath,
        "how": how,
        "atts": atts,
        "preview": " ".join(body.split())[:1500],
        "entry_id": str(getattr(mail, "EntryID", "") or "")[:80],
    }


def blob(h):
    return " ".join(
        str(h.get(k) or "")
        for k in ("from_name", "from_smtp", "to", "cc", "subject", "preview", "folder")
    ).lower()


def main():
    t0 = time.time()
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    seen = set()
    hits = []
    bart_headers = []
    stats = {}

    # Target high-value folders: default Inbox/Sent + Sales/Parts Inbox + Archive
    targets = []
    for fid, lab in ((6, "Inbox"), (5, "Sent")):
        try:
            targets.append(ns.GetDefaultFolder(fid))
            log(f"DEF {lab} {ns.GetDefaultFolder(fid).FolderPath}")
        except Exception as e:
            log(f"DEF miss {lab} {e}")
    for s in ns.Stores:
        try:
            name = str(s.DisplayName)
            root = s.GetRootFolder()
            if name.lower() in ("sales", "parts") or "jerome" in name.lower():
                for f in walk(root, 0):
                    try:
                        fp = str(f.FolderPath)
                        n = int(f.Items.Count)
                    except Exception:
                        continue
                    pl = fp.lower()
                    if n <= 0:
                        continue
                    if any(
                        x in pl
                        for x in (
                            "inbox",
                            "sent",
                            "archive",
                            "veh customer",
                            "customers",
                        )
                    ):
                        targets.append(f)
        except Exception as e:
            log(f"store {e}")

    # de-dupe folders by path
    uniq = {}
    for f in targets:
        try:
            uniq[str(f.FolderPath)] = f
        except Exception:
            pass
    log(f"target folders={len(uniq)}")

    for fpath, folder in uniq.items():
        # DASL searches
        for label, clause in DASL:
            try:
                items = folder.Items.Restrict(clause)
                n = 0
                for mail in items:
                    try:
                        if int(mail.Class) != 43:
                            continue
                    except Exception:
                        continue
                    n += 1
                    if n > 400:
                        break
                    eid = str(getattr(mail, "EntryID", "") or "")
                    if eid and eid in seen:
                        continue
                    r = rec(mail, fpath, label)
                    b = blob(r)
                    if any(k in b for k in UTI_POS) and not any(k in b for k in UMI_POS) and not re.search(r"\bumi\b", b):
                        continue
                    umi = any(k in b for k in UMI_POS) or ("umi.co.il" in b) or re.search(r"\bumi\b", b)
                    bart = any(k in b for k in BART_KEYS)
                    if not umi:
                        continue
                    if eid:
                        seen.add(eid)
                    r["bart"] = bart
                    r["umi"] = True
                    hits.append(r)
                if n:
                    stats[f"{fpath}|{label}"] = n
                    log(f"DASL {label} {fpath}: {n}")
            except Exception as e:
                log(f"DASL fail {label} {fpath}: {e}")

        # All Bart headers in this folder
        try:
            items = folder.Items.Restrict("[SenderName] = 'Bart Symons'")
            n = 0
            for mail in items:
                try:
                    if int(mail.Class) != 43:
                        continue
                except Exception:
                    continue
                n += 1
                r = rec(mail, fpath, "bart_header", body_n=0)
                bart_headers.append(
                    {
                        "received": r["received"],
                        "subject": r["subject"],
                        "to": r["to"],
                        "cc": r["cc"],
                        "folder": fpath,
                        "from_smtp": r["from_smtp"],
                    }
                )
            if n:
                log(f"BART HDR {fpath}: {n}")
        except Exception as e:
            log(f"bart hdr fail {fpath}: {e}")

    # Filter Bart headers that look UMI-related from To/CC/subject alone
    bart_umi_hdr = []
    for h in bart_headers:
        b = " ".join(str(h.get(k) or "") for k in h).lower()
        if any(k in b for k in UTI_POS) and not any(k in b for k in UMI_POS):
            continue
        if any(k in b for k in UMI_POS) or re.search(r"\bumi\b", b) or "israel" in b:
            bart_umi_hdr.append(h)

    hits.sort(key=lambda h: h.get("received") or "", reverse=True)
    bart_hits = [h for h in hits if h.get("bart")]
    subj = sorted({h["subject"] for h in bart_hits})

    payload = {
        "scanned_at": datetime.now().isoformat(timespec="seconds"),
        "elapsed_s": round(time.time() - t0, 1),
        "n_hits_umi": len(hits),
        "n_bart_involved": len(bart_hits),
        "n_bart_headers": len(bart_headers),
        "n_bart_headers_umiish": len(bart_umi_hdr),
        "subjects_bart": subj,
        "dasl_stats_sample": {k: stats[k] for k in list(stats)[:40]},
        "bart_umi_headers": bart_umi_hdr,
        "hits": hits,
    }
    JSON_OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    BART_HDR.write_text(
        json.dumps({"n": len(bart_headers), "headers": bart_headers[:2000]}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    log(
        json.dumps(
            {
                "n_hits_umi": len(hits),
                "n_bart": len(bart_hits),
                "n_hdr": len(bart_headers),
                "n_hdr_umi": len(bart_umi_hdr),
                "subjects": subj,
            },
            ensure_ascii=False,
        )
    )
    log(f"OUT {JSON_OUT}")


if __name__ == "__main__":
    main()
