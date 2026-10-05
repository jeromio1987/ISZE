# -*- coding: utf-8 -*-
r"""Bring the showcase back in step with the paper.

The showcase carries its own copy of the paper as embedded JSON, plus page references from the
tools and the map. When the paper changed from 80 pages to 25, the showcase kept pointing at the
withdrawn edition: it said "80 chapters and pages", offered a "Read the 80-page paper" button and
linked every tool to a page number that no longer existed.

This rebuilds the embedded mirror from the current markdown, points the figures at the chart files
the paper uses, makes every counter dynamic, and writes the old file aside rather than over it.

Run from the Isuzu Universe folder:  python _build_30\patch_showcase.py
"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "ISUZU_UNIVERSE_3_0_SHOWCASE.html")
MD = os.path.join(ROOT, "01_Strategy", "ISUZU_UNIVERSE_3_0_2026-09-23.md")
FIGDIR = os.path.join(HERE, "figures")
OUT = os.path.join(ROOT, "ISUZU_UNIVERSE_3_0_SHOWCASE_2026-09-23.html")
OLD = os.path.join(ROOT, "ISUZU_UNIVERSE_3_0_SHOWCASE_SUPERSEDED_2026-09-22.html")

sys.stdout.reconfigure(encoding="utf-8")


def rel_figure(n):
    for f in sorted(os.listdir(FIGDIR)):
        if f.startswith("f%02d_" % n):
            return "_build_30/figures/" + f
    return ""


def parse_md():
    """Turn the current paper into the showcase's page entries."""
    txt = open(MD, encoding="utf-8").read()
    txt = re.sub(r"^# .*?\n", "", txt, count=1)
    chunks = re.split(r"\n(?=## )", txt)
    pages = []

    for idx, ch in enumerate(chunks):
        lines = [ln for ln in ch.split("\n")]
        head = ""
        for ln in lines:
            if ln.startswith("## "):
                head = ln[3:].strip()
                break
        if not head:
            continue
        body = lines[lines.index("## " + head) + 1:]

        paras, table, stand, img, block = [], None, "", "", []
        i = 0
        while i < len(body):
            ln = body[i]
            s = ln.strip()
            if not s:
                i += 1
                continue
            m = re.match(r"^\[\[FIG(\d+)\]\]$", s)
            if m:
                img = rel_figure(int(m.group(1)))
                i += 1
                continue
            if s == "[[PAGEBREAK]]":
                i += 1
                continue
            if re.match(r"^---+\s*$", s):
                i += 1
                continue
            if s.startswith(">"):
                buf = []
                while i < len(body) and body[i].strip().startswith(">"):
                    buf.append(body[i].strip().lstrip(">").strip())
                    i += 1
                block.append(" ".join(b for b in buf if b))
                continue
            if s.startswith("|"):
                if table is None:
                    rows = []
                    while i < len(body) and body[i].strip().startswith("|"):
                        rows.append([c.strip() for c in body[i].strip().strip("|").split("|")])
                        i += 1
                    rows = [r for r in rows
                            if not all(re.fullmatch(r":?-{2,}:?", c or "-") for c in r)]
                    if rows:
                        table = {"headers": rows[0], "rows": rows[1:]}
                    continue
                while i < len(body) and body[i].strip().startswith("|"):
                    i += 1
                continue
            if re.match(r"^(#{3,4})\s+", s):
                i += 1
                continue
            if re.match(r"^\s*[-*]\s+", ln) or re.match(r"^\s*\d+\.\s+", ln):
                while i < len(body) and (re.match(r"^\s*[-*]\s+", body[i])
                                         or re.match(r"^\s*\d+\.\s+", body[i])):
                    i += 1
                continue
            buf = [s]
            i += 1
            while (i < len(body) and body[i].strip()
                   and not body[i].strip().startswith(("|", ">", "[[", "#", "---"))
                   and not re.match(r"^\s*[-*]\s+", body[i])
                   and not re.match(r"^\s*\d+\.\s+", body[i])):
                buf.append(body[i].strip())
                i += 1
            paras.append(" ".join(buf))

        def clean(t):
            t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
            t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?<!\*)", r"\1", t)
            t = re.sub(r"`([^`]+)`", r"\1", t)
            return t

        paras = [clean(p) for p in paras]
        block = [clean(b) for b in block]
        if block:
            stand = block[0]
        elif paras:
            first = paras[0]
            cut = re.split(r"(?<=[.:])\s", first)
            stand = cut[0] if cut else first
        pages.append({
            "n": len(pages) + 1,
            "chapter": "ISUZU / UNIVERSE 3.0",
            "title": clean(head),
            "stand": stand[:220],
            "paras": [p if len(p) <= 900 else p[:897] + "..." for p in paras[:9]],
            "refs": "ISUZU / UNIVERSE 3.0, 23 September 2026",
            "img": img,
            "table": table,
            "callout": block[1] if len(block) > 1 else "",
            "kind": "current edition",
        })

    # the cover chart sits before the first section, so attach it to section 3
    cover_fig = rel_figure(1)
    if cover_fig:
        for p in pages:
            if p["title"].startswith("3.") and not p["img"]:
                p["img"] = cover_fig
                break
    return pages


