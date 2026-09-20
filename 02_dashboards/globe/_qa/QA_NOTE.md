# QA note — ISZE Globe

Written 2026-09-18. This states what actually painted, what did not, and what I
could not verify. Nothing here claims more than the evidence supports.

This revision covers three changes on top of the 2026-09-18 morning build: the
Esri basemap source removed, the IDS dealer layer added, and the overlays tidied.
The morning's findings and bugs (bugs 1–6 at the end) still stand and are still
held by the checks.

---

## How it was verified

The page was served by the launcher and loaded over `http://localhost:8511` in
headless Chrome (Playwright driving the local Chrome at
`C:\Program Files\Google\Chrome\Application\chrome.exe`, WebGL via ANGLE /
SwiftShader). **It was never judged by opening `index.html` directly** — that
fails by design, because MapLibre needs a Web Worker and the data is read with
`fetch()`, both of which browsers block from a `file://` page.

Commands run, in this order:

```
cd C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\globe
python build_market_spine.py            # build the market numbers   (exit 0)
python extract_ids_dealers.py           # build the IDS dealer records (exit 0)
cmd /c OPEN_ISZE_Globe.cmd              # the real launcher, cold start
python _qa\check_spine.py               # 45 assertions on the market JSON
python _qa\check_ids.py                 # the IDS file and the IDS layer
python _qa\check_html.py                # inline-script syntax, ids, banned words
python _qa\qa_globe.py                  # drives the page, writes shots 01-21
python _qa\check_layout.py              # label overlap, clipping, panel and overlay geometry
python _qa\verify_encoding.py           # sphere test + per-column colour check
python _qa\check_offline.py             # network blocked; live-watermark test
python _qa\pixel_check.py               # are there actually coloured pixels
```

All eight checks exited 0 on the final code.

---

## Screenshots — taken and read

**21 screenshots exist after the full QA pass, plus 4 crops from the morning
build and 8 throwaway probe frames I made while working. I read all 21 of the QA
screenshots myself, one at a time, at full resolution, plus the crops and probes
listed below.** That is a read count, not a take count.

All 21, this revision:

| # | File | What I saw in it |
|---|---|---|
| 01 | `01_globe_columns.png` | 18 labelled columns on the globe, Europe and Israel, offline geography. Germany pale, Ireland and Finland dark green, Hungary dark red, Portugal and Israel terracotta. No blank canvas. |
| 02 | `02_hover_column.png` | Tooltip on Isuzu Truck UK: "Uncaptured parts spend: €6.27M / Share of target spend captured: 47.0%", with the UK pair of columns separated and both named. |
| 03 | `03_panel_open.png` | Market panel on the right for Isuzu Truck UK: €6,271,367 hero, target spend less billed, 47.0% capture bar, fleet 22,389, €248.54 per truck. Title bar and controls clear of the panel. |
| 04 | `04_zoomed_in.png` | Zoomed Benelux with pitch: columns visibly 3D with vertical faces, labels for Benelux, Germany, Denmark, Sweden, the UK pair, plus city names. |
| 05 | `05_placeholder_market.png` | Ukraine panel: amber "No column for this market" block, "no data" against target spend, gap and capture — not a zero. |
| 06 | `06_shared_coordinate_pair.png` | Israel zoomed: the two columns separated left and right of the same source point, each labelled, UMI and UTI both readable. |
| 07 | `07_metric_switched.png` | Height now "What we billed per truck", colour now "Uncaptured parts spend"; the legend title, swatches and hint text all changed with it — the switch is data-driven. |
| 08 | `08_final_state.png` | Back on the offline basemap after the toggles, page intact. |
| 09 | `09_offline_no_network.png` | Globe painted with every non-localhost request aborted: land, borders, and the 18 columns. |
| 10 | `10_column_encoding.png` | The frame used for the per-column colour test: the globe reframed over Iberia and France with the columns drawn. |
| 11 | `11_live_tiles_blocked.png` | Network blocked, "Live streets" reverted to offline and the amber banner shown; geography still drawn. |
| 12 | `12_live_tiles_online.png` | **The live street layer with no watermark.** A pale CARTO street map with real street detail; no "API KEY REQUIRED" text anywhere. |
| 13 | `13_map_band_offline.png` | The same camera on the offline geography, for the side-by-side against 12. |
| 14 | `14_layout_1440x900_all_open.png` | 1440x900 with every control unfolded. Controls stack from the top right, legend a small folded bar bottom-left, nothing overlaps, nothing off-screen. |
| 15 | `15_layout_1440x900_folded.png` | 1440x900 with everything folded: slim header strips only, map clear. |
| 16 | `16_dealers_toggle_at_europe.png` | Dealer toggle on at the Europe view: no pins, hint reading "Zoom in to see dealers. They appear from zoom 5.0 so 564 pins never clutter the Europe view. Current zoom 2.2." |
| 17 | `17_dealers_country_zoom.png` | Zoom 6.4 over France: navy cluster discs with counts, green/amber/red pins, the IDS key bottom-right. |
| 18 | `18_dealer_panel_open.png` | A surveyed MIDI dealer clicked: "IDS FRANCE", score, national average, the difference, all five sections, and the position note. |
| 19 | `19_market_panel_with_dealers_on.png` | A market column clicked with the dealer layer still on: the Isuzu Truck UK market panel, unchanged. |
| 20 | `20_dealers_offline_no_network.png` | The dealer layer drawn with every non-localhost request aborted, so the layer is fully local. |
| 21 | `21_dealers_key_1440x900.png` | 1440x900 with the dealer layer on: the IDS key panel bottom-right, complete (all five key rows plus the 160/404 note), clear of the controls and of the market legend. |
| — | `sphere_globe.png` | The globe at zoom 1: a disc floating in pale sky, corners and edges clearly not earth. |
| — | `sphere_mercator.png` | The same view on the flat map: geography fills the frame edge to edge. |

