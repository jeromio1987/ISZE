# -*- coding: utf-8 -*-
"""Patch UTI_presentation_V3.pptx — audit fixes 2026-07-06."""
from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path

from pptx import Presentation

PPTX = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\UTI_Presentation\UTI_presentation_V3.pptx")
BACKUP = PPTX.with_name("UTI_presentation_V3_pre_patch.pptx")

# Verified figures (UTI_PMS_Evolution.html + uti_iml_fy_engine family rollup)
COVER_PCT = "31% (FY2024) -> 41% (FY2025) -> 38% (FY2026)"

SLIDE14_TAKEAWAYS = (
    "—  Total PMS revenue rose to EUR 426K in FY2025 (+24% vs FY2024), then eased back to EUR 365K in FY2026 "
    "(-14% vs FY2025, still +6% vs FY2024).\n"
    f"—  Cover against modeled demand (8 active categories, 100% of UTI's PMS revenue) sits at {COVER_PCT} "
    "— most of the addressable basket is still going elsewhere.\n"
    "—  The FY2026 pullback is concentrated in oil filter and clutch — not a basket-wide slowdown. "
    "Fuel and air filter kept growing through the same period (see following slides)."
)

SLIDE16_TAKEAWAYS = (
    "—  Both wear categories run well below filters — the clearest remaining whitespace in the UTI PMS basket.\n"
    "—  Brake pad is steady in the high-20s to low-30s% across all three years (30% -> 33% -> 27%), no clear direction.\n"
    "—  Clutch family capture fell from 39% to 20% (FY2025->FY2026); kit units dropped 49% (869 -> 442) and "
    "family revenue halved (EUR 110K -> 55K) — the single biggest swing in the basket. Worth raising with UTI.\n"
    "—  Clutch is scored as complete jobs (kit PN bundles disc+plate+bearing), not per-component slices — "
    "kit-only capture % above 100% is a weighting artifact. Interval and clutch-equipped parc share are "
    "IML assumptions, not UTI-measured."
)

SLIDE18_TAKEAWAYS = (
    "—  Air filter has overtaken clutch kit as the single largest PMS revenue line — EUR 141K in FY2026 vs "
    "clutch family's EUR 55K, a reversal from FY2024/25 when clutch led.\n"
    "—  Clutch family revenue fell EUR 110K -> 55K (-50%) alongside capture dropping from 39% to 20% — "
    "the biggest single EUR swing in the whole basket.\n"
    "—  Oil filter revenue fell EUR 18K (59K -> 41K) alongside its cover drop — consistent with a real "
    "volume pullback, not just a modeling artifact.\n"
    "—  Fuel filter and brake pad are comparatively stable contributors (EUR 80-85K and EUR 42-50K respectively "
    "across the three years)."
)

SLIDE19_TITLE = "Clutch family gap stays the largest wear-category opportunity"
SLIDE19_TAKEAWAYS = (
    "—  Clutch family carries the largest wear-category gap every year (EUR 88K -> 87K -> 90K) even as "
    "revenue halved — the model still sees substantial uncaptured demand.\n"
    "—  Brake pad's gap has also widened in FY2026 (EUR 99K -> 116K) as volume eased off.\n"
    "—  Air filter's gap is shrinking fast (EUR 157K -> 102K) — proof the growth there is closing real "
    "whitespace, not just growing off a low base.\n"
    "—  These are ceiling figures (cost of reaching 100% modeled demand, not a forecast) — useful for "
    "prioritising where to focus, not as a sales target."
)

SLIDE20_FOOTNOTE = (
    "* Clutch = disc, plate, kit, booster & bearings scored as one family (20.3% FY2026). UTI buys the kit PN "
    "for nearly every job — kit-only reads above 100% are a weighting artifact, not real overshoot. "
    "Source: UTI_PMS_Score_by_PN.xlsx · IML v7 intervals."
)


