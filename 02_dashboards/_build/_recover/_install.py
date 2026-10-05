"""Install the verified reconstruction as the workspace builder.

Copies build_db_leakage_review.reconstructed.py over
02_dashboards/_build/build_db_leakage_review.py, after checking the assembled
source compiles. Run only after _verify_payload.py reports an exact match.
"""
import pathlib
import py_compile
import shutil

HERE = pathlib.Path(__file__).resolve().parent
BUILD = HERE.parent
SRC = HERE / "build_db_leakage_review.reconstructed.py"
DST = BUILD / "build_db_leakage_review.py"

src = SRC.read_text(encoding="utf-8")
compile(src, str(DST), "exec")
shutil.copyfile(SRC, DST)
py_compile.compile(str(DST), doraise=True)
print("installed bytes:", DST.stat().st_size)
print("compiles OK")
