# -*- coding: utf-8 -*-
"""
Task card 0.3 — split KS_AllProducts strings into separate products.

Honest finding: the KS string is regular ("TITLE()=£30.00[OOS]|..."), so a regex parses it
exactly and DeepSeek is NOT needed for the production parse. We use that to our advantage:
the regex answer becomes a free golden set to measure DeepSeek's accuracy before we trust
it on messy web pages (Phases 1-3).

Writes:
  04_tools/delegation/deepseek/parsed/ks_products.csv                 production parse (regex)
  04_tools/delegation/deepseek/queue/ks_products_golden.jsonl         DeepSeek test queue (public text only)
  04_tools/delegation/deepseek/golden/ks_products_golden.expected.jsonl
"""
import json
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = HERE / "deepseek"
PAT = re.compile(r"^(?P<title>.*?)\(\)=£(?P<price>[\d,]+(?:\.\d+)?)(?P<oos>\[OOS\])?$")


def parse(s):
    out = []
    for chunk in str(s).split("|"):
        m = PAT.match(chunk.strip())
        if not m:
            raise ValueError(f"unparsed chunk: {chunk!r}")
        title = m["title"].strip()
        out.append({
            "title": title,
            "price": float(m["price"].replace(",", "")),
            "is_genuine": "(GENUINE)" in title.upper(),
            "in_stock": m["oos"] is None,
        })
    return out


def main():
    k = pd.read_csv(ROOT / "04_tools/autodoc_scraper/ks_results.csv", dtype={"PN": str})
    k = k[(k["Status"] == "ok") & k["KS_AllProducts"].notna()]
    rows, q, g = [], [], []
    for _, r in k.iterrows():
        prods = parse(r["KS_AllProducts"])
        for p in prods:
            rows.append({"part_no": r["PN"], **p, "scraped_at": r["Scraped_At"], "source_url": r["KS_URL"]})
        iid = f"ks_{r['PN']}"
        # data boundary: only the public KS text goes out — no price list, no sales
        q.append({"item_id": iid, "site": "ks-international.com", "text": r["KS_AllProducts"]})
        g.append({"item_id": iid, "compare_key": "products", "expect": prods})
    for d in ("parsed", "queue", "golden"):
        (BASE / d).mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(BASE / "parsed/ks_products.csv", index=False, encoding="utf-8")
    with open(BASE / "queue/ks_products_golden.jsonl", "w", encoding="utf-8") as fh:
        fh.writelines(json.dumps(x, ensure_ascii=False) + "\n" for x in q)
    with open(BASE / "golden/ks_products_golden.expected.jsonl", "w", encoding="utf-8") as fh:
        fh.writelines(json.dumps(x, ensure_ascii=False) + "\n" for x in g)
    df = pd.DataFrame(rows)
    print(f"{len(k)} KS rows -> {len(df)} products "
          f"({int(df.is_genuine.sum())} genuine, {int((~df.is_genuine).sum())} aftermarket, "
          f"{int((~df.in_stock).sum())} out of stock); golden queue {len(q)} items")


if __name__ == "__main__":
    main()
