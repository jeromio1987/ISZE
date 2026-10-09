# -*- coding: utf-8 -*-
"""Headless Chrome full-page screenshots of the study HTML, cut into slices for reading. Offline proxy: a CDN blank would show."""
import os, subprocess, tempfile
import numpy as np
from PIL import Image
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
HTML = r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy\DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.html"
QA = r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy\_qa\other_dbs"
os.makedirs(QA, exist_ok=True)
for f in os.listdir(QA):
    os.remove(os.path.join(QA, f))
def shot(name, w, h):
    out = os.path.join(QA, name + ".png"); prof = tempfile.mkdtemp(prefix="chrome_qa_")
    url = "file:///" + HTML.replace("\\", "/").replace(" ", "%20")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars", "--virtual-time-budget=9000",
                    "--user-data-dir=" + prof, "--proxy-server=127.0.0.1:9", "--screenshot=" + out, "--window-size=%d,%d" % (w, h), url],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out
taken = []
for name, w, h, sl in (("desktop", 1360, 6600, 1050),):
    o = shot("full_" + name, w, h); im = Image.open(o); a = np.array(im.convert("RGB")); bg = a[-1, 5]
    rows = np.where((np.abs(a.astype(int) - bg.astype(int)).sum(axis=2) > 30).any(axis=1))[0]; H = int(rows.max()) + 40
    print(name, im.size, "content height", H)
    for i, y in enumerate(range(0, H, sl)):
        p = os.path.join(QA, "%s%02d.png" % (name[0], i + 1)); im.crop((0, y, w, min(y + sl, H))).save(p); taken.append(p)
print(len(taken)); print("\n".join(taken))
