# ISZE PPT Template v2

**2026-07-05 correction:** `ISZE_Template_v2_Demo.pptx` (the original demo, built with
`build_demo_deck.py`) used real distributor codes (ITUK, GA/CBC) alongside made-up
numbers — including a "0.3% oil filter capture" figure that Jerome's own
`05_memory/projects/pms-coverage.md` already flags as obsolete/rejected, and a
GA/CBC "capture rate" that can't exist (no UIO/car-park data for CIS distributors).
**Kept for reference on what went wrong — do not use as a starting point.**

**Use `ISZE_Template_v2_Demo_GENERIC.pptx` / `build_demo_deck_generic.py` instead.**
Same template/chart methodology, fully generic placeholder labels (Category A/B/C,
Region 1/2/3) — nothing tied to a real distributor, project, or figure. This is the
one to copy from for a real deck.

---


Rebuild of `91_legacy/Isuzu/isuzu-ppt-template`. Same brand colors and slide
dimensions, two things fixed:

1. **Real Isuzu logo.** `assets/isuzu_logo_red.png` and
   `assets/isuzu_group_wordmark_black.png` are the actual logo files pulled
   from existing decks (`ISZE_TeamMeeting_2026_Enhanced_Branded.pptx` /
   `ISZE_PMS_SalesPromotion_Branded.pptx`) — not text pretending to be a logo.
2. **Charts are images, not native pptx charts.** `isze_chart_theme.py` builds
   matplotlib charts in the brand palette (red for the headline series,
   charcoal/gray for everything else), with direct data labels instead of
   relying on legends/gridlines. These get inserted as pictures — this is
   what makes the difference between a "default Excel chart" look and a
   research-note look.

## Files

| File | What it does |
|---|---|
| `isze_chart_theme.py` | Chart functions: `bar_chart`, `trend_line`, `waterfall`, `donut_share`. Each takes plain data + a filename, saves a PNG. |
| `isze_deck_builder.py` | Slide layouts: `build_cover`, `build_content`, `build_two_col` (chart + takeaways side by side), `build_full_chart`, `build_closing`. |
| `build_demo_deck.py` | Worked example — generates `ISZE_Template_v2_Demo.pptx` using **illustrative, not real, numbers**. |
| `ISZE_Template_v2_Demo.pptx` | The rendered demo — open this first. |

## Using it for a real deck

```python
import isze_chart_theme as ct
import isze_deck_builder as db

ct.bar_chart(categories, {"FY2026": [...], "FY2025": [...]}, "chart1.png",
             title="...", ylabel="EUR M")

prs = db.new_presentation()
db.build_cover(prs, title="...", subtitle="...")
db.build_two_col(prs, title="<the insight, not the chart name>",
                  chart_path="chart1.png", eyebrow="Section label",
                  takeaways=["...", "...", "..."])
db.build_closing(prs)
prs.save("MyDeck.pptx")
```

## Known limitations (be aware before using for anything external-facing)

- **Font**: charts render in DejaVu Sans (only font in this sandbox). On
  Windows/Mac, set `isze_chart_theme.FONT_FAMILY = "Calibri"` (or "Arial")
  to match the ISZE deck body font exactly — one-line change, untested here
  since this sandbox has no Office fonts installed.
- **Value formatting is per-chart, not automatic.** `value_fmt` defaults to
  whole numbers (`{:,.0f}`) — for small percentages (e.g. a 0.3% capture
  rate) you must pass `value_fmt="{:,.1f}"` yourself or the number rounds to
  "0" and the point disappears. Caught this exact bug in the demo deck
  before delivering it - check your value_fmt whenever a number is <1.
- **Donut labels can sit close to the ring edge** for longer category names
  (e.g. "Electrical") — legible but tight. If it bothers you on a real
  slide, shorten the label or I can add auto label-length handling.
- **No official Isuzu brand guideline was found** in the workspace — colors
  here are inherited from the old skill's approximation (#CC0E1E etc.), not
  verified against an official IML/Isuzu brand book. If one exists, send it
  over and I'll swap in the exact values.
