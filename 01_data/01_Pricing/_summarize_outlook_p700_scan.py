"""Summarize Outlook P700/D-Max 2.2 mail scan JSON → markdown."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

RAW = Path(__file__).resolve().parent / "_raw" / "outlook_p700_dmax22_mail_scan_20260812.json"
OUT = Path(__file__).resolve().parent / "OUTLOOK_P700_DMAX22_MAIL_SCAN.md"


def main() -> None:
    d = json.loads(RAW.read_text(encoding="utf-8"))
    hits = d["hits"]
    lines = [
        "# Outlook scan — P700 / D-Max 2.2L",
        "",
        f"Scanned: {d.get('scanned_at')} · hits: {len(hits)} (Inbox + Sent, keyword-capped).",
        "",
        "## Verdict",
        "",
        "- Mail has **commercial P700 order / tender** traffic, not a clean **parts BOM** with Isuzu PNs.",
        "- **No attachment** in this scan was a parts price list / BOM Excel (images only on P700 order thread).",
        "- Launch part families still come from the **pricing engine launch basket** (placeholder TBD-* codes) until IML/IMIT send real PNs.",
        "",
        "## Threads (subject)",
        "",
    ]
    fam = Counter()
    for h in hits:
        subj = h.get("subject") or ""
        blob = (subj + " " + (h.get("preview") or "")).lower()
        tags = []
        if "p700" in blob:
            tags.append("P700")
        if any(x in blob for x in ("2.2", "rz4f", "rg21", "d-max 2.2", "dmax")):
            tags.append("DMAX22")
        if not tags:
            continue
        atts = [
            a
            for a in (h.get("attachments") or [])
            if not str(a).lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp"))
        ]
        lines.append(
            f"- {str(h.get('received'))[:10]} | {','.join(tags)} | {subj}"
        )
        if atts:
            lines.append(f"  - files: {', '.join(atts)}")
        for f in h.get("families_mentioned") or []:
            fam[f] += 1

    lines += ["", "## Families mentioned in mail body (weak signal)", ""]
    for k, v in fam.most_common(15):
        lines.append(f"- {k}: {v} mails")

    lines += [
        "",
        "## Next to get real PNs",
        "",
        "1. Ask IML/IMIT for **P700 parts catalogue / supersession / first-stock list**.",
        "2. Ask for **D-Max 2.2 (RG21/RZ4F) filter + SCR + wear** PN map (replace TBD-* placeholders).",
        "3. Optional: Israel UMI P700 warranty/claim mix (structure only; ZPR1 prices need restatement).",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
