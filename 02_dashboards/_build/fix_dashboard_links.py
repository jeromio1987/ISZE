#!/usr/bin/env python3
"""Rewrite relative links after Dashboards/ subfolder layout (one level deep)."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "manifest.yaml"


def load_file_to_folder() -> dict[str, str]:
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for folder, names in data["files"].items():
        for name in names:
            out[name] = folder
    return out


def rel(from_folder: str, to_folder: str, filename: str) -> str:
    if from_folder == to_folder:
        return filename
    return f"../{to_folder}/{filename}"


def fix_html(path: Path, file_map: dict[str, str], folder: str) -> bool:
    text = path.read_text(encoding="utf-8")
    orig = text

    for target, target_folder in file_map.items():
        for pat in (
            rf'href="{re.escape(target)}"',
            rf"href='{re.escape(target)}'",
            rf'content="0;url={re.escape(target)}"',
        ):
            new_href = rel(folder, target_folder, target)
            if pat.startswith("href"):
                text = re.sub(pat, pat.split("=")[0] + f'="{new_href}"', text)
            else:
                text = re.sub(pat, f'content="0;url={new_href}"', text)

    text = text.replace('href="_ui/', 'href="../_ui/')
    text = text.replace("href='_ui/", "href='../_ui/")
    text = text.replace('src="_ui/', 'src="../_ui/')
    text = text.replace('src="propertiq-assets/', 'src="../propertiq-assets/')
    text = text.replace("fetch('../Data/", "fetch('../../Data/")
    text = text.replace('href="../Data/', 'href="../../Data/')
    text = text.replace('href="../Isuzu/', 'href="../../Isuzu/')
    text = text.replace('href="../Projects/', 'href="../../Projects/')

    if text != orig:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    file_map = load_file_to_folder()
    changed = 0
    for folder in file_map.values():
        d = ROOT / folder
        if not d.is_dir():
            continue
        for html in d.glob("*.html"):
            f = file_map.get(html.name, folder)
            if fix_html(html, file_map, f):
                print(f"fixed: {folder}/{html.name}")
                changed += 1
    print(f"Done — {changed} files updated")


if __name__ == "__main__":
    main()
