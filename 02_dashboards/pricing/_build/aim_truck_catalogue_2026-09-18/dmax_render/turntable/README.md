# D-Max 360 turntable

A drag-to-spin 360 view of the 2021 Isuzu D-Max, built for the AIM truck catalogue.

Open `ISZE_DMax_Turntable.html` directly, or double-click `OPEN_DMAX_TURNTABLE.cmd`.

---

## What it is

The vehicle turns on a turntable. The camera does not move.

The hero render in the folder above settled the camera at **azimuth 80°, elevation 18°**,
orthographic, 16 m standoff. That camera is kept exactly, and the truck is rotated about
its own vertical axis through even steps. Turning the vehicle rather than the camera is
what a real turntable shoot does: the room's lights stay where they are, so the highlights
sweep across the panels as the truck comes round. The alternative — orbiting the camera
around a fixed truck — would have moved the reflections into different places in every
frame and looked like a slideshow of a different object.

Because the camera is fixed and the rotation is rigid about a fixed vertical axis, the
truck cannot shift, grow or shrink between frames. That is proved rather than assumed; see
the checks below.

## Files

| File | What |
|---|---|
| `ISZE_DMax_Turntable.html` | the page. Self-contained: every frame is embedded as a base64 data URI |
| `OPEN_DMAX_TURNTABLE.cmd` | opens the page from Explorer (CRLF line endings) |
| `build_turntable.py` | the Blender render script |
| `compose_turntable.py` | composites the frames onto the studio ground |
| `generate_turntable_page.py` | builds the page, embedding the frames, the zone polygons and what we billed |
| `verify_turntable.py` | headless-Chrome verification over `file://` |
| `inspect_frames.py` | per-frame bounding box, ink and symmetry measurement |
| `compare_framing.py` | predicted vs measured silhouette, the camera-stability proof |
| `qa_frames_visual.py` | clipping, backdrop, shadow and loop checks on the composited frames |
| `test_drag_feel.py` | deterministic drag/momentum/wrap behaviour test |
| `_raw_tt/` | the raw RGBA renders + `turntable_render_report.json` |
| `frames/` | the composited JPEG frames + `turntable_frames.json` |
| `build_figkey_brake_panel.py` | turns what we billed per figure key into `_figkey_panel.json`, the numbers the zones show |
| `_figkey_panel.json` | what we billed, per figure key and per zone, with the brake split |
| `verify_figkey_page.py` | headless-Chrome check of the zones, the numbers and the interaction |
| `qa_figkey_shots.py` | measures the screenshots, because image reading returns nothing here |
| `_qa/` | verification output and screenshots |

## Verification

```
python verify_turntable.py  --page ISZE_DMax_Turntable.html --shots _qa   # browser, file://
python verify_figkey_page.py                                             # zones + numbers
python qa_figkey_shots.py                                                # screenshots
python qa_frames_visual.py                                              # frames
python compare_framing.py   --raw _raw_tt                               # camera stability
python inspect_frames.py    _raw_tt _raw_tt                             # per-frame measure
python test_drag_feel.py                                                # drag behaviour
```

`verify_figkey_page.py` also fails on a zone card without a euro figure, on a
zone that reports brake money without painting it, and on a drag that does not
move the vehicle.

`verify_turntable.py` fails rather than warns on any of: a request to anything but a
`file:` URL, a console or page error, a frame that fails to decode, no still fallback, a
drag that does not change the frame in either direction, a spin that does not wrap past
both ends, arrow keys that do not step, and a page that cannot show the truck with
scripting disabled.

## Reuse of the hero — no second copy of anything

The materials, the detail geometry, the smoothing, the studio rig, the Cycles settings and
the camera are **not re-implemented here**. `build_turntable.py` slices those exact blocks
out of `../build_dmax_render.py` at run time and executes them in-process, so there is one
copy of them and this render cannot drift from the hero. The slices are anchor-checked: a
missing anchor is a hard stop, never a silent fallback. Every line range used, and a SHA-256
of the source file, are recorded in `_raw_tt/turntable_render_report.json` under `reuse`.

The composite step does the same with the background: it imports `studio_background()` from
`../compose_dmax.py`, the same function that backs `dmax_hero.png`.

## The one framing decision

A turntable has to hold one framing for every frame. If the fit were recomputed per frame,
the truck would breathe in and out as it turned — exactly the jitter to avoid.

So the fit is taken **once**, over the union of every yaw in the sequence: the projected
bounding box of each yaw is measured, the largest is kept, and that single `ortho_scale` is
used for all frames. It is then clamped so it can never go tighter than the hero's own fit,
which means frame 1 reproduces the accepted hero framing exactly.

