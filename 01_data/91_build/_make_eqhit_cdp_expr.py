from pathlib import Path

b64 = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_eqhit_inject.b64").read_text(encoding="ascii").strip()
expr = "eval(atob(" + repr(b64) + "))"
Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_eqhit_cdp_expr.txt").write_text(expr, encoding="utf-8")
print("expr_len", len(expr))