Also read, while working:

- The four morning-build crops (`crop_israel_pair.png`, `crop_panel_numbers.png`,
  `crop_placeholder_panel.png`, `crop_labels_dense.png`).
- `_probe_esri_tile_big.png` — an Esri World_Street_Map tile fetched directly.
- `_probe_carto_tile.png` — a CARTO Voyager tile, for comparison.
- `_probe_esri_montage.png` — six Esri tiles at zooms 4–12 in one image.
- `_probe_carto_only.png` — a CARTO-only raster probe rendering cleanly.
- `_probe_fallback.png`, `_probe_rotate.png` — the MapLibre raster probes.
- `_crop_pins.png`, `_crop_biggest_cluster.png` — close-ups of the dealer pins.
- `_crop_panel_top.png`, `_crop_panel_bottom.png` — the dealer panel at 2x, read
  to check the section rows and the position note.

Those probe frames and the four working crops have since been deleted, since
`qa_globe.py` and `check_layout.py` reproduce the same views permanently.

---

## Job 1 — the Esri watermark

### What was wrong, and the mechanism

The live tile source listed three URLs: two CARTO Voyager mirrors and Esri
World_Street_Map third. The page claimed that a failure would fall through to the
next URL. **That is not what MapLibre does.** It walks a raster `tiles` array by
tile sequence to spread load across mirrors. It does not treat later entries as
fallbacks.

Measured on 5.6.2, not assumed. Two probes:

- One dead URL plus one live URL: 15 requests to the dead URL, 17 to the live
  one, 15 `AJAXError`s. Both URLs were used; the dead one was **not** skipped.
- Two distinguishable live CARTO paths in one `tiles` array: 8 requests to each.
  Confirms rotation.

So Esri was not a fallback — it was serving roughly a share of every user's
tiles. Esri watermarks tiles served without an API key, and that watermark was
painting over about a third of the map.

### The fix

The Esri source is **removed**, from the source definition and from the tile
probe list. No key was requested and no account was created. The live source now
lists the two CARTO Voyager mirrors only.

### How the watermark was proved gone

Four independent pieces of evidence:

1. **The rendered page requests no Esri tiles.** `check_offline.py` counts every
   tile request: 36 tiles, hosts `a.basemaps.cartocdn.com` and
   `b.basemaps.cartocdn.com`, **0 Esri requests**.
2. **The source is not in the file.** `check_html.py` asserts that
   `arcgisonline`, `/MapServer/tile/` and `World_Street_Map/MapServer` appear
   zero times in `index.html`. The word "Esri" does appear, in the comment that
   records why the source was removed.
3. **The rendered live band is not darkened.** With the live layer on, the map
   band has mean luminance **228.1** against **216.2** for the offline
   geography — lighter, not darker. Large diagonal watermark text over the whole
   band would push it the other way. `check_offline.py` computes both numbers
   every run and prints them.
4. **I read the screenshot.** `12_live_tiles_online.png` is a clean pale street
   map. No watermark text is visible anywhere in it.

I could not test for the literal string "API KEY REQUIRED" directly: tesseract
is not installed on this machine, so OCR was unavailable. The proxy test in
point 3 is what stands in for it, and it is a proxy — a watermark that happened
to leave the mean luminance unchanged would fool it. What makes this reliable is
that the source is gone from the file and no Esri tile is requested, so there is
no route by which the watermark could return without one of the other checks
failing first.

