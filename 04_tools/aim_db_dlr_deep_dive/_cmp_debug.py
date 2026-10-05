"""Debug: why does PORTUGAL show 41 months of sales-to-dealer presence?"""
import sys
sys.path.insert(0, r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\aim_db_dlr_deep_dive")
import build_aim_comparison as B

dims = B.load_dimensions()
so, recon = B.load_sellout(["PORTUGAL"])
print("sellout month values:", sorted(so["month"].unique()))
print("sellout us total:", so["us"].sum())
bi, doc = B.load_billing(dims, ["PORTUGAL"])
facts, olds, dropped, so2, bi2, so_out, bi_out = B.build_facts(so, bi, dims, ["PORTUGAL"])
print("facts cols:", list(facts.columns))
sold = facts[facts["us"] > 0]
print("months with sold>0:", sorted(sold["month"].unique()))
print("sold units total:", facts["us"].sum())
