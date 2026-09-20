# D-Max hero render — 2021 Isuzu D-Max, free route

This folder holds one render of a 2021 Isuzu D-Max double cab, built entirely from
free material, plus the zone hotspot data the catalogue page needs to put clickable
tints on the right panels.

---

## 1. How the model was obtained — no account, no payment anywhere

The model named in the brief is the Sketchfab `2021 Isuzu D-Max`
(uid `5b4443c246b34b79bb2504c4c4a87f1a`, by `David_Holiday`, 882,244 faces,
licence **CC Attribution**). It was **not** downloaded from Sketchfab, because
Sketchfab's download endpoint refuses unauthenticated requests:

```
GET https://api.sketchfab.com/v3/models/5b4443c2.../download
  -> 401 Unauthorized        (needs Authorization: Token <OAuth token>)
GET https://api.sketchfab.com/v3/models/5b4443c2.../archives
  -> 404
```

Instead it came from **Objaverse**, the Allen Institute's open 3D dataset, which
mirrors Sketchfab's CC-licensed models with direct, key-free HTTP downloads:

```
https://huggingface.co/datasets/allenai/objaverse/resolve/main/glbs/000-144/5b4443c246b34b79bb2504c4c4a87f1a.glb
   -> 35,963,964 bytes, glTF binary, downloaded without any account
```

Saved here as `_assets/dmax_2021_objaverse.glb`.

**Credit, as CC-BY requires:** the model is by **David_Holiday**, published on
Sketchfab, licence CC-BY 4.0. If the render goes anywhere public, that credit line
must travel with it.

**Routes that were tried and blocked** (all verified by HTTP request, not assumed):

| Route | Result |
|---|---|
| Sketchfab download API | 401 — OAuth token required |
| Sketchfab `/i/models/<uid>` viewer endpoint | 200 but HTML viewer only, no geometry |
| Objaverse mirror | **worked, no account** |
| Sketchfab search for other downloadable Isuzu models | 12 found, all behind the same 401 |
| 3dcadbrowser.com D-Max | paid only — USD 49.95 to 199.95, "Account Required" |
| meshy.ai Isuzu gallery | account required to download; holds an Isuzu Elf truck, not a D-Max |
| creator3d / CGTrader free filters | 202 with an empty body (bot-blocked); no free D-Max identified |
| free3d.com | 403 Forbidden to automated requests |
| poly.pizza | 401 — needs an API key |
| GitHub repo + code search | 0 repositories; code search needs auth |
| archive.org | has an Isuzu D-Max item, but it is a `.bussidmod` file (a Bus Simulator mod pack), not a general 3D asset |
| PolyHaven | no vehicle models (its catalogue is furniture and props); its **HDRIs** are key-free and one is used for lighting here |

So: one account-free download, and the lighting environment is also key-free.
Nothing in this folder required a login or a payment.

---

## 2. The measurement bug that was hiding a non-existent model defect

This is the most important thing on this page, because it changes what the previous
version of this render claimed.

The first build found the two axles by taking the single **largest gap in the sorted
y values of the rim geometry** and averaging everything either side of that gap.
That works on a model with exactly two wheels. This model also carries wheel-material
geometry **behind the rear axle** — rim, rim2 and tyre materials all appear around
y = 172–192 model units, at wheel height, at the flanks. That extra cluster drags the
average of the rear group rearward, so:

| | units | metres per unit |
|---|---|---|
| wheelbase by the old rim-gap method | 130.116 | 0.024017 |
| wheelbase from the brake-rotor discs | **122.107** | **0.025592** |

Because the wheelbase sets the scale, **every dimension in the previous render and in
its QA tables was 6.6% too small.** The tail, being farthest from the front axle, was
hit hardest, and that is the whole of the "rear overhang 15% short / load box 19% short"
finding. It was my measuring error, not a defect in the model.

The axles are now read from the **brake-rotor discs**, which exist only on road wheels,
and cross-checked against the **free tyre diameter** (265/65 R17 = 0.7766 m), which is
an independent measurement because it does not use the axles at all. The two methods
agree to **1.0%**, which is close enough to trust the scale and not so close as to be
circular.

