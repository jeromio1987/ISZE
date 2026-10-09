import os

D = r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case"
CMD = os.path.join(D, "OPEN_Kickback_Japan_Pack.cmd")
body = '@echo off\r\nstart "" "%~dp0ISZE_Kickback_Japan_Pack_20261007.pptx"\r\n'
with open(CMD, "wb") as f:
    f.write(body.encode("ascii"))
data = open(CMD, "rb").read()
print("wrote", CMD, len(data), "bytes")
print("CRLF count:", data.count(b"\r\n"), "bare LF:", data.count(b"\n") - data.count(b"\r\n"))
