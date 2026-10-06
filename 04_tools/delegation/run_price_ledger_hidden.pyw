"""Start run_price_ledger_weekly.bat with no console window and hand back its exit code.

Task ISZE_PriceLedger_Weekly runs this with pythonw.exe. Run as a plain .bat under "run only
when user is logged on", the job opens a terminal window on the desktop; closing that window
kills the run with exit 0xC000013A (-1073741510) and leaves only "^C" in the log (5 Oct 2026).
A console created with CREATE_NO_WINDOW has no window to close.
"""
import subprocess
import sys
from pathlib import Path

BAT = Path(__file__).with_name("run_price_ledger_weekly.bat")

sys.exit(subprocess.call(["cmd.exe", "/c", str(BAT)], creationflags=subprocess.CREATE_NO_WINDOW))
