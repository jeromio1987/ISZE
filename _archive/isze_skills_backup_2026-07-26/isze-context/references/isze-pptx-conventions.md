# ISZE PPTX Conventions

*Apply when building any presentation for Jerome at ISZE.*

---

## Template Location

**ISZE branded PPTX template skill**: `claude/Isuzu/isuzu-ppt-template/`

Always use this template — read its `SKILL.md` before generating any PPTX for ISZE.
The template provides the Cover, Content, and Closing slide layouts.
The template file itself: `claude/Isuzu/isuzu-ppt-template/assets/template.pptx`

---

## Brand Colours

| Role | Hex | RGB |
|------|-----|-----|
| Isuzu Primary Red | `#CC0E1E` | (204, 14, 30) |
| Wave Highlight | `#DC606E` | (220, 96, 110) |
| Black / Body Text | `#1A1A1A` | (26, 26, 26) |
| Subtitle / Gray | `#5A5A5A` | (90, 90, 90) |
| Background | `#FFFFFF` | (255, 255, 255) |

**Never use off-brand colours.** No default blue, green, or orange in ISZE slides.

---

## Slide Dimensions

- **13.33" × 7.5"** (standard 16:9 widescreen)

---

## The Three Layouts

### Layout 0 — Cover Slide

Used for: first slide of every deck.

Elements:
- ISUZU logo (bold red "ISUZU" text, Arial Black, size 30) at top-left: x=0.38", y=0.22"
- Wave decoration (two overlapping ovals, light red + red)
- Red footer bar at bottom
- Title: x=0.45", y=2.55", w=7.5", h=1.9", size=40, bold, black
- Subtitle/date: x=0.45", y=5.30", w=5.0", h=0.45", size=16, gray

```python
build_cover(prs, title="ISZE Parts & Accessories\nSales Report", subtitle="March, 2026")
```

### Layout 1 — Content Slide

Used for: all data slides.

Elements:
- ISUZU logo (size 22) at bottom-left: x=0.28", y=6.80"
- Red footer bar: bottom of slide
- Slide title: x=0.28", y=0.22", w=12.77", h=0.72", size=30, bold, black
- Red accent line under title: x=0.28", y=1.00", w=12.77", h≈0
- **Safe content area**: x=0.28", y=1.15", w=12.77", h=5.50"

Place all charts, tables, and text within the safe content area.

```python
slide = build_content(prs, "Slide Title Here")
# Then add chart/table/textbox within: x=0.28, y=1.15, w=12.77, h=5.50
```

### Layout 2 — Closing Slide

Used for: final slide of every deck. No other content.

```python
build_closing(prs)
```

Renders: "Moving the World – for You" (grey, centered) + "ISUZU" (red, size 100, Arial Black, centered)

---

## Building with python-pptx

Always generate ISZE presentations programmatically using `python-pptx`. Do not use
openpyxl, ReportLab, or other libraries for PPTX generation.

**Standard imports and setup:**

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

SKILL_DIR = "/sessions/awesome-clever-archimedes/mnt/claude/Isuzu/isuzu-ppt-template"

RED       = RGBColor(0xCC, 0x0E, 0x1E)
LIGHT_RED = RGBColor(0xDC, 0x60, 0x6E)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
BLACK     = RGBColor(0x1A, 0x1A, 0x1A)
GRAY      = RGBColor(0x5A, 0x5A, 0x5A)

SW = Inches(13.33)
SH = Inches(7.5)

prs = Presentation(f"{SKILL_DIR}/assets/template.pptx")
# Clear template example slides:
while prs.slides:
    rId = prs.slides._sldIdLst[0].rId
    prs.part.drop_rel(rId)
    del prs.slides._sldIdLst[0]
```

Full helper functions are in `isuzu-ppt-template/SKILL.md`. Copy them into the
generation script: `set_white_bg`, `txt`, `rect`, `oval`, `add_logo`,
`add_footer_bar`, `add_wave`, `build_cover`, `build_content`, `build_closing`.

---

## Adding Charts

Charts go inside the content area on a Content slide:
- Position: x=0.28", y=1.15", w=12.77", h=5.50"
- Use `pptx.enum.chart.XL_CHART_TYPE` for type selection
- Preferred chart styles: LINE (trend over time), BAR/COLUMN (comparison), PIE/DONUT (composition)
- Chart series colours: primary = Isuzu Red (#CC0E1E), secondary = Gray (#888888)

```python
from pptx.chart.data import ChartData
from pptx.enum.chart import XL_CHART_TYPE

chart_data = ChartData()
chart_data.categories = ['FY2023', 'FY2024', 'FY2025', 'FY2026']
chart_data.add_series('VP Sales (€M)', (29.1, 30.2, 32.5, 32.3))

chart = slide.shapes.add_chart(
    XL_CHART_TYPE.LINE,
    Inches(0.28), Inches(1.15), Inches(12.77), Inches(5.50),
    chart_data
).chart
```

---

## Adding Tables

Use `slide.shapes.add_table(rows, cols, left, top, width, height)`.

Jerome's tables (e.g. MTD/YTD sales): see `isuzu-ppt-template/SKILL.md` §"Adding Tables"
for the standard PA Report table structure (3 rows × 7 cols, header row red background).

General table rules:
- Header row: Red background (#CC0E1E), white text, bold
- Data rows: alternating white / very light gray
- Numbers right-aligned; labels left-aligned
- Currency in EUR, two decimal places for prices, zero decimals for revenue in millions

---

## Typical ISZE Deck Structure

### Monthly PA Report
1. Cover: "ISZE Parts & Accessories Sales Report — [Month, Year]"
2. Content: "ISZE Sales Results – Parts & Accessories" (MTD/YTD table)
3. Content: "ISZE Total Parts Share by Category" (donut chart)
4. Content: "ISZE Customer Ranking" (map + table)
5. Content: "ISZE Fill Rate to DB" (line chart)
6. Content: "ISZE BO's to DB" (bar/combo chart)
7. Closing

### Team Meeting / Strategy Deck
1. Cover: "ISZE Sales Team Meeting [Year]"
2. Agenda slide (Content)
3. FY Performance vs Budget (Content: bar chart)
4. Key Projects Status (Content: table with RAG status)
5. ITUK / distributor performance (Content)
6. Action items / next steps (Content)
7. Closing

### Distributor / IML Briefing Deck
1. Cover
2. Context / background (Content)
3. Data / evidence slides (Content × n)
4. Proposed approach (Content)
5. Next steps and asks (Content)
6. Closing

---

## What Jerome Does NOT Want in Slides

- Walls of text (use 3–5 bullet points maximum per slide, or a chart instead)
- Default Office colours — only ISZE brand palette
- Generic clip art or Office icons
- Slides without a clear data or argument point
- "Title Slide" as the cover title — always use a real descriptive title
- Inconsistent font sizes or alignment across slides

---

## File Saving

Save the completed PPTX to:
`/sessions/awesome-clever-archimedes/mnt/claude/Isuzu/[filename].pptx`

Naming: `ISZE_[Topic]_[MonYYYY].pptx`
Example: `ISZE_TeamMeeting_Mar2026.pptx`
