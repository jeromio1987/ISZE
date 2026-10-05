# -*- coding: utf-8 -*-
"""Read-only: what each sibling launcher points at, and whether that target exists."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NAMES = [
    "OPEN_ISUZU_UNIVERSE_WHITE_PAPER.cmd",
    "OPEN_ISUZU_UNIVERSE_3_0.cmd",
    "OPEN_ISUZU_UNIVERSE_3_0_ANNEX.cmd",
    "OPEN_ISUZU_UNIVERSE_3_0_DECK.cmd",
    "OPEN_ISUZU_UNIVERSE_3_0_SHOWCASE.cmd",
    "GPT_HANDOVER_2026-09-23/OPEN_UNIVERSE_3_0_CRITIQUE.cmd",
    "OPEN_Universe_Yellow_Paper_v0.5.cmd",
]

for n in NAMES:
    p = os.path.join(ROOT, n)
    if not os.path.exists(p):
        print("MISSING  %s" % n)
        continue
    raw = open(p, "rb").read()
    text = raw.decode("utf-8", "replace")
    crlf = b"\r\n" in raw
    m = re.search(r'start\s+""\s+"([^"]+)"', text)
    tgt_txt = m.group(1) if m else "?"
    rel = tgt_txt.replace("%~dp0", "")
    tgt = os.path.join(os.path.dirname(p), rel)
    print("%-52s crlf=%-5s -> %-48s exists=%s"
          % (n, crlf, rel, os.path.exists(tgt)))
