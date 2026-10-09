from pathlib import Path

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case\OPEN_Kickback_Figures_Audit.cmd")
lines = [
    "@echo off",
    'start "" "%~dp0ISZE_Kickback_Figures_Audit_20261007.pptx"',
]
data = ("\r\n".join(lines) + "\r\n").encode("ascii")
p.write_bytes(data)
raw = p.read_bytes()
print("bytes:", len(raw))
print("CRLF count:", raw.count(b"\r\n"))
print("bare LF count:", raw.count(b"\n") - raw.count(b"\r\n"))
print(repr(raw))
