"""Inline the local Plotly into AIM_Dashboard_CY2026.html and drop the CDN fallback.

House rule (isze-html-openable.mdc): a chart library must be inlined and a CDN is
discouraged. The page currently loads ../_ui/plotly.min.js by relative path with a
cdn.plot.ly fallback in a document.write guard.

This script:
  1. backs the page up beside it,
  2. reads the local plotly.min.js,
  3. replaces the two <script> tags (local + CDN guard) with one inline <script>,
  4. leaves aim_cy2026.data.js on its relative path (the page is shipped with it),
  5. refuses to write if the CDN string survives or Plotly is not defined inline.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PAGE = ISZE / "02_dashboards" / "sales" / "AIM_Dashboard_CY2026.html"
PLOTLY = ISZE / "02_dashboards" / "_ui" / "plotly.min.js"

html = PAGE.read_text(encoding="utf-8")
plotly = PLOTLY.read_text(encoding="utf-8", errors="strict")

if "cdn.plot.ly" not in html:
    print("nothing to do: no CDN reference present")
    raise SystemExit(0)

old = re.search(
    r'<script src="\.\./_ui/plotly\.min\.js"></script>\s*<script>\s*'
    r'// offline-first.*?document\.write\(.*?\);\s*\}\s*</script>',
    html,
    re.S,
)
if not old:
    print("FAIL: could not locate the local+CDN script block", file=sys.stderr)
    raise SystemExit(2)

shutil.copy2(PAGE, PAGE.with_suffix(".html.bak_pre_plotly_inline_20260924"))

inline = "<script>\n/* Plotly 2.27.0 inlined (local ../_ui/plotly.min.js) — no CDN dependency. */\n" \
         + plotly + "\n</script>"
new_html = html[: old.start()] + inline + html[old.end():]

# The library itself mentions cdn.plot.ly in its own text, so test for a CDN SCRIPT
# TAG or a document.write of one, not for the bare string.
cdn_tag = re.search(r'<script[^>]+cdn\.plot\.ly', new_html, re.I)
cdn_write = re.search(r'document\.write\([^)]*cdn\.plot\.ly', new_html, re.I)
assert cdn_tag is None, f"CDN script tag survived: {cdn_tag.group(0) if cdn_tag else ''}"
assert cdn_write is None, "CDN document.write survived"
assert "Plotly" in new_html, "inline Plotly missing"
PAGE.write_text(new_html, encoding="utf-8")
print(f"inlined {len(plotly):,} bytes of Plotly; page {len(html):,} -> {len(new_html):,} bytes")
print("CDN script tags left:", len(re.findall(r'<script[^>]+cdn\.plot\.ly', new_html, re.I)))
print("mentions of cdn.plot.ly inside the library text:", new_html.count("cdn.plot.ly"))
