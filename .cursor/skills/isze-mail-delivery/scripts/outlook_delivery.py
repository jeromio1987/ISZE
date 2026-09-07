"""
ISZE Outlook delivery loop — draft / send / verify / outbox / status.

Authority:
  - draft: always OK when Jerome asked for mail/draft
  - send: only when caller passes --i-was-told-to-send (agent must only set that
    when Jerome's CURRENT message explicitly says send/verstuur)

Never invent a Sent receipt. Ledger appends every action.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import win32com.client  # type: ignore
except ImportError:
    print("FATAL: pywin32 required (win32com.client)", file=sys.stderr)
    sys.exit(2)

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
LEDGER = ISZE / "09_meetings" / "_mail_delivery_ledger.jsonl"
OL_MAIL = 43
OL_FOLDER_OUTBOX = 4
OL_FOLDER_SENT = 5
OL_FOLDER_DRAFTS = 16


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _ledger(event: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    event = {"ts": _now(), **event}
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def _outlook():
    return win32com.client.Dispatch("Outlook.Application")


def _ns():
    return _outlook().GetNamespace("MAPI")


def _att_names(mail) -> list[str]:
    names = []
    for i in range(1, mail.Attachments.Count + 1):
        names.append(mail.Attachments.Item(i).FileName)
    return names


def _to_matches(to_field: str, to_needle: str) -> bool:
    """Match koen.matheussen@… against display name 'Koen Matheussen' or SMTP."""
    if not to_needle:
        return True
    to_l = (to_field or "").lower()
    n = to_needle.lower().strip()
    if n in to_l:
        return True
    local = n.split("@")[0]
    if local in to_l:
        return True
    parts = [p for p in local.replace(".", " ").split() if len(p) > 1]
    return bool(parts) and all(p in to_l for p in parts)


def _ensure_files(paths: list[str]) -> list[Path]:
    out = []
    for p in paths:
        path = Path(p)
        if not path.is_file():
            raise SystemExit(f"MISSING_ATTACH {path}")
        out.append(path)
    return out


def cmd_draft(args: argparse.Namespace) -> int:
    atts = _ensure_files(args.attach or [])
    body = args.body or ""
    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")

    outlook = _outlook()
    mail = outlook.CreateItem(0)
    mail.To = args.to
    mail.Subject = args.subject
    mail.Body = body
    for p in atts:
        mail.Attachments.Add(str(p))
    mail.Save()
    if not args.no_display:
        mail.Display(False)

    payload = {
        "action": "draft",
        "to": args.to,
        "subject": args.subject,
        "attachments": [p.name for p in atts],
        "entry_id": mail.EntryID,
        "displayed": not args.no_display,
        "sent": False,
    }
    _ledger(payload)
    print("STATUS=DRAFTED")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def cmd_send(args: argparse.Namespace) -> int:
    if not args.i_was_told_to_send:
        print(
            "REFUSED: pass --i-was-told-to-send only when Jerome's CURRENT message "
            "explicitly says send/verstuur",
            file=sys.stderr,
        )
        _ledger({"action": "send_refused", "reason": "missing_flag"})
        return 3

    ns = _ns()
    mail = None

    if args.entry_id:
        mail = ns.GetItemFromID(args.entry_id)
    elif args.from_outbox or args.from_drafts:
        folder = ns.GetDefaultFolder(
            OL_FOLDER_OUTBOX if args.from_outbox else OL_FOLDER_DRAFTS
        )
        needle = (args.subject_contains or args.subject or "").lower()
        to_needle = (args.to or "").lower()
        for i in range(1, folder.Items.Count + 1):
            m = folder.Items.Item(i)
            try:
                if m.Class != OL_MAIL:
                    continue
            except Exception:
                continue
            subj = (m.Subject or "").lower()
            to = ""
            try:
                to = (m.To or "").lower()
            except Exception:
                pass
            if needle and needle not in subj:
                continue
            if not _to_matches(to, to_needle):
                continue
            mail = m
            break
        if mail is None:
            print("NOT_FOUND in folder", file=sys.stderr)
            return 4
    else:
        # Build fresh then send
        atts = _ensure_files(args.attach or [])
        body = args.body or ""
        if args.body_file:
            body = Path(args.body_file).read_text(encoding="utf-8")
        outlook = _outlook()
        mail = outlook.CreateItem(0)
        mail.To = args.to
        mail.Subject = args.subject
        mail.Body = body
        for p in atts:
            mail.Attachments.Add(str(p))
        mail.Save()

    subject = mail.Subject
    to = getattr(mail, "To", "") or ""
    atts = _att_names(mail)
    entry = mail.EntryID
    mail.Send()
    _ledger(
        {
            "action": "send_called",
            "to": to,
            "subject": subject,
            "attachments": atts,
            "entry_id": entry,
        }
    )
    print("STATUS=SEND_CALLED")
    # Immediate verify
    return cmd_verify(
        argparse.Namespace(
            to=args.to or to,
            subject_contains=args.subject_contains or subject,
            hours=args.hours or 6,
            attach_names=atts,
        )
    )


def cmd_verify(args: argparse.Namespace) -> int:
    ns = _ns()
    outbox = ns.GetDefaultFolder(OL_FOLDER_OUTBOX)
    sent = ns.GetDefaultFolder(OL_FOLDER_SENT).Items
    sent.Sort("[SentOn]", True)

    to_needle = (args.to or "").lower()
    subj_needle = (args.subject_contains or "").lower()
    want_atts = [a.lower() for a in (args.attach_names or [])]

    # Outbox first
    stuck = []
    for i in range(1, outbox.Items.Count + 1):
        m = outbox.Items.Item(i)
        try:
            if m.Class != OL_MAIL:
                continue
            subj = m.Subject or ""
            to = m.To or ""
        except Exception:
            continue
        if subj_needle and subj_needle.lower() not in subj.lower():
            continue
        if not _to_matches(to, to_needle):
            continue
        stuck.append(
            {
                "subject": subj,
                "to": to,
                "attachments": _att_names(m),
                "entry_id": m.EntryID,
            }
        )

    if stuck:
        payload = {"status": "OUTBOX_STUCK", "items": stuck}
        _ledger({"action": "verify", **payload})
        print("STATUS=OUTBOX_STUCK")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 1

    cutoff = datetime.now() - timedelta(hours=float(args.hours or 48))
    hits = []
    for i in range(1, min(sent.Count, 400) + 1):
        try:
            m = sent.Item(i)
            if m.Class != OL_MAIL:
                continue
            so = m.SentOn
            if so is not None:
                so_naive = so.replace(tzinfo=None) if getattr(so, "tzinfo", None) else so
                if so_naive < cutoff:
                    if hits:
                        break
                    continue
            to = m.To or ""
            subj = m.Subject or ""
            if not _to_matches(to, to_needle):
                continue
            if subj_needle and subj_needle.lower() not in subj.lower():
                continue
            names = _att_names(m)
            if want_atts:
                lower = [n.lower() for n in names]
                if not all(any(w in n for n in lower) for w in want_atts):
                    # soft: require at least count match if names fuzzy
                    if len(names) < len(want_atts):
                        continue
            hits.append(
                {
                    "sent_on": str(so),
                    "to": to,
                    "subject": subj,
                    "attachments": names,
                    "entry_id": m.EntryID,
                }
            )
            if len(hits) >= 5:
                break
        except Exception:
            continue

    if not hits:
        payload = {"status": "NOT_SENT", "to": args.to, "subject_contains": args.subject_contains}
        _ledger({"action": "verify", **payload})
        print("STATUS=NOT_SENT")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 2

    payload = {"status": "SENT", "hits": hits}
    _ledger({"action": "verify", **payload})
    print("STATUS=SENT")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def cmd_outbox(_: argparse.Namespace) -> int:
    ns = _ns()
    outbox = ns.GetDefaultFolder(OL_FOLDER_OUTBOX)
    items = []
    for i in range(1, outbox.Items.Count + 1):
        m = outbox.Items.Item(i)
        try:
            if m.Class != OL_MAIL:
                continue
            items.append(
                {
                    "subject": m.Subject,
                    "to": m.To,
                    "attachments": _att_names(m),
                    "size": m.Size,
                    "entry_id": m.EntryID,
                }
            )
        except Exception as e:
            items.append({"error": str(e)})
    print(json.dumps({"outbox_count": len(items), "items": items}, indent=2, ensure_ascii=False))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    # last ledger lines + outbox count
    lines = []
    if LEDGER.is_file():
        lines = LEDGER.read_text(encoding="utf-8").splitlines()[-30:]
    ns = _ns()
    out_n = ns.GetDefaultFolder(OL_FOLDER_OUTBOX).Items.Count
    print(json.dumps({"outbox_count": out_n, "ledger_tail": [json.loads(x) for x in lines if x.strip()]}, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="ISZE Outlook delivery loop")
    sp = ap.add_subparsers(dest="cmd", required=True)

    d = sp.add_parser("draft")
    d.add_argument("--to", required=True)
    d.add_argument("--subject", required=True)
    d.add_argument("--body", default="")
    d.add_argument("--body-file")
    d.add_argument("--attach", action="append", default=[])
    d.add_argument("--no-display", action="store_true")
    d.set_defaults(func=cmd_draft)

    s = sp.add_parser("send")
    s.add_argument(
        "--i-was-told-to-send",
        action="store_true",
        help="REQUIRED: only when Jerome current message says send/verstuur",
    )
    s.add_argument("--to")
    s.add_argument("--subject")
    s.add_argument("--subject-contains")
    s.add_argument("--body", default="")
    s.add_argument("--body-file")
    s.add_argument("--attach", action="append", default=[])
    s.add_argument("--entry-id")
    s.add_argument("--from-outbox", action="store_true")
    s.add_argument("--from-drafts", action="store_true")
    s.add_argument("--hours", type=float, default=6)
    s.set_defaults(func=cmd_send)

    v = sp.add_parser("verify")
    v.add_argument("--to")
    v.add_argument("--subject-contains", required=True)
    v.add_argument("--hours", type=float, default=48)
    v.add_argument("--attach-names", nargs="*", default=[])
    v.set_defaults(func=cmd_verify)

    o = sp.add_parser("outbox")
    o.set_defaults(func=cmd_outbox)

    st = sp.add_parser("status")
    st.add_argument("--hours", type=float, default=48)
    st.set_defaults(func=cmd_status)

    args = ap.parse_args()
    # argparse quirk: send flag required=True on store_true is awkward — check manually
    if args.cmd == "send" and not getattr(args, "i_was_told_to_send", False):
        print("REFUSED: --i-was-told-to-send required", file=sys.stderr)
        return 3
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
