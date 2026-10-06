"""Start one .bat or .cmd with no console window and hand back its exit code.

Scheduled tasks run this with pythonw.exe: run_hidden.pyw <path to .bat or .cmd>. Started directly,
a .bat opens a console window on the desktop, and closing that window kills the run with exit
0xC000013A (-1073741510), as happened to ISZE_PriceLedger_Weekly on 28 Sep and 5 Oct 2026.
A console created with CREATE_NO_WINDOW has no window to close. Exit codes: 64 wrong arguments,
66 target file missing, otherwise the exit code of the target.
"""
import subprocess
import sys
from pathlib import Path

if len(sys.argv) != 2:
    sys.exit(64)
target = Path(sys.argv[1]).resolve()
if not target.is_file():
    sys.exit(66)
sys.exit(subprocess.call(["cmd.exe", "/c", str(target)], cwd=str(target.parent), creationflags=subprocess.CREATE_NO_WINDOW))
