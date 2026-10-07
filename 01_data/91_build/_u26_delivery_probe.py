# -*- coding: utf-8 -*-
"""Does a saved page state a delivery basis at all? Read the visible text only."""
import html
import re
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26")
OFF = ROOT / "04_tools" / "price_ledger" / "OFFERED_ROWS.csv"
PROBE = ROOT / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"

off = pd.read_csv(OFF, dtype=str, low_memory=False)
if "verdict" in off.columns:
    off = off[~off["verdict"].fillna("").str.startswith("reject:")]
off = off[off["country"].isin(["UK", "PT"])]
print("UK/PT offered rows:", len(off))


def visible(h: str) -> str:
    h = re.sub(r"(?is)<script.*?</script>", " ", h)
    h = re.sub(r"(?is)<style.*?</style>", " ", h)
    h = re.sub(r"(?is)<noscript.*?</noscript>", " ", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(h))


TERMS = re.compile(r"(?i)\b(delivery|shipping|postage|carriage|dispatched|dispatch|collection|collect)\b")

cache: dict[str, str] = {}
out = []
for _, r in off.iterrows():
    pf = r.get("page_file")
    if not isinstance(pf, str) or not pf:
        continue
    p = PROBE / pf.replace("/", "\\")
    key = str(p)
    if key not in cache:
        try:
            cache[key] = visible(p.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            cache[key] = ""
    vis = cache[key]
    if not vis:
        continue
    hits = TERMS.findall(vis)
    m = TERMS.search(vis)
    ctx = vis[max(0, m.start() - 100): m.start() + 160].strip() if m else ""
    out.append({"loader": r.get("loader"), "part_no": r.get("part_no"),
                "page_file": pf, "mentions": len(hits), "ctx": ctx[:240]})

d = pd.DataFrame(out)
print("rows with a saved page:", len(d), " distinct pages:", d["page_file"].nunique())
print()
print("delivery-word count per page (visible text only):")
print(d.drop_duplicates("page_file")["mentions"].value_counts().sort_index().to_string())
print()
print("--- the actual wording, first mentions ---")
for _, r in d[d.mentions > 0].drop_duplicates("page_file").head(10).iterrows():
    print(f"[{r.loader}] {r.page_file}")
    print("    ", r.ctx)
