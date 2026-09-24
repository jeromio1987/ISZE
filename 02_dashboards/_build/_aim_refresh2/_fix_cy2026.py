"""AIM_Dashboard_CY2026.html — remove the CDN fallback, keep local Plotly, sign it.

The page originally did:

    <script src="../_ui/plotly.min.js"></script>
    <script>
    // offline-first: local vendored Plotly; CDN only as last resort
    if (typeof Plotly === 'undefined') {
      document.write('<scr' + 'ipt src="https://cdn.plot.ly/plotly-2.27.0.min.js"></scr' + 'ipt>');
    }
    </script>

Inlining the 4.85 MB library into the page was tried first (backup is
AIM_Dashboard_CY2026.html.bak_pre_plotly_inline_20260924) and it renders correctly, but the
house receipt writer refuses the result: it scans the page text for `cdn.plot.ly|unpkg.com|...`
and for `NaN` literals, and Plotly's own source contains both (maki icon URLs, null-handling
branches). A page carrying an inlined plotting library therefore cannot be signed.

The brief allows the other shape: no CDN dependency, and a working sibling launcher. So this
restores the pre-inline page, deletes the CDN fallback block, and leaves the local
`../_ui/plotly.min.js` reference — which resolves on a double-click, exactly as it did before.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PAGE = ISZE / "02_dashboards" / "sales" / "AIM_Dashboard_CY2026.html"
BACKUP = PAGE.with_suffix(".html.bak_pre_plotly_inline_20260924")

if not BACKUP.is_file():
    print("FAIL: pre-inline backup missing", file=sys.stderr)
    raise SystemExit(2)

html = BACKUP.read_text(encoding="utf-8")

block = re.search(
    r'<script>\s*// offline-first.*?</script>\s*',
    html,
    re.S,
)
if not block:
    print("FAIL: CDN fallback block not found in the backup", file=sys.stderr)
    raise SystemExit(3)

before = len(html)
html = html[: block.start()] + html[block.end():]

assert "cdn.plot.ly" not in html, "CDN reference survived"
assert "<script>cdn.plot" not in html
assert '../_ui/plotly.min.js' in html, "local Plotly reference missing"
PAGE.write_text(html, encoding="utf-8")
print(f"CDN fallback removed: {before:,} -> {len(html):,} bytes")
print("local Plotly reference kept:", "../_ui/plotly.min.js" in html)
print("plotly resolved from page folder:",
      (PAGE.parent / ".." / "_ui" / "plotly.min.js").resolve().is_file())
print("data file next to the page:", (PAGE.parent / "aim_cy2026.data.js").is_file())
