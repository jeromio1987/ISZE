"""Make the Portugal IDS HTML self-contained: inline Leaflet CSS + JS.

Why: when the file is attached to Outlook and previewed, Windows copies it to a
temp cache folder. `../_ui/leaflet.js` does not exist there, and the CDN fallback
is blocked, so Leaflet never loads and the map shows
"Map library unavailable offline".

Fix: embed leaflet.css and leaflet.js inside the HTML so the file works alone.

Originals are backed up next to each file as .bak_pre_inline_20260921.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
UI = ISZE / "02_dashboards" / "_ui"
LEAFLET_JS = (UI / "leaflet.js").read_text(encoding="utf-8")
LEAFLET_CSS = (UI / "leaflet.css").read_text(encoding="utf-8")

TARGETS = [
    ISZE / "02_dashboards/ids/IDS_2026_dealer_compare_Portugal.html",
    ISZE / "02_dashboards/ids/IDS_all_dashboards_2026-08-19/02_country/IDS_2026_dealer_compare_Portugal.html",
    ISZE / "09_meetings/Imotors_Portugal_IDS_2026/IDS_2026_dealer_compare_Portugal.html",
    ISZE / "09_meetings/IDS_2026_Country_Packs_v1.4/Portugal/IDS_2026_dealer_compare_Portugal.html",
    ISZE / "02_dashboards/ids/IDS_2026_Portugal_dealer_map.html",
    ISZE / "09_meetings/Imotors_Portugal_IDS_2026/IDS_2026_Portugal_dealer_map.html",
]

# any leaflet stylesheet link (local ../_ui or unpkg), with or without integrity
LINK_RE = re.compile(
    r'<link[^>]*href="[^"]*leaflet[^"]*\.css"[^>]*/?>\s*',
    re.IGNORECASE,
)

# any leaflet script tag that points elsewhere (local ../_ui or unpkg)
SCRIPT_SRC_RE = re.compile(
    r'<script[^>]*src="[^"]*leaflet[^"]*\.js"[^>]*>\s*</script>\s*',
    re.IGNORECASE,
)

# the CDN-fallback block that document.writes a leaflet script
FALLBACK_RE = re.compile(
    r"<script>\s*/\*[^*]*\*/\s*if \(typeof L === \"undefined\"\)\s*\{.*?\}\s*</script>\s*",
    re.DOTALL | re.IGNORECASE,
)

INLINE_CSS = f"<style>\n/* Leaflet 1.9.4 — inlined so the file works standalone (Outlook attachment cache) */\n{LEAFLET_CSS}\n</style>\n"
INLINE_JS = f'<script>\n/* Leaflet 1.9.4 — inlined so the file works standalone (Outlook attachment cache) */\n{LEAFLET_JS}\n</script>\n'


def convert(path: Path) -> dict:
    html = path.read_text(encoding="utf-8")
    before_len = len(html)

    backup = path.with_suffix(path.suffix + ".bak_pre_inline_20260921")
    if not backup.exists():
        shutil.copy2(path, backup)

    n_links = len(LINK_RE.findall(html))
    n_scripts = len(SCRIPT_SRC_RE.findall(html))
    n_fallback = len(FALLBACK_RE.findall(html))

    # 1. drop external leaflet css links, put the css inside the head
    html = LINK_RE.sub("", html)
    html = html.replace("</head>", INLINE_CSS + "</head>", 1)

    # 2. drop external leaflet js tags and the CDN fallback block
    html = SCRIPT_SRC_RE.sub("", html)
    html = FALLBACK_RE.sub("", html)

    # 3. put the js in the body, before the first app script, so L exists early
    app_script = re.search(r"<script>\s*\n\s*(?:\(function|const|let|var|function)", html)
    if app_script:
        html = html[: app_script.start()] + INLINE_JS + html[app_script.start():]
        placed = "before app script"
    else:
        html = html.replace("</body>", INLINE_JS + "</body>", 1)
        placed = "before </body>"

    path.write_text(html, encoding="utf-8")

    # 4. prove nothing local is left
    remaining = {
        "local_ui_refs": len(re.findall(r"\.\./_ui/", html)),
        "unpkg_refs": len(re.findall(r"unpkg\.com", html)),
        "carto_refs": len(re.findall(r"cartocdn", html)),
        "leaflet_inline": "Leaflet 1.9.4 — inlined" in html,
    }
    return {
        "file": str(path),
        "backup": str(backup),
        "links_removed": n_links,
        "script_tags_removed": n_scripts,
        "fallback_blocks_removed": n_fallback,
        "js_placed": placed,
        "kb_before": round(before_len / 1024, 1),
        "kb_after": round(len(html) / 1024, 1),
        **remaining,
    }


def main() -> int:
    problems = 0
    for t in TARGETS:
        if not t.is_file():
            print(f"MISSING {t}")
            problems += 1
            continue
        r = convert(t)
        print(f"=== {r['file']}")
        print(
            f"    links_removed={r['links_removed']} script_tags_removed={r['script_tags_removed']} "
            f"fallback_removed={r['fallback_blocks_removed']} js_placed={r['js_placed']}"
        )
        print(f"    size {r['kb_before']} KB -> {r['kb_after']} KB")
        print(
            f"    left: local_ui={r['local_ui_refs']} unpkg={r['unpkg_refs']} "
            f"carto={r['carto_refs']} inline_leaflet={r['leaflet_inline']}"
        )
        if r["local_ui_refs"] or r["unpkg_refs"] or r["carto_refs"]:
            problems += 1
            print("    !! still has external leaflet/carto references")
        if not r["leaflet_inline"]:
            problems += 1
            print("    !! leaflet not inlined")
    print(f"\nfiles with problems: {problems}")
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
