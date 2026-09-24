"""Screenshot the built comparison pages in headless Chrome, desktop and narrow, and report.

Read-only against the HTML. Writes PNGs into a _qa folder beside the tool. The PNGs are then read
back one at a time; a take count is not a read count.
"""
import json
import subprocess
import sys
from pathlib import Path

CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
DASH = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales")
QA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\aim_db_dlr_deep_dive\_qa")


def shot(html: Path, out: Path, w: int, h: int, extra_wait: int = 6000):
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
        "--hide-scrollbars", "--force-device-scale-factor=1",
        f"--window-size={w},{h}",
        f"--screenshot={out}",
        f"--virtual-time-budget={extra_wait}",
        html.as_uri(),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    ok = out.exists() and out.stat().st_size > 20000
    return ok, out.stat().st_size if out.exists() else 0, r.returncode, (r.stderr or "")[-300:]


def main():
    runs = sys.argv[1:] or ["PORTUGAL", "ALL"]
    log = {}
    for run in runs:
        html = DASH / f"ISZE_AIM_Comparison_{run}.html"
        entries = []
        for tag, w, h in (("desktop", 1500, 5600), ("narrow", 390, 6400)):
            out = QA / f"cmp_{run}_{tag}.png"
            ok, size, code, err = shot(html, out, w, h)
            entries.append({"tag": tag, "width": w, "height": h, "path": str(out),
                            "bytes": size, "ok": ok, "exit": code, "stderr": err})
            print(f"{run} {tag:<8} {w}x{h}  ok={ok}  {size/1024:.0f} KB  exit={code}")
        log[run] = entries
    (QA / "cmp_shots.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"\nwrote {QA / 'cmp_shots.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
