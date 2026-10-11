"""Convert one Markdown document to a self-contained HTML and a PDF (no charts).

Usage (from the ISZE root):
  python 09_meetings/Excellence_Partner_Program_2026/_build/build_doc.py <file.md> "<Title>" "<subtitle>" [--no-pdf]
"""
import html
import re
import sys
from pathlib import Path

import markdown

md_path = Path(sys.argv[1]).resolve()
title, sub = sys.argv[2], sys.argv[3]
src = re.sub(r"^# .*\n", "", md_path.read_text(encoding="utf-8"), count=1)
body = markdown.markdown(src, extensions=["tables", "sane_lists", "fenced_code"])
toc = []


def addid(m):
    plain = re.sub(r"<[^>]+>", "", m.group(2))
    sid = re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")[:60]
    if m.group(1) == "2":
        toc.append((sid, plain))
    return f'<h{m.group(1)} id="{sid}">{m.group(2)}</h{m.group(1)}>'


body = re.sub(r"<h([23])>(.*?)</h\1>", addid, body)
body = body.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")
body = re.sub(r"<strong>\[([MIAPU])\]</strong>", lambda m: f'<span class="tag t{m.group(1)}">{m.group(1)}</span>', body)
body = re.sub(r"\*\*\[([MIAPU])\]\*\*", lambda m: f'<span class="tag t{m.group(1)}">{m.group(1)}</span>', body)
nav = "".join(f'<a href="#{s}">{html.escape(t)}</a>' for s, t in toc)
CSS = """:root{--ink:#1d2124;--mut:#5f676e;--line:#dfe2e5;--panel:#f4f5f6;--red:#D71920;--navy:#15233C}
*{box-sizing:border-box}body{margin:0;color:var(--ink);font:15.5px/1.6 Arial,Helvetica,sans-serif}
header{background:#24282C;color:#fff;padding:36px 28px}header .in{max-width:1180px;margin:0 auto}
.eyebrow{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#ff6b70;font-weight:700}
h1{font-size:34px;margin:8px 0}header p{margin:0;color:#c9ced3;max-width:800px}
.layout{max-width:1180px;margin:0 auto;display:grid;grid-template-columns:240px minmax(0,1fr);gap:36px;padding:24px 28px}.layout>*{min-width:0}
nav{position:sticky;top:12px;align-self:start;max-height:calc(100vh - 24px);overflow:auto;font-size:13px}
nav a{display:block;color:var(--ink);text-decoration:none;padding:4px 0 4px 10px;border-left:2px solid var(--line)}nav a:hover{color:var(--red);border-left-color:var(--red)}
main h2{font-size:23px;margin:42px 0 10px;padding-top:10px;border-top:2px solid var(--ink)}main h3{font-size:17px;color:var(--navy)}
main p,main li{max-width:860px}code{font-size:12.5px;background:var(--panel);padding:1px 5px;border-radius:4px}
pre{background:var(--panel);padding:12px;border-radius:8px;overflow-x:auto;font-size:12.5px}pre code{background:none;padding:0}
.tablewrap{overflow-x:auto;margin:14px 0 20px;border:1px solid var(--line);border-radius:8px}table{border-collapse:collapse;width:100%;font-size:13px}
th,td{padding:7px 9px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}th{background:var(--panel)}tr:last-child td{border-bottom:none}
.tag{display:inline-block;font-size:10.5px;font-weight:700;border-radius:4px;padding:0 5px;color:#fff;line-height:16px}.tM{background:#2e7d4f}.tI{background:#4f6d8f}.tA{background:#b26a00}.tP{background:#6b4fa0}.tU{background:#8a9096}
@media screen and (max-width:900px){.layout{grid-template-columns:1fr;padding:16px}nav{position:static;max-height:none}}
@media print{nav{display:none}.layout{grid-template-columns:1fr;padding:0}header{background:#fff;color:#000;padding:20px 0}header p{color:#333}main h2{break-after:avoid}.tablewrap,pre{break-inside:avoid}body{font-size:11.5px}}"""
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)}</title><style>{CSS}</style></head><body>
<header><div class="in"><div class="eyebrow">Internal draft v1 · 9 October 2026</div><h1>{html.escape(title)}</h1><p>{html.escape(sub)}</p></div></header>
<div class="layout"><nav>{nav}</nav><main>{body}</main></div></body></html>"""
out = md_path.with_suffix(".html")
out.write_text(page, encoding="utf-8")
print(out)
if "--no-pdf" not in sys.argv:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
        pg = b.new_page(); pg.goto(f"file://{out}"); pg.wait_for_timeout(300)
        pg.pdf(path=str(md_path.with_suffix(".pdf")), format="A4", print_background=True, margin={"top": "16mm", "bottom": "16mm", "left": "14mm", "right": "14mm"})
        b.close()
    print(md_path.with_suffix(".pdf"))