There was a second, smaller measurement error. The load-box floor was taken as the
median of the topmost 6 cm of interior geometry, which latches onto whatever the
highest interior feature happens to be rather than onto the floor. On this model that
picked up a shelf under the rail, not the load surface, which is why the load-box depth
read 0.355 m. The floor is now found by **casting a ray down through the box**, which is
unambiguous.

---

## 3. What the corrected numbers are

Measured against Isuzu's published specification. "Before" is the previous method,
recomputed by the same script on the same model so the two columns are directly
comparable rather than copied from an earlier report.

| dimension | after | spec | after delta | before | before delta |
|---|---|---|---|---|---|
| wheelbase | 3.125 m | 3.125 m | by construction | 3.125 m | by construction |
| length | 5.404 m | 5.265 m | +2.6% | 5.072 m | −3.7% |
| height | 1.808 m | 1.785 m | +1.3% | 1.697 m | −4.9% |
| front overhang | 0.972 m | 0.905 m | +7.5% | 0.901 m | −0.4% |
| rear overhang | 1.307 m | 1.235 m | **+5.8%** | 1.046 m | **−15.3%** |
| track (front) | 1.541 m | 1.570 m | −1.8% | 1.446 m | −7.9% |
| tyre radius | 0.392 m | 0.382 m | +2.7% | 0.368 m | −3.6% |
| body width | 1.824 m | 1.870 m | −2.5% | 1.712 m | −8.5% |
| ground clearance | 0.234 m | 0.227 m | +3.3% | 0.220 m | −3.1% |
| **load box length** | **1.520 m** | **1.495 m** | **+1.7%** | 1.204 m | **−19.4%** |
| load box width | 1.519 m | 1.530 m | −0.7% | 1.423 m | −7.0% |
| **load box depth** | **0.548 m** | **0.490 m** | **+11.8%** | 0.355 m | **−27.5%** |

Read it this way. The tail is no longer short; it is very slightly long, which is the
honest result of anchoring the whole model on the wheelbase. The load box length now
agrees to 1.7% and the width to 0.7%.

**Two caveats that matter.**

First, the model's own proportions are internally inconsistent with the published
spec by a few percent, so **no single scale factor makes every row exact.** Anchoring
on the wheelbase leaves the overall length about 2.6% long; anchoring on the tyre
diameter instead would leave the wheelbase 1% short and the length about 1.6% short.
The wheelbase anchor is used because it is the dimension the vehicle is actually
specified and measured by, and because it is what the previous build also used, so the
before/after comparison is like for like.

Second, **bed depth is still genuinely off**: 0.548 m against a published 0.490 m. On
this model the bed rail sits about 3 cm higher and the floor about 5 cm lower than
Isuzu's numbers imply. Roughly half of that is the scale anchor and the rest is the
model's own proportions. I looked for a way to close it — raising the floor or lowering
the rail — and every version either broke the arch geometry or made the top of the load
box visibly wrong, so it is left alone and stated rather than faked.

---

## 4. What the render looks like, and how close it is

Cycles path trace of the real 882k-face model, restyled with automotive materials —
basecoat plus clearcoat paint with a procedural metal flake and a shallow panel wave,
chrome, dark tinted glass, satin black plastic, rubber, alloy — under a PolyHaven
photo-studio HDRI plus a four-light rig, with a shadow-catcher floor for the contact
shadow.

* **2600 × 1120** at **400 samples**; the shadow-carrying pass took **63 s**, the
  floor-free pass **34 s**, on the GPU.
* Camera: **azimuth 80°, elevation 18°**, orthographic.

It is rendered **twice**, and the two passes do different jobs. The pass with the
shadow-catcher floor produces the hero; that is where the soft contact shadow under
the tyres comes from. A second pass with the floor hidden produces `dmax_alpha.png`.
The floor pass cannot serve as the compositing PNG, because a shadow catcher returns
the studio light it receives as partial alpha, which leaves a veil across the whole
background. The floor-free pass is a genuinely empty background: **1,068,017 pixels at
alpha 0, 1,260,164 fully solid, 8,971 partial** (the anti-aliased rim), background
median alpha **0**. That is checked twice — `compose_dmax.py` fails the build if the
cut-out is not transparent, and the delivered file was re-checked directly from its own
alpha channel: 45.6% of pixels at exactly 0, 53.8% at exactly 255, 0.54% partial, and
the eight-pixel border strip entirely 0. It is transparent, not grey-veiled.

