"""Read-only HTML audit: file:// safety under 02_dashboards/.

Flags HTML that fetch() sibling JSON without an embedded application/json block
or a sibling OPEN_*.cmd launcher (isze-html-openable rule).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DASH = ROOT / "02_dashboards"

FETCH_RE = re.compile(r"""fetch\s*\(\s*['"][^'"]+\.(json|csv)['"]""", re.I)
EMBED_RE = re.compile(r"""<script[^>]+type\s*=\s*['"]application/json['"]""", re.I)
LAUNCHER_GLOB = "OPEN_*.cmd"


def audit_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    if FETCH_RE.search(text) and not EMBED_RE.search(text):
        launchers = list(path.parent.glob(LAUNCHER_GLOB))
        if not launchers:
            issues.append("fetch external data without embed or OPEN_*.cmd")
    if "Failed to fetch" in text and "file://" in text.lower():
        issues.append("contains file:// fetch failure banner")
    return issues


def main() -> int:
    if not DASH.is_dir():
        print(f"MISSING: {DASH}", file=sys.stderr)
        return 1

    html_files = sorted(DASH.rglob("*.html"))
    flagged: list[tuple[str, list[str]]] = []
    for p in html_files:
        rel = p.relative_to(ROOT).as_posix()
        hits = audit_file(p)
        if hits:
            flagged.append((rel, hits))

    print(f"scanned {len(html_files)} HTML under 02_dashboards/")
    print(f"flagged {len(flagged)}")
    for rel, hits in flagged[:40]:
        print(f"  {rel}")
        for h in hits:
            print(f"    - {h}")
    if len(flagged) > 40:
        print(f"  ... and {len(flagged) - 40} more")

    report = ROOT / "00_docs" / "_html_audit_tier1_20260819.md"
    lines = [
        "# HTML file:// audit (Tier 1 · read-only)",
        "",
        f"Scanned `{len(html_files)}` files under `02_dashboards/`.",
        f"**Flagged:** {len(flagged)}",
        "",
        "| File | Issue |",
        "|------|-------|",
    ]
    for rel, hits in flagged:
        lines.append(f"| `{rel}` | {'; '.join(hits)} |")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nreport -> {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
