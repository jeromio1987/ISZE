"""Build EQ-HIT CDP inject payload (one-shot helper)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS_SRC = ROOT / "09_meetings/IBX_Sales_Review_2026/epc_body/PASTE_IN_SNAPON_CONSOLE.js"
OUT = ROOT / "01_data/00_derived/_eqhit_inject.js"

PNS = [
    "8982120690",
    "5876100771",
    "8982551391",
    "8981649171",
    "5876100920",
    "8978293170",
    "8973319320",
    "5878320440",
    "8982447940",
    "8982169210",
    "8982169220",
    "8982831940",
    "8970388314",
    "5876100910",
    "5876101040",
    "8980400932",
    "8981596930",
    "5876150170",
    "8981941190",
    "8975425400",
    "5876101570",
    "8980374810",
    "1876102860",
    "5876150240",
]

META = {
    "8982120690": "clutch_disc",
    "5876100771": "clutch_disc",
    "8982551391": "clutch_disc",
    "8981649171": "clutch_disc",
    "5876100920": "clutch_disc",
    "8978293170": "clutch_disc",
    "8973319320": "brake_shoe",
    "5878320440": "brake_shoe",
    "8982447940": "brake_pad",
    "8982169210": "brake_pad",
    "8982169220": "brake_pad",
    "8982831940": "clutch_pressure_plate",
    "8970388314": "clutch_pressure_plate",
    "5876100910": "clutch_pressure_plate",
    "5876101040": "clutch_pressure_plate",
    "8980400932": "clutch_pressure_plate",
    "8981596930": "fuel_filter",
    "5876150170": "fuel_filter",
    "8981941190": "fuel_filter",
    "8975425400": "fuel_filter",
    "5876101570": "fuel_filter",
    "8980374810": "fuel_filter",
    "1876102860": "fuel_filter",
    "5876150240": "fuel_filter",
}


def main() -> None:
    js = JS_SRC.read_text(encoding="utf-8")
    cut = js.find("// === IBX Body")
    if cut > 0:
        js = js[:cut]
    boot = (
        f"window.__EQHIT_META = {json.dumps(META)};\n"
        f"window.__EQHIT_PNS = {json.dumps(PNS)};\n"
        "window.__allResults = [];\n"
    )
    OUT.write_text(
        boot + "\n" + js + '\nconsole.log("EQHIT inject ready", window.__EQHIT_PNS.length);\n',
        encoding="utf-8",
    )
    print(f"wrote {OUT} bytes={OUT.stat().st_size} pns={len(PNS)}")


if __name__ == "__main__":
    main()
