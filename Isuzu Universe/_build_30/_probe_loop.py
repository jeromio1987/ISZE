import sys, os, fitz
sys.path.insert(0, r"_build_30")
import docbuild, layoutqa

md = r"01_Strategy\ISUZU_UNIVERSE_3_0_2026-09-23.md"
src = open(md, encoding="utf-8").read()
hs = docbuild.headings(src)
stub = [("x", "00-00", "y")]

def body_with(b):
    return docbuild.markdown_to_html(src, r"figures", {}, breaks=b)

def assemble(body, rows):
    return docbuild.assemble_for_probe(body, rows)

# replicate the loop but print
breaks = []
for it in range(6):
    html = docbuild.assemble_probe(src, hs, breaks, stub)
    p = os.path.join(r"_build_30", "_raw_probe_%d.pdf" % it)
    open(os.path.join(r"_build_30", "_probe.html"), "w", encoding="utf-8").write(html)
    docbuild.render_probe(os.path.join(r"_build_30", "_probe.html"), p)
    d = fitz.open(p)
    got = layoutqa.chapter_breaks(d)
    print(it, "asked", breaks)
    print(it, "got  ", got, "pages", d.page_count)
    d.close()
    if got == breaks:
        print("converged at", it)
        break
    breaks = got
