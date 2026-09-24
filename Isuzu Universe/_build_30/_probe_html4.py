h = open(r"_build_30\ISUZU_UNIVERSE_3_0.html", encoding="utf-8").read()
i = h.find("4.2 The hurdle")
j = h.find("4.4 What campaign")
print(h[i - 300:j])
