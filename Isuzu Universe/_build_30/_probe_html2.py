import re

h = open(r"_build_30\ISUZU_UNIVERSE_3_0.html", encoding="utf-8").read()
print("keep count:", h.count('<div class="keep">'))
print("chapter-start count:", h.count('class="chapter-start"'))
i = h.find("<h2>Chapter schedule</h2>")
print("--- 260 chars before the Chapter schedule heading ---")
print(h[i - 260:i])
print("--- 200 after the guide table ---")
j = h.find("</table>", i)
print(h[j:j + 220])
