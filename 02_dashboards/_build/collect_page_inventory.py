"""Collect live HTML pages under 02_dashboards for the Universe board.

Writes 02_dashboards/_build/_page_inventory.json as a list of
{folder, file, title, mtime, kb} rows. The board builder groups by folder.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DASH = ROOT / "02_dashboards"
OUT = Path(__file__).resolve().parent / "_page_inventory.json"

FOLDERS = [
    "hub", "sales", "pricing", "ids", "ops", "fleet", "bi", "gps", "globe", "md_pack", "side",
]

SKIP_NAME = re.compile(r"(\.bak_|SHIP_RECEIPT|_qa|_tmp|^OPEN_)", re.I)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")


def _text(html: str) -> str:
    return re.sub(r"\s+", " ", unescape(TAG_RE.sub(" ", html))).strip()


def page_title(path: Path) -> str:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")[:80_000]
    except OSError:
        return path.stem
    m = TITLE_RE.search(raw)
    if m:
        t = _text(m.group(1))
        if t:
            return t[:160]
    m = H1_RE.search(raw)
    if m:
        t = _text(m.group(1))
        if t:
            return t[:160]
    return path.stem.replace("_", " ")


def main() -> int:
    rows = []
    for folder in FOLDERS:
        d = DASH / folder
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.html")):
            if SKIP_NAME.search(f.name):
                continue
            st = f.stat()
            rows.append({
                "folder": folder,
                "file": f.name,
                "title": page_title(f),
                "mtime": datetime.fromtimestamp(st.st_mtime).strftime("%d %b %Y"),
                "kb": max(1, round(st.st_size / 1024)),
                "bytes": st.st_size,
            })
    OUT.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    by = {}
    for r in rows:
        by[r["folder"]] = by.get(r["folder"], 0) + 1
    print(f"wrote {OUT}")
    print(f"  pages: {len(rows)}  by folder: {by}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