The cost is that the frames where the truck is longest carry a little more air than the hero
does. The benefit is that the camera is provably identical in every frame.

The frame is 1500×860 (aspect 1.744). The hero's 2600×1120 is 2.32:1; the camera looks down
at 18°, so an end-on truck eats far more image *height* than a broadside one, and a very wide
frame would either crop the ends or shrink the truck to nothing. `framing_probe.json` records
the measurement behind that choice.

## Verified numbers

| | |
|---|---|
| Frames | **48** at **7.5°** steps |
| Per-frame render | 1500×860, 64 samples + denoise, Cycles GPU, AgX Punchy, film transparent |
| Per-frame time | mean **14.35 s** (12.2–22.3 s) |
| Total render | **689 s** for 48 frames |
| Camera | azimuth 80°, elevation 18°, orthographic, one `ortho_scale` = 6.7314 for every frame |
| Hero parity | the same camera model at the hero's 2600×1120 returns **6.6866** vs the hero's recorded 6.686607 |
| Frame embedding | 1240×638 JPEG q86, **3.03 MB** total, mean 64.7 KB |
| Page size | **4.15 MB** |
| Crop | one box, identical for all frames: render (109,131)–(1391,791) → 1282×660 |

### Framing drift — what it is and what it is not

A bounding box is **not** constant across a turntable and should not be: a 5.4 × 2.1 m
vehicle projects about 2.6× narrower end-on than broadside. Measured, the width runs
460–1215 px and the height 481–598 px as the truck turns. That is the rotation.

So camera stability is proved a different way: the real vertex cloud is rotated and
projected through the single fixed camera at every yaw, and that prediction is compared
with the rendered frames (`compare_framing.py`).

| Residual, measured − predicted | spread |
|---|---|
| width | **2.67 px** (0.22% of the vehicle) |
| height | **2.02 px** (0.34%) |
| centre x | **1.54 px** (0.10% of frame) |
| centre y | **1.30 px** (0.15% of frame) |

Plus two independent invariants: the projected length at 180° matches to **1 px**, and the
silhouette centre stays within **36 px** of the frame centre.

An earlier version of this measurement read 65 px of height error and failed. That was the
measuring code, not the render: it used an alpha threshold that counted the semi-transparent
contact shadow as part of the truck, and the shadow's length follows the yaw. Measured on
body-only alpha the residual is 2 px. The correction is documented in `inspect_frames.py`.

### Loop

Last frame 352.5° → first frame 0.0° is **7.5000°**, exactly the step between all other
frames. Frame-to-frame image difference: mean 21.58, wrap step 23.49, ratio **1.09** — no
jump at the seam.

### Payload and page

Verified in headless Chrome over `file://`: **48/48** frames decode, **zero** non-`file:`
requests, zero console errors, zero page errors. Drag changes the frame in both directions
and wraps past both ends; arrow keys step; the page still shows the truck with scripting
disabled.

### JPEG quality

The frames are JPEG q86. Measured on a re-encode, the difference in flat background regions
is 0.0005 of a level, so the visible ground and backdrop are stable. The remaining ~1.2/255
(0.46%) drift in the upper background band is real and physical: the shadow-catcher floor
returns a faint ambient veil up there, which is lit partly by light bouncing off the truck,
so it changes slightly as the truck turns.

## Tuning

Everything is a flag: `--frames`, `--resx/--resy`, `--samples`, `--quality`, `--outw`,
`--margin`. 24 frames at 10° would halve the payload; 72 frames would cost ~7 MB. The
per-frame cost is dominated by samples, not pixel count, so dropping `--samples` is the
cheap lever.

## Zones

`dmax_hotspots.json` (in the folder above) holds six zones measured for the hero camera. The
turntable keeps that camera, so the zones are valid on the one frame that reproduces that
view — frame 1. They are shown **on frame 1 only**, and the page says so. They are not
re-projected onto the other 47 frames, because those were never measured.

The mapping from hero pixels to this page's pixels is derived from the two cameras (both are
orthographic, with a known ortho scale and a known crop) and is checked against the measured
frame-1 silhouette before the page will use it.

## What the zones carry

A zone is a claim about a place on the vehicle, so it is worth showing only if it holds real
numbers. Each zone shows what we billed against the figure keys that belong to it.

The spine is the **figure key**: the catalogue diagram number, e.g. `302-017`. A figure key is
a chapter in the parts catalogue, and a chapter is an assembly on the vehicle. Part numbers
inherit their place from the chapter, not from a judgement about their name.

The page read the figure key's own label first and went looking for a positional word in it.
That is the wrong test. `302-017` carries three different labels — *Pad kit; caliper,disc
BRK,FRT*, *Brake disc*, and *Review needed* — and **none of the three says "front"**. The
position is in the chapter number, not in the words. The page therefore places a part by its
chapter and uses the label only to recognise a part that has no single place on a vehicle at
all (a bolt, a seal, a gasket, and the *Review needed* / *Unmapped* buckets).

