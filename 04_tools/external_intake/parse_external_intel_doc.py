#!/usr/bin/env python
"""Acceptance check for an external intel document (Grok Bot or any outside worker).

The boundary in 00_docs/agent/EXTERNAL_AI_SERVICES.md says the Bot's output is not
used until the figures and sources are checked. This script does the mechanical part
of that check: it does not judge whether a story is true, it proves the document is
*checkable* — every item carries a source link and a date, every section is present,
and no internal-only vocabulary has leaked in.

Usage:
    python 04_tools/external_intake/parse_external_intel_doc.py --doc <path to .md>
    python 04_tools/external_intake/parse_external_intel_doc.py           # runs the example

Exit 0 = structurally valid, no leaks flagged. Non-zero = do not file the document;
read the report and send it back to the Bot.

Writes <stem>_verify.md next to the document.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

TITLE_RE = re.compile(r"^#\s*ISZE Intel Watch\s*[-–—]\s*(?P<date>.+?)\s*$", re.I)
SECTION_RE = re.compile(r"^##\s+(?P<name>.+?)\s*$")
ITEM_RE = re.compile(r"^\s*[-*]\s+(?P<body>.+)$")
URL_RE = re.compile(r"https?://[^\s)\]>\"']+")

DATE_PATTERNS = (
    "%Y-%m-%d",
    "%d %B %Y",
    "%d %b %Y",
    "%B %d, %Y",
    "%b %d, %Y",
)
DATE_IN_TEXT = re.compile(
    r"(\d{4}-\d{2}-\d{2})"
    r"|(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})"
    r"|((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s*\d{4})",
    re.I,
)

REQUIRED_SECTIONS = (
    "top items",
    "everything else worth noting",
    "sources that did not load",
)

# Internal-only vocabulary. This is a leak alarm, not a proof of correctness: it
# catches the words a public-source watcher has no reason to use, which is exactly
# how an internal figure slips into a document that should not carry one.
INTERNAL_TERMS = (
    "margin",
    "%gm",
    "list price",
    "dealer price",
    "billed",
    "capture rate",
    "wallet",
    "sell-out",
    "sellout",
    "sales to dealer",
    "kosha",
    "spa basket",
    "net price",
    "discount rate",
)


def parse_date(text: str) -> dt.date | None:
    text = text.strip().strip(".")
    for fmt in DATE_PATTERNS:
        try:
            return dt.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    match = DATE_IN_TEXT.search(text)
    if not match:
        return None
    for fmt in DATE_PATTERNS:
        try:
            return dt.datetime.strptime(match.group(0), fmt).date()
        except ValueError:
            continue
    return None


def parse_sections(lines: list[str]) -> tuple[str | None, dict[str, list[str]]]:
    title_date = None
    sections: dict[str, list[str]] = {}
    current = None
    for line in lines:
        title = TITLE_RE.match(line)
        if title:
            title_date = title.group("date")
            continue
        head = SECTION_RE.match(line)
        if head:
            # "Top items (at most five, ...)" and "Top items" are the same section.
            current = head.group("name").split("(")[0].strip().lower()
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)
    return title_date, sections


def check_item(body: str, allow_no_link: bool) -> list[str]:
    problems = []
    url = URL_RE.search(body)
    if not url and not allow_no_link:
        problems.append("no source link")
    if parse_date(body) is None:
        problems.append("no date")
    return problems


def iter_items(section_lines: list[str]):
    """Yield each bullet as one body, folding wrapped continuation lines in.

    A real briefing wraps a long item over several lines; the source link and the
    date often land on the last of them. A bullet ends at the next bullet, a blank
    line, or a heading.
    """
    current: list[str] = []
    for line in section_lines:
        if SECTION_RE.match(line):
            if current:
                yield " ".join(current).strip()
                current = []
            continue
        match = ITEM_RE.match(line)
        if match:
            if current:
                yield " ".join(current).strip()
            current = [match.group("body").strip()]
            continue
        if not line.strip():
            if current:
                yield " ".join(current).strip()
                current = []
            continue
        if current:
            current.append(line.strip())
    if current:
        yield " ".join(current).strip()


def main() -> int:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--doc",
        default=str(here / "EXAMPLE_intel_watch_doc.md"),
        help="path to the external intel document",
    )
    args = parser.parse_args()

    doc = Path(args.doc)
    if not doc.exists():
        print(f"ABORTED - document not found: {doc}")
        return 2

    text = doc.read_text(encoding="utf-8")
    lines = text.splitlines()

    title_date_raw, sections = parse_sections(lines)

    errors: list[str] = []
    warnings: list[str] = []

    # 1. Title and document date
    if title_date_raw is None:
        errors.append("title missing or not in the form '# ISZE Intel Watch - <date>'")
    elif parse_date(title_date_raw) is None:
        errors.append(f"title date not readable: {title_date_raw!r}")

    # 2. Every required section present
    for name in REQUIRED_SECTIONS:
        if name not in sections:
            errors.append(f"section missing: '## {name.title()}'")

    # 3. Every item carries a source link and a date
    item_counts: dict[str, int] = {}
    for name in REQUIRED_SECTIONS:
        bodies = list(iter_items(sections.get(name, [])))
        item_counts[name] = len(bodies)
        allow_no_link = name == "sources that did not load"
        for body in bodies:
            problems = check_item(body, allow_no_link)
            if problems:
                errors.append(f"[{name}] item {problems}: {body[:90]}")

    # 4. Leak alarm - internal-only vocabulary in a public-source document
    lowered = text.lower()
    for term in INTERNAL_TERMS:
        if re.search(rf"(?<![a-z]){re.escape(term)}(?![a-z])", lowered):
            warnings.append(f"internal-only term appears: {term!r}")

    # 5. Honesty check - a document where nothing failed to load is fine, but an
    #    empty 'did not load' section must be explicitly stated, not just blank.
    if item_counts.get("sources that did not load", 0) == 0:
        empty_body = " ".join(sections.get("sources that did not load", [])).strip().lower()
        if "none" not in empty_body and "no source" not in empty_body:
            warnings.append(
                "'sources that did not load' is empty without saying so - state 'none' "
                "explicitly rather than leaving it blank"
            )

    ok = not errors
    stamp = dt.date.today().isoformat()
    report_lines = [
        f"# External intel document - acceptance check",
        "",
        f"- Document: `{doc.name}`",
        f"- Checked: {stamp}",
        f"- Verdict: **{'PASS' if ok else 'FAIL'}**",
        f"- Items: "
        + ", ".join(f"{k} = {v}" for k, v in item_counts.items())
        + f" (total {sum(item_counts.values())})",
        "",
        "## Errors (block filing)",
        "",
    ]
    report_lines += [f"- {e}" for e in errors] or ["- none"]
    report_lines += ["", "## Warnings (read before use)", ""]
    report_lines += [f"- {w}" for w in warnings] or ["- none"]
    report_lines += [
        "",
        "## What this does not check",
        "",
        "- Whether a story is true, or whether a quoted price is the real market price.",
        "- A source link that returns 404 is not detected here; open the link.",
        "- Only the mechanical form is checked. The figures still have to be read "
        "against the page they name before anything enters a dashboard or a deck.",
        "",
        "Related: `00_docs/agent/EXTERNAL_AI_SERVICES.md` (the boundary), "
        "`00_docs/agent/GROK_BOT_SETUP.md` (section 7, the checkpoint).",
        "",
    ]

    report = doc.with_name(f"{doc.stem}_verify.md")
    report.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"Verdict: {'PASS' if ok else 'FAIL'}")
    print(f"Items: {item_counts} (total {sum(item_counts.values())})")
    print(f"Errors: {len(errors)}  Warnings: {len(warnings)}")
    print(f"Report: {report}")
    for e in errors:
        print(f"  ERROR   {e}")
    for w in warnings:
        print(f"  WARNING {w}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
