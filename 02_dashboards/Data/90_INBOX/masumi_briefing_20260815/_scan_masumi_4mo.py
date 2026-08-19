#!/usr/bin/env python3
"""Masumi mail + calendar, last 4 months (2026-04-15 → 2026-08-15). Outlook COM."""
from __future__ import annotations

import json
import re
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

try:
    import win32com.client
except ImportError:
    print("NO_WIN32COM")
    raise SystemExit(2)

OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)

CUTOFF = datetime(2026, 4, 15)
END = datetime(2026, 8, 16)
DATE_FILTER = "[ReceivedTime] >= '04/15/2026 12:00 AM'"
CAL_START = "2026-04-15"
CAL_END = "2026-08-16"

NAME_KEYS = ["masumi.hayakawa", "masumi hayakawa"]
THEMES = {
    "PMS": r"\bpms\b|periodic maintenance|n75|oil filter|air filter",
    "GPS": r"\bgps\b|genuine parts share|spend per unit|kickback|stretch|parts sales target",
    "UIO": r"\buio\b|car.?park|units in operation|matriculas|保有",
    "IDS": r"\bids\b|dealer standard|kaizen|dealer compare|dealer ranking",
    "KPI": r"\bkpi\b|fill rate|spi\b",
    "LUBES": r"lubricant|lube",
    "SPA": r"\bspa\b|special price",
}


def log(msg: str) -> None:
    print(msg, flush=True)


def to_dt(rt) -> datetime | None:
    try:
        if hasattr(rt, "year"):
            return datetime(rt.year, rt.month, rt.day, rt.hour, rt.minute, getattr(rt, "second", 0) or 0)
        return datetime.fromisoformat(str(rt)[:19])
    except Exception:
        return None


def smtp_of(mail) -> str:
    try:
        ae = mail.Sender
        if ae is not None:
            try:
                v = ae.PropertyAccessor.GetProperty(
                    "http://schemas.microsoft.com/mapi/proptag/0x39FE001E"
                )
                if v:
                    return str(v).lower()
            except Exception:
                pass
        return str(getattr(mail, "SenderEmailAddress", "") or "").lower()
    except Exception:
        return str(getattr(mail, "SenderEmailAddress", "") or "").lower()


def is_masumi_text(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in NAME_KEYS)


def themes_of(text: str) -> list[str]:
    t = (text or "").lower()
    return [name for name, pat in THEMES.items() if re.search(pat, t, re.I)]


def mail_record(mail, fpath: str) -> dict:
    rdt = to_dt(mail.ReceivedTime) or CUTOFF
    body = ""
    try:
        body = str(mail.Body or "")[:3500]
    except Exception:
        body = ""
    att = []
    try:
        for i in range(1, mail.Attachments.Count + 1):
            try:
                att.append(str(mail.Attachments.Item(i).FileName))
            except Exception:
                pass
    except Exception:
        pass
    subj = str(getattr(mail, "Subject", "") or "")
    blob = f"{subj}\n{body}\n{' '.join(att)}"
    return {
        "received": rdt.isoformat(sep=" "),
        "folder": fpath,
        "from_name": str(getattr(mail, "SenderName", "") or ""),
        "from_smtp": smtp_of(mail),
        "to": str(getattr(mail, "To", "") or ""),
        "cc": str(getattr(mail, "CC", "") or ""),
        "subject": subj,
        "from_masumi": is_masumi_text(
            f"{getattr(mail, 'SenderName', '')} {smtp_of(mail)}"
        ),
        "attachments": att,
        "themes": themes_of(blob),
        "body_preview": body[:1800],
        "entry_id": str(getattr(mail, "EntryID", "") or "")[:80],
    }


def default_folders(ns):
    out = []
    for fid, label in ((6, "Inbox"), (5, "Sent")):
        try:
            f = ns.GetDefaultFolder(fid)
            out.append(f)
            log(f"FOLDER {label}: {f.FolderPath}")
        except Exception as exc:
            log(f"FOLDER_MISS {label}: {exc}")
    return out


def pull_from_masumi(folder, seen, hits) -> int:
    fpath = folder.FolderPath
    t0 = time.time()
    n = 0
    for clause in (
        "[SenderName] = 'Masumi Hayakawa'",
        "[SenderName] = 'Hayakawa Masumi'",
    ):
        try:
            items = folder.Items.Restrict(f"{DATE_FILTER} AND {clause}")
        except Exception as exc:
            log(f"RESTRICT_FAIL {fpath} {clause}: {exc}")
            continue
        for mail in items:
            try:
                if int(mail.Class) != 43:
                    continue
            except Exception:
                continue
            eid = str(getattr(mail, "EntryID", "") or "")
            if eid and eid in seen:
                continue
            rec = mail_record(mail, fpath)
            rdt = to_dt(mail.ReceivedTime)
            if rdt and rdt >= END:
                continue
            if eid:
                seen.add(eid)
            hits.append(rec)
            n += 1
    log(f"FROM Masumi @ {fpath}: {n} in {time.time()-t0:.1f}s")
    return n


