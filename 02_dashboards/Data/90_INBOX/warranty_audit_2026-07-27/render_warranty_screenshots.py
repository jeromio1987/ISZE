"""Build faithful Excel-like HTML replicas + PNG screenshots from Warranty_CV_2025.xlsx."""
from __future__ import annotations

import json
import re
from pathlib import Path

import openpyxl

try:
    from playwright.sync_api import sync_playwright

    HAS_PW = True
except ImportError:
    HAS_PW = False

CV = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\06_Warranty\Warranty_CV_2025.xlsx")
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\warranty_audit_2026-07-27")
OUT.mkdir(parents=True, exist_ok=True)


def parse_price(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s or "#N/A" in s.upper() or s.upper() == "N/A":
        return None
    s = s.replace("\xa0", "").replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def fmt_eur(x: float | None) -> str:
    if x is None:
        return ""
    return f"€{x:,.2f}"


def fmt_price_cell(raw) -> str:
    if raw is None:
        return ""
    return str(raw)


def load_sheet4_rows():
    wb = openpyxl.load_workbook(CV, data_only=True)
    ws = wb["Sheet4"]
    rows = []
    for r in range(1, ws.max_row + 1):
        a, b, c = ws.cell(r, 1).value, ws.cell(r, 2).value, ws.cell(r, 3).value
        if a is None and b is None and c is None:
            continue
        rows.append({"r": r, "a": a, "b": b, "c": c})
    wb.close()
    return rows


def is_header_label(a) -> bool:
    if a is None:
        return False
    s = str(a).strip()
    if s.lower().startswith("grand") or s.lower() == "row labels":
        return True
    if re.fullmatch(r"\d{6,}", s):
        return False
    # numeric 0 / 0000000000 displayed as 0
    if s in ("0", "0.0") or re.fullmatch(r"0+", s):
        return False  # treat as part number row (dummy PARTNBR)
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9 _\-]{0,40}", s):
        return True
    return False


def analyze(rows):
    """Two views: (A) naive '0-as-country' matching the documented €314K, (B) correct country attribution."""
    # View A — match prior audit (0 as bucket)
    cur = None
    buckets_a: dict[str, float] = {}
    sections_a = []
    for row in rows:
        a, b, c = row["a"], row["b"], row["c"]
        s = str(a).strip() if a is not None else ""
        if s.lower() == "row labels":
            continue
        if s.lower().startswith("grand"):
            continue
        if not re.match(r"^\d{8,}", s) and s not in ("",):
            # includes "0"
            cur = s
            buckets_a.setdefault(cur, 0.0)
            sections_a.append({"row": row["r"], "label": cur, "count": b, "cell_c": c})
            continue
        if cur is None:
            continue
        price = parse_price(c)
        try:
            qty = float(b) if b is not None else 0.0
        except (TypeError, ValueError):
            qty = 0.0
        if price is not None:
            buckets_a[cur] += qty * price

    # View B — correct: country headers only; 0/0000000000 is a part row
    cur = None
    buckets_b: dict[str, float] = {}
    zero_part_rows = []
    country_parts: dict[str, list] = {}
    for row in rows:
        a, b, c = row["a"], row["b"], row["c"]
        if a is None:
            continue
        if is_header_label(a):
            s = str(a).strip()
            if s.lower() in ("row labels",) or s.lower().startswith("grand"):
                cur = None
                continue
            cur = s
            buckets_b.setdefault(cur, 0.0)
            country_parts.setdefault(cur, [])
            continue
        if cur is None:
            continue
        s = str(a).strip()
        price = parse_price(c)
        try:
            qty = float(b) if b is not None else 0.0
        except (TypeError, ValueError):
            qty = 0.0
        is_zero_part = s in ("0", "0.0") or re.fullmatch(r"0+", s)
        country_parts[cur].append(
            {
                "row": row["r"],
                "part": a,
                "qty": qty,
                "price_raw": c,
                "price": price,
                "is_zero_part": is_zero_part,
            }
        )
        if is_zero_part:
            zero_part_rows.append({"country": cur, "row": row["r"], "count": qty, "price_raw": c})
        elif price is not None:
            buckets_b[cur] += qty * price

    zero_a = round(buckets_a.get("0", 0.0), 2)
    return {
        "buckets_a": {k: round(v, 2) for k, v in sorted(buckets_a.items(), key=lambda x: -x[1])},
        "buckets_b": {k: round(v, 2) for k, v in sorted(buckets_b.items(), key=lambda x: -x[1])},
        "zero_bucket_a_eur": zero_a,
        "zero_part_rows": zero_part_rows,
        "sections_a": sections_a,
        "country_parts": country_parts,
    }


