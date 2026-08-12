"""Generate the DB e-mail domain allow-list from the distributor master.

Source : ISZE_ROOT/01_data/08_Distributor/DB_email_22_DBs.xlsx  (sheet '22 DBs', column 'E-mails')
Output : 04_tools/interactions/db_domains.yaml

The allow-list is the door of the collector: a message is only ever processed if a
domain listed here appears in the sender or a recipient. Everything else is dropped
before any field is read.

Generated, but REVIEW BY HAND before use — shared/webmail domains and agency domains
(astara.com etc.) are flagged, not silently trusted.
"""

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict

import pandas as pd
import yaml

ROOT = os.environ.get("ISZE_ROOT", r"C:\Users\jerom\Desktop\claude\ISZE")
SRC = os.path.join(ROOT, "01_data", "08_Distributor", "DB_email_22_DBs.xlsx")
OUT = os.path.join(ROOT, "04_tools", "interactions", "db_domains.yaml")

# Domains that serve many parties (agencies, group shells, free mail). Kept but flagged:
# a hit on these alone is NOT sufficient to attribute a message to a DB.
AMBIGUOUS = {
    "astara.com",
    "gmail.com",
    "outlook.com",
    "hotmail.com",
    "yahoo.com",
}

EMAIL_RE = re.compile(r"[\w.+'-]+@([\w-]+(?:\.[\w-]+)+)", re.UNICODE)


def main() -> int:
    if not os.path.exists(SRC):
        print(f"SOURCE MISSING: {SRC}", file=sys.stderr)
        return 1

    df = pd.read_excel(SRC, sheet_name="22 DBs")
    by_db: dict[str, set[str]] = defaultdict(set)

    for _, row in df.iterrows():
        db = str(row.get("DB", "")).strip()
        if not db or db.lower() == "nan":
            continue
        cell = row.get("E-mails")
        if pd.isna(cell):
            continue
        for domain in EMAIL_RE.findall(str(cell)):
            by_db[db].add(domain.lower())

    doc = {
        "version": 1,
        "generated_from": "DB_email_22_DBs.xlsx (sheet '22 DBs')",
        "note": (
            "Allow-list for the local MAPI collector. A domain marked ambiguous is shared "
            "with other parties: a match on it alone does not attribute the message to a DB."
        ),
        "ambiguous_domains": sorted(AMBIGUOUS),
        "distributors": {
            db: {
                "domains": sorted(d for d in doms if d not in AMBIGUOUS),
                "ambiguous": sorted(d for d in doms if d in AMBIGUOUS),
            }
            for db, doms in sorted(by_db.items())
        },
        "no_contact_on_file": sorted(
            str(r["DB"]).strip()
            for _, r in df.iterrows()
            if pd.isna(r.get("E-mails")) and str(r.get("DB", "")).strip()
        ),
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        yaml.safe_dump(doc, fh, sort_keys=False, allow_unicode=True)

    n_dom = sum(len(v["domains"]) for v in doc["distributors"].values())
    print(f"wrote {OUT}")
    print(f"  distributors with contacts : {len(doc['distributors'])}")
    print(f"  unambiguous domains        : {n_dom}")
    print(f"  no contact on file         : {doc['no_contact_on_file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
