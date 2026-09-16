"""Inventory APL files already in 90_INBOX — ITUK vs UTI P700. UTF-8 report."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX")
ITUK = ROOT / "APL_ITUK_202607"
UTI = ROOT / "APL_UTI_P700"
SUZUKI = ROOT / "suzuki_pms_mail_pull"
META = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_raw\apl_inbox_inventory_20260812.json"
)
MD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\OUTLOOK_APL_MAIL_SCAN.md")


def files(p: Path) -> list[Path]:
    if not p.exists():
        return []
    return sorted([f for f in p.rglob("*") if f.is_file()], key=lambda x: x.name.lower())


def zip_names(z: Path) -> list[str]:
    try:
        with zipfile.ZipFile(z) as zf:
            return zf.namelist()
    except Exception as e:
        return [f"ERROR:{e}"]


def main() -> None:
    ituk_files = files(ITUK)
    uti_files = files(UTI)
    suzuki_files = [
        f
        for f in files(SUZUKI)
        if f.suffix.lower() in {".zip", ".xlsx", ".xls", ".csv", ".xlsm"}
        or "1037" in f.name
        or "apl" in f.name.lower()
    ]

    inv = {
        "rg21_note": "RG21 = D-Max 2.2L",
        "ituk_dir": str(ITUK),
        "uti_dir": str(UTI),
        "ituk_files": [
            {"name": f.name, "path": str(f), "bytes": f.stat().st_size} for f in ituk_files
        ],
        "uti_files": [
            {"name": f.name, "path": str(f), "bytes": f.stat().st_size} for f in uti_files
        ],
        "suzuki_related": [
            {"name": f.name, "path": str(f), "bytes": f.stat().st_size} for f in suzuki_files
        ],
        "zip_contents": {},
    }

    for f in ituk_files + uti_files + suzuki_files:
        if f.suffix.lower() == ".zip":
            inv["zip_contents"][str(f)] = zip_names(f)

    META.write_text(json.dumps(inv, indent=2), encoding="utf-8")

    # Key ITUK markers
    ituk_key = [
        f
        for f in ituk_files
        if any(
            k in f.name.lower()
            for k in ("20260714", "1037", "vr05", "rg21", "recommended", "apl")
        )
    ]
    uti_key = [
        f
        for f in uti_files
        if f.suffix.lower() in {".zip", ".xlsx", ".xls", ".csv", ".xlsm"}
    ]

    lines = [
        "# APL inventory — ITUK vs UTI P700",
        "",
        "**RG21 = D-Max 2.2L.**",
        "",
        "Outlook live COM hung this session; files below were **already on disk** under `90_INBOX` "
        "(from earlier Suzuki / APL mail pulls). No part numbers invented.",
        "",
        "## 1) ITUK APL / Recommended parts list",
        "",
        f"Folder: `{ITUK}` · **{len(ituk_files)}** files",
        "",
    ]
    if not ituk_files:
        lines.append("**Not found** on disk.")
    else:
        lines.append("### Key files")
        lines.append("")
        for f in ituk_key or ituk_files:
            lines.append(f"- `{f.name}` ({f.stat().st_size:,} bytes)")
            if f.suffix.lower() == ".zip":
                names = inv["zip_contents"].get(str(f), [])
                lines.append(f"  - zip entries ({len(names)}):")
                for n in names[:25]:
                    lines.append(f"    - {n}")
                if len(names) > 25:
                    lines.append(f"    - … +{len(names)-25} more")
        lines.append("")
        lines.append("### Suzuki `20260714_1037.zip` status")
        lines.append("")
        z1037 = [f for f in ituk_files if "20260714" in f.name or "1037" in f.name]
        z1037 += [f for f in suzuki_files if "20260714" in f.name or "1037" in f.name]
        if z1037:
            for f in z1037:
                lines.append(f"- **FOUND:** `{f}`")
        else:
            lines.append("- **Not found** as `20260714_1037.zip` in these folders.")
        # RG21 note
        rg21 = [f for f in ituk_files if "rg21" in f.name.lower()]
        if rg21:
            lines.append("")
            lines.append("### RG21 (= 2.2L) related")
            for f in rg21:
                lines.append(f"- `{f.name}`")

    lines += ["", "## 2) UTI P700 APL", ""]
    lines.append(f"Folder: `{UTI}` · **{len(uti_files)}** files")
    lines.append("")
    if not uti_key:
        lines.append(
            "**No distinct UTI-P700-only APL package found.** "
            "Folder may only contain copies of the ITUK/Suzuki zip renamed with UTI_P700 prefix "
            "(check names below). Do not treat ITUK VR05 as UTI P700 without reading the sheets."
        )
        lines.append("")
    for f in uti_files:
        lines.append(f"- `{f.name}` ({f.stat().st_size:,} bytes)")
        if f.suffix.lower() == ".zip":
            names = inv["zip_contents"].get(str(f), [])
            # flag if same as ITUK 1037
            lines.append(f"  - zip entries ({len(names)}): {', '.join(names[:8])}" + ("…" if len(names) > 8 else ""))

    # Compare UTI zip to ITUK 1037 by size/name overlap
    lines += ["", "## Cross-check: UTI folder vs ITUK Suzuki zip", ""]
    ituk_1037 = next((f for f in ituk_files if "20260714_1037" in f.name), None)
    uti_1037 = next((f for f in uti_files if "20260714_1037" in f.name), None)
    if ituk_1037 and uti_1037:
        same = ituk_1037.stat().st_size == uti_1037.stat().st_size
        lines.append(
            f"- ITUK `{ituk_1037.name}` size={ituk_1037.stat().st_size:,} · "
            f"UTI copy `{uti_1037.name}` size={uti_1037.stat().st_size:,} · "
            f"**{'SAME SIZE (likely duplicate of ITUK APL, not a separate UTI P700 APL)' if same else 'DIFFERENT SIZE'}**"
        )
    elif not uti_1037:
        lines.append("- No `20260714_1037` copy under UTI folder.")
    else:
        lines.append("- UTI has 1037 zip; ITUK folder missing matching name.")

    lines += [
        "",
        "## Outlook live scan",
        "",
        "COM Restrict/brute scans **hung** this session (Outlook locked). "
        "Disk inventory above is the evidence source for now.",
        "",
        f"Machine inventory JSON: `{META}`",
        "",
    ]

    MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"ituk_files={len(ituk_files)} uti_files={len(uti_files)}")
    print(f"ituk_key={len(ituk_key)} uti_key={len(uti_key)}")
    print(f"wrote {MD}")


if __name__ == "__main__":
    main()
