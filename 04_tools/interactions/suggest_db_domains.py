"""Find the distributor domains the allow-list is missing.

Five DBs have no contact on file (ARMENIA, KAZAKHSTAN, PALESTINE, UMI, UTI), so their
correspondence is invisible to the collector. Rather than guess addresses, this reads
which *unmatched* domains actually carry traffic in the mailbox and ranks them.

Reads   : Outlook via MAPI, read-only (same G0a scope as collect_mapi.py)
Writes  : 04_tools/interactions/domain_review.csv   — a proposal, not a change

NOTHING IS ADDED AUTOMATICALLY. Jerome confirms rows, then they go into
db_domains.yaml by hand (or via build_db_domains.py once the master is updated).

Output holds domains and counts only — no address, no name, no subject, no body.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import Counter
from datetime import datetime, timedelta

from collect_mapi import (
    ALLOWLIST,
    OL_FOLDER,
    OL_MAIL_CLASS,
    _domain,
    _forbid_remote_network,
    _safe,
    _sender_smtp,
    _smtp,
    load_allowlist,
    open_own_store,
)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "domain_review.csv")

OWN_DOMAINS = {"isuzu-e.com"}

# Bulk senders that will otherwise dominate the ranking. Not distributors.
NOISE = re.compile(
    r"(microsoft|office365|linkedin|google|apple|adobe|zoom|docusign|salesforce|sap\.com"
    r"|dropbox|atlassian|calendly|eventbrite|mailchimp|sendgrid|amazonses|newsletter"
    r"|noreply|no-reply|bounce|notification)",
    re.IGNORECASE,
)

# Hints that a domain may belong to a DB with no contact on file.
HINTS = {
    "UMI": ["universalmotors", "umi", "isuzu.co.il", "universal-motors"],
    "UTI": ["universaltrucks", "uti", "trucks.co.il"],
    "ARMENIA": ["grandavto", "grand-avto", ".am"],
    "KAZAKHSTAN": ["cbc", "cbctrans", ".kz"],
    "PALESTINE": ["kima", ".ps"],
}


def candidate_for(domain: str) -> str:
    hits = [db for db, needles in HINTS.items() if any(n in domain for n in needles)]
    return "|".join(hits)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", default=(datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d"))
    ap.add_argument("--folders", default="inbox,sent")
    ap.add_argument("--min-count", type=int, default=3)
    args = ap.parse_args()

    if sys.platform != "win32":
        print("Windows + classic Outlook only.")
        return 2

    import win32com.client

    domain_to_db, ambiguous = load_allowlist(ALLOWLIST)
    known = set(domain_to_db) | ambiguous | OWN_DOMAINS

    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    store_name, own_smtp = open_own_store(ns)
    print(f"store: {store_name}")
    _forbid_remote_network()

    since = datetime.strptime(args.since, "%Y-%m-%d")
    restrict = f"[ReceivedTime] >= '{since.strftime('%m/%d/%Y')} 12:00 AM'"

    counts: Counter[str] = Counter()
    seen = 0

    for folder_name in [f.strip() for f in args.folders.split(",") if f.strip()]:
        if folder_name not in OL_FOLDER:
            continue
        items = ns.GetDefaultFolder(OL_FOLDER[folder_name]).Items
        items.Sort("[ReceivedTime]", True)
        try:
            items = items.Restrict(restrict)
        except Exception as exc:
            print(f"restrict failed on {folder_name} ({exc})")

        print(f"scanning {folder_name} …")
        for msg in items:
            seen += 1
            try:
                if _safe(lambda: msg.Class, 0) != OL_MAIL_CLASS:
                    continue
                addresses = [_sender_smtp(msg)]
                for rcp in _safe(lambda: msg.Recipients, []) or []:
                    addresses.append(_smtp(rcp))
                for dom in {_domain(a) for a in addresses if a}:
                    if dom and dom not in known and not NOISE.search(dom):
                        counts[dom] += 1
            except Exception:
                continue

    rows = [
        {
            "domain": dom,
            "messages": n,
            "candidate_for": candidate_for(dom),
            "decision": "",          # Jerome fills: DB code, or 'ignore'
        }
        for dom, n in counts.most_common()
        if n >= args.min_count
    ]

    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["domain", "messages", "candidate_for", "decision"])
        writer.writeheader()
        writer.writerows(rows)

    flagged = [r for r in rows if r["candidate_for"]]
    print(f"\nscanned {seen:,} items · {len(rows)} unmatched domains at >= {args.min_count} messages")
    print(f"wrote {OUT}")
    if flagged:
        print("\nlikely matches for the five DBs with no contact on file:")
        for r in flagged:
            print(f"  {r['domain']:<40} {r['messages']:>5}  → {r['candidate_for']}")
    else:
        print("\nno hint matches — review the CSV by volume instead.")
    print("\nNothing was added. Fill the 'decision' column, then update the DB master.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
