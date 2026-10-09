"""Mail volume by month — read-only, own mailbox, counts only.

Answers one question: how much mail arrives per month, and how does a month
compare with the same month a year earlier?

WHAT THIS DOES
    Walks the local Outlook Inbox and Sent (and their subfolders, own store
    only), reads the received/sent time of every message, and writes a monthly
    count summary. Nothing else.

WHAT THIS NEVER DOES
    - never stores a subject, a body, a sender, or an attachment
    - never sends, moves, deletes or marks anything read
    - never leaves this machine
    - never touches the shared Sales / Parts mailboxes (refused, same as the
      G0a collector)

HOW IT READS (and why this way)
    One enumeration per folder for the whole range, walking the items in date
    order, rather than one Restrict per month. The per-month approach re-opens
    the Outlook connection dozens of times and takes many minutes; a single pass
    per folder finishes in seconds. Only Class / ReceivedTime / Attachments.Count
    is touched — never the subject or the body.

WHY IT EXISTS
    interaction_fact.parquet counts distributor-related mail only, and it holds
    a single 12-month window. That cannot answer "less mail than the same month
    last year". This counts every message, by month, for as far back as the
    local Outlook store actually holds — and it says plainly where that stops.

USAGE
    python measure_mail_volume.py --dry-run --since 2023-08-01
    python measure_mail_volume.py --since 2023-08-01

OUT
    01_data/17_interactions/mail_volume_monthly.json
    01_data/17_interactions/mail_volume_monthly.csv

Read-only. Safe to re-run; a re-run overwrites the two summary files only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(os.environ.get("ISZE_ROOT", r"C:\Users\jerom\Desktop\claude\ISZE"))
OUT_DIR = ROOT / "01_data" / "17_interactions"
OUT_JSON = OUT_DIR / "mail_volume_monthly.json"
OUT_CSV = OUT_DIR / "mail_volume_monthly.csv"

OL_FOLDER = {"inbox": 6, "sent": 5}
OL_MAIL_CLASS = 43
REFUSED_STORE_TOKENS = ("sales", "parts")


def _safe(getter, default=None):
    try:
        return getter()
    except Exception:
        return default


def _connect():
    import win32com.client

    app = win32com.client.Dispatch("Outlook.Application")
    ns = app.GetNamespace("MAPI")
    return app, ns


def _own_store_check(ns) -> str:
    store_name = _safe(lambda: ns.GetDefaultFolder(OL_FOLDER["inbox"]).Store.DisplayName, "") or ""
    store_l = store_name.lower()
    if any(tok == store_l or tok in store_l.split() for tok in REFUSED_STORE_TOKENS):
        raise SystemExit(
            f"REFUSED: store '{store_name}' looks like a shared Sales/Parts mailbox. Own mailbox only."
        )
    return store_name


def _folder_tree(root_key: str, root_folder):
    """Yield (path, folder) for the root and every nested folder, own store only."""
    yield root_key, root_folder

    def _recurse(folder, path: str):
        folders = _safe(lambda: folder.Folders)
        if folders is None:
            return
        n = int(_safe(lambda: folders.Count, 0) or 0)
        for i in range(1, n + 1):
            sub = _safe(lambda i=i: folders.Item(i))
            if sub is None:
                continue
            store = (_safe(lambda: sub.Store.DisplayName, "") or "").lower()
            if any(tok == store or tok in store.split() for tok in REFUSED_STORE_TOKENS):
                print(f"  SKIP refused store under {path}: {store}")
                continue
            name = _safe(lambda: sub.Name, "") or f"sub{i}"
            yield from _recurse(sub, f"{path}/{name}")

    yield from _recurse(root_folder, root_key)


def measure(args) -> int:
    print("measure_mail_volume.py - read-only monthly counts (no content stored)")

    app, ns = _connect()
    store_name = _own_store_check(ns)
    print(f"store: {store_name}")

    since = datetime.strptime(args.since, "%Y-%m-%d")
    until = datetime.now() + timedelta(days=1)
    cutoff = since
    months: dict[str, dict[str, int]] = defaultdict(lambda: {"in": 0, "out": 0, "with_attach": 0})
    seen = 0
    errors = 0
    min_seen = None
    max_seen = None
    reached_back = False

    for root_key in ("inbox", "sent"):
        _, ns2 = _connect()
        root = ns2.GetDefaultFolder(OL_FOLDER[root_key])
        tree = list(_folder_tree(root_key, root))
        print(f"  {root_key}: {len(tree)} folder(s)")

        # Sent items usually have an empty ReceivedTime, so the date to read and
        # sort on differs by folder: SentOn for Sent, ReceivedTime for Inbox.
        is_sent = root_key == "sent"
        sort_field = "[SentOn]" if is_sent else "[ReceivedTime]"

        for path, folder in tree:
            items = _safe(lambda: folder.Items)
            if items is None:
                continue
            _safe(lambda: items.Sort(sort_field, True))
            count = int(_safe(lambda: items.Count, 0) or 0)
            i = 1
            while i <= count:
                msg = _safe(lambda i=i: items.Item(i))
                if msg is None:
                    errors += 1
                    i += 1
                    continue
                try:
                    if _safe(lambda: msg.Class, 0) != OL_MAIL_CLASS:
                        i += 1
                        continue
                    received = _safe(lambda: msg.SentOn) if is_sent else _safe(lambda: msg.ReceivedTime)
                    if received is None:
                        errors += 1
                        i += 1
                        continue
                    dt = datetime(received.year, received.month, received.day)
                    if dt < cutoff:
                        # Sorted newest-first: everything after this is older.
                        reached_back = True
                        break
                    if dt > until:
                        i += 1
                        continue
                    key = dt.strftime("%Y-%m")
                    direction = "out" if path.split("/", 1)[0] == "sent" else "in"
                    months[key][direction] += 1
                    if int(_safe(lambda: msg.Attachments.Count, 0) or 0) > 0:
                        months[key]["with_attach"] += 1
                    seen += 1
                    min_seen = dt if min_seen is None or dt < min_seen else min_seen
                    max_seen = dt if max_seen is None or dt > max_seen else max_seen
                except Exception as exc:
                    errors += 1
                    if errors <= 5:
                        print(f"  item error: {exc}")
                i += 1
            print(f"    {path} done | seen {seen:,}"
                  + (" (reached the since-date)" if reached_back else ""))
            reached_back = False

    if not months:
        print("nothing found")
        return 0

    keys = sorted(months)
    rows = []
    for m in keys:
        b = months[m]
        rows.append({
            "month": m,
            "in": b["in"],
            "out": b["out"],
            "total": b["in"] + b["out"],
            "with_attach": b["with_attach"],
        })

    by_key = {r["month"]: r for r in rows}
    for r in rows:
        y, mo = r["month"].split("-")
        prev = f"{int(y) - 1}-{mo}"
        if prev in by_key:
            r["prev_year_total"] = by_key[prev]["total"]
            r["yoy_delta"] = r["total"] - by_key[prev]["total"]
            r["yoy_pct"] = (
                round((r["total"] - by_key[prev]["total"]) / by_key[prev]["total"] * 100, 1)
                if by_key[prev]["total"] else None
            )

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "store": store_name,
        "scope": "own mailbox, Inbox + Sent + subfolders, every message (no allow-list filter)",
        "contains_message_content": False,
        "counts_by": "month and direction",
        "coverage": {
            "earliest_month": keys[0],
            "latest_month": keys[-1],
            "months": len(keys),
            "messages_counted": seen,
            "errors": errors,
        },
        "months": rows,
        "year_on_year_available": any("prev_year_total" in r for r in rows),
    }

    print(f"\ncounted {seen:,} messages over {len(keys)} months ({keys[0]} .. {keys[-1]}), errors {errors}")
    print("year-on-year pairs:", "yes" if summary["year_on_year_available"] else
          "NO — the local store does not reach back far enough")

    if args.dry_run:
        print("\nDRY RUN — nothing written.")
        for r in rows:
            extra = f"   yoy {r['yoy_delta']:+d} ({r['yoy_pct']:+}%)" if "yoy_delta" in r else ""
            print(f"  {r['month']}  in {r['in']:>5}  out {r['out']:>5}  total {r['total']:>5}{extra}")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    header = ["month", "in", "out", "total", "with_attach", "prev_year_total", "yoy_delta", "yoy_pct"]
    lines = [",".join(header)]
    for r in rows:
        lines.append(",".join(str(r.get(h, "")) for h in header))
    OUT_CSV.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT_JSON}")
    print(f"wrote {OUT_CSV}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--since", default="2023-08-01")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if sys.platform != "win32":
        print("Runs on Windows with classic Outlook only.")
        return 2
    return measure(args)


if __name__ == "__main__":
    raise SystemExit(main())
