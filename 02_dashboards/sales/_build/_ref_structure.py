"""Strip payloads/libraries out of a big self-contained HTML so the skeleton is readable."""
from __future__ import annotations

import re
import sys
from pathlib import Path

p = Path(sys.argv[1])
t = p.read_text(encoding="utf-8", errors="replace")
print(f"# file {p.name}  {len(t)/1024:.0f} KB")

# replace huge inline script blocks with a marker
def shrink(m):
    body = m.group(2)
    head = m.group(1)
    return f"<script{head}>/* [STRIPPED {len(body)/1024:.0f} KB] */</script>"

t = re.sub(r"<script([^>]*)>(.*?)</script>", shrink, t, flags=re.S)
# collapse very long attribute values / json
t = re.sub(r"(\"[a-zA-Z0-9_\-]*json[a-zA-Z0-9_\-]*\"\s*:\s*)\{[^{}]{200,}\}", r"\1{...}", t)
out = Path(sys.argv[2]) if len(sys.argv) > 2 else p.with_suffix(".skeleton.txt")
out.write_text(t, encoding="utf-8")
print(f"# written {out}  {len(t)/1024:.0f} KB  lines {t.count(chr(10))}")
