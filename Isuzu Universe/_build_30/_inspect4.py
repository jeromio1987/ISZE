import sys
sys.stdout.reconfigure(encoding="utf-8")
h = open("ISUZU_UNIVERSE_3_0_SHOWCASE_2026-09-23.html", encoding="utf-8").read()
for pat in ["[22,23,24,25,26,27,28,29,30,78]", "n>=35&&n<=41", "n>=42&&n<=54",
            "[8].includes(n)", "n===4||n===10", "n>=5&&n<=7",
            "Read the 80-page", "80-page", "/ 80"]:
    print("%-34s %d" % (pat, h.count(pat)))
