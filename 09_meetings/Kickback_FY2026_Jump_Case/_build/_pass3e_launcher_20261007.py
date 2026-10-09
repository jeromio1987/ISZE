import re, zipfile, pathlib
P = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case")
z = zipfile.ZipFile(P / "ISZE_Kickback_Management_Revised_v2_2026-10-07.pptx")
n = [x for x in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", x)]
print("slide parts:", len(n))
ct = z.read("[Content_Types].xml").decode("utf-8")
print("missing from content types:", [x for x in n if "/" + x not in ct])
cmd = P / "OPEN_Kickback_Management_Revised_v2.cmd"
body = '@echo off\r\nstart "" "%~dp0ISZE_Kickback_Management_Revised_v2_2026-10-07.pptx"\r\n'
cmd.write_bytes(body.encode("ascii"))
print("launcher written:", cmd, len(body), "bytes")
raw = cmd.read_bytes()
print("CRLF count:", raw.count(b"\r\n"), "lone LF:", raw.count(b"\n") - raw.count(b"\r\n"))
