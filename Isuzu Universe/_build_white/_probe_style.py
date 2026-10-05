# -*- coding: utf-8 -*-
"""Read-only: report the theme palette and fonts inside the AIM style-reference deck."""
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
P = r"C:\Users\jerom\Desktop\claude\ISZE\Pricing revision\ISZE_AIM_Management_20_Slides_2026-09-21.pptx"
z = zipfile.ZipFile(P)
for n in z.namelist():
    if "theme" in n and n.endswith(".xml"):
        x = z.read(n).decode("utf-8", errors="replace")
        cols = re.findall(r'<a:(dk1|lt1|dk2|lt2|accent[1-6]|hlink|folHlink)>\s*<a:srgbClr val="([0-9A-Fa-f]{6})"', x)
        if cols:
            print("==", n)
            for k, v in cols:
                print("    %-9s #%s" % (k, v))
        for k, v in re.findall(r'<a:(majorFont|minorFont)>\s*<a:latin typeface="([^"]*)"', x):
            print("    font %-9s %s" % (k, v))