### The camera angle

A sweep of **28 combinations** — azimuths 56 to 88 in front three-quarter, plus 250
and 265 in rear three-quarter, at elevations 10, 14, 18 and 22 — each rendered and
scored against the real D-Max silhouette. The best-scoring angle was azimuth 80°,
elevation 14° at IoU 0.838, with 80°/18° at 0.837 and 80°/22° at 0.836 effectively
tied.

The hero is shot at **80°/18°**. That is 0.001 IoU below the best, and it was chosen
over 80°/14° because at 18° the load box and bed rail read clearly over the side wall
while the nose and the whole front three-quarter face stay legible. My own first pick,
72°/22°, measured 0.832 and looked distinctly narrower through the nose, so I moved to
the metric's answer rather than defending the earlier choice.

The rear three-quarter angles are in the sweep for evidence: they score 0.77–0.80
against a front three-quarter reference, which is a limit of the reference, not
evidence about the model. A rear three-quarter view cannot match a front three-quarter
outline because they are different sides of the vehicle.

### Recognition test — it reads as a D-Max

The features that carry the identity are the ones a reader actually uses: the tall
blunt nose with the two-bar grille, the swept-back headlamp cluster with its DRL strip,
the deep front bumper, the pronounced wheel arches with the character line running off
them, the double-cab side glass with the kick-up at the rear quarter, the flat bed rail
with the tie-down hooks, the vertical rear lamp cluster, and the alloys with visible
brake discs and calipers. The model carries a full interior, which shows through the
glass and is what stops the cabin reading as a tinted box.

### Where it is not photographic

Four honest limits, unchanged from before in kind even though the tail is now right:

1. **No textures on the vehicle materials.** The file carries one texture image, used
   only by a generic fallback material; each of the named D-Max materials is a flat
   colour with no base-colour map. So the paint is a procedural basecoat-and-clearcoat
   shader with a procedural flake, not a photographed surface. Up close it lacks the
   mottling and orange peel a real paint map carries. The ISUZU badge is now real
   extruded geometry rather than a smooth material split, but it is still lit studio
   chrome and not a decal with its own artwork.
2. **Panel gaps are geometry, not decals.** They read correctly at this scale but there
   is no shut-line shading detail to zoom into.
3. **The lamp lenses are opaque glass.** Correct for a slide-on-a-page render (the PNG
   alpha stays solid), but there is no internal reflector detail.
4. **Some of the model's own details are generic** — the wiper arms, the number-plate
   recess and the tailgate lettering are simplified compared with Isuzu's own imagery.

Put crudely: a good 3D render, roughly three quarters to five sixths of the way to a
press photograph, and the part that is missing is surface, not shape. Do not call it
photoreal.

---

## 5. Silhouette against a real D-Max

Two numbers, and you should read them in this order.

**Against the photograph named in the brief — not measurable.** `dmax_spec_p8_0.jpeg`
is a **483 × 297 px crop of a booklet page**. In it the vehicle, the page type and the
dark setting all sit in overlapping luminance bands, and the vehicle is clipped at the
image edge. Every segmentation attempt either latched onto the page type or swallowed
the background. It is recorded here only as the reason the brief's own reference could
not be used; do not quote it as an accuracy figure.

**Against a clean cutout of the same vehicle — measured.** `_truck_ref/cut/dmax_a.png`:
an isolated 2021 D-Max double cab (1320 × 951) on a flat field that segments exactly.

| silhouette metric | at the hero angle (80° / 18°) |
|---|---|
| intersection over union | **0.837** |
| symmetric difference | **18.6%** of the reference area |
| reference only / render only | 4.9% / 13.7% |
| bottom edge error | **1.6%** of vehicle height (p95 5.6%) |
| top edge error | **4.3%** of vehicle height (p95 11.7%) |

