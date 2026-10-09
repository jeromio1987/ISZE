# -*- coding: utf-8 -*-
"""Loop tick 5: record remaining return gap; mark loop stopped."""
from pathlib import Path
from datetime import datetime, timezone

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy")
md = OUT / "ISZE_MD_TRACK_BUSINESS_PLAN_2026-10-08.md"
log = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_md_track_loop_log_20261008.txt")

MARK = "Loop tick 5 — remaining gap + stop (8 Oct 2026)"

BLOCK = f"""

## {MARK}

**Still unknown (honest):** Duncan's deal file does not carry a won / lost / unknown outcome field, so we still cannot print a measured win rate or a euro “brought back” figure. Do not invent one for Japan. The next discipline after competitor price on the line is outcome + subsequent order reference.

**Loop status:** auto-harden every 20 minutes is **stopped** after this tick (diminishing returns: MOA, margin layers, speak line, motion film, floor/stretch ask are already in the pack). Say **continue loop** if you want it restarted.

"""


def main() -> None:
    t = md.read_text(encoding="utf-8")
    if MARK not in t:
        md.write_text(t.rstrip() + BLOCK, encoding="utf-8")
        print("md patched")
    else:
        print("md already marked")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with log.open("a", encoding="utf-8") as f:
        f.write(f"{stamp} tick5 STOP — remaining gap: no won/lost field; loop killed\n")
    print("log appended")


if __name__ == "__main__":
    main()
