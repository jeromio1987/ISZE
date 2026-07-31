"""Visual QA for a deck — as contact sheets instead of one image per slide.

    python qa_contact_sheet.py --pptx "C:\\Users\\jerom\\Downloads\\ISZE_IUK_Sales_Review_FY2027.pptx"

Exports every slide via PowerPoint COM, writes the PDF next to the pptx, then
stitches the slides into 3x2 contact sheets (6 slides per image, numbered). An
18-slide deck becomes 3 images instead of 18 — same defects visible (text
overflow, collisions, empty blocks, truncated table cells), a fraction of the
cost to review.

The mandatory QA pass in DB_SALES_REVIEW_BLUEPRINT.md section 4 is satisfied by
looking at these sheets. Individual slides stay in the _slides subfolder if one
needs a closer look.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

COLS, ROWS = 3, 2
TILE_W = 1000          # px per slide in the sheet; 3x1000 = 3000px wide sheets
LABEL_H = 34

PS = r"""
$path   = "{pptx}"
$outDir = "{outdir}"
$pdf    = "{pdf}"
if (Test-Path $outDir) {{ Remove-Item $outDir -Recurse -Force }}
New-Item -ItemType Directory -Force $outDir | Out-Null
$ppt = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open($path, $true, $true, $false)
$pres.SaveAs($outDir, 17)
$pres.SaveAs($pdf, 32)
$pres.Close()
$ppt.Quit()
"""


def export(pptx: Path) -> tuple[Path, Path]:
    slides = pptx.parent / f"_{pptx.stem}_slides"
    pdf = pptx.with_suffix(".pdf")
    script = pptx.parent / f"_{pptx.stem}_qa.ps1"
    script.write_text(PS.format(pptx=pptx, outdir=slides, pdf=pdf), encoding="utf-8")
    r = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script)],
                       capture_output=True, text=True)
    script.unlink(missing_ok=True)
    if not slides.exists():
        print(r.stdout, r.stderr, file=sys.stderr)
        raise SystemExit("PowerPoint COM export failed — is PowerPoint installed and closed?")
    return slides, pdf


def sheets(slides_dir: Path, out_stem: Path) -> list[Path]:
    def num(p):
        m = re.search(r"(\d+)", p.stem)
        return int(m.group(1)) if m else 0

    imgs = sorted(slides_dir.rglob("*.JPG"), key=num) or sorted(slides_dir.rglob("*.jpg"), key=num)
    if not imgs:
        raise SystemExit(f"No slide images under {slides_dir}")

    with Image.open(imgs[0]) as im:
        ar = im.height / im.width
    th = int(TILE_W * ar)
    made = []
    per = COLS * ROWS
    for s_i in range(0, len(imgs), per):
        batch = imgs[s_i:s_i + per]
        sheet = Image.new("RGB", (COLS * TILE_W, ROWS * (th + LABEL_H)), "white")
        draw = ImageDraw.Draw(sheet)
        for i, ip in enumerate(batch):
            x, y = (i % COLS) * TILE_W, (i // COLS) * (th + LABEL_H)
            with Image.open(ip) as im:
                sheet.paste(im.convert("RGB").resize((TILE_W, th), Image.LANCZOS), (x, y + LABEL_H))
            draw.rectangle([x, y, x + TILE_W, y + LABEL_H], fill="#CC0E1E")
            draw.text((x + 10, y + 9), f"SLIDE {num(ip)}", fill="white")
            draw.rectangle([x, y + LABEL_H, x + TILE_W - 1, y + LABEL_H + th - 1], outline="#B7B7B7")
        out = out_stem.with_name(f"{out_stem.name}_sheet{len(made)+1}.png")
        sheet.save(out, optimize=True)
        made.append(out)
    return made


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", required=True)
    ap.add_argument("--keep-slides", action="store_true",
                    help="keep the per-slide JPGs (default: delete after stitching)")
    a = ap.parse_args()

    pptx = Path(a.pptx)
    if not pptx.exists():
        raise SystemExit(f"Not found: {pptx}")
    slides_dir, pdf = export(pptx)
    out = sheets(slides_dir, pptx.parent / f"_{pptx.stem}_qa")
    if not a.keep_slides:
        shutil.rmtree(slides_dir, ignore_errors=True)

    print(f"PDF:    {pdf}")
    for s in out:
        print(f"SHEET:  {s}")
    print(f"\n{len(out)} contact sheet(s) — read these instead of the individual slides.")


if __name__ == "__main__":
    main()
