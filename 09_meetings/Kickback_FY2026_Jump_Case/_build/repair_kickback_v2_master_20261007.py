"""Repair the duplicate slide master in the kickback v2 deck so PowerPoint can open it.

DIAGNOSIS (2026-10-07)
  ISZE_Kickback_Management_Revised_v2_2026-10-07.pptx as delivered would not open in PowerPoint
  at all ('The file or directory is corrupted and unreadable', HRESULT 0x80070570). python-pptx
  read it happily, every OOXML reference resolved, and the zip was intact, so this was not a
  broken package - PowerPoint specifically rejected it while the 17-slide
  'ISZE_Kickback_Management_Revised_2026-10-07.pptx' opened fine.

  Bisection (drop-one-part-group-at-a-time, testing with PowerPoint COM) showed the cause is the
  duplicate second slide master and its layout:
      ppt/slideMasters/vis_slideMaster1.xml   (byte-identical to slideMaster1.xml)
      ppt/slideLayouts/vis_slideLayout1.xml   (byte-identical to slideLayout1.xml)
  Both masters registered their layout under the SAME sldLayoutId '2147483649' (and the same
  r:id 'rId1'), so the presentation had one layout id claimed twice. Slides 6, 7, 8 and 10
  referenced vis_slideLayout1; every other slide referenced slideLayout1.
  Test evidence: dropping both vis_* master/layout parts fixes the open (OPEN_OK, 20 slides);
  dropping only the theme or only the notesSlides does not; renaming the id alone does not.

REPAIR (the minimum that works, and presentation-neutral)
  1. remove ppt/slideMasters/vis_slideMaster1.xml and its rels part
  2. remove ppt/slideLayouts/vis_slideLayout1.xml and its rels part
  3. repoint the slideLayout reference of slides 6, 7, 8 and 10 from vis_slideLayout1.xml to
     slideLayout1.xml - safe because the two layout parts are byte-identical
  4. drop the second master's entry from sldMasterIdLst and its presentation relationship
  5. drop the two parts from [Content_Types].xml
  Nothing else is touched: slide content, charts, themes, notesSlides and fonts are unchanged.
  ppt/theme/vis_theme1.xml is left in place (now unreferenced, which OOXML allows) so the change
  stays as small as possible.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from lxml import etree

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MASTER = "ppt/slideMasters/vis_slideMaster1.xml"
MASTER_RELS = "ppt/slideMasters/_rels/vis_slideMaster1.xml.rels"
LAYOUT = "ppt/slideLayouts/vis_slideLayout1.xml"
LAYOUT_RELS = "ppt/slideLayouts/_rels/vis_slideLayout1.xml.rels"
DROP = {MASTER, MASTER_RELS, LAYOUT, LAYOUT_RELS}

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _norm(base, tgt):
    out = []
    for seg in (base + tgt).split("/"):
        if seg == "..":
            if out:
                out.pop()
        elif seg not in ("", "."):
            out.append(seg)
    return "/".join(out)


def repair(src: Path, dst: Path) -> dict:
    z = zipfile.ZipFile(src)
    names = z.namelist()
    for needed in (MASTER, LAYOUT):
        if needed not in names:
            print("nothing to repair: %s absent (already repaired)" % needed)
            Path(dst).write_bytes(Path(src).read_bytes())
            return {"already_repaired": True, "retargeted": []}

    swaps = {}
    retargeted = []
    # 3. repoint slideLayout references
    for n in names:
        if not n.endswith(".rels"):
            continue
        base = n.rsplit("_rels/", 1)[0]
        root = etree.fromstring(z.read(n))
        hit = False
        for r in list(root):
            tgt = r.get("Target") or ""
            if tgt.startswith("http"):
                continue
            t = _norm(base, tgt)
            if t == LAYOUT:
                r.set("Target", tgt.replace("vis_slideLayout1.xml", "slideLayout1.xml"))
                hit = True
            elif t in DROP:
                root.remove(r)
        if hit:
            retargeted.append(n)
        swaps[n] = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    # 4. drop the second master from sldMasterIdLst
    pres = etree.fromstring(z.read("ppt/presentation.xml"))
    prr = etree.fromstring(z.read("ppt/_rels/presentation.xml.rels"))
    relmap = {r.get("Id"): r for r in prr}
    for lst in pres.iter("{%s}sldMasterIdLst" % P_NS):
        for e in list(lst):
            rid = e.get("{%s}id" % R_NS)
            r = relmap.get(rid)
            if r is not None and _norm("ppt/", r.get("Target")) == MASTER:
                lst.remove(e)
                prr.remove(r)
    swaps["ppt/presentation.xml"] = etree.tostring(pres, xml_declaration=True, encoding="UTF-8",
                                                  standalone=True)
    swaps["ppt/_rels/presentation.xml.rels"] = etree.tostring(prr, xml_declaration=True,
                                                              encoding="UTF-8", standalone=True)

    # 5. content types
    ct = etree.fromstring(z.read("[Content_Types].xml"))
    for e in list(ct):
        if e.tag.endswith("Override") and e.get("PartName").lstrip("/") in DROP:
            ct.remove(e)
    swaps["[Content_Types].xml"] = etree.tostring(ct, xml_declaration=True, encoding="UTF-8",
                                                  standalone=True)

    remaining = [n for n in names if n not in DROP]
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as w:
        for n in remaining:
            w.writestr(n, swaps.get(n, z.read(n)))
    return {"already_repaired": False, "retargeted": retargeted,
            "dropped": sorted(DROP), "parts": len(remaining)}


if __name__ == "__main__":
    info = repair(Path(sys.argv[1]), Path(sys.argv[2]))
    print(info)
