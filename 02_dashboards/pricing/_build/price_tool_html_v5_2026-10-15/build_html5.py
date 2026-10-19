from pathlib import Path
H = Path(__file__).parent
OUT = H.parents[1] / "ISZE_Price_Revision_Simulator_v5_2026-10-15.html"
t = (H / "template5.html").read_text(encoding="utf-8")
p = (H / "payload5.json").read_text(encoding="utf-8").replace("</", "<\\/")
t = t.replace("/*PAYLOAD*/", p).replace("/*MODEL*/", (H / "model5.js").read_text(encoding="utf-8")).replace("/*XL*/", (H / "xl.js").read_text(encoding="utf-8")).replace("/*UI*/", (H / "ui5.js").read_text(encoding="utf-8"))
OUT.write_text(t, encoding="utf-8")
(OUT.parent / "OPEN_Price_Revision_Simulator_v5.cmd").write_bytes(b'@echo off\r\nstart "" "%~dp0ISZE_Price_Revision_Simulator_v5_2026-10-15.html"\r\n')
print(OUT, len(t))