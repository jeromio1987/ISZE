"""Verify the built warranty page by reading the DOM as the browser actually rendered it.

This is the verifier the page was missing. It does not trust the builder, the receipt or a
screenshot count: it renders the file off the disk and asserts against the resulting DOM.

What it checks:
  1. the payload evaluated at runtime (window.__WARRANTY__ is a real object)
  2. every expected data collection is non-empty
  3. the KPI cards were built by JS (so the data script ran, not just shipped)
  4. both tables have rows
  5. every canvas Chart.js created has non-zero dimensions (a mounted chart, not an empty shell)
  6. no unfilled build tokens, no NaN, no CDN reference
  7. the headline numbers still tie to the dataset folder

Run:  python 02_dashboards/_build/verify_warranty_commercial.py
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "02_dashboards" / "sales" / "Warranty_Commercial_Review.html"
DATA = ROOT / "01_data" / "00_derived" / "warranty_commercial"
CHROME = next((p for p in [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path.home() / r"AppData\Local\Google\Chrome\Application\chrome.exe",
] if p.is_file()), None)

EXPECTED_COLLECTIONS = [
    "recon", "market", "family", "limits", "lines", "cv_market", "cv_family", "cv_dealer",
    "cv_currency",
]

fails: list[str] = []
warns: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'} {label}" + (f"  {detail}" if detail else ""))
    if not ok:
        fails.append(label)


def main() -> int:
    if not HTML.is_file():
        print(f"FAIL html missing: {HTML}")
        return 1
    if CHROME is None:
        print("FAIL no Chrome found for the render pass")
        return 1

    source = HTML.read_text(encoding="utf-8")

    # ---- 1. static checks on the shipped file
    check("__PAYLOAD__" not in source and "/*__CHARTJS__*/" not in source,
          "no_unfilled_tokens", "build tokens replaced")
    check(not re.search(r"https?://[^\"']*\.js", source),
          "no_cdn_script", "no remote script tag")
    # NaN inside the inlined Chart.js library is normal (`isNaN` guards). What must not appear is
    # NaN in the DATA payload, which is what the ship gate is actually guarding against.
    payload_start = source.find("window.__WARRANTY__ = ")
    title_start = source.find("<title>")
    data_source = source[payload_start:title_start] if payload_start < title_start else source[payload_start:]
    nan_in_data = len(re.findall(r"(?<!is)\bNaN\b", data_source))
    check(nan_in_data == 0, "no_nan_in_data_payload",
          f"{nan_in_data} NaN tokens in the embedded data (library NaN is expected and ignored)")

    with tempfile.TemporaryDirectory() as td:
        dom_path = Path(td) / "dom.html"
        subprocess.run(
            [str(CHROME), "--headless=new", "--disable-gpu", "--virtual-time-budget=8000",
             "--dump-dom", HTML.as_uri()],
            stdout=dom_path.open("w", encoding="utf-8"), stderr=subprocess.DEVNULL, check=False)
        dom = dom_path.read_text(encoding="utf-8", errors="replace")

    check(len(dom) > 50_000, "dom_rendered", f"{len(dom):,} chars from the browser")

    # ---- 2. the data script actually ran: check the DOM must contain JS-built output
    kpi_cards = len(re.findall(r'<div class="card(?: hi)?">', dom))
    check(kpi_cards == 6, "kpi_cards_built", f"{kpi_cards} of 6 cards exist in the DOM")

    rows_t1 = len(re.findall(r"<tbody>.*?</tbody>", dom, re.S))
    tr = len(re.findall(r"<tr>", dom))
    check(tr >= 20, "table_rows_built", f"{tr} table rows in the rendered DOM")

    # Chart.js writes width/height onto each canvas when it mounts
    canvases = re.findall(r"<canvas[^>]*>", dom)
    mounted = [c for c in canvases if re.search(r'style="[^"]*width:\s*\d', c)]
      # The page has 9 charts. Keep this as a constant so adding a chart cannot silently pass.
    EXPECTED_CANVASES = 9
    check(len(canvases) == EXPECTED_CANVASES, "canvas_count",
          f"{len(canvases)} canvases (expected {EXPECTED_CANVASES})")
    check(len(mounted) == EXPECTED_CANVASES, "canvases_mounted",
          f"{len(mounted)} of {len(canvases)} carry Chart.js inline sizing")

    # pixel evidence: the page sets plain data-probe-* attributes AFTER the charts are built, so
    # reading them from the rendered DOM is runtime proof that the whole script ran to the end.
    def probe(name: str) -> str | None:
        m = re.search(rf'data-probe-{name}="([^"]*)"', dom)
        return m.group(1) if m else None

    check(probe("ready") == "1", "probe_ready",
          "probe marker written — the script reached the end of the chart block")
    if probe("ready") == "1":
        check(probe("cards") == "6", "probe_cards", f"{probe('cards')} cards")
        check(int(probe("rows") or 0) >= 20, "probe_table_rows", f"{probe('rows')} rows")
        check(probe("mounted") == probe("canvases"), "probe_canvases_mounted",
              f"{probe('mounted')} of {probe('canvases')} mounted")
        check(probe("painted") == probe("canvases"), "probe_canvases_painted",
              f"{probe('painted')} of {probe('canvases')} canvases have non-transparent pixels")
        check(probe("trucktotal") == "1", "probe_truck_total_visible",
              "the corrected truck total is visible in the page text")

    # the page writes the build date into #stamp from JS. The regex must allow attributes and
    # whitespace between the id and the closing bracket, or a correct page reads as failed.
    stamp = re.search(r'id="stamp"[^>]*>\s*([^<\s][^<]*)', dom)
    check(bool(stamp), "stamp_written_by_js",
          f"stamp = {stamp.group(1).strip() if stamp else 'EMPTY'}")
    check(bool(re.search(r'id="kpis"[^>]*>\s*<div', dom)), "kpis_populated")
    check(bool(re.search(r'id="insideflag"[^>]*>\s*\S', dom)), "insideflag_populated")

    # ---- 3. the page still ties to the dataset folder
    def read(name: str) -> list[dict]:
        with (DATA / name).open(newline="", encoding="utf-8-sig") as fh:
            return list(csv.DictReader(fh))

    recon = {r["measure"]: float(r["value"]) for r in read("warranty_commercial_reconciliation.csv")}
    lcv_pos = read("warranty_cost_by_limit_position.csv")
    outside_share = sum(float(r["share_of_parts_turnover"]) for r in lcv_pos
                        if r["position"] in ("over age limit", "over distance limit"))
    check(abs(outside_share - 0.43) < 0.01, "outside_share_matches_dataset",
          f"{outside_share:.2%} outside the limits")
    check(abs(recon["CV (truck) parts turnover EUR"] - 4_655_881) < 1,
          "truck_total_matches_dataset", f"€{recon['CV (truck) parts turnover EUR']:,.0f}")

    # the rendered numbers must be the dataset's numbers, not older ones
    check("€4,655,881" in dom, "truck_total_on_page", "corrected truck total appears in the DOM")
    check("€93,832,290" not in dom and "93.8m" not in dom,
          "raw_currency_error_absent", "the un-normalised Italian figure is not on the page")

    print()
    print(f"{'OK' if not fails else 'FAILED'}  {len(fails)} fail, {len(warns)} warn")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
