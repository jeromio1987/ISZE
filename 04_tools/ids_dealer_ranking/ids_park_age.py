"""Park ageing proxy from UIO.xlsx for IDS DB posture."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

UIO_XLSX = (
    Path(__file__).resolve().parents[2]
    / "03_analytics"
    / "Isuzu"
    / "prism"
    / "data"
    / "UIO.xlsx"
)

UIO_NAME_BY_COUNTRY: dict[str, list[str]] = {
    "BE": ["IBX"],
    "NL": ["IBX"],
    "PETROS": ["Petros Petropoulos"],
    "RSA": ["RSA"],
    "IUK": ["IUK"],
    "ITUK": ["ITUK"],
    "ISRAEL": ["UMI"],
    "MALTA": ["GasanZammit"],
    "CYPRUS": ["Loutsios & Sons", "Loutsios"],
    "ROMANIA": ["Isuzu Rom Auto"],
    "PORTUGAL": ["Imotors"],
    "HUNGARY": ["AutoWallis"],
    # No Poland-specific UIO row in UIO.xlsx — leave unmapped (unknown) rather than IBX.
    "POLAND": [],
    # MIDI CodDivs share one MIDI Europe park in UIO.xlsx (not split FR/IT/ES/CH).
    "MIDI_FR": ["MIDI Europe"],
    "MIDI_IT": ["MIDI Europe"],
    "MIDI_ES": ["MIDI Europe"],
    "MIDI_CH": ["MIDI Europe"],
    "MIDI": ["MIDI Europe"],
}


def load_park_age_proxy(path: Path | None = None) -> dict[str, dict[str, Any]]:
    path = path or UIO_XLSX
    if not path.is_file():
        return {}

    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb["1.UIO Overview"]
    hdr = list(next(ws.iter_rows(min_row=6, max_row=6, values_only=True)))
    year_idx: dict[int, int] = {}
    for i, c in enumerate(hdr):
        try:
            y = int(float(c))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        if 1985 <= y <= 2035:
            year_idx[y] = i
    if not year_idx:
        wb.close()
        return {}
    latest = max(year_idx)
    agg: dict[str, dict[int, float]] = defaultdict(lambda: defaultdict(float))
    for r in ws.iter_rows(min_row=7, values_only=True):
        if not r or len(r) < 6 or r[5] is None:
            continue
        db = str(r[5]).strip()
        for y, i in year_idx.items():
            if i < len(r) and isinstance(r[i], (int, float)):
                agg[db][y] += float(r[i])
    wb.close()

    out: dict[str, dict[str, Any]] = {}
    for db, series in agg.items():
        u_now = float(series.get(latest) or 0)
        if u_now <= 0:
            continue
        u5 = float(series.get(latest - 5) or 0)
        u10 = float(series.get(latest - 10) or 0)
        ch5 = (u_now - u5) / u_now
        ch10 = (u_now - u10) / u_now if u10 else None
        if ch5 <= -0.10:
            ageing, risk = "Shrinking / likely older", "high"
        elif ch5 < 0:
            ageing, risk = "Slightly shrinking", "elevated"
        elif ch5 < 0.15:
            ageing, risk = "Stable / mixed", "medium"
        else:
            ageing, risk = "Growing / likely younger", "low"
        out[db] = {
            "uio_name": db,
            "uio_year": latest,
            "uio_units": u_now,
            "park_change_5y_pct": ch5,
            "park_change_10y_pct": ch10,
            "ageing_label": ageing,
            "ageing_risk": risk,
        }
    return out


def attach_park_age(join_rows: list[dict[str, Any]], park: dict[str, dict[str, Any]]) -> None:
    by_low = {k.casefold(): v for k, v in park.items()}
    for row in join_rows:
        names = UIO_NAME_BY_COUNTRY.get(row["ids_country"], [])
        matched = None
        for n in names:
            matched = by_low.get(n.casefold())
            if matched:
                break
            for k, v in by_low.items():
                if n.casefold() in k or k.startswith(n.casefold()[:6]):
                    matched = v
                    break
            if matched:
                break
        if not matched:
            row["park_change_5y_pct"] = None
            row["park_change_10y_pct"] = None
            row["uio_units_park"] = None
            row["ageing_label"] = "No UIO age proxy"
            row["ageing_risk"] = "unknown"
            continue
        row["park_change_5y_pct"] = matched["park_change_5y_pct"]
        row["park_change_10y_pct"] = matched.get("park_change_10y_pct")
        row["uio_units_park"] = matched["uio_units"]
        row["ageing_label"] = matched["ageing_label"]
        row["ageing_risk"] = matched["ageing_risk"]
        row["uio_park_year"] = matched["uio_year"]
        row["uio_park_name"] = matched["uio_name"]
