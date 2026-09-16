#!/usr/bin/env python3
"""Scan Jerome's Outlook for GPS / business-review status on named DBs."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import win32com.client

OUT = Path(__file__).resolve().parent
CUTOFF = datetime(2026, 4, 1)
END = datetime(2026, 9, 30)

# Each bucket: subject/body keywords that should keep a mail
BUCKETS = {
    "iceland": r"\biceland\b|\bbl ehf\b|\bblehf\b",
    "denmark": r"\bdenmark\b|\bdanske\b|\bisuzu denmark\b|\bmagelssen\b",
    "cyprus": r"\bcyprus\b|\bloutsios\b",
    "finland": r"\bfinland\b|\bsuomi\b|\bisuzu finland\b",
    "belgium": r"\bbelgium\b|\bbenelux\b|\bibx\b|\bisuzu benelux\b",
    "hungary": r"\bhungary\b|\bautowallis\b|\bsterki\b",
}

KEEP = re.compile(
    r"gps|business review|sales review|extended target|meeting|teams|"
    r"invite|invitation|calendar|slot|book|schedule|confirm|"
    r"sales to dealer|std|kpi",
    re.I,
)

SKIP_SUBJ = re.compile(r"^(fw:\s*)?(automatic reply|out of office|undeliverable)", re.I)


def to_dt(rt):
    try:
        if hasattr(rt, "year"):
            return datetime(rt.year, rt.month, rt.day, rt.hour, rt.minute)
        return datetime.fromisoformat(str(rt)[:19])
    except Exception:
        return None


def scan_folder(folder, label, rows, limit=4000):
    items = folder.Items
    items.Sort("[ReceivedTime]", True)
    n = 0
    for it in items:
        n += 1
        if n > limit:
            break
        try:
            rec = to_dt(getattr(it, "ReceivedTime", None) or getattr(it, "SentOn", None))
            if rec is None:
                continue
            if rec < CUTOFF or rec > END:
                if rec < CUTOFF:
                    break
                continue
            subj = str(getattr(it, "Subject", "") or "")
            if SKIP_SUBJ.search(subj):
                continue
            sender = str(getattr(it, "SenderName", "") or "")
            to = str(getattr(it, "To", "") or "")
            cc = str(getattr(it, "CC", "") or "")
            body = str(getattr(it, "Body", "") or "")[:2500]
            blob = f"{subj}\n{sender}\n{to}\n{cc}\n{body}"
            if not KEEP.search(blob):
                continue
            hits = [k for k, pat in BUCKETS.items() if re.search(pat, blob, re.I)]
            if not hits:
                continue
            rows.append({
                "folder": label,
                "when": rec.isoformat(sep=" ")[:16],
                "subject": subj[:180],
                "from": sender[:80],
                "to": to[:200],
                "hits": hits,
                "preview": re.sub(r"\s+", " ", body)[:420],
            })
        except Exception:
            continue


outlook = win32com.client.Dispatch("Outlook.Application")
ns = outlook.GetNamespace("MAPI")
inbox = ns.GetDefaultFolder(6)
sent = ns.GetDefaultFolder(5)
rows = []
scan_folder(inbox, "inbox", rows, 5000)
scan_folder(sent, "sent", rows, 2500)

# Calendar again, wider
cal = ns.GetDefaultFolder(9)
items = cal.Items
items.IncludeRecurrences = True
items.Sort("[Start]")
items = items.Restrict("[Start] >= '04/01/2026 12:00 AM' AND [Start] < '09/30/2026 12:00 AM'")
cal_rows = []
for ev in items:
    try:
        subj = str(getattr(ev, "Subject", "") or "")
        body = str(getattr(ev, "Body", "") or "")[:800]
        required = str(getattr(ev, "RequiredAttendees", "") or "")
        blob = f"{subj} {body} {required}"
        hits = [k for k, pat in BUCKETS.items() if re.search(pat, blob, re.I)]
        if not hits:
            continue
        start = to_dt(ev.Start)
        cal_rows.append({
            "start": start.isoformat(sep=" ")[:16] if start else "",
            "subject": subj[:180],
            "organizer": str(getattr(ev, "Organizer", "") or "")[:80],
            "required": required[:300],
            "hits": hits,
        })
    except Exception:
        continue

out = {"mails": rows, "calendar": cal_rows}
(OUT / "gps_db_mail_scan.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print("mails", len(rows), "cal", len(cal_rows))
print("--- CAL ---")
for r in cal_rows:
    print(r["start"], r["hits"], "|", r["subject"][:90])
print("--- MAIL (latest 80) ---")
for r in sorted(rows, key=lambda x: x["when"], reverse=True)[:80]:
    print(r["when"], r["folder"], r["hits"], "|", r["subject"][:90])
