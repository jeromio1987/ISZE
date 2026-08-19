#!/usr/bin/env python3
"""Upcoming GPS / sales-review meetings from Outlook calendar."""
from datetime import datetime
from pathlib import Path
import json
import re

import win32com.client

OUT = Path(__file__).resolve().parent
CAL_START = "2026-08-15"
CAL_END = "2026-09-30"
KW = re.compile(
    r"gps|sales review|business review|extended target|astara|imotors|"
    r"ituk|iuk|umi|uti|harris|petros|isd|portugal|ireland|sweden|norway|"
    r"denmark|romania|hungary|finland|iceland|cyprus|malta|benelux|ibx|"
    r"sterki|gasan|loutsios|petropoulos|rom auto|sverige|rsa",
    re.I,
)

def to_dt(rt):
    try:
        if hasattr(rt, "year"):
            return datetime(rt.year, rt.month, rt.day, rt.hour, rt.minute)
        return datetime.fromisoformat(str(rt)[:19])
    except Exception:
        return None

outlook = win32com.client.Dispatch("Outlook.Application")
ns = outlook.GetNamespace("MAPI")
cal = ns.GetDefaultFolder(9)
items = cal.Items
items.IncludeRecurrences = True
items.Sort("[Start]")
items = items.Restrict(f"[Start] >= '{CAL_START} 12:00 AM' AND [Start] < '{CAL_END} 12:00 AM'")
rows = []
for ev in items:
    try:
        subj = str(getattr(ev, "Subject", "") or "")
        body = str(getattr(ev, "Body", "") or "")[:800]
        required = str(getattr(ev, "RequiredAttendees", "") or "")
        blob = f"{subj} {body} {required}"
        if not KW.search(blob):
            continue
        start = to_dt(ev.Start)
        rows.append({
            "start": start.isoformat(sep=" ") if start else "",
            "subject": subj,
            "organizer": str(getattr(ev, "Organizer", "") or ""),
            "required": required[:400],
            "location": str(getattr(ev, "Location", "") or "")[:80],
        })
    except Exception:
        continue
(OUT / "gps_meetings_upcoming.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
print("kept", len(rows))
for r in rows:
    print(r["start"][:16], "|", r["subject"][:90])
