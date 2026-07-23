"""
ISZE — IAM price drift trend view.

refresh_and_check_drift.py's own console output only compares each run to the
single immediately-prior run. This script reads the cumulative
_snapshots/drift_history.csv it appends to every run and renders a per-key
price trend across all runs collected so far — so a slow multi-run creep
(each step under DRIFT_THRESHOLD, but the sum over 5 runs isn't) is visible,
not just single-step jumps.

Self-contained HTML, no CDN — inline SVG sparklines, no JS chart library.

Usage:
    python build_drift_trend_view.py
"""
from __future__ import annotations

import html
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).parent
DRIFT_HISTORY_CSV = SCRIPT_DIR / "_snapshots" / "drift_history.csv"
OUT_PATH = SCRIPT_DIR / "_html_previews" / "isze_iam_drift_trend.html"
MIN_RUNS_FOR_TREND = 2


def _sparkline_svg(prices: list[float], width: int = 220, height: int = 40) -> str:
    if len(prices) < 2:
        return "<span class='muted'>not enough runs yet</span>"
    lo, hi = min(prices), max(prices)
    span = (hi - lo) or 1.0
    n = len(prices)
    pts = []
    for i, p in enumerate(prices):
        x = (i / (n - 1)) * (width - 8) + 4
        y = height - 4 - ((p - lo) / span) * (height - 8)
        pts.append(f"{x:.1f},{y:.1f}")
    path = " ".join(pts)
    last_x, last_y = pts[-1].split(",")
    up = prices[-1] > prices[0]
    color = "#c0392b" if up else "#1a7a3c"
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<polyline points="{path}" fill="none" stroke="{color}" stroke-width="1.6"/>'
        f'<circle cx="{last_x}" cy="{last_y}" r="2.5" fill="{color}"/>'
        f"</svg>"
    )


def main():
    if not DRIFT_HISTORY_CSV.exists():
        print(f"No drift history yet at {DRIFT_HISTORY_CSV} — run refresh_and_check_drift.py first "
              f"(at least {MIN_RUNS_FOR_TREND} runs needed for a trend).")
        body = (
            "<p>No drift history yet. Run <code>refresh_and_check_drift.py</code> at least "
            f"{MIN_RUNS_FOR_TREND} times (e.g. via the scheduled weekly task) to populate a trend.</p>"
        )
        rows_count = 0
        n_keys = 0
    else:
        df = pd.read_csv(DRIFT_HISTORY_CSV, parse_dates=False)
        df["new_price_eur"] = pd.to_numeric(df["new_price_eur"], errors="coerce")
        df = df.dropna(subset=["new_price_eur"]).sort_values("run_date")
        rows_count = len(df)

        parts = []
        groups = list(df.groupby(["source", "key"]))
        n_keys = len(groups)
        # Rank by total observed swing (last vs first) so the most-moved keys sort to the top.
        ranked = sorted(
            groups,
            key=lambda kv: abs(kv[1]["new_price_eur"].iloc[-1] - kv[1]["new_price_eur"].iloc[0]),
            reverse=True,
        )
        for (source, key), g in ranked:
            prices = g["new_price_eur"].tolist()
            n_runs = len(prices)
            first, last = prices[0], prices[-1]
            change = (last - first) / first if first else 0.0
            parts.append(f"""
            <tr>
              <td>{html.escape(str(source))}</td>
              <td>{html.escape(str(key))}</td>
              <td class="num">{n_runs}</td>
              <td class="num">&euro;{first:.2f}</td>
              <td class="num">&euro;{last:.2f}</td>
              <td class="num">{change:+.0%}</td>
              <td>{_sparkline_svg(prices)}</td>
            </tr>""")
        body = f"""<table>
  <thead><tr>
    <th>Source</th><th>Key (PN or category)</th><th>Runs</th>
    <th>First price</th><th>Last price</th><th>Total change</th><th>Trend</th>
  </tr></thead>
  <tbody>{"".join(parts)}</tbody>
</table>"""

    out_html = f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>ISZE IAM Price Drift Trend</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Arial, sans-serif; margin: 24px; color: #1a1a1a; background: #fff; }}
  .banner {{ background: #eef2ff; border: 1px solid #4a5cc7; padding: 12px 16px; border-radius: 6px; margin-bottom: 20px; font-size: 14px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
  th, td {{ border: 1px solid #ddd; padding: 8px 10px; text-align: left; vertical-align: middle; }}
  th {{ background: #f5f5f5; }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .muted {{ color: #999; }}
</style></head>
<body>
<div class="banner">
  IAM scraped price context only &mdash; not PMS actuals. {rows_count} price points across {n_keys} (source, key)
  combinations since history logging started.
</div>
<h1>IAM price drift &mdash; trend across all runs</h1>
{body}
</body></html>"""

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(out_html, encoding="utf-8")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
