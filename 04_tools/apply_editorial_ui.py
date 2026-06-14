# -*- coding: utf-8 -*-
"""Inject shared editorial UI shell into all Dashboards/*.html files."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "Dashboards"
MARKER = "isze-shell.js"
INJECT = (
    '  <link rel="stylesheet" href="_ui/editorial.css">\n'
    '  <link rel="stylesheet" href="_ui/editorial-full.css">\n'
    '  <script src="_ui/editorial-charts.js"></script>\n'
    '  <script src="_ui/isze-shell.js" defer></script>\n'
)
CHARTS_MARKER = "editorial-charts.js"

SKIP = {"PROJECT_HUB.html"}


def inject(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    changed = False

    if MARKER not in text and "</head>" in text:
        text = text.replace("</head>", INJECT + "</head>", 1)
        changed = True
    elif CHARTS_MARKER not in text and MARKER in text:
        text = text.replace(
            '  <script src="_ui/isze-shell.js" defer></script>\n',
            '  <script src="_ui/editorial-charts.js"></script>\n'
            '  <script src="_ui/isze-shell.js" defer></script>\n',
            1,
        )
        changed = True
    elif "editorial-full.css" not in text and MARKER in text:
        text = text.replace(
            '  <script src="_ui/isze-shell.js" defer></script>\n',
            '  <link rel="stylesheet" href="_ui/editorial-full.css">\n'
            '  <script src="_ui/isze-shell.js" defer></script>\n',
            1,
        )
        changed = True

    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def main():
    changed = []
    for html in sorted(DASH.glob("*.html")):
        if html.name in SKIP:
            continue
        if inject(html):
            changed.append(html.name)
    print(f"Updated {len(changed)} files:")
    for name in changed:
        print(f"  + {name}")


if __name__ == "__main__":
    main()
