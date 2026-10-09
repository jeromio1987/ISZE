# -*- coding: utf-8 -*-
"""Record the DLOD motion HTML with Playwright → mp4 via ffmpeg."""
from __future__ import annotations

import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT_DIR = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy")
HTML = OUT_DIR / "DLOD_OPEX_MOTION_FILM_2026-10-08.html"
MP4 = OUT_DIR / "DLOD_OPEX_MOTION_FILM_2026-10-08.mp4"
QA = OUT_DIR / "_qa_dlod_motion"
CMD_MP4 = OUT_DIR / "OPEN_DLOD_OPEX_MOTION_FILM_MP4_2026-10-08.cmd"


def main() -> None:
    QA.mkdir(exist_ok=True)
    uri = HTML.resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1600, "height": 900},
            record_video_dir=str(QA),
            record_video_size={"width": 1600, "height": 900},
        )
        page = context.new_page()
        page.goto(uri, wait_until="domcontentloaded")
        page.wait_for_timeout(84000)
        page.screenshot(path=str(QA / "final_frame.png"), full_page=False)
        context.close()
        browser.close()

    vids = sorted(QA.glob("*.webm"), key=lambda x: x.stat().st_mtime, reverse=True)
    print("videos", vids)
    if not vids:
        raise SystemExit("no webm recorded")
    src = vids[0]
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(MP4),
        ],
        check=True,
    )
    print("MP4", MP4, MP4.stat().st_size)
    CMD_MP4.write_bytes(
        b'@echo off\r\nstart "" "%~dp0DLOD_OPEX_MOTION_FILM_2026-10-08.mp4"\r\n'
    )
    print("CMD", CMD_MP4)


if __name__ == "__main__":
    main()
