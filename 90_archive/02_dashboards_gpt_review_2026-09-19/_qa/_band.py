from PIL import Image
qa = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\_qa"
img = Image.open(qa + r"\AFTER_pathfix_20260919.png")
img.crop((0, 240, 1440, 760)).save(qa + r"\AFTER_band1.png")
img.crop((0, 740, 1440, 1200)).save(qa + r"\AFTER_band2.png")
print("ok")
