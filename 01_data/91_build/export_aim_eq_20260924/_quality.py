"""Quality check: how many parts inherit a system family because of the figure
they sit on, when the description says they are a small part of something else?

This does not change anything. It measures how big the figure-inheritance effect is.
"""
import re
import pandas as pd

CLASS = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\export_aim_eq_20260924\classified.csv"

c = pd.read_csv(CLASS, dtype=str)
c = c[c["aim_level_1"].fillna("") != ""].copy()
c["desc"] = c["Description"].fillna("").str.strip().str.upper()

# A small part of some other assembly.
SMALL = r"^(GASKET|NUT|BOLT|SCREW|WASHER|CLAMP|BRACKET|SEAL|O-RING|ORING|RING|PIN|CLIP|STUD|PLUG|CAP|COLLAR|SPRING|U-BOLT|HOSE|PIPE|TUBE|CUSHION|RUBBER|SHIM|SPACER|STAY|REINFORCEMENT|STIFFENER|HOOK|ADAPTER|PLATE|COVER|SUPPORT|PAD)"

small = c[c["desc"].str.match(SMALL, na=False)]
print(f"classified rows: {len(c)}")
print(f"rows whose description is a small/fastener part: {len(small)}")
print()
print("what those small parts were filed under (Level 2):")
print(small.groupby(["aim_level_1", "aim_level_2"]).size()
      .sort_values(ascending=False).head(25).to_string())
print()
print("rows whose label came from the EPC figure name alone:",
      int((c["aim_source_this_pass"] == "EPC figure name").sum()))
print("rows whose label came from a unanimous figure key   :",
      int((c["aim_source_this_pass"] == "figure key, unanimous on the master").sum()))
