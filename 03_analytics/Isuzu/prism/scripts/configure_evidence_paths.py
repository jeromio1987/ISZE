#!/usr/bin/env python3
"""Rewrite Evidence SQL sources to use ISZE_DERIVED (portable paths)."""

from __future__ import annotations

import os
import re
from pathlib import Path

PRISM_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_SOURCES = PRISM_ROOT / "evidence-app" / "sources" / "prism"
OLD_PREFIX = r"C:/Users/jerom/Desktop/claude/ISZE/Data/derived"


def resolve_derived() -> Path:
    if env := os.environ.get("ISZE_DERIVED"):
        return Path(env).resolve()
    # Repo layout: evidence-app + data/derived at repo root
    candidate = PRISM_ROOT.parent.parent.parent.parent / "Data" / "derived"
    if candidate.is_dir():
        return candidate.resolve()
    return (PRISM_ROOT / "data" / "derived").resolve()


def main() -> int:
    derived = resolve_derived()
    d = str(derived).replace("\\", "/")
    n = 0
    for sql in EVIDENCE_SOURCES.glob("*.sql"):
        text = sql.read_text(encoding="utf-8")
        new = text.replace(OLD_PREFIX, d)
        if new != text:
            sql.write_text(new, encoding="utf-8")
            n += 1
    print(f"Evidence SQL paths -> {d} ({n} files updated)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
