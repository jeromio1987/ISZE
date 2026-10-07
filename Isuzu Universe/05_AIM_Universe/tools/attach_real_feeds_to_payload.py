"""Merge the real feeds into the INTERNAL payload, without editing the restricted pack.

Reads the existing payload (`aim_payload_20260922.json`), attaches the real feed block built
by `connect_real_feeds.py`, and links each case to its own market:

  * `tender_notice_ids`  the ITUK notices go to a case whose `market` is ITUK, the Portugal
                         notices to a Portugal case. The link is the case's own market, not a
                         guess about the buyer.
  * `prism_level`        national, for the case's own market. Recorded as `scope: national`.

Writes a NEW payload file. The restricted source pack is never modified.

Run:  python tools/attach_real_feeds_to_payload.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

COMPONENT = Path(__file__).resolve().parent.parent
PAYLOAD_DIR = COMPONENT / "payload"
SOURCE = PAYLOAD_DIR / "aim_payload_20260922.json"
FEEDS = PAYLOAD_DIR / "real_feeds.local.json"
OUT = PAYLOAD_DIR / "aim_payload_u29c_real_feeds.local.json"

# A market in the case vs a market key in the feed.
MARKET_KEYS = {"ITUK": "ITUK", "PORTUGAL": "PORTUGAL"}


def main() -> int:
    if not SOURCE.exists():
        print(f"missing payload: {SOURCE}", file=sys.stderr)
        return 2
    if not FEEDS.exists():
        print(f"missing feed block: {FEEDS}  (run tools/connect_real_feeds.py first)",
              file=sys.stderr)
        return 2

    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    feeds = json.loads(FEEDS.read_text(encoding="utf-8"))

    notices = (feeds.get("tender_data") or {}).get("notices") or []
    by_market: dict[str, list[str]] = {}
    for n in notices:
        code = n.get("distributor_code")
        if code:
            by_market.setdefault(code, []).append(n["opportunity_id"])

    # Top-level: the feed the product reads, plus PRISM measures.
    payload["tender_data"] = {"notices": notices}
    payload["prism_measures"] = feeds.get("prism_measures") or []

    linked = {}
    for case in payload.get("cases") or []:
        market = MARKET_KEYS.get((case.get("market") or "").upper())
        if not market:
            continue
        ids = by_market.get(market) or []
        if ids:
            case["tender_notice_ids"] = ids
        case["prism_level"] = {
            "dealer_id": None,
            "distributor": market,
            "scope": "national",
        }
        linked[case.get("id")] = {"market": market, "tender_notice_ids": len(ids)}

    # Provenance so a reader can see where the block came from.
    meta = payload.setdefault("meta", {})
    meta["real_feeds"] = {
        "built_at": feeds.get("built_at"),
        "tender_notices": len(notices),
        "tender_by_market": {k: len(v) for k, v in by_market.items()},
        "prism_measures": len(payload["prism_measures"]),
        "source": "01_data/14_dashboards/tender_data.json + 01_data/00_derived/ (ITUK, PORTUGAL)",
        "rule": ("the link is the case's own market; a notice value is never parts revenue; "
                 "a national PRISM total is never split to a dealer"),
    }

    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"  tender notices attached: {len(notices)}")
    print(f"  prism measures attached: {len(payload['prism_measures'])}")
    for cid, info in linked.items():
        print(f"  case {cid}: market {info['market']}, {info['tender_notice_ids']} notice(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
