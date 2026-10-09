"""Save the IMIT 'Fill Rate to ISZE' series (read-only), no folder cap.

The first pull missed the April 2026 mail because it sat beyond the 4,000-item
folder cap. This run scans each folder to the end, matches the exact IMIT
fill-rate subjects, and saves EVERY attachment (any extension) plus the body.

Nothing is sent, moved, flagged or replied.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_kpi_panel_20261007\imit_fill_rate")
OUT.mkdir(parents=True, exist_ok=True)

RX = re.compile(r"imit\s+fill\s+rate\s+to\s+isze", re.I)

SKIP_FOLDERS = {"Sync Issues", "RSS Feeds", "Conversation History",
                "Outbox", "Drafts"}


def safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._ -]", "_", name)[:110]


def html_to_text(html: str) -> str:
    if not html:
        return ""
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    t = re.sub(r"(?i)</(p|div|tr|li|h[1-6])>", "\n", t)
    t = re.sub(r"(?i)</t[dh]>", " | ", t)
    t = re.sub(r"(?s)<[^>]+>", "", t)
    t = t.replace("&nbsp;", " ").replace("&amp;", "&")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def main() -> int:
    import win32com.client  # type: ignore

    ns = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    hits: list[dict] = []

    for store in ns.Stores:
        try:
            sname = store.DisplayName
            root = store.GetRootFolder()
        except Exception:
            continue

        def walk(folder, depth=0):
            if depth > 6:
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
                for it in items:                     # NO cap -> reaches older mail
                    try:
                        subj = str(getattr(it, "Subject", "") or "")
                    except Exception:
                        continue
                    if not RX.search(subj):
                        continue
                    try:
                        eff = str(getattr(it, "ReceivedTime", "") or "")[:19]
                        sender = str(getattr(it, "SenderName", "") or "")
                        # thread root date for subject period
                        hits.append({
                            "received": eff, "store": sname, "folder": name,
                            "sender": sender, "subject": subj,
                            "unread": bool(getattr(it, "UnRead", False)),
                            "html": str(getattr(it, "HTMLBody", "") or ""),
                            "plain": str(getattr(it, "Body", "") or ""),
                            "item": it,
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

    hits.sort(key=lambda h: h["received"], reverse=True)
    print(f"IMIT fill-rate mails found: {len(hits)}")

    manifest = []
    for h in hits:
        stamp = re.sub(r"[^0-9]", "", h["received"][:10]) or "nodate"
        period = safe(h["subject"].split("-")[-1].strip())[:24]
        dest_dir = OUT / f"{stamp}_{period}"
        dest_dir.mkdir(parents=True, exist_ok=True)

        att_rows = []
        for a in range(1, (h["item"].Attachments.Count or 0) + 1):
            try:
                att = h["item"].Attachments.Item(a)
                fn = str(att.FileName or "")
                atype = int(getattr(att, "Type", 0) or 0)
            except Exception as exc:
                att_rows.append({"name": "?", "error": str(exc)})
                continue
            row = {"name": fn, "type": atype, "saved": None,
                   "size": int(getattr(att, "Size", 0) or 0)}
            if fn:
                dest = dest_dir / safe(fn)
                i = 2
                base = dest
                while dest.exists():
                    dest = base.with_name(f"{base.stem}_{i}{base.suffix}")
                    i += 1
                try:
                    att.SaveAsFile(str(dest))
                    row["saved"] = str(dest)
                except Exception as exc:
                    row["saved"] = f"FAIL {exc}"
            att_rows.append(row)

        body = html_to_text(h["html"])
        (dest_dir / "body_text.txt").write_text(body, encoding="utf-8")
        (dest_dir / "body_plain.txt").write_text(h["plain"], encoding="utf-8")

        row = {k: v for k, v in h.items() if k not in ("item", "html", "plain")}
        row["attachments"] = att_rows
        row["body_len"] = len(body)
        row["saved_dir"] = str(dest_dir)
        manifest.append(row)
        print(f"  {h['received']} | {h['sender'][:26]:26s} | {h['subject'][:40]:40s} "
              f"| atts={[a.get('name') for a in att_rows]}")

    (OUT / "IMIT_MANIFEST.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    print("OUT", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
