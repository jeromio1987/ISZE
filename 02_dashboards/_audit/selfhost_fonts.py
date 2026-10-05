"""Self-host the two web fonts so the dashboards stop pulling from Google Fonts.

What it does:
  1. fetches the Google Fonts CSS for Fraunces + Inter with a browser UA (woff2)
  2. downloads every referenced woff2 into _ui/fonts/
  3. writes _ui/fonts.css with @font-face rules pointing at those local files
  4. rewrites _ui/editorial.css to import fonts.css instead of the CDN
  5. rewrites any dashboard that declares its own Google Fonts <link>

Backups are written next to each modified file with a .bak_20260916 suffix.
"""
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards")
UI = ROOT / "_ui"
FONTS = UI / "fonts"
STAMP = ".bak_20260916"

CSS_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700"
    "&family=Inter:wght@400;500;600&display=swap"
)
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)

FONTS.mkdir(parents=True, exist_ok=True)


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


print("1. fetching Google Fonts CSS")
css = fetch(CSS_URL).decode("utf-8")
faces = re.findall(r"@font-face\s*\{[^}]*\}", css)
print(f"   @font-face blocks returned: {len(faces)}")

print("2. downloading woff2 files")
url_re = re.compile(r"url\((https://[^)]+\.woff2)\)")
downloaded = {}
for u in sorted(set(url_re.findall(css))):
    name = u.split("/")[-1]
    dest = FONTS / name
    if not dest.exists():
        dest.write_bytes(fetch(u))
    downloaded[u] = name
    print(f"   {name}  {dest.stat().st_size:,} bytes")

print("3. writing _ui/fonts.css with local paths")
local_css = css
for u, name in downloaded.items():
    local_css = local_css.replace(u, f"fonts/{name}")
local_css = (
    "/* self-hosted copy of the Google Fonts CSS, generated 2026-09-16.\n"
    "   Original: " + CSS_URL + "\n"
    "   Why: the shared stylesheet pulled these from the network, which made\n"
    "   every dashboard that links it network-dependent. */\n\n"
    + local_css
)
(UI / "fonts.css").write_text(local_css, encoding="utf-8")
print(f"   fonts.css  {(UI / 'fonts.css').stat().st_size:,} bytes")

print("4. rewriting _ui/editorial.css")
ed = UI / "editorial.css"
src = ed.read_text("utf-8", errors="surrogateescape")
imp = re.compile(r"@import\s+url\(['\"]https://fonts\.googleapis\.com[^)]*\)\s*;?")
if imp.search(src):
    (UI / ("editorial.css" + STAMP)).write_text(src, encoding="utf-8", errors="surrogateescape")
    new = imp.sub("@import url('fonts.css'); /* self-hosted 2026-09-16 */", src)
    ed.write_text(new, encoding="utf-8", errors="surrogateescape")
    print("   replaced the Google Fonts @import with a local import")
else:
    print("   no Google Fonts @import found (already done?)")

print("5. rewriting dashboards with their own Google Fonts <link>")
link_re = re.compile(
    r"<link[^>]+href=['\"]https://fonts\.googleapis\.com[^'\"]*['\"][^>]*>", re.I
)
fixed = 0
for p in ROOT.rglob("*.html"):
    if re.search(r"(_archive|_build|node_modules|_qa|_audit)", str(p), re.I):
        continue
    t = p.read_text("utf-8", errors="surrogateescape")
    if not link_re.search(t):
        continue
    depth = len(p.relative_to(ROOT).parts) - 1
    prefix = "../" * depth
    repl = f'<link rel="stylesheet" href="{prefix}_ui/fonts.css" />'
    p.with_suffix(p.suffix + STAMP).write_text(t, encoding="utf-8", errors="surrogateescape")
    p.write_text(link_re.sub(repl, t), encoding="utf-8", errors="surrogateescape")
    print(f"   {p.relative_to(ROOT)}")
    fixed += 1

print()
print(f"woff2 downloaded      : {len(downloaded)}")
print(f"own-link files fixed  : {fixed}")
print()
print("verification:")
import subprocess
leftovers = []
for p in ROOT.rglob("*"):
    if p.suffix.lower() not in (".html", ".css") or not p.is_file():
        continue
    if re.search(r"(_archive|_build|node_modules|_audit)", str(p), re.I):
        continue
    try:
        if "fonts.googleapis.com" in p.read_text("utf-8", errors="ignore"):
            leftovers.append(p.relative_to(ROOT))
    except Exception:
        pass
print(f"  files still referencing fonts.googleapis.com (live set): {len(leftovers)}")
for l in leftovers:
    print(f"    {l}")
print(f"  fonts dir now holds: {len(list(FONTS.glob('*.woff2')))} woff2")
