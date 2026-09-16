"""Save an official Isuzu Truck UK N75 / P700 image into the SHARE assets folder."""
from __future__ import annotations

import re
from pathlib import Path

import requests

ASSETS = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Preparation Meetings"
    r"\IML_ITUK_PMS\mp\SHARE\assets"
)
ASSETS.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,*/*;q=0.8",
}

PAGES = [
    "https://www.isuzutruck.co.uk/products/n75-190/",
    "https://www.isuzutruck.co.uk/products/n75-150e/",
    "https://www.isuzutruck.co.uk/isuzu-to-debut-new-truck-range-at-rtx-2026/",
]


def first_images(html: str) -> list[str]:
    found = []
    for pat in (
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'src=["\'](https://www\.isuzutruck\.co\.uk/wp-content/uploads/[^"\']+\.(?:jpg|jpeg|png|webp))["\']',
        r'src=["\'](https://www\.isuzutruck\.co\.uk/wp-content/uploads/[^"\']+)["\']',
    ):
        found.extend(re.findall(pat, html, flags=re.I))
    out = []
    for u in found:
        if u not in out and not u.endswith(".svg"):
            out.append(u)
    return out


def main():
    session = requests.Session()
    session.headers.update(HEADERS)
    saved = []
    notes = []
    for page in PAGES:
        try:
            r = session.get(page, timeout=25)
            r.raise_for_status()
        except Exception as e:
            notes.append(f"FAIL page {page}: {e}")
            continue
        imgs = first_images(r.text)
        notes.append(f"{page} -> {len(imgs)} image URL(s)")
        for i, url in enumerate(imgs[:3]):
            ext = Path(url.split("?")[0]).suffix or ".jpg"
            if "rtx" in page:
                name = f"P700_ITUK_RTX2026_{i+1}{ext}"
                source = "Isuzu Truck UK — P700 range announcement (RTX 2026)"
            else:
                name = f"N75_ITUK_product_{Path(page.rstrip('/').split('/')[-1])}_{i+1}{ext}"
                source = "Isuzu Truck UK — N75 product page (illustration)"
            dest = ASSETS / name
            try:
                ir = session.get(url, timeout=25)
                ir.raise_for_status()
                if len(ir.content) < 8000:
                    notes.append(f"skip small {url} ({len(ir.content)} bytes)")
                    continue
                dest.write_bytes(ir.content)
                saved.append((dest, url, source, len(ir.content)))
                notes.append(f"saved {dest.name} {len(ir.content)} from {url}")
            except Exception as e:
                notes.append(f"FAIL img {url}: {e}")

    src = ASSETS / "SOURCE.txt"
    lines = [
        "N75 / P700 images — source and copyright",
        "",
        "Owner: Isuzu Truck (UK) Limited. Pictures are for illustration.",
        "Use: internal Tuesday pack / ISZE meeting only. Do not publish as our own photography.",
        "Do not write these files to Downloads.",
        "",
    ]
    for dest, url, source, n in saved:
        lines += [f"File: {dest.name}", f"Bytes: {n}", f"Page/source: {source}", f"URL: {url}", ""]
    if not saved:
        lines.append("No image downloaded this pass. See notes below.")
    lines += ["Notes:"] + notes
    src.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(notes))
    print("SOURCE", src)
    print("saved", len(saved))


if __name__ == "__main__":
    main()