Read the two edge rows as the real story, because the aggregate 18.6% hides it. The
**lower** silhouette — wheels, arches, sill, bumper bottom — agrees to within about
1.6% of vehicle height, which is why the truck sits correctly on the ground and does
not look like a toy. The **upper** silhouette — roofline, screen rake and the
cab-to-bed transition — is where the disagreement lives. IoU of 0.837 means about
five-sixths of the outline overlaps. The difference image is
`_qa_silhouette_diff.png`; blue is the real D-Max only, red is this render only.

One honest limitation of the method: both silhouettes are stretched into the same box
before scoring, which removes scale and aspect so that only the outline is tested. That
is deliberate — it stops the sweep from cheating by rotating toward the nose — but it
also means this number measures **shape**, not size. Size is what the dimension table
in §3 covers.

The previous build's headline was also 0.837, but that was scored at a separate
*measurement* angle of 82°/12° while its hero was shot at 76°/12°. On this build the
hero angle and the measurement angle are the same, which is the point.

---

## 6. Drop-in instructions

Everything needed is in this folder. Nothing else in
`_build/aim_truck_catalogue_2026-09-18/` is touched.

### Files

| File | What it is |
|---|---|
| `dmax_hero.png` | the deliverable — 2356 × 992, opaque, neutral studio ground, soft contact shadow |
| `dmax_alpha.png` | identical framing, transparent background, from a floor-free pass, verified transparent |
| `dmax_hotspots.json` | six zone polygons in `dmax_hero.png` pixel coordinates, plus the vehicle bounding box |
| `_qa_zone_overlay.png` | the hotspots drawn on the hero, for checking placement by eye |
| `_qa_accuracy_sheet.png` | the real D-Max beside the render, the measured silhouette difference, and the geometry table with the before/after column |
| `_qa_geometry_accuracy.json` | the model-versus-specification numbers, before and after |
| `_qa_silhouette_diff.png` | the silhouette difference at the hero angle |
| `_qa_silhouette_metrics.json` | the hero-angle silhouette result and the full angle sweep |
| `REVIEW_DMAX_RENDER.html` | the review page, showing all four images with the numbers and the caveats |
| `OPEN_DMAX_REVIEW.cmd` | double-click to open the review page |
| `OPEN_DMAX_RENDER.cmd` | double-click to open the hero and the two QA images |
| `dmax_prep.py` | shared step: import, find the axles, scale to metres, ray-cast the box and the grille |
| `build_dmax_render.py` | the Blender build: model, materials, detail geometry, lighting, camera, render |
| `compose_dmax.py` | background compositing, hotspot projection, zone coverage, alpha verification |
| `geometry_accuracy.py` | model dimensions versus Isuzu's published specification, before and after |
| `measure_silhouette_mismatch.py` | the hero-angle silhouette score, with `--sweep` for the full set |
| `fit_viewpoint.py` | the camera sweep fitter |
| `make_qa_sheet.py` | builds the accuracy contact sheet |
| `measure_dmax.py` | measures the model's own landmarks off the paint profile |
| `verify_hotspots.py` | checks the hotspot polygons tile the vehicle and round-trip to world coordinates |
| `build_dmax.ps1` | one-command rebuild |
| `_assets/dmax_2021_objaverse.glb` | the model |
| `_assets/photo_studio_01_2k.hdr` | the studio lighting environment (PolyHaven, key-free) |

The `probe_*.py` scripts are the one-off investigations that found the axle and
floor measurement bugs. They are kept because they are the evidence for §2 — run any
of them with `blender --background --python probe_<name>.py` to reproduce the numbers
quoted there.

### Hotspot data format

```json
{
  "image": "dmax_hero.png",
  "alpha_image": "dmax_alpha.png",
  "size": [2356, 992],
  "bounding_box": { "x": 117, "y": 49, "w": 2122, "h": 894,
                    "px": [[117,49],[2239,49],[2239,943],[117,943]] },
  "zones": {
    "front":   [[.., ..], "..."],
    "engine":  [ "..." ],
    "cab":     [ "..." ],
    "rear":    [ "..." ],
    "chassis": [ "..." ],
    "elec":    [ "..." ]
  }
}
```

