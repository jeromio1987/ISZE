src = open(r"01_Strategy\ISUZU_UNIVERSE_3_0_2026-09-23.md", encoding="utf-8").read()
i = src.find("Two consequences follow")
print(repr(src[i:i + 700]))