# Which section of the new paper answers each tool's question.
TOOL_PAGE = {
    "atlas": "5. AIM Commercial Atlas",
    "ids": "6. IDS Development Studio",
    "range": "7. Range, pricing and market tools",
    "pricing": "7. Range, pricing and market tools",
    "market": "7. Range, pricing and market tools",
    "tenders": "2. The portfolio",
    "deal": "4. The economics, and what the investment must earn",
}


def main():
    assert os.path.exists(SRC), SRC
    if not os.path.exists(OLD):
        shutil.copy2(SRC, OLD)
        print(f"old showcase written aside -> {os.path.basename(OLD)}")

    h = open(SRC, encoding="utf-8").read()
    m = re.search(r'(<script id="universe-data" type="application/json">)(.*?)(</script>)',
                  h, re.S)
    d = json.loads(m.group(2))
    before = (len(d["paper"]), h.count("/ 80"), h.count('n===80'))

    pages = parse_md()
    d["paper"] = pages
    d["sources"]["V"] = {
        "title": "ISUZU / UNIVERSE 3.0 - commercial vision and participation",
        "date": "23 September 2026",
        "use": (f"The current {len(pages)}-page proposition, with the scope boundary, the five-tool "
                "portfolio, the campaign economics and the participation assessment. Chapters are "
                "included in this showcase for reading."),
        "note": ("Supersedes the Commercial Vision 3.0 and the Commercial Tools Edition of "
                 "22 September 2026. New designs and hypothetical arithmetic are labelled; "
                 "operating acceptance is separate."),
    }
    d["version"] = "3.0"
    d["date"] = "23 September 2026"

    by_title = {p["title"]: p["n"] for p in pages}

    # every tool reference now points at a real section of the current paper
    for key, title in TOOL_PAGE.items():
        if key in d.get("products", {}) and title in by_title:
            d["products"][key]["refs"] = [f"V:{by_title[title]}"]

    # any remaining V: reference pointing past the end of the paper is capped
    def fix_refs(obj):
        if isinstance(obj, dict):
            if "refs" in obj and isinstance(obj["refs"], list):
                out = []
                for r in obj["refs"]:
                    mm = re.match(r"^V:(\d+)$", str(r))
                    if mm:
                        num = min(int(mm.group(1)), len(pages))
                        out.append(f"V:{num}")
                    elif str(r).startswith("V:"):
                        nums = [int(x) for x in re.findall(r"\d+", str(r))]
                        if nums:
                            out.append("V:" + ",".join(
                                str(min(x, len(pages))) for x in nums))
                    else:
                        out.append(r)
                obj["refs"] = out
            for v in obj.values():
                fix_refs(v)
        elif isinstance(obj, list):
            for v in obj:
                fix_refs(v)

    fix_refs(d.get("chapters", []))
    fix_refs(d.get("products", {}))

    h = h[:m.start(2)] + json.dumps(d, separators=(",", ":"), ensure_ascii=False) + h[m.end(2):]

    # make the counters read from the data instead of a number typed in 2026-09-22
    h = h.replace(
        "${p.fig&&D.figures[p.fig]?`<div class=\"paper-figure\">${D.figures[p.fig]}</div>`:''}",
        "${p.img?`<div class=\"paper-figure\"><img src=\"${p.img}\" "
        "alt=\"${esc(p.title)}\" loading=\"lazy\"></div>`:p.fig&&D.figures[p.fig]?"
        "`<div class=\"paper-figure\">${D.figures[p.fig]}</div>`:''}")
    h = h.replace("'80 chapters and pages, with source-based charts, proposed dynamics and the "
                  "developed application examples.'",
                  "`${D.paper.length} chapters and pages, with source-based charts and the "
                  "developed application examples.`")
    h = re.sub(r"\$\{n===(\d+)\?", "${n===D.paper.length?", h)
    h = h.replace("<span class=\"label\">PAGE ${String(n).padStart(2,'0')} / 80</span>",
                  "<span class=\"label\">PAGE ${String(n).padStart(2,'0')} / ${D.paper.length}</span>")
    h = h.replace("filter(n=>n>=1&&n<=80)", "filter(n=>n>=1&&n<=D.paper.length)")
    h = re.sub(r"\[\[1,'Vision'\],\[11,'AIM / Atlas'\],\[22,'IDS'\],\[31,'PRISM'\],\[35,'Tenders'\],"
               r"\[42,'Deal of the Day'\],\[55,'Participation'\],\[62,'Economics'\],\[65,'Roadmap'\],"
               r"\[71,'Reference'\]\]",
               "[[1,'How to read this'],[2,'Executive summary'],[3,'The scope boundary'],"
               "[4,'The portfolio'],[6,'The money'],[7,'The Atlas'],[8,'IDS'],"
               "[10,'Participation'],[11,'What to build first'],[16,'Reference']]", h)
    h = h.replace("btn('Read the 80-page paper','data-paper=\"index\"',true)",
                  "btn(`Read the ${D.paper.length}-page paper`,'data-paper=\"index\"',true)")

    # the in-page demo buttons used to test page ranges of the withdrawn 80-page edition.
    # point them at the sections of the current paper that actually carry those designs.
    h = h.replace("[22,23,24,25,26,27,28,29,30,78].includes(n)", "[8].includes(n)")
    h = h.replace("n>=35&&n<=41||n===76", "n===4||n===10")
    h = h.replace("n>=42&&n<=54||n===77", "n>=5&&n<=7")
    h = h.replace("btn('Read the 80-page paper','data-paper=\"index\"')",
                  "btn(`Read the ${D.paper.length}-page paper`,'data-paper=\"index\"')")
    h = h.replace('"Universe commercial vision 3.0"', '"ISUZU / UNIVERSE 3.0"')

    if "paper-figure img" not in h:
        h = h.replace(".paper-figure{",
                      ".paper-figure img{width:100%;height:auto;border:1px solid #48525B;"
                      "border-radius:4px}.paper-figure{", 1)

    open(OUT, "w", encoding="utf-8").write(h)

    # verify in the written file, not in the loop
    w = open(OUT, encoding="utf-8").read()
    i = w.find("paper-jumps\">")
    jump = w[i:i + 400]
    nums = [int(x) for x in re.findall(r"\[(\d+),'", jump)]
    checks = {
        "hardcoded / 80": w.count("/ 80"),
        "hardcoded n===80": w.count("n===80"),
        "old 80-page label": w.count("Read the 80-page"),
        "dynamic count used": w.count("D.paper.length"),
        "jump targets within range": int(bool(nums) and max(nums) <= len(pages)),
        "figures in the mirror": sum(1 for p in pages if p["img"]),
    }
    print(f"paper mirror: {before[0]} pages -> {len(pages)} pages")
    print(f"  jump targets: {nums}")
    for k, v in checks.items():
        print(f"  {k}: {v}")
    print(f"tool refs: { {k: d['products'][k]['refs'] for k in TOOL_PAGE if k in d.get('products', {})} }")
    print(f"written -> {OUT}  ({os.path.getsize(OUT):,} bytes)")
    return OUT


if __name__ == "__main__":
    main()
