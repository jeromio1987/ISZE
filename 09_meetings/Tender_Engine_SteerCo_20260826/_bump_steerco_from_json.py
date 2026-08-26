#!/usr/bin/env python3
"""Bump SteerCo HTML to post-CZ desk figures — no portal browsers."""
from pathlib import Path

p = Path(__file__).resolve().parent / "ISZE_Tender_Engine_SteerCo.html"
t = p.read_text(encoding="utf-8")
repls = [
    ("319 notices / 284 opps", "326 notices / 291 opps"),
    ("notices 319 / opps 284", "notices 326 / opps 291"),
    ("Freeze 319 notices / 284 opps", "Freeze 326 notices / 291 opps"),
    ("of 284 opportunities", "of 291 opportunities"),
    ("national LIVE ~52% (15/29)", "national LIVE ~55% (16/29)"),
    ("National LIVE ~52% (14/29)", "National LIVE ~55% (16/29)"),
    ("National LIVE ~52% (15/29)", "National LIVE ~55% (16/29)"),
    ("LIVE ~52%", "LIVE ~55%"),
    ("~52% (15/29)", "~55% (16/29)"),
    ("15 / 29", "16 / 29"),
    (
        "UK, NL, BE, IL, FR, PL, IT, DE, RO, AT, NO, FI, DK, PT, BG. Was ~48% before BG.",
        "UK, NL, BE, IL, FR, PL, IT, DE, RO, AT, NO, FI, DK, PT, BG, CZ. Was ~52% before CZ.",
    ),
    ("with NO+FI+DK+PT+BG in", "with NO+FI+DK+PT+BG+CZ in"),
    ("ES WAF · CZ filters · LT apiKey", "ES WAF · LT apiKey"),
    ("BG LIVE; next ES WAF / CZ auth / LT key", "CZ LIVE; next ES WAF / LT key"),
    ('style="width:52%"', 'style="width:55%"'),
    ('style="width:10%"', 'style="width:7%"'),
    (">52%</div>", ">55%</div>"),
    (">10%</div>", ">7%</div>"),
    ("~10%", "~7%"),
    ("DE OV, RO SEAP, AT USP, <strong>NO + FI</strong> (keys DONE), <strong>DK udbud</strong>, <strong>PT BASE</strong>. National LIVE ~55% (16/29). Stated fleet hero is extract-subset only.",
     "DE OV, RO SEAP, AT USP, <strong>NO + FI</strong> (keys DONE), <strong>DK udbud</strong>, <strong>PT BASE</strong>, <strong>BG EOP</strong>, <strong>CZ VVZ</strong>. National LIVE ~55% (16/29). Stated fleet hero is extract-subset only."),
]
for a, b in repls:
    if a == b:
        continue
    n = t.count(a)
    if n:
        t = t.replace(a, b)
        print(f"ok x{n}: {a[:70]}")
    else:
        print(f"skip: {a[:70]}")

# CV layer b: 213 -> 215
if '<div class="n">215</div>' not in t:
    for old in ("213", "210"):
        needle = f'<div class="n">{old}</div>'
        if needle in t:
            t = t.replace(needle, '<div class="n">215</div>', 1)
            print(f"layer b {old}->215")
            break

# DARK band leftovers that still say ~52% for dark share → keep ~38%
t2 = (
    t.replace("~52% DARK", "~38% DARK")
    .replace("DARK/BLOCKED ~52%", "DARK/BLOCKED ~38%")
    .replace("DARK (TED-only)</div><div class=\"track\"><div class=\"fill muted\" style=\"width:55%\"></div></div><div class=\"pct\">55%</div>",
             "DARK (TED-only)</div><div class=\"track\"><div class=\"fill muted\" style=\"width:38%\"></div></div><div class=\"pct\">38%</div>")
)
if t2 != t:
    print("dark band normalize")
    t = t2

# CODE_READY tip / still CODE_READY section
t = t.replace("Still CODE_READY", "Still CODE_READY (ES · LT)")
t = t.replace(
    "Portal map + overnight runlog 2026-08-25.",
    "Portal map + overnight runlog 2026-08-25 (CZ LIVE).",
)

p.write_text(t, encoding="utf-8")
print("--- verify ---")
for s in ("326 notices", "291 opps", "~55%", "16 / 29", "215", "174", "CZ"):
    print(s, t.count(s))
