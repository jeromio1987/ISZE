from PIL import Image
qa = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\_qa"
img = Image.open(qa + r"\AFTER_fullpage.png")
w,h = img.size
print("size", w, h)
# slice into readable bands
for i,(y0,y1) in enumerate([(1150,1750),(1750,2350),(2350,2950),(2950,3550),(3550,4150),(4150,len(range(h)))][:5]):
    img.crop((0,y0,w,min(y1,h))).save(qa + rf"\FP_{i}.png")
print("wrote FP_0..FP_4")
