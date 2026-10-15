"""Write sample harvest from browser session dump (status-only)."""
from __future__ import annotations

import json
from pathlib import Path

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
OUT = DER / "_eq_hit_harvest_sample_20261007.json"

# Captured from live EQ session 2026-10-07 (ui_status scraper).
HITS = [
    {"pn": "1059230520", "eq_status": "FOUND", "eq_total": None, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "", "method": "ui_status", "applied": "N"},
    {"pn": "108058700", "eq_status": "FOUND", "eq_total": None, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "", "method": "ui_status", "applied": "N"},
    {"pn": "108064800", "eq_status": "FOUND", "eq_total": None, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "", "method": "ui_status", "applied": "N"},
    {"pn": "108108600", "eq_status": "FOUND", "eq_total": None, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "", "method": "ui_status", "applied": "N"},
    {"pn": "108564800", "eq_status": "FOUND", "eq_total": None, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "", "method": "ui_status", "applied": "N"},
    {"pn": "1090000070", "eq_status": "FOUND", "eq_total": 186, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10511 - CXG/CXH 86.0 - 91.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090001950", "eq_status": "FOUND", "eq_total": 4, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10907 - 2003- FXZ(THAI) 03.0 - 03.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090002310", "eq_status": "FOUND", "eq_total": 13, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "51060 - 1978.5-1989 UM4BA1 DOM/EXP 78.5 - 89.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090002340", "eq_status": "FOUND", "eq_total": 3, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10510 - CXK/CXL/CXM/CXZ 86.0 - 88.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090002950", "eq_status": "FOUND", "eq_total": 12, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10551 - CVS/CXW/CYW 87.0 - 99.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090002960", "eq_status": "FOUND", "eq_total": 11, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10661 - 900-950 CVR EXP FINAL 90.0 - 95.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090003260", "eq_status": "FOUND", "eq_total": 169, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10510 - CXK/CXL/CXM/CXZ 86.0 - 88.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090003340", "eq_status": "FOUND", "eq_total": None, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10511 - CXG/CXH 86.0 - 91.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090003850", "eq_status": "FOUND", "eq_total": 4, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10510 - CXK/CXL/CXM/CXZ 86.0 - 88.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090004890", "eq_status": "FOUND", "eq_total": 277, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10551 - CVS/CXW/CYW 87.0 - 99.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090005360", "eq_status": "FOUND", "eq_total": 333, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10600 - CXK/CXL/CXM 89.0 - 91.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090005700", "eq_status": "FOUND", "eq_total": 102, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "12057 - 2022 FRR/FSR(AUST/NZ)SPACECAB 22.0 - 24.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090005830", "eq_status": "FOUND", "eq_total": 161, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10551 - CVS/CXW/CYW 87.0 - 99.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090006100", "eq_status": "FOUND", "eq_total": 273, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "11113 - 080-CXY(AUSTRALIA)JNLT05/EURO5 08.0 -", "method": "ui_status", "applied": "N"},
    {"pn": "1090007410", "eq_status": "FOUND", "eq_total": 5, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10755 - FRR/FSR 98.0 - 05.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090007800", "eq_status": "FOUND", "eq_total": 89, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "12057 - 2022 FRR/FSR(AUST/NZ)SPACECAB 22.0 - 24.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090007860", "eq_status": "FOUND", "eq_total": 360, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10953 - 040-070 CXH/CYH(NEW ZEALAND) 04.0 -", "method": "ui_status", "applied": "N"},
    {"pn": "1090007870", "eq_status": "FOUND", "eq_total": 75, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "11102 - 2008- FRR(RHD)SPACECAB EURO2/4 08.0 - 12.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090007871", "eq_status": "FOUND", "eq_total": 366, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "11395 - 2011- FRR(RHD)EURO1 11.0 -", "method": "ui_status", "applied": "N"},
    {"pn": "1090007890", "eq_status": "FOUND", "eq_total": 369, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10953 - 040-070 CXH/CYH(NEW ZEALAND) 04.0 -", "method": "ui_status", "applied": "N"},
    {"pn": "1090090580", "eq_status": "FOUND", "eq_total": 62, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10511 - CXG/CXH 86.0 - 91.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090090620", "eq_status": "FOUND", "eq_total": 10, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10783 - FRS-J/FSS-J 99.0 - 04.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090090650", "eq_status": "FOUND", "eq_total": 172, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10510 - CXK/CXL/CXM/CXZ 86.0 - 88.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090090660", "eq_status": "FOUND", "eq_total": 477, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10511 - CXG/CXH 86.0 - 91.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090091640", "eq_status": "FOUND", "eq_total": 234, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10930 - 030-060 CXH(RHD)381 FINAL 03.0 - 06.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090091900", "eq_status": "FOUND", "eq_total": 392, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10953 - 040-070 CXH/CYH(NEW ZEALAND) 04.0 -", "method": "ui_status", "applied": "N"},
    {"pn": "1090091910", "eq_status": "FOUND", "eq_total": 188, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "11395 - 2011- FRR(RHD)EURO1 11.0 -", "method": "ui_status", "applied": "N"},
    {"pn": "1090201530", "eq_status": "FOUND", "eq_total": 31, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10788 - FRS/FSS 99.0 - 04.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090300140", "eq_status": "FOUND", "eq_total": 2, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10502 - FRD/FRR 85.5 - 89.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090300300", "eq_status": "FOUND", "eq_total": None, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "", "method": "ui_status", "applied": "N"},
    {"pn": "1090300301", "eq_status": "FOUND", "eq_total": 2, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10502 - FRD/FRR 85.5 - 89.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090300302", "eq_status": "FOUND", "eq_total": 10, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10739 - 960-990 FSR(FRAME BUS)LHD EXP 96.0 -", "method": "ui_status", "applied": "N"},
    {"pn": "1090300320", "eq_status": "FOUND", "eq_total": 3, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10502 - FRD/FRR 85.5 - 89.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090300390", "eq_status": "FOUND", "eq_total": 2, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10502 - FRD/FRR 85.5 - 89.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090300940", "eq_status": "FOUND", "eq_total": 548, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "11756 - 2016-CYH(RHD)EURO6 16.0 -", "method": "ui_status", "applied": "N"},
    {"pn": "1090400620", "eq_status": "FOUND", "eq_total": 4, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10510 - CXK/CXL/CXM/CXZ 86.0 - 88.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090400621", "eq_status": "FOUND", "eq_total": 14, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10600 - CXK/CXL/CXM 89.0 - 91.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090400720", "eq_status": "FOUND", "eq_total": 26, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10510 - CXK/CXL/CXM/CXZ 86.0 - 88.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090400921", "eq_status": "FOUND", "eq_total": 16, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10639 - CXK/CXL 92.0 - 94.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090400951", "eq_status": "FOUND", "eq_total": 19, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10675 - ZXR/ZYZ/ZZZ 85.5 -", "method": "ui_status", "applied": "N"},
    {"pn": "1090420211", "eq_status": "FOUND", "eq_total": 2, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10502 - FRD/FRR 85.5 - 89.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090420290", "eq_status": "FOUND", "eq_total": 2, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10502 - FRD/FRR 85.5 - 89.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090420291", "eq_status": "FOUND", "eq_total": 11, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10643 - FRR 92.0 - 93.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090420292", "eq_status": "FOUND", "eq_total": 23, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10685 - NRR 94.5 - 98.0", "method": "ui_status", "applied": "N"},
    {"pn": "1090440700", "eq_status": "FOUND", "eq_total": 15, "found": True, "eq_fig_name": "", "eq_part_name": "", "eq_catalog": "10639 - CXK/CXL 92.0 - 94.0", "method": "ui_status", "applied": "N"},
]


def main() -> int:
    assert len(HITS) == 50, len(HITS)
    OUT.write_text(json.dumps(HITS, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT} n={len(HITS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
