# -*- coding: utf-8 -*-
from pathlib import Path

p7 = Path(__file__).resolve().parent / "07_ISZE_MD_Pack_Capture_FY27_FY28.html"
t7 = p7.read_text(encoding="utf-8")

old_dark = """@media (prefers-color-scheme:dark){
 body{background:#16161a;color:#d8d6cf} h1,h2,h3{color:#c3d4ef}
 .chartbox,.callout,table{background:#1e1e23;border-color:#33333a}
 .callout.gate{background:#2a1e1e} .callout.good{background:#182521}
 td{border-color:#2f2f36} tbody tr:nth-child(even){background:#232329}
 .lede{color:#c9c7c0} .lede b{color:#e8eaf0} .callout p{color:#c2c0b9}
}"""

new_dark = """@media (prefers-color-scheme:dark){
 body{background:#16161a;color:#d8d6cf} h1,h2,h3{color:#c3d4ef}
 .chartbox,.callout,table{background:#1e1e23;border-color:#33333a}
 .callout.gate{background:#2a1e1e} .callout.good{background:#182521}
 td{border-color:#2f2f36} tbody tr:nth-child(even){background:#232329}
 .lede{color:#c9c7c0} .lede b{color:#e8eaf0} .callout p{color:#c2c0b9}
 .chartttl{color:#b8b4aa}
 /* N10B-059: SVG labels must not stay charcoal on dark chart panels */
 .chartbox svg text{fill:#e8e4dc!important}
 .chartbox svg [fill="#52514e"],.chartbox svg [fill="#6b6256"]{fill:#e8e4dc!important}
}"""

if old_dark in t7:
    t7 = t7.replace(old_dark, new_dark, 1)
    print("dark: LF replaced")
elif old_dark.replace("\n", "\r\n") in t7:
    t7 = t7.replace(old_dark.replace("\n", "\r\n"), new_dark.replace("\n", "\r\n"), 1)
    print("dark: CRLF replaced")
else:
    raise SystemExit("dark block not found")

t7 = t7.replace(
    "Gross profit given up when a genuine sale becomes BVP · CY2025 · € per year",
    "Unit-profit difference if a genuine sale is substituted by BVP · CY2025 · € per year (scenario)",
)
t7 = t7.replace(
    "and the total gross profit given up to down-trade is <b>€110,391 a year</b>.<sup>3</sup></p>",
    "and the unit-profit difference if observed BVP volume had otherwise been genuine is <b>€110,391 a year</b> under that substitution scenario — not a proven realised loss.<sup>3</sup></p>",
)
t7 = t7.replace(
    "Mix is a genuine sale that became a BVP sale — the customer stayed\ninside the tent, we earned a thinner margin.",
    "Mix is treated here as a genuine sale compared with a BVP sale on a substitution basis — "
    "the customer may have stayed, left, or never bought genuine; the page does not prove which.",
)
t7 = t7.replace(
    "Mix is a genuine sale that became a BVP sale — the customer stayed\r\ninside the tent, we earned a thinner margin.",
    "Mix is treated here as a genuine sale compared with a BVP sale on a substitution basis — "
    "the customer may have stayed, left, or never bought genuine; the page does not prove which.",
)

banner = """
<div class="callout" id="n10b-060">
  <h3>Conditional substitution sensitivity</h3>
  <p>The original-to-value unit-profit comparison is a scenario: it asks what the margin difference would be
  if the observed value-part volume had otherwise been original-part volume at the assumed price.
  It does not establish displacement. The same sale could replace an original sale, retain a customer who
  would otherwise leave, or win volume that would not have occurred. No displacement percentage is assumed.</p>
</div>
"""

anchor = '<h2 class="sec"><span class="no">2</span>Mix risk vs. true leakage</h2>'
if "n10b-060" not in t7:
    if anchor not in t7:
        raise SystemExit("section 2 anchor missing")
    t7 = t7.replace(anchor, anchor + "\n" + banner, 1)
    print("060 banner inserted")

p7.write_text(t7, encoding="utf-8")
print("07 written", p7.stat().st_size)
