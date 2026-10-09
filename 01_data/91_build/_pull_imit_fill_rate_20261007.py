"""Read-only mailbox pull for the two missing IMIT fill-rate mails (2026-10-07).

Finds, from Outlook:
  - "IMIT Fill Rate to ISZE - July 2026"   (Peeraya Sawangsaensuk, 08 Sep 2026)
  - "IMIT Fill Rate to ISZE - April 2026"  (Peeraya Sawangsaensuk, 26 May 2026)

For each: reports whether the numbers sit in the message body (text / pasted table),
in the HTML body, or in an attachment (incl. .msg / .png / .jpg). Saves EVERY
attachment (any extension) into the target folder, and walks one level into any
embedded .msg so nested items are visible. Nothing is sent, moved, flagged or replied.

Scan pattern copied from `_pull_iml_delay_mail_20261007.py` (proven 2026-10-07):
cap each folder at 4,000 items, skip system folders by name before touching Items,
Sort("[ReceivedTime]", True) with a plain loop (no DASL Restrict), depth-cap at 4,
wrap every folder in try/except.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_kpi_panel_20261007\imit_fill_rate")
OUT.mkdir(parents=True, exist_ok=True)

# subject fragments we want
WANTED = [
    re.compile(r"imit\s+fill\s+rate", re.I),
    re.compile(r"fill\s+rate\s+to\s+isze", re.I),
]

SENDER_HINTS = ("sawangsaensuk", "imit", "peeraya")

SKIP_FOLDERS = {"Sync Issues", "RSS Feeds", "Junk Email", "Deleted Items",
                "Calendar", "Contacts", "Tasks", "Notes", "Conversation History",
                "Drafts", "Outbox"}

# attachment extensions Outlook could have skipped in the earlier save
NOTE_EXTS = (".msg", ".png", ".jpg", ".jpeg", ".pdf", ".xlsx", ".xls", ".csv", ".txt", ".eml")


def safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._ -]", "_", name)[:120]


def save_attachments(item, dest_dir: Path, rows: list[dict], depth: int = 0) -> None:
    """Save every attachment; recurse one level into embedded messages."""
    try:
        n = item.Attachments.Count
    except Exception:
        return
    for a in range(1, n + 1):
        try:
            att = item.Attachments.Item(a)
            fn = str(att.FileName or "")
            atype = int(getattr(att, "Type", 0) or 0)  # 5 = olEmbeddedItem
        except Exception as exc:
            rows.append({"name": "?", "error": str(exc)})
            continue
        row = {"name": fn, "type": atype, "saved": None, "nested": []}
        dest = dest_dir / safe(fn) if fn else None
        try:
            if dest is not None:
                i = 2
                base = dest
                while dest.exists():
                    dest = base.with_name(f"{base.stem}_{i}{base.suffix}")
                    i += 1
                att.SaveAsFile(str(dest))
                row["saved"] = str(dest)
        except Exception as exc:
            row["saved"] = f"FAIL {exc}"
        # embedded message / .msg -> look inside
        if atype == 5 or fn.lower().endswith(".msg"):
            try:
                sub = att  # _MailItem via EmbeddedMsg
                if depth < 2:
                    save_attachments(sub, dest_dir / safe(fn or "embedded"), row["nested"], depth + 1)
            except Exception as exc:
                row["nested"].append({"error": str(exc)})
        rows.append(row)


def html_to_text(html: str) -> str:
    if not html:
        return ""
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    t = re.sub(r"(?i)</(p|div|tr|li|h[1-6])>", "\n", t)
    t = re.sub(r"(?i)</t[dh]>", " | ", t)
    t = re.sub(r"(?s)<[^>]+>", "", t)
    t = re.sub(r"&nbsp;", " ", t)
    t = re.sub(r"&amp;", "&", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


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
                cnt = 0
                for it in items:
                    cnt += 1
                    if cnt > 4000:
                        break
                    try:
                        subj = str(getattr(it, "Subject", "") or "")
                    except Exception:
                        continue
                    if not any(rx.search(subj) for rx in WANTED):
                        continue
                    try:
                        sender = str(getattr(it, "SenderName", "") or "")
                        email = ""
                        try:
                            email = str(it.SenderEmailAddress or "")
                        except Exception:
                            pass
                        blob = (sender + " " + email).lower()
                        if not any(h in blob for h in SENDER_HINTS):
                            continue
                        hits.append({
                            "when": str(getattr(it, "ReceivedTime", "") or ""),
                            "store": store.DisplayName,
                            "folder": name,
                            "sender": sender,
                            "email": email,
                            "subject": subj,
                            "unread": bool(getattr(it, "UnRead", False)),
                            "has_attachments": bool(getattr(it, "Attachments", None) and it.Attachments.Count),
                            "body": html_to_text(str(getattr(it, "HTMLBody", "") or "")),
                            "body_raw": str(getattr(it, "Body", "") or ""),
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

    hits.sort(key=lambda h: h["when"], reverse=True)
    print(f"matching mails: {len(hits)}")

    manifest = []
    for idx, h in enumerate(hits):
        stamp = re.sub(r"[^0-9]", "", h["when"][:10]) or "nodate"
        nameslug = safe(h["subject"])[:70]
        dest_dir = OUT / f"{stamp}_{nameslug}"
        dest_dir.mkdir(parents=True, exist_ok=True)

        att_rows: list[dict] = []
        save_attachments(h["item"], dest_dir, att_rows)

        # dump bodies for inspection
        (dest_dir / "body_text.txt").write_text(h["body"], encoding="utf-8")
        (dest_dir / "body_raw.txt").write_text(h["body_raw"], encoding="utf-8")

        row = {k: v for k, v in h.items() if k != "item"}
        row["attachments"] = att_rows
        row["saved_dir"] = str(dest_dir)
        row["body_len"] = len(h["body"])
        del row["body_raw"]
        manifest.append(row)

        print("\n=== ", h["subject"], "|", h["when"], "|", h["sender"])
        print("    folder:", h["folder"], "| store:", h["store"], "| unread:", h["unread"])
        print("    attachments:", [(a.get("name"), a.get("type"), "SAVED" if str(a.get("saved","")).startswith(str(OUT)) else a.get("saved")) for a in att_rows])
        print("    body length:", len(h["body"]), "chars")
        print("    body head:", repr(h["body"][:300]))

    (OUT / "IMIT_MANIFEST.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    print("\nOUT", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
