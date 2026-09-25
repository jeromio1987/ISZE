"""Pre-ship check for the dealer development progress page.

Static and file-level checks only: encoding, self-containment, internal terms,
launcher line endings, and that the embedded payload matches the source extract.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = REPO / "02_dashboards" / "ids" / "IDS_2026_Development_Progress.html"
CMD = REPO / "02_dashboards" / "ids" / "OPEN_IDS_2026_Development_Progress.cmd"
SRC = REPO / "02_dashboards" / "ids" / "IDS_2026_dealer_compare.html"

WORDS = ["AIM", "PRISM", "DLOD", "IDS", "GPS", "BVP", "IML", "ITUK", "IUK",
         "UMI", "UTI", "campaign", "goed", "slecht"]
LITERALS = [".csv", ".json", ".py"]
PAT = re.compile(
    r"(?:\b(?:" + "|".join(WORDS) + r")\b)|(?:" + "|".join(re.escape(x) for x in LITERALS) + r")",
    re.I,
)

fails: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   [{detail}]" if not ok else ""))
    if not ok:
        fails.append(name)


def main() -> int:
    raw = HTML.read_bytes()
    check("no BOM", raw[:3] != b"\xef\xbb\xbf")
    text = raw.decode("utf-8")

    hits = PAT.findall(text)
    check("internal terms absent", not hits, f"count {len(hits)}: {sorted(set(hits))}")
    print(f"    internal-term count: {len(hits)}")

    urls = sorted(set(re.findall(r"https?://[^\"' >)]+", text)))
    check("no external URL", not urls, " ".join(urls[:4]))
    check("no fetch", "fetch(" not in text)
    check("no XMLHttpRequest", "XMLHttpRequest" not in text)
    refs = sorted(set(re.findall(r'(?:src|href)="([^"]+)"', text)))
    check("no sibling file reference", not refs, " ".join(refs[:4]))

    # payload must still be the assessment extract, dealer for dealer
    blob = re.search(r'<script type="application/json" id="devdata">(.*?)</script>', text, re.S)
    check("payload embedded", bool(blob))
    if blob:
        data = json.loads(blob.group(1))
        src_text = SRC.read_text(encoding="utf-8")
        marker = "const DATA = "
        idx = src_text.index(marker) + len(marker)
        src, _ = json.JSONDecoder().raw_decode(src_text, idx)
        check("dealer count matches extract", len(data["dealers"]) == len(src["dealers"]),
              f"{len(data['dealers'])} vs {len(src['dealers'])}")
        by_name: dict[tuple[str, str], list[dict]] = {}
        for d in data["dealers"]:
            by_name.setdefault((d["c"], d["n"]), []).append(d)
        mismatch = []
        # Multi-site companies repeat a name inside one market; build page data in
        # the same source order and compare position by position.
        pos: dict[tuple[str, str], int] = {}
        for s in src["dealers"]:
            key = (s["country"], s["name"])
            bucket = by_name.get(key)
            if bucket is None:
                alt = [d for d in data["dealers"]
                       if d["c"] == s["country"] and s["name"].endswith(d["n"])]
                found = alt[0] if len(alt) == 1 else None
            else:
                i = pos.get(key, 0)
                pos[key] = i + 1
                found = bucket[i] if i < len(bucket) else None
            if found is None:
                mismatch.append(s["name"])
                continue
            for sid, sec in (s.get("sections") or {}).items():
                want = round(sec["pct"], 4) if sec.get("pct") is not None else None
                if found["sec"].get(sid, {}).get("p") != want:
                    mismatch.append(f"{s['name']}:{sid}")
            wt = round(s["total_pct"], 4) if s.get("total_pct") is not None else None
            if found["tot"] != wt:
                mismatch.append(f"{s['name']}:total")
        check("every section score matches the extract", not mismatch,
              f"{len(mismatch)} mismatched: {mismatch[:5]}")

        markets = {d["c"] for d in data["dealers"]}
        check("all markets present", markets == set(src["country_profiles"]),
              f"missing {sorted(set(src['country_profiles']) - markets)}")

    # launcher
    cbr = CMD.read_bytes()
    check("launcher has no BOM", cbr[:3] != b"\xef\xbb\xbf")
    check("launcher is CRLF", cbr.count(b"\n") == cbr.count(b"\r\n"), repr(cbr[:40]))
    check("launcher opens this page", HTML.name.encode() in cbr, repr(cbr))

    print(f"\nfailures: {len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
