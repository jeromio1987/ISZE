"""Write the internal partner-intake trial monitor next to this file.

The page is a made-up trial. It never prints company euros. If feed_status.py
is missing or does not return the three trial codes, the fixture below is used.
"""

from __future__ import annotations

import html
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "Partner_Intake_Monitor.html"

CODES = ("DEMO-A", "DEMO-B", "DEMO-C")
STATUSES = ("no file yet", "accepted", "not accepted")

FIXTURE: list[dict] = [
    {
        "distributor": "DEMO-A",
        "latest_period": "2026-09",
        "status": "accepted",
        "accepted_months_in_a_row": 3,
        "last_receipt_outcome": "Accepted. The file was kept.",
    },
    {
        "distributor": "DEMO-B",
        "latest_period": "2026-09",
        "status": "not accepted",
        "accepted_months_in_a_row": 0,
        "last_receipt_outcome": "Not accepted. Remove the price column and resend.",
    },
    {
        "distributor": "DEMO-C",
        "latest_period": "—",
        "status": "no file yet",
        "accepted_months_in_a_row": 0,
        "last_receipt_outcome": "No file yet, so there is no receipt.",
    },
]


def _feed_status_path() -> Path | None:
    for path in (HERE.parent / "feed_status.py", HERE / "feed_status.py"):
        if path.is_file():
            return path
    return None


def _as_trial_rows(raw: object) -> list[dict] | None:
    if not isinstance(raw, list) or len(raw) != 3:
        return None
    by_code: dict[str, dict] = {}
    for item in raw:
        if not isinstance(item, dict):
            return None
        code = str(item.get("distributor", "")).strip()
        status = str(item.get("status", "")).strip()
        if code not in CODES or status not in STATUSES or code in by_code:
            return None
        try:
            streak = int(item["accepted_months_in_a_row"])
        except (KeyError, TypeError, ValueError):
            return None
        if streak < 0:
            return None
        period = str(item.get("latest_period", "")).strip() or "—"
        outcome = str(item.get("last_receipt_outcome", "")).strip()
        if not outcome:
            return None
        by_code[code] = {
            "distributor": code,
            "latest_period": period,
            "status": status,
            "accepted_months_in_a_row": streak,
            "last_receipt_outcome": outcome,
        }
    if set(by_code) != set(CODES):
        return None
    return [by_code[code] for code in CODES]


def load_rows() -> list[dict]:
    path = _feed_status_path()
    if path is None:
        return FIXTURE
    try:
        spec = importlib.util.spec_from_file_location("_partner_feed_status", path)
        if spec is None or spec.loader is None:
            return FIXTURE
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        getter = getattr(module, "trial_rows", None) or getattr(module, "rows", None)
        if not callable(getter):
            return FIXTURE
        cleaned = _as_trial_rows(getter())
        return cleaned if cleaned is not None else FIXTURE
    except Exception:
        return FIXTURE


def _row_html(row: dict) -> str:
    status = row["status"]
    kind = {"accepted": "accepted", "not accepted": "not-accepted", "no file yet": "no-file"}[status]
    values = [
        row["distributor"],
        row["latest_period"],
        status,
        str(row["accepted_months_in_a_row"]),
        row["last_receipt_outcome"],
    ]
    cells = []
    for index, value in enumerate(values):
        extra = f' class="status {kind}"' if index == 2 else ""
        cells.append(f"<td{extra}>{html.escape(value)}</td>")
    return "<tr>" + "".join(cells) + "</tr>"


def render(rows: list[dict]) -> str:
    body = "\n".join(_row_html(row) for row in rows)
    payload = json.dumps(rows, ensure_ascii=False).replace("<", "\\u003c")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Which trial feeds have an accepted file?</title>
<style>
  :root {{
    --navy: #15233c;
    --terracotta: #c0552d;
    --paper: #f7f4ee;
    --ink: #222;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--paper);
    color: var(--ink);
    font-family: "Segoe UI", system-ui, sans-serif;
    line-height: 1.45;
  }}
  header {{
    background: var(--navy);
    color: var(--paper);
    padding: 28px 40px 22px;
  }}
  h1 {{
    font-family: Georgia, "Times New Roman", serif;
    font-weight: normal;
    font-size: 32px;
    line-height: 1.2;
    margin: 0 0 8px;
    color: var(--paper);
  }}
  header p {{
    margin: 0;
    color: var(--paper);
    max-width: 40rem;
  }}
  .banner {{
    margin: 24px 40px 0;
    padding: 12px 16px;
    background: #f3e6df;
    color: var(--ink);
    border-left: 4px solid var(--terracotta);
  }}
  table {{
    width: calc(100% - 80px);
    margin: 20px 40px 40px;
    border-collapse: collapse;
    background: var(--paper);
  }}
  th {{
    background: var(--navy);
    color: var(--paper);
    text-align: left;
    font-weight: 600;
    padding: 10px 12px;
  }}
  td {{
    background: var(--paper);
    color: var(--ink);
    padding: 10px 12px;
    border-bottom: 1px solid #e4dfd6;
    vertical-align: top;
  }}
  td.status {{ font-weight: 600; }}
  td.status.accepted {{ color: var(--navy); }}
  td.status.not-accepted {{ color: var(--terracotta); }}
  td.status.no-file {{ color: var(--ink); }}
</style>
</head>
<body>
<header>
  <h1>Which trial feeds have an accepted file?</h1>
  <p>Internal trial. One row per made-up distributor code. File acceptance only.</p>
</header>
<div class="banner">made-up rows, not live feeds</div>
<table>
  <thead>
    <tr>
      <th>Distributor</th>
      <th>Latest period</th>
      <th>Status</th>
      <th>Accepted months in a row</th>
      <th>Last receipt outcome</th>
    </tr>
  </thead>
  <tbody>
{body}
  </tbody>
</table>
<script type="application/json" id="payload">{payload}</script>
</body>
</html>
"""


def main() -> None:
    rows = load_rows()
    OUT.write_text(render(rows), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
