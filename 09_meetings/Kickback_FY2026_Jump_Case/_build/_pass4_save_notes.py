# -*- coding: utf-8 -*-
"""Preserve the pass-3 receipt notes before the writer resets them."""
import json, pathlib, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case")
R = P / "ISZE_Kickback_Management_Revised_v2_2026-10-07.SHIP_RECEIPT.json"
d = json.loads(R.read_text(encoding="utf-8"))
(P / "_build" / "_receipt_notes_pass3.txt").write_text(d.get("notes", ""), encoding="utf-8")
print("saved pass-3 notes:", len(d.get("notes", "")), "chars")