EXCEL_CSS = """
:root {
  --grid: #d0d0d0;
  --header-bg: #4472C4;
  --header-fg: #fff;
  --country-bg: #D6DCE4;
  --zero-bg: #FCE4D6;
  --na-bg: #FFC7CE;
  --na-fg: #9C0006;
  --sum-bg: #E2EFDA;
  --title: #1F4E79;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Calibri, "Segoe UI", Arial, sans-serif;
  background: #f3f3f3;
  color: #222;
}
.workbook {
  max-width: 980px;
  margin: 16px auto 24px;
  background: #fff;
  border: 1px solid #bbb;
  box-shadow: 0 2px 10px rgba(0,0,0,.12);
}
.tabs {
  display: flex;
  gap: 0;
  background: #e7e6e6;
  border-bottom: 1px solid #bbb;
  padding: 6px 8px 0;
  font-size: 12px;
}
.tab {
  padding: 6px 14px;
  border: 1px solid #bbb;
  border-bottom: none;
  background: #f2f2f2;
  margin-right: 2px;
  border-radius: 4px 4px 0 0;
  color: #555;
}
.tab.active {
  background: #fff;
  color: #000;
  font-weight: 600;
  border-bottom: 1px solid #fff;
  margin-bottom: -1px;
}
.sheet-bar {
  padding: 10px 16px 6px;
  border-bottom: 1px solid #eee;
}
.sheet-bar h1 {
  margin: 0;
  font-size: 16px;
  color: var(--title);
  font-weight: 700;
}
.sheet-bar .meta {
  margin-top: 4px;
  font-size: 12px;
  color: #666;
}
.callout {
  margin: 10px 16px;
  padding: 10px 12px;
  border-left: 4px solid #C65911;
  background: #FFF2CC;
  font-size: 13px;
  line-height: 1.35;
}
.callout strong { color: #C65911; }
.grid-wrap { padding: 0 16px 16px; overflow-x: auto; }
table.excel {
  border-collapse: collapse;
  width: 100%;
  font-size: 12.5px;
  table-layout: fixed;
}
table.excel th, table.excel td {
  border: 1px solid var(--grid);
  padding: 4px 8px;
  vertical-align: middle;
}
table.excel th {
  background: var(--header-bg);
  color: var(--header-fg);
  font-weight: 600;
  text-align: left;
}
col.c-row { width: 48px; }
col.c-a { width: 160px; }
col.c-b { width: 120px; }
col.c-c { width: 140px; }
col.c-note { width: 220px; }
.rownum { color: #888; text-align: right; background: #f7f7f7; font-size: 11px; }
.country { background: var(--country-bg); font-weight: 700; }
.zero-row { background: var(--zero-bg); font-weight: 700; }
.na { background: var(--na-bg); color: var(--na-fg); font-weight: 600; }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.sum-row { background: var(--sum-bg); font-weight: 700; }
.muted { color: #777; font-size: 11px; }
.kpi-row {
  display: flex;
  gap: 10px;
  padding: 0 16px 12px;
  flex-wrap: wrap;
}
.kpi {
  flex: 1;
  min-width: 140px;
  border: 1px solid #ddd;
  padding: 8px 10px;
  background: #fafafa;
}
.kpi .lbl { font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: .03em; }
.kpi .val { font-size: 18px; font-weight: 700; color: #1F4E79; margin-top: 2px; }
.kpi.warn .val { color: #C65911; }
.kpi.bad .val { color: #C00000; }
.footer {
  padding: 8px 16px 14px;
  font-size: 11px;
  color: #777;
  border-top: 1px solid #eee;
}
.hl { outline: 2px solid #C65911; outline-offset: -2px; }
"""


