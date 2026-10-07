"""Read-only mailbox pull for the IML delay proof (2026-10-07).

Grabs, from Outlook:
  - the WK41 per-distributor "BO overview ..." mails (customer-attributed)
  - Natalie's central "Backlog info file VP - update WK41" (already saved elsewhere; re-saved here for one folder)
  - IMIT "Fill Rate to ISZE" reports
  - Iceland / BO lines and fill rate
  - the "Delivery time request" and "Part availability" threads

Never Send. No item is modified, moved, flagged or replied to.
Discovery was done in the agent browser (Outlook web open); this saves the attachments.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_iml_delay_wk41_20261007")
OUT.mkdir(parents=True, exist_ok=True)

# subject fragments we want, with a bucket name
WANTED = [
    ("bo_overview", re.compile(r"bo overview", re.I)),
    ("bo_overview", re.compile(r"backlog info file vp", re.I)),
    ("fill_rate", re.compile(r"fill rate", re.I)),
    ("fill_rate", re.compile(r"bo lines and fill rate", re.I)),
    ("delivery_time", re.compile(r"delivery time request", re.I)),
    ("part_availability", re.compile(r"part availability", re.I)),
]

SENDER_HINTS = ("natalie", "sawangsaensuk", "imit", "cheung", "zekri")

SKIP_FOLDERS = {"Sync Issues", "RSS Feeds", "Junk Email", "Deleted Items",
                "Calendar", "Contacts", "Tasks", "Notes", "Conversation History"}


def safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._ -]", "_", name)[:120]


def main() -> int:
    import win32com.client  # type: ignore

    ns = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    hits: list[dict] = []

    for store in ns.Stores:
        try:
            root = store.GetRootFolder()
        except Exception:
            continue

        def walk(folder, depth=0):
            if depth > 4:
                return
            try:
                name = folder.Name
            except Exception:
                return
            if name in SKIP_FOLDERS:
                return
            try:
                items = folder.Items
                items.Sort("[ReceivedTime]", True)
                n = 0
                for it in items:
                    n += 1
                    if n > 4000:
                        break
                    try:
                        subj = str(getattr(it, "Subject", "") or "")
                    except Exception:
                        continue
                    bucket = None
                    for b, rx in WANTED:
                        if rx.search(subj):
                            bucket = b
                            break
                    if bucket is None:
                        continue
                    try:
                        rec = it.ReceivedTime
                        rec_s = str(rec or "")
                        sender = str(getattr(it, "SenderName", "") or "")
                        email = ""
                        try:
                            email = str(it.SenderEmailAddress or "")
                        except Exception:
                            pass
                        blob = (sender + " " + email).lower()
                        if bucket in ("bo_overview", "delivery_time", "part_availability"):
                            if not any(h in blob for h in SENDER_HINTS):
                                continue
                        atts = []
                        for a in range(1, it.Attachments.Count + 1):
                            atts.append(it.Attachments.Item(a).FileName)
                        hits.append({
                            "bucket": bucket, "when": rec_s, "store": store.DisplayName,
                            "folder": name, "sender": sender, "email": email,
                            "subject": subj, "atts": atts, "item": it,
                        })
                    except Exception:
                        continue
            except Exception:
                pass
            try:
                for sub in folder.Folders:
                    walk(sub, depth + 1)
            except Exception:
                pass

        walk(root)

    hits.sort(key=lambda h: h["when"], reverse=True)
    print(f"candidate mails: {len(hits)}")

    manifest = []
    seen_att = set()
    for h in hits[:400]:
        stamp = re.sub(r"[^0-9]", "", h["when"][:10]) or "nodate"
        buck = OUT / h["bucket"]
        buck.mkdir(parents=True, exist_ok=True)
        row = {k: v for k, v in h.items() if k != "item"}
        row["saved"] = []
        for a in range(1, h["item"].Attachments.Count + 1):
            try:
                att = h["item"].Attachments.Item(a)
                fn = att.FileName
            except Exception:
                continue
            if not fn.lower().endswith((".xlsx", ".xls", ".csv", ".pdf")):
                continue
            key = (h["bucket"], fn, stamp)
            if key in seen_att:
                continue
            seen_att.add(key)
            dest = buck / f"{stamp}_{safe(fn)}"
            i = 2
            while dest.exists():
                dest = buck / f"{stamp}_{i}_{safe(fn)}"
                i += 1
            try:
                att.SaveAsFile(str(dest))
                row["saved"].append(str(dest))
            except Exception as exc:
                row["saved"].append(f"FAIL {fn}: {exc}")
        manifest.append(row)

    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")

    # short human summary
    from collections import Counter
    c = Counter(m["bucket"] for m in manifest)
    print("mails by bucket:", dict(c))
    files = sorted(str(p.relative_to(OUT)) for p in OUT.rglob("*") if p.is_file())
    print(f"files on disk: {len(files)}")
    for f in files[:60]:
        print("  ", f)
    print("OUT", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
