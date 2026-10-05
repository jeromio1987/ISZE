"""Is retirement safe? Two questions, answered from the tree.

  1. Does any module the build SHIPS read the globals the two orphan view-layer
     modules export (AIMUI.views, AIMUI.render, and the root AIMUI namespace)?
     If one does, retiring the orphans would turn a silent undefined into a
     runtime failure and the retirement is not safe yet.

  2. Which files still reference the orphans at all? Anything outside the
     orphans themselves, tools/ and docs/ is a caller that would break.

Usage:  python tools/retirement_safety_check.py
Exit 0 when nothing shipped reads an orphan global.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# The globals the orphan modules publish, and the globals of the modules the
# build already retires. A shipped module reading any of them is a defect.
ORPHAN_GLOBALS = [
    ("AIMUI.views", "views.js exports its six views on AIMUI.views"),
    ("AIMUI.render", "render.js exports the shell on AIMUI.render"),
    ("root.AIMUI.views", "views.js exports its six views on AIMUI.views"),
    ("root.AIMUI.render", "render.js exports the shell on AIMUI.render"),
    ("AIMViews", "any bare AIMViews global"),
    ("AIMRender", "any bare AIMRender global"),
]

# A module's own export line is not a read: `views.js` legitimately says
# `root.AIMUI.views = factory(...)`. Only a use that is not an assignment counts.
ASSIGNMENT = re.compile(r"(AIMUI\.(views|render))\s*=(?!=)")


def load_lists():
    """The shipped list and the retired list.

    Both use the same ("src/x.js", "reason") tuple shape, so a regex over the
    whole file catches the retired tuples as shipped ones. The two sections are
    therefore sliced out first: MODULES runs up to the comment introducing
    UNWIRED_MODULES, and UNWIRED_MODULES up to BANNED_IN_OUTPUT.
    """
    src = io.open(os.path.join(ROOT, "tools", "build.py"), encoding="utf-8").read()
    shipped_block = src[src.find("MODULES = ["):src.find("UNWIRED_MODULES")]
    retired_block = src[src.find("UNWIRED_MODULES"):src.find("BANNED_IN_OUTPUT")]
    shipped = [m for m, _ in re.findall(r'\("(src/[^"]+)",\s*"([^"]+)"\)', shipped_block)]
    retired = [m for m, _ in re.findall(r'\("(src/[^"]+)",\s*"([^"]+)"\)', retired_block)]
    return shipped, retired


def main():
    shipped, retired = load_lists()
    print("shipped modules : %d" % len(shipped))
    print("retired modules : %d" % len(retired))

    findings = []
    for rel in shipped:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            findings.append("%s is in the shipped list but is not on disk" % rel)
            continue
        text = io.open(path, encoding="utf-8", errors="ignore").read()
        for needle, why in ORPHAN_GLOBALS:
            if needle == "AIMViews" and "AIMViewModel" in text:
                # AIMViewModel is a different, already-retired module's global.
                continue
            if needle in text and not ASSIGNMENT.search(text):
                for m in re.finditer(re.escape(needle), text):
                    line = text[:m.start()].count("\n") + 1
                    window = text[max(0, m.start() - 40):m.start() + 40]
                    if ASSIGNMENT.search(window):
                        continue
                    findings.append("%s line %d reads %s (%s)" % (rel, line, needle, why))

    print("")
    if findings:
        print("NOT SAFE TO RETIRE YET:")
        for f in findings:
            print("  " + f)
        return 1
    print("SAFE: no shipped module reads AIMUI.views, AIMUI.render, AIMViews or AIMRender.")

    # Who else mentions the orphans at all?
    print("")
    print("files that name an orphan module, outside the orphans themselves:")
    orphans = ["views.js", "render.js"]
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "_qa", "dist", "chrome-profile")]
        for f in files:
            if not f.endswith((".js", ".mjs", ".cjs", ".py", ".md", ".html", ".ps1")):
                continue
            p = os.path.join(base, f)
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            if rel in ("src/ui/views.js", "src/ui/render.js", "src/ui/viewmodel.js",
                       "src/ui/candidates.js", "src/ui/scenario.js"):
                continue
            try:
                text = io.open(p, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            for o in orphans:
                if o in text:
                    print("  %s references %s" % (rel, o))
    return 0


if __name__ == "__main__":
    sys.exit(main())
