import sys

sys.path.insert(0, "_build_30")
import docbuild

els = ["<h2>Chapter schedule</h2>", "<p>Every chapter, its pages.</p>",
       "<table><thead><tr><th>Chapter</th></tr></thead></table>",
       "<h2>Executive summary</h2>", "<p>What the programme is.</p>", "<p>More.</p>"]
for plain, html in docbuild.keep_together(els):
    print(repr(plain), "->", html[:90])
print()
print("headings regex test:", bool(__import__("re").match(r"^<(h[234])>(.*?)</h\1>$", els[0])))
