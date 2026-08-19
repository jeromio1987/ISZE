#!/usr/bin/env python3
"""Tomoe IDS mails ~Jun–Aug 2026: split Excel / process / averages."""
from datetime import datetime
from pathlib import Path
import json
import re

import win32com.client

OUT = Path(__file__).resolve().parent
CUTOFF = datetime(2026, 5, 1)
END = datetime(2026, 8, 16)

KEEP_SUBJ = re.compile(r"ids|dealer standard|evaluation result|excel|split|average|ranking", re.I)
TOMOE = re.compile(r"tomoe", re.I)


def to_dt(rt):
    try:
        if hasattr(rt, "year"):
            return datetime(rt.year, rt.month, rt.day, rt.hour, rt.minute)
        return datetime.fromisoformat(str(rt)[:19])
    except Exception:
        return None


def scan(folder, label, rows, limit=4000):
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
            if rec < CUTOFF:
                break
            if rec > END:
                continue
            subj = str(getattr(it, "Subject", "") or "")
            sender = str(getattr(it, "SenderName", "") or "") + " " + str(getattr(it, "SenderEmailAddress", "") or "")
            to = str(getattr(it, "To", "") or "")
            cc = str(getattr(it, "CC", "") or "")
            blob_people = f"{sender} {to} {cc}"
            if not TOMOE.search(blob_people) and not TOMOE.search(subj):
                continue
            if not KEEP_SUBJ.search(subj) and "ids" not in (str(getattr(it, "Body", "") or "")[:400]).lower():
                # still keep if Tomoe + IDS in body start
                body0 = str(getattr(it, "Body", "") or "")[:800]
                if not re.search(r"\bids\b|dealer standard|excel", body0, re.I):
                    continue
            body = re.sub(r"\s+", " ", str(getattr(it, "Body", "") or "")[:900])
            rows.append({
                "folder": label,
                "when": rec.isoformat(sep=" ")[:16],
                "subject": subj[:200],
                "from": sender[:120],
                "preview": body[:700],
            })
        except Exception:
            continue


outlook = win32com.client.Dispatch("Outlook.Application")
ns = outlook.GetNamespace("MAPI")
rows = []
scan(ns.GetDefaultFolder(6), "inbox", rows, 5000)
scan(ns.GetDefaultFolder(5), "sent", rows, 2500)
(OUT / "tomoe_ids_mails.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
txt = []
for r in sorted(rows, key=lambda x: x["when"]):
    txt.append(f"{r['when']} [{r['folder']}] {r['subject']}\n  from: {r['from']}\n  {r['preview'][:500]}\n")
(OUT / "tomoe_ids_mails.txt").write_text("\n".join(txt), encoding="utf-8")
print("kept", len(rows))
for r in sorted(rows, key=lambda x: x["when"]):
    print(r["when"], r["folder"], "|", r["subject"][:90])
