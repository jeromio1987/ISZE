"""One-off: scan evaluation dates in incoming NL/DK/LUX IDS sheets."""
from __future__ import annotations

from pathlib import Path

import openpyxl

STAGE = Path(__file__).resolve().parent


def scan_dates(path: Path, max_rows: int = 50, max_cols: int = 14) -> list[tuple]:
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    hits: list[tuple] = []
    for sn in wb.sheetnames[:4]:
        ws = wb[sn]
        for i, row in enumerate(
            ws.iter_rows(min_row=1, max_row=max_rows, max_col=max_cols, values_only=True),
            1,
        ):
            for j, v in enumerate(row, 1):
                if v is None:
                    continue
                if hasattr(v, "year") and getattr(v, "year", 0) >= 2020:
                    hits.append((sn, i, j, repr(v)))
                    continue
                s = str(v).strip()
                low = s.lower()
                if any(
                    k in low
                    for k in (
                        "date",
                        "datum",
                        "évalu",
                        "evaluat",
                        "2024",
                        "2025",
                        "2026",
                        "jaar",
                    )
                ):
                    hits.append((sn, i, j, s[:140]))
    wb.close()
    return hits


def dump_cover(path: Path, rows: int = 25, cols: int = 6) -> None:
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb[wb.sheetnames[0]]
    print(f"\n## {path.name}  sheet={ws.title}")
    for i, row in enumerate(
        ws.iter_rows(min_row=1, max_row=rows, max_col=cols, values_only=True), 1
    ):
        vals = ["" if v is None else str(v)[:60] for v in row]
        if any(vals):
            print(f"  R{i}: {vals}")
    print("  date-hits:")
    for h in scan_dates(path)[:25]:
        print(f"    {h}")
    wb.close()


def main() -> None:
    lux = list((STAGE / "LUX").rglob("*.xlsx"))
    nl = sorted((STAGE / "NL").rglob("*.xlsx"))
    dk = sorted((STAGE / "Denmark").rglob("*.xlsx"))
    print("counts NL", len(nl), "DK", len(dk), "LUX", len(lux))

    for p in lux:
        dump_cover(p)

    for p in nl[:1]:
        dump_cover(p)

    summary = [p for p in dk if "grafiek" in p.name.lower()]
    dealers = [p for p in dk if "grafiek" not in p.name.lower()]
    for p in summary + dealers[:3] + dealers[-1:]:
        dump_cover(p)

    # Collect unique date-like values from all DK dealers (col scan)
    print("\n## DK dealer evaluation-date harvest")
    for p in dealers:
        hits = [h for h in scan_dates(p) if "datetime" in h[3] or "/202" in h[3] or "-202" in h[3]]
        print(f"  {p.name}: {hits[:8]}")


if __name__ == "__main__":
    main()
