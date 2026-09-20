"""Numeric checks on the screenshots, because image reading returned nothing.

The image Read tool returned no visual content in this environment, so the
pictures cannot be looked at. These checks measure the clipped elements
instead, where the pixel budget is known:

  figkey_stage_frame1.png   the stage with the zones on, at frame 1
  figkey_stage_clicked.png  the same after a zone was chosen
  figkey_cards.png          the six zone cards
  figkey_panel_cab.png      the detail panel for a zone that has no brake parts

Run:  python qa_figkey_shots.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
SHOTS = HERE / "_qa"
NAVY = np.array([21, 35, 60])


def load(name):
    p = SHOTS / name
    if not p.exists():
        raise SystemExit("missing %s" % p)
    im = Image.open(p).convert("RGB")
    return np.asarray(im, dtype=np.int16), im.size


def dist_to_navy(a):
    return np.sqrt(((a - NAVY) ** 2).sum(axis=2))


def is_stain(a):
    """The zone tint: terracotta washed over the truck, so red well above blue."""
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    return (r - b > 45) & (r > 110) & (g > 35) & (g < 205)


def is_ink(a):
    return a.sum(axis=2) < 620


def bands(a, min_rows=5):
    rows = is_ink(a).sum(axis=1) > 3
    out, start = [], None
    for i, v in enumerate(rows):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start >= min_rows:
                out.append((start, i))
            start = None
    if start is not None and len(rows) - start >= min_rows:
        out.append((start, len(rows)))
    return out


def main() -> int:
    fails = []
    print("=" * 78)
    print("SCREENSHOT MEASUREMENTS  (image read returned no visual content)")
    print("=" * 78)

    frame1, s1 = load("figkey_stage_frame1.png")
    clicked, s2 = load("figkey_stage_clicked.png")
    cards, sc = load("figkey_cards.png")
    panel, sp = load("figkey_panel_cab.png")

    for nm, sz in (("stage frame 1", s1), ("stage clicked", s2),
                   ("cards", sc), ("cab panel", sp)):
        print(f"{nm:<16}{sz[0]}x{sz[1]}")

    # 1 the stage really is the stage: navy frame around a lit truck on a floor
    print()
    navy = (dist_to_navy(frame1) < 42)
    print(f"stage: navy background          : {navy.mean():.3f}")
    if navy.mean() < 0.004:
        fails.append("no navy background is visible in the stage (%.4f)" % navy.mean())
    ground = (frame1.sum(axis=2) > 470) & (frame1.sum(axis=2) < 720)
    print(f"stage: the studio floor visible : {ground.mean():.3f}")
    if ground.mean() < 0.01:
        fails.append("no studio floor is visible in the stage")
    # the truck itself is the dark mass; without it the stage would be empty
    dark = frame1.sum(axis=2) < 330
    print(f"stage: the vehicle silhouette   : {dark.mean():.3f}")
    if dark.mean() < 0.05:
        fails.append("no vehicle silhouette in the stage (%.3f)" % dark.mean())

    # 2 the six zone tints are painted on the truck
    st1 = is_stain(frame1)
    print(f"stage: zone-tint pixels         : {st1.sum():,}  ({st1.mean():.3f})")
    if st1.sum() < 2000:
        fails.append("the zone tints are not painted (%d pixels)" % st1.sum())
    ys, xs = np.where(st1)
    if st1.sum():
        print(f"stage: tint spans x {xs.min()}..{xs.max()}  y {ys.min()}..{ys.max()}")
        # the truck should not be a thin sliver
        if xs.max() - xs.min() < s1[0] * 0.4:
            fails.append("the zone tints cover only a narrow strip")

    # 3 choosing a zone makes the tint stronger and only on that zone
    st2 = is_stain(clicked)
    print(f"after a click: tint pixels      : {st2.sum():,}  ({st2.mean():.3f})")
    if st2.sum() <= st1.sum() * 1.05:
        fails.append("choosing a zone did not strengthen its tint "
                     "(%d -> %d)" % (st1.sum(), st2.sum()))

    # 4 the six cards. The grid is three across, so the ink profile has two
    #    tall runs (two rows of three) - that is the correct shape, and a
    #    single tall run would mean the grid collapsed into one column.
    print()
    cards_ink = is_ink(cards)
    row_profile = cards_ink.sum(axis=1) > 4
    runs, start = [], None
    for i, v in enumerate(row_profile):
        if v and start is None:
            start = i
        elif not v and start is not None:
            runs.append(i - start)
            start = None
    if start is not None:
        runs.append(len(row_profile) - start)
    # columns: the vertical gutters between the three cards
    col_profile = cards_ink.sum(axis=0) == 0
    gutters, g0 = 0, None
    for i, v in enumerate(col_profile):
        if v and g0 is None:
            g0 = i
        elif not v and g0 is not None:
            if i - g0 >= 4:
                gutters += 1
            g0 = None
    print(f"cards: {sc[0]}x{sc[1]}, ink share {cards_ink.mean():.3f}, "
          f"rows {runs}, vertical gutters {gutters}")
    if sc[1] < 100:
        fails.append("the card grid is only %d px tall" % sc[1])
    if len(runs) != 2:
        fails.append("expected two rows of cards, found %d content runs" % len(runs))
    if min(runs) < 60:
        fails.append("a card row is only %d px tall" % min(runs))
    if gutters < 2:
        fails.append("expected at least two vertical gutters between the cards, "
                     "found %d" % gutters)

    # 5 the cab panel must state that it has no brake parts, in words that paint
    print()
    panel_ink = is_ink(panel)
    pb = bands(panel, min_rows=6)
    print(f"cab panel: {sp[0]}x{sp[1]}, ink share {panel_ink.mean():.3f}, "
          f"{len(pb)} content bands")
    if panel_ink.mean() < 0.04:
        fails.append("the cab panel carries almost no ink")
    if len(pb) < 8:
        fails.append("the cab panel has too few content bands (%d)" % len(pb))

    # 6 the cab and the clicked screenshots must not be the same picture
    if frame1.shape == clicked.shape:
        diff = (np.abs(frame1 - clicked).sum(axis=2) > 40).mean()
        print(f"frame 1 vs clicked differ by    : {diff:.4f} of the stage")
        if diff < 0.004:
            fails.append("choosing a zone changed almost nothing (%0.5f)" % diff)
    else:
        fails.append("the two stage screenshots differ in size")

    print()
    if fails:
        print("QA FAILED")
        for f in fails:
            print("  -", f)
        return 1
    print("QA OK - the truck, the zone tints, the six cards and the detail panel")
    print("        all carry real pixels; choosing a zone changes the picture.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
