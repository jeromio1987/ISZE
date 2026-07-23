"""Extract distributor UIO rows from canonical workbook → uio_2026.json."""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import openpyxl

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
UIO_XLSX = ROOT / "06_uio" / "_CURRENT" / "ISUZU_UIO_Overview_2026.xlsx"
OUT_JSON = ROOT / "01_data" / "91_build" / "uio_2026.json"


def extract_uio(xlsx: Path) -> list[dict]:
    wb = openpyxl.load_workbook(xlsx, data_only=True, read_only=True)
    ws = wb["1.UIO Overview"]
    all_rows = list(ws.iter_rows(values_only=True))
    hdr_i = next(i for i, r in enumerate(all_rows) if r[0] is not None and "Ctry" in str(r[0]))
    hdr = all_rows[hdr_i]
    ycols = {}
    for j, h in enumerate(hdr):
        m = re.match(r"^\s*(\d{4})[EF]?\s*$", str(h or ""))
        if m and 2024 <= int(m.group(1)) <= 2028:
            ycols[int(m.group(1))] = j
    agg: dict[tuple[str, str, str], dict[int, float]] = defaultdict(lambda: defaultdict(float))
    for r in all_rows[hdr_i + 1 :]:
        if r[1] is None or r[5] is None:
            continue
        key = (str(r[1]).strip(), str(r[5]).strip(), str(r[3] or "").strip())
        for y, j in ycols.items():
            if isinstance(r[j], (int, float)):
                agg[key][y] += r[j]
    wb.close()
    return [
        {"country": k[0], "dist": k[1], "mtype": k[2], **{str(y): round(v, 1) for y, v in yv.items()}}
        for k, yv in sorted(agg.items())
    ]


def main() -> None:
    out = extract_uio(UIO_XLSX)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=0), encoding="utf-8")
    print(f"wrote {OUT_JSON} from {UIO_XLSX}")
    uti = {y: int(round(sum(r[str(y)] for r in out if r.get("dist") == "UTI" and str(y) in r))) for y in range(2024, 2028)}
    print("UTI totals:", uti)


if __name__ == "__main__":
    main()
