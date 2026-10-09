# -*- coding: utf-8 -*-
from pathlib import Path

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy")
md = OUT / "ISZE_MD_TRACK_BUSINESS_PLAN_2026-10-08.md"
html = OUT / "ISZE_MD_TRACK_BUSINESS_PLAN_2026-10-08.html"

NOTE = """

## Motion film (8 Oct 2026, loop tick 3)

Timed opex-lever film for the Japan / board conversation (MOA EUR 30k, Duncan register, three margin layers, 1/218 evidence hole, floor/stretch ask):

- Interactive: `OPEN_DLOD_OPEX_MOTION_FILM_2026-10-08.cmd`
- MP4 (~85s): `OPEN_DLOD_OPEX_MOTION_FILM_MP4_2026-10-08.cmd`

Same folder as this plan. Does not replace the scorecard; it is the spoken arc.

"""

INJECT = """
<section class="panel" id="motion-film" style="margin:28px 0;padding:18px 20px;border-left:4px solid #c0552d;background:#f7f4ee">
  <h2 style="font-family:Georgia,serif;color:#15233c;margin:0 0 8px">Motion film</h2>
  <p style="color:#222;margin:0 0 8px">~85s opex-lever arc: MOA EUR 30k, Duncan register, three margin layers, 1/218 evidence hole, floor/stretch Japan ask.</p>
  <p style="margin:0;font-size:14px">Double-click OPEN_DLOD_OPEX_MOTION_FILM_MP4_2026-10-08.cmd (movie) or OPEN_DLOD_OPEX_MOTION_FILM_2026-10-08.cmd (interactive).</p>
</section>
"""


def main() -> None:
    t = md.read_text(encoding="utf-8")
    if "Motion film (8 Oct 2026" not in t:
        md.write_text(t.rstrip() + NOTE, encoding="utf-8")
        print("md patched")
    else:
        print("md already has film note")

    h = html.read_text(encoding="utf-8")
    if "OPEN_DLOD_OPEX_MOTION_FILM" not in h:
        if "</body>" not in h:
            raise SystemExit("no body tag")
        html.write_text(h.replace("</body>", INJECT + "\n</body>", 1), encoding="utf-8")
        print("html patched")
    else:
        print("html already linked")
    print("tick3 done")


if __name__ == "__main__":
    main()
