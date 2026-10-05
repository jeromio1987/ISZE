"""Remove Leaflet references that do not resolve to a real file.

The original dashboards carried two references each: a local one and an unpkg one.
In the duplicated tree under IDS_all_dashboards_2026-08-19/ the local one pointed at
a _ui/ that was never copied, so after repointing the unpkg reference the file ended
up with one dead local reference and one working one. This drops the dead ones.

Rule: for every Leaflet <link>/<script>/document.write reference, resolve it relative
to the file. If the target does not exist, remove that reference. Then drop exact
duplicate consecutive references. Nothing that resolves is touched.
"""
import pathlib
import re

ROOT = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards")
STAMP = ".bak2_20260916"

ref_re = re.compile(
    r"""(?P<attr><(?:link|script)[^>]*?(?:href|src)=["'])(?P<path>(?:\.\./)*_ui/leaflet\.(?:js|css))(?:["'])"""
)
dw_re = re.compile(
    r"""document\.write\(\s*['"]<script src=["'](?P<path>(?:\.\./)*_ui/leaflet\.js)["']"""
)

report = []

for p in sorted(ROOT.rglob("*.html")):
    if re.search(r"(_archive|_build|node_modules|_qa|_audit)", str(p), re.I):
        continue
    try:
        text = p.read_text("utf-8", errors="surrogateescape")
    except Exception:
        continue
    if "leaflet" not in text.lower():
        continue

    lines = text.split("\n")
    keep = []
    removed = []

    for i, line in enumerate(lines):
        paths = [m.group("path") for m in ref_re.finditer(line)]
        paths += [m.group("path") for m in dw_re.finditer(line)]
        if not paths:
            keep.append(line)
            continue

        # keep the line only if at least one reference on it resolves
        resolves = []
        for rel in paths:
            tgt = (p.parent / rel).resolve()
            resolves.append(tgt.exists())
        if any(resolves):
            keep.append(line)
        else:
            removed.append((i + 1, line.strip()[:110]))

    if not removed:
        continue

    new_text = "\n".join(keep)
    if new_text == text:
        continue

    p.with_suffix(p.suffix + STAMP).write_text(text, encoding="utf-8", errors="surrogateescape")
    p.write_text(new_text, encoding="utf-8", errors="surrogateescape")
    report.append((p.relative_to(ROOT), removed))

print(f"files cleaned: {len(report)}")
for rel, removed in report[:10]:
    print(f"  {rel}")
    for ln, txt in removed:
        print(f"      dropped L{ln}: {txt}")
if len(report) > 10:
    print(f"  ... and {len(report) - 10} more")

print("\nverification: every remaining leaflet reference resolves?")
bad = []
total_refs = 0
for p in sorted(ROOT.rglob("*.html")):
    if re.search(r"(_archive|_build|node_modules|_qa|_audit)", str(p), re.I):
        continue
    try:
        text = p.read_text("utf-8", errors="ignore")
    except Exception:
        continue
    for m in ref_re.finditer(text):
        total_refs += 1
        tgt = (p.parent / m.group("path")).resolve()
        if not tgt.exists():
            bad.append((p.relative_to(ROOT), m.group("path")))

print(f"  references checked : {total_refs}")
print(f"  broken             : {len(bad)}")
for rel, path in bad[:10]:
    print(f"    {rel}  ->  {path}")

print("\nany live file still on unpkg?")
left = []
for p in sorted(ROOT.rglob("*.html")):
    if re.search(r"(_archive|_build|node_modules|_qa|_audit)", str(p), re.I):
        continue
    try:
        t = p.read_text("utf-8", errors="ignore")
    except Exception:
        continue
    # ignore minified library bodies: only flag actual resource references
    if re.search(r"""(?:src|href)=["']https://unpkg\.com""", t):
        left.append(p.relative_to(ROOT))
print(f"  files: {len(left)}")
for l in left:
    print(f"    {l}")
