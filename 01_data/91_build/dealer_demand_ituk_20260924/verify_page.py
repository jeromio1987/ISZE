#!/usr/bin/env python3
"""Ship-gate checks for the ITUK dealer demand page. Reads the built file, not the builder."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BUILD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\dealer_demand_ituk_20260924")
PAGE = BUILD / "page" / "Dealer_Parts_Demand_ITUK_CY2025_INTERNAL.html"

fails, warns, passes = [], [], []


def chk(cond, name, detail=""):
    (passes if cond else fails).append(f"{name}{(' - ' + detail) if detail else ''}")


def warn(cond, name, detail=""):
    if cond:
        passes.append(f"{name}{(' - ' + detail) if detail else ''}")
    else:
        warns.append(f"{name}{(' - ' + detail) if detail else ''}")


html = PAGE.read_text(encoding="utf-8")

# 1 self-contained: no fetch, no CDN, no external script/link
chk("fetch(" not in html, "no fetch() call")
chk("http://" not in html and "https://" not in html, "no external URL")
chk("<script" not in html.lower(), "no script tags at all")
chk("cdn" not in html.lower(), "no CDN reference")
chk("sourceMappingURL" not in html, "no source map reference")

# 2 no broken placeholders
chk("NaN" not in html, "no NaN in the page")
chk("nan" not in html.replace("finance", "").replace("maintenance", ""), "no stray nan")
chk("None" not in html, "no Python None leaked into the page")
chk("{{" not in html and "}}" not in html, "no unresolved template braces")

# 3 tables actually have rows
for key, label in [("<tbody>", "tbody blocks")]:
    n = html.count(key)
    chk(n >= 4, f"{label} present", f"{n} found")

rows = len(re.findall(r"<tr>", html))
chk(rows > 60, "table rows painted", f"{rows} rows")

# 4 the killer number and the honest verdict are on the page
chk("does it beat just knowing the dealer" in html.lower(), "falsification test section present")
chk("beats dealer size on" in html or "wins on" in html, "wins/losses verdict present")
chk("not in this model at all" in html, "Israel exclusion stated")

# 5 wording rules
banned = ["sell-out", "sellout", "sell out", "capture rate", "parc ", "wallet",
          "Mode A", "Mode B", "ship-gate", "harness", "lane"]
for b in banned:
    chk(b.lower() not in html.lower(), f"no banned wording: {b!r}")

# 6 no file names / paths in the body
body = re.sub(r"<style.*?</style>", "", html, flags=re.S)
body = re.sub(r"<footer.*?</footer>", "", body, flags=re.S)
for token in [".csv", ".parquet", "01_data", "C:\\", "\\\\"]:
    chk(token.lower() not in body.lower(), f"no path/file token in body: {token!r}")

# 7 amber banners where there is no data
chk(html.count('class="amber"') >= 3, "amber banners present", f"{html.count('class=\"amber\"')}")

# 8 every family row carries a basis badge
chk(html.count('class="badge b-') >= 14, "basis badges on rows",
    f"{html.count('class=\"badge b-')}")

# 9 launcher exists and is CRLF
cmd = BUILD / "page" / "OPEN_Dealer_Parts_Demand_ITUK.cmd"
chk(cmd.exists(), "launcher exists")
if cmd.exists():
    raw = cmd.read_bytes()
    chk(b"\r\n" in raw, "launcher is CRLF")

# 11 the scatter is present with painted points
chk('class="dot"' in html, "scatter points present", f"{html.count('class=\"dot\"')} dots")
chk(html.count('class="dot"') >= 50, "enough points to read the shape")

# 10 euro first, fleet beside it
chk("&euro;" in html, "euro used")
chk("trucks in service" in html.lower(), "fleet named in words")

report = {
    "checked_at": datetime.now(timezone.utc).isoformat(),
    "page": str(PAGE),
    "passes": len(passes),
    "warns": len(warns),
    "fails": len(fails),
    "fail_detail": fails,
    "warn_detail": warns,
}
(BUILD / "page" / "verify_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(f"PASS {len(passes)}  WARN {len(warns)}  FAIL {len(fails)}")
for f in fails:
    print("  FAIL:", f)
for w in warns:
    print("  WARN:", w)
sys.exit(1 if fails else 0)
