#!/usr/bin/env python3
"""Rename AIM L2 label Friction -> Pads & Shoes across ISZE text artefacts.

Exact whole-token / whole-cell replacements only. Skips binary, archives,
worktrees, and Python sources (those keep the old name in mapping tables).
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OLD = "Friction"
NEW = "Pads & Shoes"

SKIP_DIRS = {
    ".git", "node_modules", "07_deploy", "__pycache__", ".cursor",
    "_archive", "worktrees",
}
SKIP_SUFFIX = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip",
               ".parquet", ".xlsx", ".xlsm", ".exe", ".dll", ".pyc", ".py"}
RX = re.compile(r"(?<![A-Za-z])Friction(?![A-Za-z])")

CSV_COLS = {
    "aim_l2", "aim_l2_fixed", "workbook_l2", "l2", "AIM L2", "aim_level_2",
    "level_2", "L2", "family_l2", "group_l2",
}


def should_skip(path: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    if path.suffix.lower() in SKIP_SUFFIX:
        return True
    name = path.name.lower()
    if name.startswith("partgroups_") and name.endswith(".json"):
        return True
    if name == "autodoc_results.csv":
        return True
    if "_build" in path.parts and "history" in path.parts:
        return True
    return False


def patch_csv(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8-sig")
    if OLD not in text:
        return 0
    try:
        with path.open(encoding="utf-8", newline="") as f:
            sample = f.read(4096)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;")
            except csv.Error:
                dialect = csv.excel
            reader = csv.DictReader(f, dialect=dialect)
            if not reader.fieldnames:
                return 0
            rows = list(reader)
            fields = [c for c in reader.fieldnames if c is not None]
    except Exception:
        n = len(RX.findall(text))
        if not n:
            return 0
        path.write_text(RX.sub(NEW, text), encoding="utf-8")
        return n

    changed = 0
    aimish = any(c in CSV_COLS or "aim" in (c or "").lower() or c in ("l2", "L2") for c in fields)
    out_rows = []
    for row in rows:
        row2 = {k: v for k, v in row.items() if k is not None}
        for c, v in list(row2.items()):
            if v is None:
                continue
            if str(v).strip() == OLD:
                if aimish or c in CSV_COLS or (c or "").lower().endswith("l2"):
                    row2[c] = NEW
                    changed += 1
            elif OLD in str(v) and aimish:
                nv = RX.sub(NEW, str(v))
                if nv != v:
                    row2[c] = nv
                    changed += 1
        out_rows.append(row2)
    if changed:
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
            w.writeheader()
            w.writerows(out_rows)
    return changed


def patch_text(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return 0
    if OLD not in text:
        return 0
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(text)
            n = 0

            def walk(o):
                nonlocal n
                if isinstance(o, dict):
                    for k, v in list(o.items()):
                        if v == OLD:
                            o[k] = NEW
                            n += 1
                        else:
                            walk(v)
                elif isinstance(o, list):
                    for i, v in enumerate(o):
                        if v == OLD:
                            o[i] = NEW
                            n += 1
                        else:
                            walk(v)

            walk(data)
            if n:
                path.write_text(
                    json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                    encoding="utf-8",
                )
            return n
        except json.JSONDecodeError:
            pass
    n = len(RX.findall(text))
    if not n:
        return 0
    path.write_text(RX.sub(NEW, text), encoding="utf-8")
    return n


def main() -> int:
    total = 0
    files = 0
    for path in ISZE.rglob("*"):
        if not path.is_file() or should_skip(path):
            continue
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        if b"Friction" not in raw and OLD.encode() not in raw:
            continue
        try:
            if path.suffix.lower() == ".csv":
                c = patch_csv(path)
            elif path.suffix.lower() in {".md", ".txt", ".html", ".json", ".yml", ".yaml"}:
                c = patch_text(path)
            else:
                continue
        except (OSError, ValueError) as e:
            print(f"  SKIP {path.relative_to(ISZE)}: {e}")
            continue
        if c:
            files += 1
            total += c
            print(f"  {c:5d}  {path.relative_to(ISZE)}")
    print(f"DONE files={files} replacements={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
