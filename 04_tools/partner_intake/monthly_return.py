"""Monthly return for one distributor, as plain text or one HTML file.

The caller passes the euros in. This module does not read billing files.
It names one distributor, and it does not rank that distributor.

Warranty is its own line. When warranty_eur is null the text says
"warranty split unknown" and stock is left out. When stock_eur is present
the line says it is stock, not lost sales.
"""

from __future__ import annotations

import html
from pathlib import Path

_HEADER = (
    "Monthly return",
    "draft, for one distributor",
    "A person sends this.",
)


def build_return(
    distributor_name: str,
    period: str,
    own: dict,
    network_average: dict | None,
    *,
    network_n: int | None = None,
    decoy_name: str | None = None,
) -> str:
    """Plain-text monthly return. decoy_name is accepted and never printed."""
    _seal_decoy(decoy_name)
    lines = list(_HEADER)
    lines.append("")
    lines.extend(
        _body_lines(distributor_name, period, own, network_average, network_n)
    )
    return "\n".join(lines) + "\n"


def write_html(
    path: str | Path,
    distributor_name: str,
    period: str,
    own: dict,
    network_average: dict | None,
    *,
    network_n: int | None = None,
    decoy_name: str | None = None,
) -> None:
    """Write one self-contained HTML file at path. No launcher, no external file."""
    _seal_decoy(decoy_name)
    body = _body_lines(distributor_name, period, own, network_average, network_n)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(_html_page(body), encoding="utf-8", newline="\n")


def _seal_decoy(decoy_name: str | None) -> None:
    """Keep the unused name out of the return. A test passes it to prove that."""
    if decoy_name is not None and not isinstance(decoy_name, str):
        raise TypeError("decoy_name must be a string or None")


def _body_lines(
    distributor_name: str,
    period: str,
    own: dict,
    network_average: dict | None,
    network_n: int | None,
) -> list[str]:
    show_average = network_average is not None
    average = network_average or {}
    count = _checked_count(network_n) if show_average else None
    lines = [
        f"Distributor: {distributor_name}",
        f"Period: {period}",
        "",
    ]
    if show_average:
        if count is None:
            lines.append("Anonymous network average.")
        else:
            lines.append(
                f"Anonymous network average, across {count} distributors."
            )
        lines.append("")

    lines.append(
        _money_line("Billed", own.get("billed_eur"), average.get("billed_eur"), show_average)
    )
    lines.append(
        _warranty_line(
            own.get("warranty_eur"), average.get("warranty_eur"), show_average
        )
    )
    lines.append(
        _money_line(
            "Sales to dealer",
            own.get("sales_to_dealer_eur"),
            average.get("sales_to_dealer_eur"),
            show_average,
        )
    )
    # Stock is only meaningful once warranty is its own known figure.
    if own.get("warranty_eur") is not None:
        lines.append(
            _stock_line(own.get("stock_eur"), average.get("stock_eur"), show_average)
        )
    lines.append(
        _money_line(
            "Genuine parts, in euros",
            own.get("genuine_eur"),
            average.get("genuine_eur"),
            show_average,
        )
    )
    lines.append(
        _money_line(
            "BVP, in euros",
            own.get("bvp_eur"),
            average.get("bvp_eur"),
            show_average,
        )
    )
    lines.append(
        _money_line(
            "Maintenance parts, in euros",
            own.get("maintenance_eur"),
            average.get("maintenance_eur"),
            show_average,
        )
    )
    lines.append("")
    note = own.get("ids_note")
    if note:
        lines.append(f"IDS note: {note}")
    else:
        lines.append("IDS note: none supplied.")
    return lines


def _checked_count(network_n: int | None) -> int | None:
    if network_n is None:
        return None
    if isinstance(network_n, bool) or not isinstance(network_n, int):
        raise TypeError("network_n must be an int or None")
    return network_n


def _format_eur(value: int | float) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"euro value must be a number, got {type(value).__name__}")
    if isinstance(value, float) and not value.is_integer():
        return f"EUR {value:,.2f}"
    return f"EUR {int(value):,}"


def _money_line(
    label: str,
    own_value: int | float | None,
    average_value: int | float | None,
    show_average: bool,
) -> str:
    own_text = "not stated" if own_value is None else _format_eur(own_value)
    if not show_average:
        return f"{label}: {own_text}."
    average_text = (
        "not stated" if average_value is None else _format_eur(average_value)
    )
    return f"{label}: {own_text}. Anonymous network average: {average_text}."


def _warranty_line(
    own_value: int | float | None,
    average_value: int | float | None,
    show_average: bool,
) -> str:
    if own_value is None:
        return "Warranty: warranty split unknown."
    return _money_line("Warranty", own_value, average_value, show_average)


def _stock_line(
    own_value: int | float | None,
    average_value: int | float | None,
    show_average: bool,
) -> str:
    if own_value is None:
        return "Stock: not stated."
    base = _money_line("Stock", own_value, average_value, show_average)
    if base.endswith("."):
        base = base[:-1]
    return f"{base}. This is stock, not lost sales."


def _html_page(body_lines: list[str]) -> str:
    paragraphs: list[str] = []
    for line in body_lines:
        if line == "":
            continue
        kind = "note" if line.startswith("IDS note:") else "money"
        if line.startswith("Distributor:") or line.startswith("Period:"):
            kind = "who"
        if line.startswith("Anonymous network average"):
            kind = "who"
        paragraphs.append(f'<p class="{kind}">{html.escape(line)}</p>')
    body = "\n".join(paragraphs)
    title, draft, sender = _HEADER
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>
body {{
  margin: 0;
  background: #f7f4ee;
  color: #222;
  font-family: "Segoe UI", Calibri, sans-serif;
  line-height: 1.45;
}}
header {{
  background: #15233c;
  color: #f7f4ee;
  padding: 28px 40px 22px;
}}
header h1 {{
  font-family: Georgia, "Times New Roman", serif;
  font-size: 32px;
  font-weight: normal;
  margin: 0 0 6px;
  background: #15233c;
  color: #f7f4ee;
}}
header p {{
  margin: 0;
  background: #15233c;
  color: #f7f4ee;
}}
main {{
  background: #f7f4ee;
  color: #222;
  padding: 28px 40px 48px;
  max-width: 40rem;
}}
main p {{
  margin: 0 0 10px;
  background: #f7f4ee;
  color: #222;
}}
main p.money {{
  border-left: 4px solid #c0552d;
  padding-left: 12px;
}}
</style>
</head>
<body>
<header>
<h1>{html.escape(title)}</h1>
<p>{html.escape(draft)}</p>
<p>{html.escape(sender)}</p>
</header>
<main>
{body}
</main>
</body>
</html>
"""
