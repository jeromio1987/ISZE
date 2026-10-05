# Complete the four photo additions locally

The enclosed PowerPoint is the actual 24-slide layout-checked deck. Its business wording and presenter notes are preserved. The source-information block on slide 3 now fits, and the rendered text on every slide has been checked. All original slide words remain present in the PDF export. No photographs have been added to this input deck.

## Why this separate step exists

The ChatGPT runtime could read some image-source pages but could not transfer image binaries from the internet. The candidate originals have therefore NOT been downloaded or resolution-verified here. This package is an executable handoff for Cursor on an internet-connected computer, not a claim that the photos are already installed.

## Ask Cursor to do this

Use the enclosed script and existing checked deck. Retrieve the four photographs, inspect them, and embed them on slides 8 and 24 only. Do not rewrite any slide. Do not add slides or an appendix. Preserve every word and the existing approved colours and sequence. If a candidate source is unavailable, locate an equivalent authorised real photograph, or use an original supplied locally. Do not use generated images, enlarge a thumbnail, replace a housing with a cover, or assemble unrelated components into an invented kit.

The candidate source URLs and their descriptions are in `image_sources.json`. Some are representative supplier photographs, not verified Genuine Isuzu product references. Keep the notes explicit. The truck source is Australian-market MY25 N Series; do not describe it as a European model launch.

### Commands

The script needs Python, Pillow and python-pptx. Where they are not installed:

```text
python -m pip install Pillow python-pptx
```

Download and check actual native pixel dimensions:

```text
python add_photos.py --download
```

Inspect `REVIEW_IMAGES_BEFORE_APPLYING.png` and the individual originals. Confirm the housing is a housing, the kit is an actual kit, and permissions suit the intended use. A failed or undersized download stops without changing the presentation.

After that inspection:

```text
python add_photos.py --apply-reviewed-images
```

The output is `AIM_with_reviewed_photos.pptx`. The original `AIM_checked_input.pptx` remains intact. Images are embedded, not linked. The script checks that all slide words remain and that the other 22 slide XML documents are unchanged. Open the output in PowerPoint, inspect slides 8 and 24, then export a PDF and inspect every page for clipping or overlap.

## Using locally supplied photographs

Place authorised originals in a `photos` folder with these names (JPG, PNG, JPEG or WebP):

- `element.jpg`
- `housing.jpg`
- `kit.jpg`
- `truck.jpg`

Then run the apply command. The native resolution checks still run. The product minimum is a 1,200-pixel long edge and 600-pixel short edge. The truck minimum is a 2,000-pixel long edge and 1,000-pixel short edge. Larger originals are welcome; the script does not upscale.

When using different photographs, update the source page and explanatory note in `image_sources.json`; do not attribute a local photo to the supplied website.

## Source and verification boundaries

Only public candidate-image URLs are contacted. No private data, account credentials or PowerPoint files are sent to an external service. The script has no macros. Its image-insertion and text-preservation behaviour was tested locally using labelled test fixtures; real image downloading was not testable in the ChatGPT runtime. The fixtures are not included in this package.
