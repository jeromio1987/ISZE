#!/usr/bin/env python3
"""Catch HTML that will render as garbled characters.

The usual ISZE failure: a dashboard is authored as an artifact fragment, so it
has no <head> and no charset declaration. The bytes are valid UTF-8, but a
browser opening it from file:// on a Windows locale falls back to windows-1252
and every en dash, arrow and euro sign turns into mojibake.

Checks, per file:
  NO_CHARSET    non-ASCII content and no charset declared in the first 1024
                bytes (browsers ignore a late <meta charset>)
  BAD_UTF8      bytes are not valid UTF-8 -- the file is in a legacy encoding
  MOJIBAKE      already double-encoded on disk; re-saving will not fix it
  BOM           UTF-8 BOM present -- harmless in a browser, noisy in diffs

Usage
  python 04_tools/html_encoding_check.py                 # whole repo
  python 04_tools/html_encoding_check.py 02_dashboards   # one subtree
  python 04_tools/html_encoding_check.py --staged        # pre-commit hook
  python 04_tools/html_encoding_check.py --fix           # inject the meta tag

Exit code is 1 when anything at ERROR level is found, so it works as a
pre-commit hook or CI gate.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

# Written so the report itself is pure ASCII -- this script must not become
# the thing it is checking for.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SKIP_DIRS = {".git", "node_modules", ".claude", "__pycache__", ".venv", "venv"}
HTML_EXT = (".html", ".htm")

# Sequences that only occur when UTF-8 has already been decoded as cp1252 and
# re-encoded. Their presence means the damage is baked into the bytes.
MOJIBAKE_MARKERS = (
    "â€™",  # '
    "â€œ",  # "
    "â€",  # "
    "â€“",  # en dash
    "â€”",  # em dash
    "â†’",  # arrow
    "â‚¬",  # euro
    "Ã©",        # e-acute
    "Ã¨",        # e-grave
    "Ã¼",        # u-umlaut
    "Â ",        # nbsp
    "ï»¿",  # BOM read as latin-1
)

CHARSET_WINDOW = 1024  # browsers only honour a declaration this early
META_TAG = '<meta charset="utf-8">'


def find_html(root: str) -> list[str]:
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.lower().endswith(HTML_EXT):
                out.append(os.path.join(dirpath, name))
    return sorted(out)


def staged_html() -> list[str]:
    res = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True,
    )
    return [p for p in res.stdout.splitlines()
            if p.lower().endswith(HTML_EXT) and os.path.exists(p)]


def inspect(path: str) -> list[tuple[str, str, str]]:
    """Return [(level, code, detail)] for one file."""
    with open(path, "rb") as fh:
        raw = fh.read()

    findings: list[tuple[str, str, str]] = []
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    body = raw[3:] if has_bom else raw

    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [("ERROR", "BAD_UTF8",
                 f"not valid UTF-8 at byte {exc.start} -- file is in a legacy encoding")]

    non_ascii = sum(1 for ch in text if ord(ch) > 127)

    hits = [m for m in MOJIBAKE_MARKERS if m in text]
    if hits:
        findings.append(("ERROR", "MOJIBAKE",
                         f"{len(hits)} double-encoded sequence type(s) already in the bytes"))

    head = text[:CHARSET_WINDOW].lower()
    declared = "charset" in head and "utf-8" in head.replace("utf8", "utf-8")
    if non_ascii and not declared:
        findings.append(("ERROR", "NO_CHARSET",
                         f"{non_ascii} non-ASCII chars, no charset in first {CHARSET_WINDOW} bytes"))

    if has_bom:
        findings.append(("WARN", "BOM", "UTF-8 BOM present"))

    return findings


def fix(path: str) -> bool:
    """Inject the meta tag. Only safe for NO_CHARSET; never touches broken bytes."""
    with open(path, "rb") as fh:
        raw = fh.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return False

    lowered = text.lower()
    if "<head>" in lowered:
        idx = lowered.index("<head>") + len("<head>")
        patched = text[:idx] + "\n" + META_TAG + text[idx:]
    else:
        # Artifact-style fragment: no head to insert into, so prepend.
        patched = META_TAG + "\n" + text

    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(patched)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Check HTML files for encoding faults.")
    ap.add_argument("root", nargs="?", default=".", help="directory to scan (default: repo root)")
    ap.add_argument("--staged", action="store_true", help="check git-staged HTML only")
    ap.add_argument("--fix", action="store_true", help="inject <meta charset> where it is missing")
    ap.add_argument("--quiet", action="store_true", help="print findings only")
    args = ap.parse_args()

    files = staged_html() if args.staged else find_html(args.root)

    errors = warns = fixed = 0
    for path in files:
        for level, code, detail in inspect(path):
            rel = os.path.relpath(path)
            if level == "ERROR":
                errors += 1
                if args.fix and code == "NO_CHARSET" and fix(path):
                    fixed += 1
                    print(f"  FIXED  {code:<11} {rel}")
                    continue
                print(f"  ERROR  {code:<11} {rel}\n         {detail}")
            else:
                warns += 1
                if not args.quiet:
                    print(f"  warn   {code:<11} {rel}")

    scope = "staged" if args.staged else args.root
    print(f"\nscanned {len(files)} HTML file(s) in {scope}: "
          f"{errors} error(s), {warns} warning(s)"
          + (f", {fixed} fixed" if args.fix else ""))

    if args.fix:
        return 1 if (errors - fixed) else 0
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