The numbers come from `build_figkey_brake_panel.py`:

| Source | Columns used |
|---|---|
| `01_data/00_derived/sales_by_db_fig_key_year.csv` | `net_sales_eur`, `fig_key`, `fig_key_label`, `billed_qty`, `distinct_pns` |
| `01_data/00_derived/parts_catalog_dimension.csv` | `part_number`, `fig_key`, `fig_key_label`, `pms_category` |
| `01_data/00_derived/aim_pn_classification_v2.csv` | `part_number`, `catalog_l1`, `catalog_l2`, `catalog_l3` |
| `03_analytics/Isuzu/prism/data/gps_model_targets.csv` | `model_group`, `target_eur_per_vehicle`, `notes` |

The window is 2023 to 2026 to date, all markets: **EUR 103,993,893** over 5,841 figure keys.

What the figures do and do not say:

- **95.7%** of that euro sits on a chapter that can be given a place. It is spread across six
  zones, so a zone figure is one zone's share, not a market total.
- **4.3%** is reported as *not on the vehicle* rather than forced onto a zone: EUR 4,198,489
  is not a figure key at all (rebates, transport, lubricant part numbers), and EUR 198,678 is
  *Review needed* or *Unmapped*.
- The zone totals add back to the euro we billed, and the brake buckets add back to the brake
  total. Both identities are checked in the builder and it stops if they break.
- The **target** is EUR 250 per vehicle per year, which is a whole-vehicle figure. A per-zone
  target is that figure split by the zone's share of what we billed. It is an allocation, not a
  separately published per-zone target, and the page says so. Against the 12 markets that
  carry a vehicle count, we billed 80.5% of that ceiling across 2023–2025.
- Zones with no brake content — the **cab** and the **electrical** area — say so in words. They
  do not show a zero, because a zero would read as a finding.

## What did not work

The three-digit **prefix** is not reliable enough on its own. Judged on the labels inside each
prefix, 105 prefixes are clean and carry 50.0% of the euro, but 30 prefixes carry two or more
zones and EUR 15,045,950 (**14.5%**). Prefix `146` alone holds 58% electrical and 30% chassis.
So the prefix is a useful index, not a rule.

The figure key is also **not a better locator than the catalogue category name**: using only
positional words, the figure key label places 78.4% of the euro and the category name places
80.1%. With an assembly fallback the two are 86.9% and 89.8%; the category name is slightly
**better**, because the category names are already written as assembly words.
Where both place a figure key but disagree, the stake is 0.40% of the euro.

What the figure key does better is the **front/rear brake split**. Both D-Max pad part numbers
that `03_analytics/Isuzu/prism/data/lcv_pms_genuine.yaml` records as "front/rear position not
confirmed" sit on `302-017`, the front chapter. The figure key settles what the category name
could not: `523` rows are tagged only `brake_pad`, with no axle. EUR 5,299,935 of brake euro
(**38.9%**) is a brake part whose chapter is a general chassis chapter — `411`, `420`, `156`,
`155` — where the catalogue genuinely does not state an axle.

`verify_figkey_page.py` runs the page in the system Chrome over `file://` and fails on any
request that is not `file://`, any console or page error, a zone card without a euro figure, a
zone that reports brake money without painting it, a click on the vehicle that opens nothing,
and a drag that does not move the vehicle.
`qa_figkey_shots.py` measures the screenshots, because image reading returns no visual content
in this environment — that limitation is real and is recorded in `_qa/figkey_read_note.txt`.

## Credit

3D model: **2021 Isuzu D-Max by David_Holiday**, published on Sketchfab, **CC-BY 4.0**,
obtained from the Objaverse open dataset. The licence requires the credit to travel with the
render; it is in the page footer and in this file. Rendered in Blender 4.2 with Cycles.

## Known limitation of this build

The frames were checked by measurement, not by eye. Image viewing returned no visual content
to the agent that built this, for every file tried including the known-good `dmax_hero.png`,
so the "look at a sample of frames and confirm the truck looks right" step could not be done.
The substitutes are numeric: body-to-edge clearance (117 px minimum), the predicted-vs-measured
silhouette comparison, the 180° width symmetry, ink coverage per frame, tone distribution
against the hero, and the smoothness of the frame-to-frame difference. Those would catch a
clipped, blank, drifting or wrongly-scaled frame, but they cannot catch a texture or shading
fault that a person would spot instantly. **Somebody should look at `_qa/frames_four_angles.png`
and the four `_qa/page_0*.png` screenshots before this goes in front of anyone.**
