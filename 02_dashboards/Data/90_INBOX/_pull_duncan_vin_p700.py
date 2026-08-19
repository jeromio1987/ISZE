"""Pull Duncan VIN lists + James Marsh Unpriced P700 from Outlook. Save under ISZE INBOX."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import win32com.client  # type: ignore

DEST = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\Duncan_VIN_20260723")
P700_DEST = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\P700_Unpriced_JamesMarsh")
META = DEST / "_outlook_pull.json"
PR_SMTP = "http://schemas.microsoft.com/mapi/proptag/0x39FE001E"

WANT_ATT = re.compile(
    r"(vin\s*list|fleet\s*vin|cbu\s*master|unpriced\s*p700|p700\s*parts)",
    re.I,
)
SKIP_IMG = re.compile(r"\.(png|jpg|jpeg|gif|bmp|tif)$", re.I)


def smtp_of(mail) -> str:
    try:
        ae = mail.Sender
        if ae is not None:
            v = ae.PropertyAccessor.GetProperty(PR_SMTP)
            if v:
                return str(v).lower()
    except Exception:
        pass
    return str(getattr(mail, "SenderEmailAddress", "") or "").lower()


def safe_name(name: str) -> str:
    return re.sub(r"[^\w.\-]+", "_", name).strip("_")


def consider_folder(folder, label: str, hits: list, saved: list, seen: set) -> None:
    clauses = (
        "[SenderName] = 'Duncan Young'",
        "[SenderName] = 'James Marsh'",
        "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001F\" LIKE '%VIN%'",
        "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001F\" LIKE '%Unpriced%'",
        "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001F\" LIKE '%Meeting today%'",
        "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001F\" LIKE '%Cabs ordering%'",
    )
    for clause in clauses:
        try:
            items = folder.Items.Restrict(clause)
        except Exception as e:
            hits.append({"error": f"{label} {clause}: {e}"})
            continue
        n = 0
        for mail in items:
            n += 1
            if n > 400:
                break
            try:
                if int(mail.Class) != 43:
                    continue
            except Exception:
                continue
            eid = str(getattr(mail, "EntryID", "") or "")
            if eid in seen:
                continue
            seen.add(eid)
            who = str(mail.SenderName or "")
            smtp = smtp_of(mail)
            subj = str(mail.Subject or "")
            to = str(mail.To or "")
            blob = f"{who} {smtp} {subj} {to}".lower()
            duncan = "duncan" in blob or "duncan.young" in smtp
            james = "james marsh" in blob or "james.marsh" in smtp
            vinish = any(k in blob for k in ("vin", "cbu", "clutch", "transmission", "parc"))
            p700ish = "unpriced" in blob or "p700" in blob
            if not (duncan or (james and (vinish or p700ish)) or ("vin list" in blob)):
                continue
            rec = {
                "label": label,
                "when": str(mail.ReceivedTime)[:19],
                "who": who,
                "smtp": smtp,
                "to": to[:200],
                "subj": subj,
                "n_att": int(mail.Attachments.Count),
                "atts": [],
                "saved": [],
                "body_snip": "",
            }
            body = str(mail.Body or "")
            rec["body_snip"] = body[:2500]
            dest = DEST if duncan or vinish else P700_DEST
            dest.mkdir(parents=True, exist_ok=True)
            for i in range(1, mail.Attachments.Count + 1):
                att = mail.Attachments.Item(i)
                name = str(att.FileName)
                rec["atts"].append(name)
                low = name.lower()
                if SKIP_IMG.search(low):
                    continue
                keep = bool(WANT_ATT.search(low) or WANT_ATT.search(subj))
                keep = keep or low.endswith((".xlsx", ".xls", ".xlsm", ".csv")) and any(
                    k in low for k in ("vin", "cbu", "unpriced", "p700", "fleet")
                )
                if not keep:
                    continue
                stamp = str(mail.ReceivedTime)[:10]
                path = dest / f"{stamp}_{safe_name(name)}"
                if not path.exists():
                    att.SaveAsFile(str(path))
                rec["saved"].append(str(path))
                saved.append(str(path))
                print(f"SAVED {path} ({path.stat().st_size})", flush=True)
            if rec["atts"] or duncan or (james and p700ish):
                hits.append(rec)


def scan_quotes(folder, label: str, quotes: list) -> None:
    try:
        items = folder.Items.Restrict("[SenderName] = 'Duncan Young'")
    except Exception as e:
        quotes.append({"error": f"{label}: {e}"})
        return
    n = 0
    keys = ("47%", "47 percent", "47 per cent", "manual", "transmission", "6-8", "6 to 8", "6 – 8", "wear")
    for mail in items:
        n += 1
        if n > 250:
            break
        try:
            if int(mail.Class) != 43:
                continue
        except Exception:
            continue
        body = str(mail.Body or "")
        low = body.lower()
        if not any(k.lower() in low for k in keys):
            continue
        # keep only if 47 or 6-8 / transmission clutch context
        if not (
            "47" in body
            or "6-8" in body
            or "6 to 8" in low
            or "6 – 8" in body
            or "transmission" in low
            or "manual" in low
        ):
            continue
        quotes.append(
            {
                "label": label,
                "when": str(mail.ReceivedTime)[:19],
                "subj": str(mail.Subject or ""),
                "hits": [k for k in keys if k.lower() in low],
                "snip": body[:4000],
            }
        )


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    P700_DEST.mkdir(parents=True, exist_ok=True)
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)
    sent = ns.GetDefaultFolder(5)
    hits: list = []
    saved: list = []
    seen: set = set()
    quotes: list = []
    consider_folder(inbox, "Inbox", hits, saved, seen)
    consider_folder(sent, "Sent", hits, saved, seen)
    # one level of inbox subfolders (Sales etc.)
    try:
        for i in range(1, min(inbox.Folders.Count, 25) + 1):
            sub = inbox.Folders.Item(i)
            consider_folder(sub, f"IN:{sub.Name}", hits, saved, seen)
    except Exception:
        pass
    scan_quotes(inbox, "Inbox", quotes)
    scan_quotes(sent, "Sent", quotes)
    data = {
        "ran": datetime.now().isoformat(timespec="seconds"),
        "n_hits": len(hits),
        "saved": saved,
        "hits": hits,
        "duncan_quotes": quotes,
    }
    META.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    print("META", META, flush=True)
    print("SAVED_N", len(saved), "HITS", len(hits), "QUOTES", len(quotes), flush=True)


if __name__ == "__main__":
    main()
