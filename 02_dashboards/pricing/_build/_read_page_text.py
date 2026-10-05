"""Read the visible prose of a page, with embedded JSON payloads replaced by a marker."""
import html
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")
s = re.sub(r'<script[^>]*type="application/json"[^>]*>.*?</script>', ' [PAYLOAD] ', s, flags=re.S)
s = re.sub(r'<script[^>]*>.*?</script>', ' ', s, flags=re.S)
s = re.sub(r'<style[^>]*>.*?</style>', ' ', s, flags=re.S)
t = html.unescape(re.sub(r'<[^>]+>', '\n', s))
lines = [l.strip() for l in t.split('\n') if l.strip()]
print('\n'.join(lines))