def html_sheet4_zero(rows, analysis) -> str:
    """Replica focusing on country totals + the three 0 buckets that sum to €314K (doc view)."""
    # Build display rows: country headers + zero part rows + a few sample parts under each zero
    want_countries = {"IRELAND", "PORTUGAL", "UTI", "ITUK", "ISD", "MALTA", "GREECE", "CYPRUS"}
    display = []
    # Summary table from view A
    summary_order = ["ITUK", "0", "ISD", "MALTA", "GREECE", "CYPRUS", "IRELAND", "PORTUGAL", "UTI"]
    buckets = analysis["buckets_a"]

    # Extract key visual slices from Sheet4
    # 1) IRELAND block rows 9-21
    # 2) PORTUGAL block rows 421-430 (header + 0 + samples)
    # 3) UTI block rows 494-505
    slices = []
    for start, end, title in (
        (9, 21, "IRELAND-blok (Sheet4 r9–21)"),
        (421, 435, "PORTUGAL-blok (Sheet4 r421–435)"),
        (494, 510, "UTI-blok met grote '0'-nest (Sheet4 r494–510)"),
    ):
        block = [r for r in rows if start <= r["r"] <= end]
        slices.append((title, block))

    # Also grand total
    gt = next((r for r in rows if str(r["a"]).lower().startswith("grand")), None)

    body_tables = []
    # Summary totals as if pivot country rollup (doc/audit view)
    sum_rows = []
    for lab in summary_order:
        if lab not in buckets and lab != "0":
            # still show Ireland/Portugal as 0 in naive country-header-only sense
            pass
        val = buckets.get(lab, 0.0)
        cls = "zero-row" if lab == "0" else ""
        if lab == "0":
            note = "← gedocumenteerde orphan-bucket (€314.213,97)"
        elif lab in ("IRELAND", "PORTUGAL") and val == 0:
            note = "header toont €0 / claims zitten onder geneste '0'"
        else:
            note = ""
        sum_rows.append(
            f"<tr class='{cls}'><td class='rownum'></td><td><b>{lab}</b></td>"
            f"<td class='num'>{fmt_eur(val)}</td><td class='muted'>{note}</td></tr>"
        )
    sum_rows.append(
        f"<tr class='sum-row'><td class='rownum'></td><td>Som van alle '0'-nesten</td>"
        f"<td class='num'>{fmt_eur(analysis['zero_bucket_a_eur'])}</td>"
        f"<td>3× PARTNBR 0 / 0000000000-secties (IE+PT+UTI)</td></tr>"
    )

    body_tables.append(
        f"""
        <h2 style="font-size:14px;margin:12px 16px 6px;color:#1F4E79">Country roll-up (zelfde rekensom als audit €314.213,97)</h2>
        <div class="grid-wrap">
        <table class="excel">
          <colgroup><col class="c-row"><col class="c-a"><col class="c-c"><col class="c-note"></colgroup>
          <thead><tr><th>#</th><th>Row Labels (land / bucket)</th><th>Σ qty × ISZE EUR</th><th>Opmerking</th></tr></thead>
          <tbody>{''.join(sum_rows)}</tbody>
        </table>
        </div>
        """
    )

    for title, block in slices:
        trs = []
        for r in block:
            a, b, c = r["a"], r["b"], r["c"]
            s = str(a).strip() if a is not None else ""
            classes = []
            note = ""
            if is_header_label(a):
                classes.append("country")
            if s in ("0", "0.0") or (isinstance(a, (int, float)) and float(a) == 0):
                classes.append("zero-row")
                classes.append("hl")
                note = "PARTNBR 0000000000 → Excel toont '0'"
            c_cls = "num"
            c_txt = fmt_price_cell(c)
            if c is not None and "#N/A" in str(c).upper():
                c_cls += " na"
                note = note or "VLOOKUP prijs = #N/A"
            cls = " ".join(classes)
            trs.append(
                f"<tr class='{cls}'>"
                f"<td class='rownum'>{r['r']}</td>"
                f"<td>{a if a is not None else ''}</td>"
                f"<td class='num'>{b if b is not None else ''}</td>"
                f"<td class='{c_cls}'>{c_txt}</td>"
                f"<td class='muted'>{note}</td></tr>"
            )
        body_tables.append(
            f"""
            <h2 style="font-size:14px;margin:12px 16px 6px;color:#1F4E79">{title}</h2>
            <div class="grid-wrap">
            <table class="excel">
              <colgroup><col class="c-row"><col class="c-a"><col class="c-b"><col class="c-c"><col class="c-note"></colgroup>
              <thead><tr><th>Excel rij</th><th>A — Row Labels</th><th>B — Count of PARTNBR</th><th>C — ISZE EUR price</th><th></th></tr></thead>
              <tbody>{''.join(trs)}</tbody>
            </table>
            </div>
            """
        )

    gt_txt = f"Grand Total count = {gt['b']}" if gt else ""
    return f"""<!DOCTYPE html>
<html lang="nl"><head><meta charset="utf-8"><title>Sheet4 — 0-bucket €314K</title>
<style>{EXCEL_CSS}</style></head><body>
<div class="workbook" id="capture">
  <div class="tabs">
    <div class="tab">Sheet1</div><div class="tab">Sheet3</div>
    <div class="tab active">Sheet4</div>
    <div class="tab">UTI</div><div class="tab">ITUK</div>
  </div>
  <div class="sheet-bar">
    <h1>Warranty_CV_2025.xlsx → Sheet4</h1>
    <div class="meta">Bronbestand: 01_data\\06_Warranty\\Warranty_CV_2025.xlsx · pivot Row Labels / Count of PARTNBR / ISZE EUR · {gt_txt}</div>
  </div>
  <div class="callout">
    <strong>Wat je ziet:</strong> Sheet4 toont onder IRELAND, PORTUGAL en UTI een rij <b>0</b>
    (in Sheet3 staat die als PARTNBR <b>0000000000</b>). Als je alle geprijsde regels ná die drie ‘0’-rijen
    optelt (audit-methode), kom je op <strong>{fmt_eur(analysis['zero_bucket_a_eur'])}</strong> —
    de gedocumenteerde orphan-bucket. IRELAND/PORTUGAL-headers zelf blijven €0 / #N/A.
  </div>
  <div class="kpi-row">
    <div class="kpi warn"><div class="lbl">'0' bucket (audit)</div><div class="val">{fmt_eur(analysis['zero_bucket_a_eur'])}</div></div>
    <div class="kpi"><div class="lbl">ITUK (Sheet4)</div><div class="val">{fmt_eur(buckets.get('ITUK',0))}</div></div>
    <div class="kpi bad"><div class="lbl">IRELAND header</div><div class="val">{fmt_eur(buckets.get('IRELAND',0))}</div></div>
    <div class="kpi bad"><div class="lbl">PORTUGAL header</div><div class="val">{fmt_eur(buckets.get('PORTUGAL',0))}</div></div>
  </div>
  {''.join(body_tables)}
  <div class="footer">Getrouwe cel-replica uit openpyxl data_only · bedragen = Count × prijs in kolom C (zoals eerdere audit).</div>
</div>
</body></html>"""