### Not regressed

`check_offline.py` still blocks every non-localhost request and confirms the
offline geography paints: **98.1%** earth-toned in the sampled map band, the land
layer holding 110 features, and **19 rendered column features for 18 columns**
(one straddles a tile edge and is counted twice). The failed live-tile switch
still reverts cleanly with the amber banner and **99.6%** earth-toned.

---

## Job 2 — the IDS dealer layer

### Extraction

`extract_ids_dealers.py` reads the `const DATA = {...}` payload out of
`02_dashboards/ids/IDS_2026_dealer_compare.html` by brace matching (not a regex —
the question text contains braces and escaped quotes) and writes
`data/ids_dealers.json`.

**564 dealers extracted. 160 real-coordinate pins, 404 approximate.**
**The file is 461 KB (471,809 bytes)**, down from the 4.4 MB source, because the
per-question `q` array is dropped — that array is 196 floats per dealer, about
3.4 MB across the network, and the globe panel does not show per-question detail.

`02_dashboards/ids/` was **read only**. `build_ids_dashboard.py` was not run and
`IDS_2026_dealer_compare.html` was not modified; `check_ids.py` asserts the file
is still 4,628,834 bytes and still declares 564 dealers.

Dealers per IDS tab: France 84, Spain 45, UK LCV 45, UK CV 44, Benelux 43,
Italy 41, Norway 38, Belgium 34, Greece 34, Israel LCV 29, Poland 23,
Switzerland 22, Denmark 20, Hungary 19, Portugal 16, Romania 15, Netherlands 9,
Cyprus 1, Luxembourg 1, Malta 1.

### The zoom threshold: 5, with clustering to 7

Two thresholds, for two different problems.

**`dealerMinZoom: 5`** is where the pins first appear. This was chosen against
measurements, not by feel. At the default view (zoom 3.1) the smallest
column-centre gap on screen is 24 px, against a 22×16 px column footprint: the
columns are already close to touching. The gaps between European capitals are
300–500 km, so at zoom 5 a country is roughly 500–800 km across the viewport —
enough for a dealer's street position to be meaningful rather than a dot inside a
city blob. Below zoom 5 the market columns stay the primary mark, which is the
existing design.

Turning the layer on while zoomed out does not silently do nothing: the camera
moves to zoom 5, fitted to all 564 dealers. That is why the toggle reads
"Show / Hide" rather than "On / Off" — tapping it at the Europe view has to
answer with the dealers. `shots 16` records the state with the toggle on and the
pins still hidden, together with the hint that explains it. That state is only
reachable by setting the camera directly, which is what the QA script does.

**`dealerClusterMaxZoom: 7`** is where the pins separate. Without grouping, zoom
6.4 over France rendered 48 overlapping pins in a pile; with grouping it renders
36 cluster discs carrying counts and 26 cluster labels, which is readable. This
was changed after seeing the first version (grouping only up to zoom 4) draw a
pile — the measurement drove the number.

### Real versus approximate pins

Carried through from the IDS `geo_label`, unchanged. The map draws a solid navy
ring for the 160 MIDI-surveyed positions and a broken ring with a pale centre for
the 404 approximate ones. Both are coloured by band so the two pieces of
information do not compete.

The panel states it in words per dealer — for a MIDI dealer, "This position comes
from the MIDI network survey, so it sits on a real surveyed coordinate"; for the
rest, "This position is approximate: the IDS build resolved it from the address,
the dealer name or a known directory entry, not from a survey. Read it as a town,
not as a forecourt." `check_layout.py` asserts the note is present.

The IDS key panel carries the same honesty in one place: **160 of 564 dealers
carry a surveyed coordinate. The other 404 sit on a town, a directory entry or,
for nine of them, the country centre.**

### Performance

- 564 features in one GeoJSON source. `check_ids.py` asserts
  `source._data.features.length === 564`, which is the count handed to MapLibre.
  `querySourceFeatures` is **not** a valid way to assert this: it returns only
  what is in the tiles currently in view, so the number moves with the camera. I
  made that mistake in a first version of the check and corrected it.
- No per-dealer labels exist. The only dealer DOM nodes are cluster counts, with
  a hand-written collision test that also avoids the floating overlays. At zoom
  6.4 over France: **26 cluster labels for 564 dealers**, 137 label nodes in
  total including all city and market labels.