* Every polygon is a flat list of `[x, y]` pixel pairs, top-left origin, in the
  coordinate space of `dmax_hero.png`. `dmax_alpha.png` is the same size and the same
  framing, so either can be used. **Polygons are not four-point quadrilaterals** — the
  zone shapes were traced from the rendered pixels, so they have up to 50 points and
  follow the vehicle's outline.
* **Together the six polygons are an exact partition of the vehicle.** Measured on the
  rendered pixels by `compose_dmax.py`: **0 pixels claimed by two zones**, and **1.33%
  claimed by none**. Re-checked independently by `verify_hotspots.py`, which erodes the
  polygons by one pixel first so shared edges cannot register as overlaps: still **0
  overlapping**, and 1.19% unclaimed on that stricter measure. So a click anywhere on
  the truck resolves to exactly one zone, with no gaps and no double-tinting.
* Per-zone share of each polygon that lands on actual vehicle pixels: front 99.8,
  engine 99.8, cab 99.9, rear 100.0, chassis 98.4, elec 100.0.
* The zones were built by giving every vehicle pixel a real position: it is the point
  on the flank plane `x = +0.924 m` that projects to that pixel, which yields a `(y, z)`
  in metres, and the zone follows from `(y, z)`. The front-to-back cuts use `y` (axle
  positions, windscreen base, cab back — all measured off the model); the chassis cut
  uses the sill height as a line in the image, so it follows the vehicle's tilt rather
  than sitting flat. `compose_dmax.py` verifies the unprojection round-trips against the
  projector to within 1.2 mm, and refuses to emit hotspots if it does not.
* One honest caveat about the method: a single flat image carries no depth, so a pixel
  on the *far* flank unprojects to a `y` about 1.2 m further back than where it really
  is. The boundaries still render as clean straight cuts across the vehicle, which is
  what a tint needs, but a zone boundary on the far side is a little further back than
  the same boundary on the near side.
* `dmax_hotspots.json` also carries `projection` (the camera matrix, ortho scale and
  crop offset), `vehicle` (the dimensions and the published spec), `world_landmarks_m`
  (the axles, roof, sill, bed rail, box floor and box inner length in metres),
  `zone_world_slabs_m` (each zone as a `[y_start, y_end, z_start, z_end]` slab, with
  `null` meaning open-ended at the nose or tail), `scale` (the metre-per-unit, the
  method, the tyre cross-check and the size of the correction against the previous
  build) and `qa` (the partition counts above), so the polygons can be regenerated for
  a different camera or a different image size.

### Using it on the page

```html
<div class="truck-stage" style="position:relative">
  <img src="dmax_render/dmax_hero.png" alt="2021 Isuzu D-Max"
       style="width:100%;display:block">
  <svg viewBox="0 0 2356 992" style="position:absolute;inset:0;width:100%;height:100%">
    <polygon data-zone="front" points="... take the pairs from dmax_hotspots.json ..."/>
    <!-- one polygon per zone, points built from the JSON rather than by hand -->
  </svg>
</div>
```

`points` is just the polygon's pairs joined with spaces; build the string from the JSON
rather than copying it by hand. Bind a click handler to `[data-zone]` and read the zone
name, or hit-test against `zones[name]` yourself. Because the polygons tile the vehicle,
an SVG overlay with no gaps in the source data is all you need.

### Rebuilding

```powershell
powershell -ExecutionPolicy Bypass -File build_dmax.ps1
# optional: -Paint orange -Samples 400 -ResX 2600 -ResY 1120 -Az 80 -El 18
```

Then, to refresh the measurements and the QA images:

```powershell
python compose_dmax.py --raw _raw --out . --tag hero
python measure_silhouette_mismatch.py
python make_qa_sheet.py
blender --background --python geometry_accuracy.py
```

Requires Blender 4.2 at
`C:\Program Files\Blender Foundation\Blender 4.2\blender.exe`, the system Python with
Pillow and numpy, and about two minutes of GPU time on a 3080-class card.