def html_ie_pt_gaps(pricing: dict) -> str:
    ie = pricing["DATA WITHOUT MIDI:IRELAND"]
    pt = pricing["DATA WITHOUT MIDI:PORTUGAL"]

    def sample_table(title, samples, kind):
        trs = []
        for s in samples:
            price_cell = (
                f"<td class='num'>{fmt_eur(s['price'])}</td>"
                if kind == "priced"
                else "<td class='na'>geen ISZE EUR in ITUK/UTI price-map</td>"
            )
            trs.append(
                "<tr>"
                f"<td class='rownum'>{s['row']}</td>"
                f"<td>{s.get('dst') or ''}</td>"
                f"<td>{s['part']}</td>"
                f"<td class='num'>{s['qty']}</td>"
                f"{price_cell}"
                f"<td class='muted'>BILLYMD={s.get('billy','')} PARTAMT1={s.get('partamt','')}</td>"
                "</tr>"
            )
        return f"""
        <h2 style="font-size:14px;margin:12px 16px 6px;color:#1F4E79">{title}</h2>
        <div class="grid-wrap">
        <table class="excel">
          <thead><tr><th>Rij (Sheet1 / DATA WITHOUT MIDI)</th><th>DST_Name</th><th>PARTNBR</th><th>QTY1</th><th>ISZE EUR (ITUK/UTI map)</th><th></th></tr></thead>
          <tbody>{''.join(trs) if trs else '<tr><td colspan=6>geen samples</td></tr>'}</tbody>
        </table>
        </div>"""

    # Sheet4 Ireland/Portugal header evidence
    sheet4_ie_pt = f"""
    <h2 style="font-size:14px;margin:12px 16px 6px;color:#1F4E79">Sheet4 — IRELAND &amp; PORTUGAL headers (claims bestaan, €-totaal leeg/#N/A)</h2>
    <div class="grid-wrap">
    <table class="excel">
      <thead><tr><th>Excel rij</th><th>A</th><th>B Count</th><th>C prijs</th><th>Interpretatie</th></tr></thead>
      <tbody>
        <tr class="country"><td class="rownum">9</td><td>IRELAND</td><td class="num">17</td><td></td><td>17 claim-regels — geen landstotaal in C</td></tr>
        <tr class="zero-row hl"><td class="rownum">10</td><td>0</td><td class="num">2</td><td></td><td>dummy PARTNBR 0000000000</td></tr>
        <tr class="country"><td class="rownum">421</td><td>PORTUGAL</td><td class="num">139</td><td class="na">#N/A</td><td>139 claim-regels — header prijs #N/A</td></tr>
        <tr class="zero-row hl"><td class="rownum">422</td><td>0</td><td class="num">25</td><td class="na">#N/A</td><td>dummy PARTNBR + #N/A</td></tr>
      </tbody>
    </table>
    </div>
    """

    cov_ie = ie["coverage_pct"]
    cov_pt = pt["coverage_pct"]
    # Doc said 82%/52% — our cell coverage on CY2025 part cells is 93.3%/63.2%.
    # Also compute piece-qty coverage for comparison.
    note_cov = (
        f"Cel-dekking (unieke claim-partcellen CY2025, price-map ITUK+UTI): "
        f"IE {cov_ie}% · PT {cov_pt}%. "
        f"Doc (Warranty_CY2025_by_DB.md) noemde 82%/52% — zelfde richting, andere telbasis. "
        f"Geprijsde ondergrens CV: IE {fmt_eur(ie['value_priced_eur'])} · PT {fmt_eur(pt['value_priced_eur'])}."
    )

    return f"""<!DOCTYPE html>
<html lang="nl"><head><meta charset="utf-8"><title>IE/PT CV price gaps</title>
<style>{EXCEL_CSS}</style></head><body>
<div class="workbook" id="capture">
  <div class="tabs">
    <div class="tab">Sheet1</div><div class="tab active">DATA WITHOUT MIDI</div>
    <div class="tab">Sheet4</div><div class="tab">ITUK</div><div class="tab">UTI</div>
  </div>
  <div class="sheet-bar">
    <h1>Warranty_CV_2025.xlsx — Ireland / Portugal CV incomplete pricing</h1>
    <div class="meta">Niet: ontbrekende claims. Wel: ontbrekende ISZE EUR prijzen op truck-warranty PARTNBR’s via ITUK/UTI price-map.</div>
  </div>
  <div class="callout">
    <strong>Wat je ziet:</strong> claims voor IRELAND (17) en PORTUGAL (139) staan wél in het bestand.
    Sheet4 toont €0 / #N/A op de land-header. De CV-waarde in GPS (€3.908* / €28.836*) is een
    <em>lower bound</em> — alleen parts die in de ITUK/UTI-prijskaart zitten. {note_cov}
  </div>
  <div class="kpi-row">
    <div class="kpi"><div class="lbl">Ireland CY2025 claims</div><div class="val">{ie['cy2025_rows']}</div></div>
    <div class="kpi warn"><div class="lbl">IE price-map dekking</div><div class="val">{cov_ie}%</div></div>
    <div class="kpi"><div class="lbl">IE CV geprijsd (lower bound)</div><div class="val">{fmt_eur(ie['value_priced_eur'])}</div></div>
    <div class="kpi"><div class="lbl">Portugal CY2025 claims</div><div class="val">{pt['cy2025_rows']}</div></div>
    <div class="kpi warn"><div class="lbl">PT price-map dekking</div><div class="val">{cov_pt}%</div></div>
    <div class="kpi"><div class="lbl">PT CV geprijsd (lower bound)</div><div class="val">{fmt_eur(pt['value_priced_eur'])}</div></div>
  </div>
  {sheet4_ie_pt}
  {sample_table(f"PORTUGAL — sample parts ZONDER ISZE EUR prijs ({pt['part_cells'] - pt['priced_cells']} van {pt['part_cells']} cellen)", pt['samples_missing'], 'missing')}
  {sample_table(f"IRELAND — sample parts ZONDER ISZE EUR prijs ({ie['part_cells'] - ie['priced_cells']} van {ie['part_cells']} cellen)", ie['samples_missing'], 'missing')}
  {sample_table("PORTUGAL — sample parts mét prijs (ter vergelijking)", pt['samples_priced'], 'priced')}
  <div class="footer">Bron: Warranty_CV_2025.xlsx · Sheet1 / DATA WITHOUT MIDI gefilterd CTY_Name + BILLYMD 2025 · prijs uit tabs ITUK+UTI.</div>
</div>
</body></html>"""