- The whole layer is local, so it draws with the network off — asserted by
  `check_offline.py`, which rendered 32 real and 11 approximate pins with every
  non-localhost request aborted (`20_dealers_offline_no_network.png`).

### Where the deeper view is

The panel says the dealer radar and per-question scores already exist in
`02_dashboards/ids/IDS_2026_dealer_compare.html` and points there. **No radar is
drawn on the globe**, and `check_ids.py` counts `.radar` elements to confirm
none was invented.

---

## Job 3 — arranging the map

The framing measurement first, because "cluttered" needed a number. At the
default view the 18 columns project to a 47% × 57% span of a 1440x900 window,
with 129 px average labels and 18 of them, 0 overlapping after the stacking pass.
The columns themselves are 22×16 px at the default zoom — physically small. At
zoom 4.5, 35 labels including the city names is where it does read as a wall, and
that view is not the default.

What was changed, each against a measurement:

- **The four grey "no target spend" labels are hidden below zoom 4.** They are
  drawn, clickable, and their panel still explains the gap; only the label waits.
  They sit in the middle of the map and their four labels were what tipped that
  band into text.
- **Every control folds**, and the stack scrolls if it ever needs to. Unfolded
  the stack is 629 px in a 900 px window (bottom edge 645) — it fits, and the
  scrollbar is there for shorter windows.
- **The legend folds**, and opens folded on a window under 1010 px tall. At
  1440x900 the full legend was 531 px tall reaching from y=353 to y=884 across
  the middle of the map; folded it is 45 px at the bottom. Turning the dealer
  layer on unfolds it, so the layer is not left with its key hidden.
- **The dealer key is its own panel**, bottom right, shown only while the dealer
  layer is drawn. It is not folded into the market legend: the two together do
  not fit above that legend's bottom edge on a 900 px window, and the market
  legend is the one that has to stay where it is.
- **The bottom padding in `resetView` was reduced from 90 px to 40 px**, which
  lifts the columns and Israel clear of the bottom edge.

Measured result at 1440x900: **0 overlay-vs-overlay overlaps**, the three
floating panels cover **12.2%** of the window, folding reduces the controls from
629 px to 256 px, and every label in every view (including with the dealer layer
on) has **0 overlapping pairs**.

House look kept: navy `#15233c`, terracotta `#c0552d`, paper `#f7f4ee`. The
cluster discs are navy with paper text and the IDS key uses dark text on paper;
nothing in the new markup is pale on pale.

The metric switch and the offline-first behaviour were not touched, and both are
re-asserted by the checks (`07_metric_switched.png` state is read by
`qa_globe.py`; `check_offline.py` covers offline).

---

## Console

**0 console messages, 0 page errors, 0 non-2xx responses** on the normal path,
across `qa_globe.py`, `check_ids.py`, `check_layout.py`, `check_offline.py` and
`verify_encoding.py`. No WebGL or worker errors. The WebGL renderer is ANGLE
(SwiftShader), which is the headless software path, not a GPU.

The tile-fetch errors the page counts separately (`.tileFetchErrors`) are 0 with
the network up.

---

## What does not work, or is not there

1. **The active projection cannot be read from script in MapLibre 5.6.2.**
   `map.getProjection()` returns `undefined` and `getStyle().projection` is
   `null`. The page reports what it requested. The sphere test settles it from
   rendered pixels (43% of canvas height, 0% edge coverage, against 90% and
   full-width on the flat map).
2. **The per-column colour check is partly occlusion-limited.** 9 exact matches,
   8 within blending range, 1 occluded by a label, of 18.
3. **The offline colour check sees one class of five.** At the default zoom the
   smaller columns are a few pixels wide; only the largest class has enough area
   to pass a pixel count. The offline claim rests on the rendered feature count
   (19 for 18 columns) and the Earth coverage share (98.1%).
4. **No OCR on this machine.** Tesseract is not installed, so the watermark test
   is a luminance/contrast proxy rather than a literal string search. See Job 1.
5. **Labels are HTML, not a MapLibre text layer**, so collision handling is
   hand-written for both the market labels and the dealer cluster counts.
6. **Live tiles are unverified on Jerome's actual network.** They work here; a
   corporate proxy blocking CARTO has not been tested.
7. **The 120 km column footprint is fixed.** At very high zoom the squares read
   as squares.
8. **Height and colour use different scales by design**, so a column's height and
   its colour are not two views of one number unless you pick the same metric.
