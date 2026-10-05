"""Inline Leaflet CSS+JS into IDS master so SharePoint is single-file."""
from __future__ import annotations

import re
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
MASTER = ISZE / "02_dashboards" / "ids" / "IDS_2026_dealer_compare.html"
CSS = ISZE / "02_dashboards" / "_ui" / "leaflet.css"
JS = ISZE / "02_dashboards" / "_ui" / "leaflet.js"

html = MASTER.read_text(encoding="utf-8")
bak = MASTER.with_suffix(MASTER.suffix + ".bak_inline_leaflet_20260916")
if not bak.exists():
    bak.write_text(html, encoding="utf-8")
    print("backup", bak)

css = CSS.read_text(encoding="utf-8")
js = JS.read_text(encoding="utf-8")

# Drop missing image sprites (pins use divIcon). Keep VML behavior untouched.
css = re.sub(r"url\((['\"]?)images/[^)]+\1\)", "none", css)

style_block = (
    "  <!-- Leaflet inlined for SharePoint / single-file open (no ../_ui dependency) -->\n"
    "  <style id=\"leaflet-css\">\n"
    + css
    + "\n  </style>\n"
)

script_block = (
    "  <script id=\"leaflet-js\">\n"
    + js
    + "\n  </script>\n"
)

# Remove duplicate local leaflet link tags
html2 = re.sub(
    r'\s*<!-- Local Leaflet[^>]*>\s*',
    "\n",
    html,
    count=1,
)
html2 = re.sub(
    r'\s*<link rel="stylesheet" href="\.\./_ui/leaflet\.css"\s*/>\s*',
    "\n",
    html2,
)

# Insert inlined CSS after <title>…</title> or right after charset viewport block — after <head> open content
if "<style id=\"leaflet-css\">" in html2:
    raise SystemExit("already has leaflet-css")

m = re.search(r"(<title>[^<]*</title>\s*)", html2)
if not m:
    raise SystemExit("title not found")
html2 = html2[: m.end()] + style_block + html2[m.end() :]

# Remove bottom leaflet script tags + document.write fallback
html2 = html2.replace('<script src="../_ui/leaflet.js"></script>', "")
# Fallback block (exact text from master)
old_fb = """  <script>
    /* CDN fallback if local _ui missing (online only) */
    if (typeof L === "undefined") {
      document.write('<script src="../_ui/leaflet.js"><\\/script>');
    }
  </script>"""
if old_fb in html2:
    html2 = html2.replace(old_fb, "")
else:
    # tolerant: drop any script that only document.writes ../_ui/leaflet.js
    html2 = re.sub(
        r"<script>\s*/\*[^*]*\*/\s*if \(typeof L === \"undefined\"\) \{\s*"
        r"document\.write\('.*?leaflet\.js.*?'\);\s*\}\s*</script>",
        "",
        html2,
        flags=re.S,
    )
    html2 = re.sub(
        r"<script>\s*if \(typeof L === \"undefined\"\) \{\s*"
        r"document\.write\('.*?leaflet\.js.*?'\);\s*\}\s*</script>",
        "",
        html2,
        flags=re.S,
    )

# Insert inlined JS just before the main DATA/app script — find last large inline app script
# Prefer: insert before `</body>` after removing external leaflet
if 'id="leaflet-js"' in html2:
    raise SystemExit("leaflet-js already present")

# Place leaflet before the first big application <script> that contains DATA or renderMap
idx = html2.find("<script>\n    const DATA")
if idx < 0:
    idx = html2.find("function renderMap")
    # walk back to script tag
    idx = html2.rfind("<script>", 0, idx)
if idx < 0:
    raise SystemExit("app script not found")
html2 = html2[:idx] + script_block + html2[idx:]

# Sanity: no remaining ../_ui/leaflet refs
left = [ln for ln in html2.splitlines() if "../_ui/leaflet" in ln]
if left:
    raise SystemExit("still has _ui leaflet refs:\n" + "\n".join(left[:10]))

MASTER.write_text(html2, encoding="utf-8")
print("wrote", MASTER, "bytes", MASTER.stat().st_size)
print("has L check: leaflet-js id", 'id="leaflet-js"' in html2)
print("has leaflet-css id", 'id="leaflet-css"' in html2)
