"""Mark ISZE_UNIVERSE_BOARD stale (7 Oct 2026). Does not re-grade Sep scores."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML_PATH = ROOT / "02_dashboards" / "hub" / "ISZE_UNIVERSE_BOARD.html"
JSON_PATH = ROOT / "01_data" / "00_derived" / "universe_board_state.json"
BUILDER = ROOT / "02_dashboards" / "_build" / "build_universe_board.py"

BANNER = """
<div class="stale-banner" role="status" style="background:#7a2e0e;color:#f7f4ee;padding:14px 20px;font:15px/1.45 Georgia,serif;border-bottom:4px solid #c0552d;">
<strong>STALE SCORES — content frozen 24 September 2026.</strong>
Marked 7 October 2026. This page still says "0 of 5 tools" and Sep pillar scores.
It does <em>not</em> include Oct U1-U29 waves, ITUK/Portugal pilot pages, AIM v04, or PR 70/72 on main.
For where Universe is now, open
<code style="color:#fff;background:#15233c;padding:2px 6px;">00_docs/UNIVERSE_U1_U26_STATUS_2026-10-07.md</code>
or the Universe map. Double-click
<code style="color:#fff;background:#15233c;padding:2px 6px;">OPEN_ISZE_UNIVERSE_MAP.cmd</code>.
</div>
"""

MARKER = "# STALE_BOARD_BANNER_2026-10-07"


def patch_html() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    if "stale-banner" not in html:
        if "<body>\n\n<header class=\"hero\">" in html:
            html = html.replace(
                "<body>\n\n<header class=\"hero\">",
                "<body>\n" + BANNER + "\n<header class=\"hero\">",
                1,
            )
        else:
            html = html.replace("<body>", "<body>\n" + BANNER, 1)
        print("HTML banner: inserted")
    else:
        print("HTML banner: already present")

    old_stamp = "Built 24 September 2026, 22:39."
    new_stamp = (
        "Scores built 24 September 2026, 22:39. "
        "STALE banner added 7 October 2026 — see UNIVERSE_U1_U26_STATUS_2026-10-07.md."
    )
    if old_stamp in html:
        html = html.replace(old_stamp, new_stamp, 1)
        print("stamp updated")
    HTML_PATH.write_text(html, encoding="utf-8")


def patch_json() -> None:
    state = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    state["content_vintage"] = "2026-09-24T22:39:23"
    state["stale"] = True
    state["stale_marked_at"] = datetime.now().isoformat(timespec="seconds")
    state["stale_reason"] = (
        "Pillar scores and distributor-tool headline are frozen from 24 Sep 2026. "
        "Oct U-waves, pilots, AIM v04, and merged PRs 70/72 are not in these scores. "
        "Use 00_docs/UNIVERSE_U1_U26_STATUS_2026-10-07.md and ISZE_UNIVERSE_MAP.html."
    )
    state["live_status_doc"] = "00_docs/UNIVERSE_U1_U26_STATUS_2026-10-07.md"
    state["decisions_doc"] = "00_docs/UNIVERSE_DECISIONS_2026-10-07.md"
    state["scores_built_at"] = state.get("built_at")
    state["built_at"] = state["stale_marked_at"]
    JSON_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("JSON stale fields written")


def patch_builder() -> None:
    b = BUILDER.read_text(encoding="utf-8")
    if MARKER in b:
        print("builder already patched")
        return

    const = f'''
{MARKER}
# Amber notice injected until pillar scores are re-run against Oct U-wave reality.
STALE_BOARD_NOTICE_HTML = (
    '<div class="stale-banner" role="status" '
    'style="background:#7a2e0e;color:#f7f4ee;padding:14px 20px;'
    'font:15px/1.45 Georgia,serif;border-bottom:4px solid #c0552d;">'
    '<strong>STALE SCORES — check the Oct status note.</strong> '
    'Live status: 00_docs/UNIVERSE_U1_U26_STATUS_2026-10-07.md '
    'and OPEN_ISZE_UNIVERSE_MAP.cmd. Set SHOW_STALE_BOARD_BANNER = False '
    'only after a deliberate re-score.'
    '</div>'
)
SHOW_STALE_BOARD_BANNER = True
'''
    anchor = 'OUT_JSON = os.path.join(ROOT, "01_data", "00_derived", "universe_board_state.json")\n'
    if anchor not in b:
        raise SystemExit("builder anchor missing")
    b = b.replace(anchor, anchor + const, 1)

    old = (
        '    html = build_html(F, pillars)\n'
        '    with io.open(OUT_HTML, "w", encoding="utf-8") as fh:\n'
        '        fh.write(html)'
    )
    new = (
        '    html = build_html(F, pillars)\n'
        '    if SHOW_STALE_BOARD_BANNER and "stale-banner" not in html:\n'
        '        html = html.replace("<body>", "<body>\\n" + STALE_BOARD_NOTICE_HTML, 1)\n'
        '    with io.open(OUT_HTML, "w", encoding="utf-8") as fh:\n'
        '        fh.write(html)'
    )
    if old not in b:
        raise SystemExit("builder html write block missing")
    b = b.replace(old, new, 1)

    old_state = '        "tools_total": len(TOOLS),\n'
    new_state = (
        '        "tools_total": len(TOOLS),\n'
        '        "stale": bool(SHOW_STALE_BOARD_BANNER),\n'
        '        "live_status_doc": "00_docs/UNIVERSE_U1_U26_STATUS_2026-10-07.md",\n'
        '        "stale_reason": (\n'
        '            "Board scores need an intentional re-measure after Oct U-waves; "\n'
        '            "see live_status_doc while SHOW_STALE_BOARD_BANNER is True."\n'
        '        ),\n'
    )
    if 'live_status_doc' not in b:
        if old_state not in b:
            raise SystemExit("builder state anchor missing")
        b = b.replace(old_state, new_state, 1)

    BUILDER.write_text(b, encoding="utf-8")
    print("builder written")


def main() -> int:
    patch_html()
    patch_json()
    patch_builder()
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