9. **The market frame and the dealer frame are different.** The default view
   frames the 18 columns; the dealer view fits all 564 dealers including the
   three French overseas ones in the Atlantic and Indian oceans. Switching the
   layer on reframes the globe. France in `data/ids_dealers.json` has 84
   recordings, 81 with MIDI coordinates, and lat/lon ranges from −21.34
   (Réunion) to 55.47 — so the two frames cannot be the same view without
   shrinking Europe to a speck.
10. **`querySourceFeatures` is not a count of the source.** It returns only the
    tiles in view. The source count is asserted from `source._data.features`.
11. **MapLibre's raster fallback does not exist**, which is a limitation of the
    library rather than of this page, but it is why only one tile provider is
    listed and why adding a second is not a safe way to add redundancy.
12. **Not verified: any browser other than Chrome.** Edge and Firefox were not
    tested.

---

## Bugs found during this revision, and fixed

1. **A duplicated `map.on("click")` block**, from a bad edit, left a
   `map.on("click", function (e) {` open with no closer and broke the whole
   page's JS with `missing ) after argument list`. Caught by `check_html.py`
   running the inline script through `node --check` before any browser run —
   this is the same class as bug 5 below and the check now exists for good.
2. **The generic map-click handler closed the dealer panel immediately after a
   pin opened it.** Clicking a pin opened the panel and the same click then
   reached the catch-all handler, which decided no market column was under the
   cursor and closed the panel again. The handler now ignores a click that
   landed on a dealer layer, using the layers that exist at click time rather
   than the layer set as it was when the handlers were wired.
3. **Cluster counts overlapped the market and city labels**, 7 colliding pairs at
   zoom 5.6. The cluster counts are now placed first with a real collision test
   that also avoids the floating overlays, and `layoutLabels` seeds its own
   placement list from the cluster boxes so the market labels give way.
4. **The dealer key was hidden on a short window.** It lived inside the market
   legend, which starts folded under 1010 px; turning the layer on showed a
   correctly-rendered key inside a folded panel. It is now its own panel, and the
   check asserts it has real height (305 px) and that its last row is inside its
   own box.
5. **`state.ids` was used for two different things** — the fetched payload and
   the built lookup — so `buildIds` read its own output. Split into `idsRaw` and
   `ids`.
6. **The screenshot-that-proves-nothing trap.** The first dealer probe picked
   `queryRenderedFeatures(...)[0]`, which was a pin at a negative screen
   coordinate, so the hover and the click missed and the panel appeared broken.
   The probe now filters to pins that are on the canvas and clear of the
   overlays, and reports which one it chose.

The morning build's bugs 1–6 (panel never opened without `promoteId`; the live
tile probe using `sourcedata`; the undeclared live source; the NaN truthiness in
the coordinate-offset flag; the mismatched quote in the amber block; labels
disappearing instead of stacking) were **not** re-broken: `check_spine.py`,
`check_ids.py` and `check_layout.py` all cover them.

---

## Data decisions worth knowing

- **2025, not 2026.** 2026 is `partial_year` and 2023–2024 have no
  `max_spend_eur`. Putting a part year beside full years would compare unlike
  periods. The build prints the per-year tally and picks the most recent full year
  that carries a target spend.
- **18 of 22 markets get a column.** Armenia, Kazakhstan, Palestine and Ukraine
  have no target spend, so no gap can be computed. They are drawn as flat grey
  ringed markers labelled "no target spend", and their panel leads with an amber
  block saying the figure is missing rather than zero.
- **`max_spend_eur` is populated for all 18 drawn markets**, so the height
  measure is real data throughout. Had it been empty, the build was written to
  stop and report rather than substitute a different metric.
- **The four joins share one key, `distributor_code`**, with no crosswalk. The
  build verifies that UMI resolves to `sold_to_sap` 1797 and UTI to 1799, and
  aborts if not, so the two Israel businesses can never be blended. `UNMAPPED`
  (no coordinates) is excluded and the build log records it.
- **The parts-market-scan panel leads with total capture**, with genuine and
  alternative parts as secondary lines, per the house rule.
- **Israel in the IDS layer is UMI only.** The IDS Israel network is the UMI
  dealer network and UTI did not take part in that round. The country label is
  "Israel (UMI)", Section E is not scored for that network (so its dealers score
  on A–D, max 253), and `check_ids.py` asserts no UTI dealer is present.
- **44 of the 564 dealers are "totals only"** — their IDS result carries a total
  but no section breakdown, so all five sections are shown as "no score in the
  IDS result" rather than as zeros. `check_ids.py` asserts the count and that
  none of them has a section score.
- **Three UK LCV dealers are blank on Section E**, and 29 Israel dealers are
  `not_scored` on it. Both are shown as such, never as zero.
