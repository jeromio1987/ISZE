# -*- coding: utf-8 -*-
"""Loop tick 4: add a speakable next-week opex line to MD-track md + html."""
from pathlib import Path

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy")
md = OUT / "ISZE_MD_TRACK_BUSINESS_PLAN_2026-10-08.md"
html = OUT / "ISZE_MD_TRACK_BUSINESS_PLAN_2026-10-08.html"

MARK = "Speak line (8 Oct 2026, loop tick 4)"

MD_BLOCK = f"""

## {MARK}

One sentence for the opex conversation (floor first; stretch only if they ask):

> Please confirm the existing EUR 30,000 Don't Lose the Deal line for ITUK under the signed MOA (activity record required). If you want network scale, the next step is a EUR 70–80k pilot for IUK plus one other book market, with competitor price on every case — not a full-book envelope yet.

Do not lead with ~EUR 163k full-book 0.5%. Do not invent a dealer keep-rate; the MOA has none.

"""

HTML_BLOCK = """
<section class="panel" id="speak-line" style="margin:28px 0;padding:18px 20px;border:1px solid #c0552d;background:#15233c;color:#f7f4ee">
  <h2 style="font-family:Georgia,serif;color:#f7f4ee;margin:0 0 10px">Speak line — next week</h2>
  <p style="margin:0;line-height:1.45;font-size:16px">Please confirm the existing <strong style="color:#e07848">EUR 30,000</strong> Don't Lose the Deal line for ITUK under the signed MOA (activity record required). If you want network scale, the next step is a <strong style="color:#e07848">EUR 70–80k</strong> pilot for IUK plus one other book market, with competitor price on every case — not a full-book envelope yet.</p>
</section>
"""


def main() -> None:
    t = md.read_text(encoding="utf-8")
    if MARK not in t:
        md.write_text(t.rstrip() + MD_BLOCK, encoding="utf-8")
        print("md patched")
    else:
        print("md already has speak line")

    h = html.read_text(encoding="utf-8")
    if 'id="speak-line"' not in h:
        # Prefer insert after motion-film if present, else before </body>
        if 'id="motion-film"' in h:
            h = h.replace('id="motion-film"', 'id="motion-film"', 1)
            # insert after closing </section> of motion-film — find first occurrence block end
            key = 'id="motion-film"'
            i = h.find(key)
            j = h.find("</section>", i)
            if j == -1:
                raise SystemExit("motion-film section end missing")
            j += len("</section>")
            h = h[:j] + "\n" + HTML_BLOCK + h[j:]
        elif "</body>" in h:
            h = h.replace("</body>", HTML_BLOCK + "\n</body>", 1)
        else:
            raise SystemExit("no insert point")
        html.write_text(h, encoding="utf-8")
        print("html patched")
    else:
        print("html already has speak line")
    print("tick4 done")


if __name__ == "__main__":
    main()