def pull_involving(folder, seen, hits, limit=12000) -> int:
    fpath = folder.FolderPath
    t0 = time.time()
    try:
        items = folder.Items
        items.Sort("[ReceivedTime]", True)
        items = items.Restrict(DATE_FILTER)
    except Exception as exc:
        log(f"INVOLVE_FAIL {fpath}: {exc}")
        return 0
    added = 0
    scanned = 0
    for mail in items:
        scanned += 1
        if scanned > limit:
            break
        try:
            if int(mail.Class) != 43:
                continue
        except Exception:
            continue
        eid = str(getattr(mail, "EntryID", "") or "")
        if eid and eid in seen:
            continue
        blob = " ".join(
            [
                str(getattr(mail, "SenderName", "") or ""),
                smtp_of(mail),
                str(getattr(mail, "To", "") or ""),
                str(getattr(mail, "CC", "") or ""),
            ]
        )
        if not is_masumi_text(blob):
            continue
        rec = mail_record(mail, fpath)
        rdt = to_dt(mail.ReceivedTime)
        if rdt and rdt >= END:
            continue
        if eid:
            seen.add(eid)
        hits.append(rec)
        added += 1
    log(f"INVOLVE {fpath}: scanned={scanned} added={added} in {time.time()-t0:.1f}s")
    return added


def scan_calendar(ns) -> list[dict]:
    cal = ns.GetDefaultFolder(9)
    items = cal.Items
    items.IncludeRecurrences = True
    items.Sort("[Start]")
    restriction = f"[Start] >= '{CAL_START} 12:00 AM' AND [Start] < '{CAL_END} 12:00 AM'"
    try:
        items = items.Restrict(restriction)
    except Exception as exc:
        log(f"CAL_RESTRICT_FAIL: {exc}")
        return []
    rows = []
    kw = re.compile(
        r"gps|pms|ids|uio|sales review|target study|genuine|dealer standard|"
        r"astara|imotors|ituk|iuk|umi|uti|harris|petros|isd|portugal|ireland",
        re.I,
    )
    n = 0
    for ev in items:
        n += 1
        try:
            subj = str(getattr(ev, "Subject", "") or "")
            body = str(getattr(ev, "Body", "") or "")[:1500]
            loc = str(getattr(ev, "Location", "") or "")
            start = to_dt(ev.Start)
            required = str(getattr(ev, "RequiredAttendees", "") or "")
            optional = str(getattr(ev, "OptionalAttendees", "") or "")
            blob = f"{subj} {body} {required} {optional}"
            if not (kw.search(blob) or is_masumi_text(blob)):
                continue
            rows.append(
                {
                    "start": start.isoformat(sep=" ") if start else "",
                    "subject": subj,
                    "location": loc,
                    "organizer": str(getattr(ev, "Organizer", "") or ""),
                    "required": required[:400],
                    "optional": optional[:300],
                    "masumi": is_masumi_text(blob),
                    "themes": themes_of(blob),
                    "preview": body[:500],
                }
            )
        except Exception:
            continue
    log(f"CAL scanned={n} kept={len(rows)}")
    return rows


def main() -> int:
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    folders = default_folders(ns)
    seen: set[str] = set()
    hits: list[dict] = []
    for f in folders:
        pull_from_masumi(f, seen, hits)
    for f in folders:
        pull_involving(f, seen, hits)

    hits.sort(key=lambda r: r.get("received") or "", reverse=True)
    from_m = [h for h in hits if h.get("from_masumi")]
    by_month = Counter((h["received"][:7] for h in from_m))
    theme_c = Counter()
    for h in from_m:
        for t in h.get("themes") or []:
            theme_c[t] += 1

    # Keep a readable subject digest for from-Masumi
    digest = [
        {
            "received": h["received"],
            "subject": h["subject"],
            "themes": h["themes"],
            "attachments": h["attachments"],
            "preview": (h.get("body_preview") or "")[:400],
        }
        for h in from_m
    ]

    cal = scan_calendar(ns)

    summary = {
        "scanned_at": datetime.now().isoformat(sep=" ", timespec="seconds"),
        "window": "2026-04-15 to 2026-08-15",
        "hits_involving_masumi": len(hits),
        "from_masumi": len(from_m),
        "from_masumi_by_month": dict(sorted(by_month.items())),
        "from_masumi_themes": dict(theme_c),
    }
    (OUT / "masumi_4mo_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUT / "masumi_4mo_from.json").write_text(
        json.dumps(digest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT / "masumi_4mo_hits.json").write_text(
        json.dumps(hits, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT / "masumi_4mo_calendar.json").write_text(
        json.dumps(cal, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log(json.dumps(summary, indent=2))
    log(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