def screenshot_html(html_path: Path, png_path: Path, width: int = 1100):
    if HAS_PW:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900}, device_scale_factor=2)
            page.goto(html_path.as_uri())
            page.wait_for_timeout(400)
            el = page.locator("#capture")
            el.screenshot(path=str(png_path), type="png")
            browser.close()
        return "playwright"

    # Fallback: matplotlib table render is weaker; try selenium or imgkit — else write note
    try:
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_agg import FigureCanvasAgg

        # minimal fallback message image
        fig, ax = plt.subplots(figsize=(12, 8), dpi=150)
        ax.axis("off")
        ax.text(0.5, 0.5, f"Open HTML and screenshot manually:\n{html_path}", ha="center", va="center")
        fig.savefig(png_path, bbox_inches="tight")
        plt.close(fig)
        return "matplotlib-fallback"
    except Exception as e:
        raise RuntimeError(f"No screenshot backend: {e}") from e


def main():
    rows = load_sheet4_rows()
    analysis = analyze(rows)
    pricing = json.loads((OUT / "_ie_pt_pricing.json").read_text(encoding="utf-8"))

    html1 = OUT / "sheet4_zero_bucket_314k.html"
    html2 = OUT / "ireland_portugal_cv_price_gaps.html"
    html1.write_text(html_sheet4_zero(rows, analysis), encoding="utf-8")
    html2.write_text(html_ie_pt_gaps(pricing), encoding="utf-8")
    print("Wrote", html1)
    print("Wrote", html2)
    print("zero_bucket_a_eur", analysis["zero_bucket_a_eur"])
    print("buckets_a", analysis["buckets_a"])
    print("buckets_b (correct country)", analysis["buckets_b"])
    print("zero_part_rows", analysis["zero_part_rows"])

    png1 = OUT / "sheet4_zero_bucket_314k.png"
    png2 = OUT / "ireland_portugal_cv_price_gaps.png"
    m1 = screenshot_html(html1, png1)
    m2 = screenshot_html(html2, png2)
    print("PNG", png1, "via", m1)
    print("PNG", png2, "via", m2)

    meta = {
        "pngs": [str(png1), str(png2)],
        "htmls": [str(html1), str(html2)],
        "zero_bucket_eur": analysis["zero_bucket_a_eur"],
        "buckets_a": analysis["buckets_a"],
        "buckets_b_correct": analysis["buckets_b"],
        "ie_coverage_pct": pricing["DATA WITHOUT MIDI:IRELAND"]["coverage_pct"],
        "pt_coverage_pct": pricing["DATA WITHOUT MIDI:PORTUGAL"]["coverage_pct"],
        "ie_value": pricing["DATA WITHOUT MIDI:IRELAND"]["value_priced_eur"],
        "pt_value": pricing["DATA WITHOUT MIDI:PORTUGAL"]["value_priced_eur"],
    }
    (OUT / "_screenshot_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
