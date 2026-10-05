"""Point the Leaflet loads at the local _ui copy instead of unpkg.

42 live dashboards load Leaflet from unpkg (a stylesheet on one line, a runtime
document.write for the script on another). The local copy exists in _ui/, but the
relative depth differs between the top-level files and the duplicated tree under
IDS_all_dashboards_2026-08-19/, which is why the nested copies were broken.

Backups get a .bak_20260916 suffix before any file is rewritten.
"""
import pathlib
import re

ROOT = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards")
UI_REL_FROM_ROOT = "_ui"
STAMP = ".bak_20260916"

link_re = re.compile(
    r"(<link[^>]+href=['\"])https://unpkg\.com/leaflet@[\d.]+/dist/leaflet\.css(['\"])"
)
script_re = re.compile(
    r"(<script[^>]+src=['\"])https://unpkg\.com/leaflet@[\d.]+/dist/leaflet\.js(['\"])"
)
# the runtime fallback:  document.write('<script src="https://unpkg.com/...leaflet.js"><\/script>');
dw_re = re.compile(
    r"https://unpkg\.com/leaflet@[\d.]+/dist/leaflet\.js"
)

changed = []
skipped = []

for p in sorted(ROOT.rglob("*.html")):
    s = str(p)
    if re.search(r"(_archive|_build|node_modules|_qa|_audit)", s, re.I):
        continue
    t = p.read_text("utf-8", errors="surrogateescape")
    if "unpkg.com/leaflet" not in t:
        continue

    depth = len(p.relative_to(ROOT).parts) - 1
    up = "../" * depth if depth else ""
    css_rel = f"{up}{UI_REL_FROM_ROOT}/leaflet.css"
    js_rel = f"{up}{UI_REL_FROM_ROOT}/leaflet.js"

    n_css = len(link_re.findall(t))
    n_js = len(script_re.findall(t))
    n_dw = len(dw_re.findall(t))

    new = link_re.sub(lambda m: f"{m.group(1)}{css_rel}{m.group(2)}", t)
    new = script_re.sub(lambda m: f"{m.group(1)}{js_rel}{m.group(2)}", new)
    # the document.write fallback: point it at the local file as well
    new = new.replace("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js", js_rel)

    if new == t:
        skipped.append(p.relative_to(ROOT))
        continue

    p.with_suffix(p.suffix + STAMP).write_text(t, encoding="utf-8", errors="surrogateescape")
    p.write_text(new, encoding="utf-8", errors="surrogateescape")
    changed.append((p.relative_to(ROOT), depth, up or "(root)", n_css, n_js, n_dw))

print(f"files rewritten: {len(changed)}")
for rel, depth, up, a, b, c in changed[:12]:
    print(f"  {str(rel):<70} depth={depth} prefix={up!r} css={a} js={b} docwrite={c}")
if len(changed) > 12:
    print(f"  ... and {len(changed) - 12} more")
if skipped:
    print(f"\nskipped (already local?): {len(skipped)}")
    for s in skipped[:5]:
        print(f"  {s}")

print("\nverification")
remaining = []
for p in sorted(ROOT.rglob("*.html")):
    if re.search(r"(_archive|_build|node_modules|_qa|_audit)", str(p), re.I):
        continue
    try:
        if "unpkg.com" in p.read_text("utf-8", errors="ignore"):
            remaining.append(p.relative_to(ROOT))
    except Exception:
        pass
print(f"  live files still referencing unpkg.com: {len(remaining)}")
for r in remaining[:10]:
    print(f"    {r}")

# does the local target exist for each depth used?
print("\n  local target check:")
present = sorted({d for _, d, _, _, _, _ in changed})
for d in present:
    up = "../" * d if d else ""
    tgt = (p if (p := None) else None)
    candidate = (ROOT / up / UI_REL_FROM_ROOT / "leaflet.js")
    try:
        resolved = (ROOT / pathlib.Path(up + UI_REL_FROM_ROOT) / "leaflet.js").resolve()
        ok = resolved.exists()
    except Exception:
        ok = False
    print(f"    depth {d}: {'OK' if ok else 'MISSING'}  {up}{UI_REL_FROM_ROOT}/leaflet.js")
