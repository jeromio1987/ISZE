from pathlib import Path
H = Path(__file__).parent
OUT = H.parents[1] / "ISZE_Price_Revision_Simulator_v2_2026-10-15.html"
t = (H / "template2.html").read_text(encoding="utf-8")
p = (H / "payload2.json").read_text(encoding="utf-8").replace("</", "<\\/")
m = (H / "model2.js").read_text(encoding="utf-8")
u = (H / "ui2.js").read_text(encoding="utf-8")
t = t.replace("/*PAYLOAD*/", p).replace("/*MODEL*/", m).replace("/*UI*/", u)
OUT.write_text(t, encoding="utf-8")
(OUT.parent / "OPEN_Price_Revision_Simulator_v2.cmd").write_bytes(b'@echo off\r\nstart "" "%~dp0ISZE_Price_Revision_Simulator_v2_2026-10-15.html"\r\n')
print(OUT, len(t))