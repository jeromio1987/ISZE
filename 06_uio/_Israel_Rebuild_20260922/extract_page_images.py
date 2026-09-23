"""Extract embedded image objects from the UTI deck pages 14-18 and render them at native size."""
from __future__ import annotations

import json
from pathlib import Path

import fitz

SRC = Path(r"C:\Users\jerom\Downloads\מצגת לחלפים בלגיה - אפריל 2026.pdf")
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Israel_Rebuild_20260922\_pdf")
OUT.mkdir(parents=True, exist_ok=True)

doc = fitz.open(SRC)
report = []
for p in range(13, 19):
    page = doc[p - 1]
    imgs = page.get_images(full=True)
    page_info = {"page": p, "rect": list(page.rect), "n_images": len(imgs), "images": []}
    print(f"--- page {p}: rect={tuple(round(v) for v in page.rect)} images={len(imgs)}")
    for k, im in enumerate(imgs):
        xref = im[0]
        d = doc.extract_image(xref)
        name = f"p{p:02d}_img{k:02d}_{d['width']}x{d['height']}.{d['ext']}"
        f = OUT / name
        f.write_bytes(d["image"])
        page_info["images"].append(
            {"xref": xref, "w": d["width"], "h": d["height"], "ext": d["ext"], "file": name}
        )
        print(f"    img{k}: xref={xref} {d['width']}x{d['height']} {d['ext']} ext={d['colorspace']} -> {name}")
    # also copy the full-page render at very high dpi for the smallest-text legibility
    pix = page.get_pixmap(dpi=400)
    hp = OUT / f"p{p:02d}_hi.png"
    pix.save(hp)
    page_info["hi_render"] = hp.name
    print(f"    hi-res render: {hp.name} {pix.width}x{pix.height}")
    report.append(page_info)

(OUT / "page_images.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("\nwrote:", OUT / "page_images.json")