def delete_slide(prs: Presentation, index: int) -> None:
    sld_id_lst = prs.slides._sldIdLst
    r_id = sld_id_lst[index].rId
    prs.part.drop_rel(r_id)
    del sld_id_lst[index]


def set_shape_text(shape, text: str) -> bool:
    if not hasattr(shape, "text_frame"):
        return False
    tf = shape.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    p.text = text
    return True


def replace_in_slide(slide, replacements: list[tuple[str, str]]) -> int:
  n = 0
  for shape in slide.shapes:
    if not hasattr(shape, "text") or not shape.text.strip():
      continue
    original = shape.text
    updated = original
    for old, new in replacements:
      if old in updated:
        updated = updated.replace(old, new)
    if updated != original:
      set_shape_text(shape, updated)
      n += 1
  return n


def find_takeaways_shape(slide):
  for shape in slide.shapes:
    if hasattr(shape, "text") and shape.text.strip().startswith("—"):
      return shape
  return None


def is_page_number_shape(shape) -> bool:
  if not hasattr(shape, "text"):
    return False
  t = shape.text.strip()
  return bool(re.fullmatch(r"\d{1,2}", t))


def main() -> None:
  if not BACKUP.exists():
    BACKUP.write_bytes(PPTX.read_bytes())
    print(f"Backup: {BACKUP}")

  prs = Presentation(str(PPTX))

  # 1) Remove duplicate GPS slide (was slide 9 -> index 8)
  delete_slide(prs, 8)
  print("Deleted duplicate GPS slide (old slide 9)")

  slides = list(prs.slides)

  # 2) Slide 14 -> index 12 after delete: PMS revenue takeaways
  s14 = slides[12]
  tk = find_takeaways_shape(s14)
  if tk:
    set_shape_text(tk, SLIDE14_TAKEAWAYS)
    print("Updated slide 14 PMS cover % and takeaways")

  # 3) Slide 16 -> index 14: brake & clutch
  s16 = slides[14]
  tk = find_takeaways_shape(s16)
  if tk:
    set_shape_text(tk, SLIDE16_TAKEAWAYS)
    print("Updated slide 16 clutch family takeaways")

  # 4) Slide 18 -> index 16: revenue by category
  s18 = slides[16]
  tk = find_takeaways_shape(s18)
  if tk:
    set_shape_text(tk, SLIDE18_TAKEAWAYS)
    print("Updated slide 18 revenue takeaways")

  # 5) Slide 19 -> index 17: opportunity
  s19 = slides[17]
  for shape in s19.shapes:
    if hasattr(shape, "text") and shape.text.strip() == "Clutch kit's gap is growing, not shrinking":
      set_shape_text(shape, SLIDE19_TITLE)
  tk = find_takeaways_shape(s19)
  if tk:
    set_shape_text(tk, SLIDE19_TAKEAWAYS)
    print("Updated slide 19 clutch family gap takeaways")

  # 6) Slide 20 -> index 18: footnote
  s20 = slides[18]
  for shape in s20.shapes:
    if hasattr(shape, "text") and shape.text.strip().startswith("* Clutch"):
      set_shape_text(shape, SLIDE20_FOOTNOTE)
      print("Updated slide 20 footnote")

  # 7) Renumber page footers: slides 2..19 get 2..19
  for i, slide in enumerate(slides[1:19], start=2):
    for shape in slide.shapes:
      if is_page_number_shape(shape):
        set_shape_text(shape, str(i))
  print("Renumbered page footers 2-19")

  # 8) Remove stray "." on fill-rate slide (index 5)
  s6 = slides[5]
  for shape in s6.shapes:
    if hasattr(shape, "text") and shape.text.strip() == ".":
      set_shape_text(shape, "")
      print("Cleared stray placeholder on fill-rate slide")

  try:
    prs.save(str(PPTX))
    print(f"Saved: {PPTX}")
  except PermissionError:
    alt = PPTX.with_name("UTI_presentation_V3.1.pptx")
    prs.save(str(alt))
    print(f"File locked — saved: {alt}")


if __name__ == "__main__":
  main()
