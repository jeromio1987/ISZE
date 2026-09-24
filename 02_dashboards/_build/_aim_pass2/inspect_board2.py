"""Print the raw structure of the board around the change-log tables, ASCII-safe."""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = r"00_docs\agent\DELEGATOR_BOARD.md"
t = open(P, "rb").read().decode("utf-8")
lines = t.split("\n")

for i in range(100, min(136, len(lines))):
    raw = lines[i]
    safe = raw.encode("ascii", "replace").decode("ascii")
    kind = "ROW" if raw.strip().startswith("|") else ("---" if not raw.strip() else "txt")
    print(f"{i + 1:>4} [{kind}] {safe[:170]}")
