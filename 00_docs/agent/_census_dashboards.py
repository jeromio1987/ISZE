#!/usr/bin/env python3
"""Full census of 02_dashboards HTML for BI audit."""
from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DASH = ROOT / "02_dashboards"
OUT = ROOT / "00_docs" / "agent" / "BI_DASHBOARD_CENSUS_2026-09-06.csv"
SKIP = {"_build", "_archive", "history", "_extracted", "node_modules"}


def main() -> None:
    rows: list[dict] = []
    for html in DASH.rglob("*.html"):
        if SKIP & set(html.parts):
            continue
        rel = html.relative_to(DASH).as_posix()
        folder = html.parent.relative_to(DASH).as_posix() if html.parent != DASH else "."
        top = folder.split("/")[0] if folder != "." else "root"
        size = html.stat().st_size
        mtime = datetime.fromtimestamp(html.stat().st_mtime).strftime("%Y-%m-%d")
        text = html.read_text(encoding="utf-8", errors="ignore")
        head = text[:12000]
        title = ""
        low = head.lower()
        if "<title>" in low:
            i = low.find("<title>")
            j = low.find("</title>", i)
            title = head[i + 7 : j].strip().replace("\n", " ")[:120]
        open_hit = ""
        for c in sorted(html.parent.glob("OPEN_*.cmd")):
            body = c.read_text(encoding="utf-8", errors="ignore").lower()
            if html.name.lower() in body:
                open_hit = c.name
                break
        if not open_hit:
            cmds = sorted(p.name for p in html.parent.glob("OPEN_*.cmd"))
            open_hit = ";".join(cmds[:4])
        rows.append(
            {
                "rel_path": rel,
                "folder": top,
                "file": html.name,
                "title": title,
                "size_kb": round(size / 1024, 1),
                "mtime": mtime,
                "open_cmd": open_hit,
                "has_named_open": "Y" if any(
                    html.name.lower() in p.read_text(encoding="utf-8", errors="ignore").lower()
                    for p in html.parent.glob("OPEN_*.cmd")
                )
                else "N",
                "folder_has_open": "Y" if list(html.parent.glob("OPEN_*.cmd")) else "N",
                "cdn": "Y" if ("cdn.jsdelivr" in text or "cdnjs.cloudflare" in text) else "N",
                "fetch": "Y" if "fetch(" in text else "N",
                "embed_json": "Y" if "application/json" in text else "N",
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows.sort(key=lambda r: r["rel_path"])
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    fc = Counter(r["folder"] for r in rows)
    print(f"TOTAL {len(rows)}")
    print("BY_FOLDER", dict(sorted(fc.items())))
    print("NO_NAMED_OPEN", sum(1 for r in rows if r["has_named_open"] == "N"))
    print("NO_FOLDER_OPEN", sum(1 for r in rows if r["folder_has_open"] == "N"))
    print("CDN", sum(1 for r in rows if r["cdn"] == "Y"))
    print("FETCH", sum(1 for r in rows if r["fetch"] == "Y"))
    print(f"WROTE {OUT}")


if __name__ == "__main__":
    main()
