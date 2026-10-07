# -*- coding: utf-8 -*-
"""Do the pages behind the UK/PT focus rows state a DELIVERY BASIS (not a shipping policy)?"""
import html
import re
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26")
DERIVED = ROOT / "01_data" / "00_derived"
OFF = ROOT / "04_tools" / "price_ledger" / "OFFERED_ROWS.csv"
PROBE = ROOT / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"

focus = pd.read_csv(DERIVED / "epc_decode_worklist.csv", dtype={"part_number": str})
focus = focus[focus["pms_category"].isin(["brake_pad", "oil_filter"])]
focus_pns = set(focus["part_number"].astype(str))

off = pd.read_csv(OFF, dtype=str, low_memory=False)
if "verdict" in off.columns:
    off = off[~off["verdict"].fillna("").str.startswith("reject:")]
focus_rows = off[off["country"].isin(["UK", "PT"]) & off["part_no"].isin(focus_pns)].copy()
print("focus rows (UK+PT):", len(focus_rows))
print(focus_rows.groupby(["country", "loader"]).size().to_string())


def visible(h: str) -> str:
    h = re.sub(r"(?is)<script.*?</script>", " ", h)
    h = re.sub(r"(?is)<style.*?</style>", " ", h)
    h = re.sub(r"(?is)<noscript.*?</noscript>", " ", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(h))


# A delivery BASIS is a per-listing statement: included / excluded / cost.
# A shipping POLICY is site boilerplate: dispatch times, a footer "Delivery Information" link,
# "we ship worldwide". Only the first can populate the ledger field without inventing it.
BASIS = re.compile(
    r"(?i)(free (uk )?delivery|delivery (is )?(included|free|charged?|costs?|not included)|"
    r"(excl|excluding|plus|incl|including)[^.]{0,20}delivery|"
    r"delivery (charge|cost|fee)s?\b|carriage (paid|included|extra)|"
    r"shipping (is )?(included|free|charged)|p&p\b|postage (included|extra))")
POLICY = re.compile(r"(?i)(dispatch|delivery information|we ship|next day|collection in store|"
                    r"delivery polic|returns)")

cache: dict[str, str] = {}
rows = []
for _, r in focus_rows.iterrows():
    pf = r.get("page_file")
    if not isinstance(pf, str) or not pf:
        rows.append({"loader": r.get("loader"), "part_no": r.get("part_no"),
                     "page": "(none)", "basis": "", "policy": ""})
        continue
    key = str(PROBE / pf.replace("/", "\\"))
    if key not in cache:
        try:
            cache[key] = visible(Path(key).read_text(encoding="utf-8", errors="replace"))
        except OSError:
            cache[key] = ""
    vis = cache[key]
    b = BASIS.search(vis)
    p = POLICY.search(vis)
    rows.append({
        "loader": r.get("loader"), "part_no": r.get("part_no"), "page": Path(pf).name,
        "basis": (vis[max(0, b.start() - 80): b.start() + 140].strip()[:220] if b else ""),
        "policy": (vis[max(0, p.start() - 40): p.start() + 90].strip()[:140] if p else ""),
    })

d = pd.DataFrame(rows)
print()
print("=== per loader: rows / with a delivery BASIS / with only a POLICY / neither ===")
g = d.groupby("loader").apply(lambda x: pd.Series({
    "rows": len(x),
    "basis": int((x["basis"] != "").sum()),
    "policy_only": int(((x["policy"] != "") & (x["basis"] == "")).sum()),
    "neither": int(((x["policy"] == "") & (x["basis"] == "")).sum()),
}), include_groups=False)
print(g.to_string())
print()
print("TOTAL rows:", len(d), " with a delivery basis:", int((d['basis'] != '').sum()))
print()
if (d["basis"] != "").any():
    print("--- the basis wording found ---")
    for _, r in d[d["basis"] != ""].head(8).iterrows():
        print(f"[{r.loader}] {r.page}")
        print("    ", r.basis)
