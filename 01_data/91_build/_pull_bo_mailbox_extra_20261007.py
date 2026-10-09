"""Read-only mailbox pull - the five named mails plus SPI/KPI, IMIT fill-rate and
Iceland fill/BO sweeps. Saves attachments only.

Pattern copied from _pull_iml_delay_mail_20261007.py / _pull_natalie_wk41_bo_20261007.py:
plain Python loop after items.Sort, per-folder cap, skip folders by name, depth cap,
try/except around every folder. NO Restrict / DASL (that is what crashed earlier).

Never send, move, flag, delete or reply.
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_bo_scrape_3m_20261007\mailbox_extra")
OUT.mkdir(parents=True, exist_ok=True)
SINCE = datetime(2025, 9, 15)          # 12+ months of SPI & KPI
PER_FOLDER_CAP = 3500
MAX_DEPTH = 5

SKIP_FOLDERS = {"Sync Issues", "RSS Feeds", "Junk Email", "Deleted Items", "Calendar",
                "Contacts", "Tasks", "Notes", "Conversation History",
                "Conversation Action Settings", "Quick Step Settings", "Drafts", "Outbox"}

# subject families we want to SEE (loose)
SUBJ = {
    "fill_rate":  re.compile(r"fill\s*rate", re.I),
    "spi_kpi":    re.compile(r"spi\s*&?\s*kpi|kpi\s*check\s*sheet|check\s*sheet", re.I),
    "iceland":    re.compile(r"iceland", re.I),
    "bo_lines":   re.compile(r"bo\s*lines|back\s*order|backorder|backlog", re.I),
}
SEND = {
    "IMIT":    re.compile(r"sawangsaensuk|imit", re.I),
    "CHEUNG":  re.compile(r"cheung", re.I),
    "BAUMANN": re.compile(r"baumann", re.I),
    "JACOBS":  re.compile(r"jacobs", re.I),
}
# what we actually SAVE attachments for
SAVE_IF = [
    ("imit_fill",  lambda s, sn, em: bool(SUBJ["fill_rate"].search(s))),
    ("spi_kpi",    lambda s, sn, em: bool(SUBJ["spi_kpi"].search(s))),
    ("iceland",    lambda s, sn, em: bool(SUBJ["iceland"].search(s) and re.search(r"fill|bo|backlog|order", s, re.I))),
    ("bo_lines",   lambda s, sn, em: bool(re.search(r"bo\s*lines|fill\s*rate", s, re.I))),
]

def safe(n: str) -> str:
    return re.sub(r"[^A-Za-z0-9._ -]", "_", str(n))[:110]

def norm(s: str) -> str:
    return re.sub(r"^(RE|FW|FWD|AW|TR|SV):\s*", "", str(s).strip(), flags=re.I).strip()

def main() -> int:
    import win32com.client  # type: ignore

    ns = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    seen_mails = []      # candidates (subject or sender matched)
    scanned = 0
    t0 = time.time()

    for store in ns.Stores:
        try:
            root = store.GetRootFolder()
        except Exception as exc:
            print("store fail", store.DisplayName, exc); continue
        print("STORE", store.DisplayName, flush=True)

        def walk(folder, depth=0):
            nonlocal scanned
            if depth > MAX_DEPTH:
                return
            try:
                name = folder.Name
            except Exception:
                return
            if name in SKIP_FOLDERS:
                return
            try:
                items = folder.Items
                try:
                    items.Sort("[ReceivedTime]", True)
                except Exception:
                    pass
                n = 0
                for it in items:
                    n += 1
                    if n > PER_FOLDER_CAP:
                        break
                    try:
                        subj = str(getattr(it, "Subject", "") or "")
                    except Exception:
                        continue
                    try:
                        sender = str(getattr(it, "SenderName", "") or "")
                    except Exception:
                        sender = ""
                    email = ""
                    try:
                        email = str(it.SenderEmailAddress or "")
                    except Exception:
                        pass
                    blob = sender + " " + email
                    hit_subj = [k for k, rx in SUBJ.items() if rx.search(subj)]
                    hit_send = [k for k, rx in SEND.items() if rx.search(blob)]
                    if not hit_subj and not hit_send:
                        continue
                    try:
                        rec = str(it.ReceivedTime)[:19]
                    except Exception:
                        rec = ""
                    try:
                        recdt = datetime.strptime(rec[:10], "%Y-%m-%d")
                        if recdt < SINCE:
                            continue
                    except Exception:
                        recdt = None
                    try:
                        atts = [str(it.Attachments.Item(a).FileName)
                                for a in range(1, it.Attachments.Count + 1)]
                    except Exception:
                        atts = []
                    scanned += 1
                    seen_mails.append({
                        "received": rec, "store": str(store.DisplayName), "folder": str(name),
                        "sender": sender, "email": email, "subject": subj, "atts": atts,
                        "hit_subj": hit_subj, "hit_send": hit_send, "item": it,
                    })
            except Exception:
                pass
            try:
                for sub in folder.Folders:
                    walk(sub, depth + 1)
            except Exception:
                pass

        walk(root)
        print(f"  store done: {len(seen_mails)} candidates so far", flush=True)

    print(f"TOTAL candidates: {len(seen_mails)} in {time.time()-t0:.0f}s", flush=True)

    # newest first, dedupe on (norm subject, sender, date, attachment set)
    seen_mails.sort(key=lambda h: h["received"], reverse=True)
    dedup = {}
    for h in seen_mails:
        key = (norm(h["subject"]).lower(), h["sender"].lower(), h["received"][:10],
               tuple(sorted(h["atts"])))
        if key not in dedup:
            dedup[key] = h
    uniq = list(dedup.values())
    print(f"unique candidates: {len(uniq)}", flush=True)

    manifest = []
    saved_total = 0
    for h in uniq:
        subj_raw = h["subject"]
        labels = [lab for lab, fn in SAVE_IF if fn(subj_raw, h["sender"], h["email"])]
        row = {
            "received": h["received"], "sender": h["sender"], "email": h["email"],
            "subject": subj_raw, "folder": h["folder"], "store": h["store"],
            "attachments": h["atts"], "match": labels, "hit_subj": h["hit_subj"],
            "hit_send": h["hit_send"], "saved": [],
        }
        if labels and h["atts"]:
            m = re.match(r"(\d{4})-(\d{2})-(\d{2})", h["received"])
            stamp = (m.group(1) + m.group(2) + m.group(3)) if m else "nodate"
            who = safe(h["sender"].split(",")[0].split("(")[0].strip().replace(" ", ""))[:22] or "unknown"
            for fn in h["atts"]:
                if not fn.lower().endswith((".xlsx", ".xls", ".csv", ".pdf", ".zip")):
                    row["saved"].append("SKIP(non-sheet) " + fn); continue
                dest = OUT / f"{who}_{stamp}_{safe(fn)}"
                i = 2
                while dest.exists():
                    dest = OUT / f"{who}_{stamp}_{i}_{safe(fn)}"; i += 1
                try:
                    h["item"].Attachments.Item(
                        h["atts"].index(fn) + 1).SaveAsFile(str(dest))
                    row["saved"].append(str(dest)); saved_total += 1
                except Exception as exc:
                    row["saved"].append(f"FAIL {fn}: {exc}")
        # short body only for kept mails
        if labels:
            try:
                row["body"] = str(h["item"].Body or "")[:4000]
            except Exception:
                row["body"] = ""
        manifest.append({k: v for k, v in row.items() if k != "item"})

    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False),
                                       encoding="utf-8")

    interesting = [r for r in manifest if r["match"]]
    print("=" * 90)
    print(f"interesting mails: {len(interesting)}  attachments saved: {saved_total}")
    for r in interesting:
        print(f"{r['received'][:10]} | {r['sender'][:26]:26} | {r['match']} | {r['subject'][:66]}")
        for s in r["saved"]:
            print("      ->", Path(s).name if not s.startswith(("SKIP", "FAIL")) else s)
    print("=" * 90)
    from collections import Counter
    print("by family:", Counter(l for r in interesting for l in r["match"]))
    print("spi_kpi months found:", sorted({r["received"][:7] for r in interesting if "spi_kpi" in r["match"]}))
    print("IMIT fill-rate mails:", [(r["received"][:10], r["subject"][:52]) for r in interesting
                                    if "imit_fill" in r["match"] or ("fill_rate" in r["hit_subj"])])
    print("OUT", OUT)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
