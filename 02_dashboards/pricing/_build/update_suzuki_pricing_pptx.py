#!/usr/bin/env python3
"""Update Suzuki's ISZE Parts Pricing Structure to current-reality (Legend) variables.

Keeps Suzuki's exact 7-slide format. Updates, per the pricing simulation Legend:
  - PR00 factors  (C .475 D .495 F .555 J .555 M .50 P .44 V .56) + EV kept
  - UK -2.4% and Iceland/Norway -1.2% recomputed from the same factors
  - Israel: UMI 1797 and UTI 1799 multipliers updated; GM labels kept; EBP recalculated
  - CIS 0.40 -> 60% GM
  - FX -> 163.7, EBP@100JPY recalculated throughout
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation

SRC = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\20260820_Takayoshi Suzuki ISZ_ISZE Parts Pricing 202507 _002_.pptx")
OUT_DIR = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing")
OUT = OUT_DIR / "ISZE_Parts_Pricing_Structure_FY2027.pptx"

FX = 163.7
DJ, DT = 0.62, 0.611
UK_ADJ = 0.976    # -2.4%
ISL_ADJ = 0.988   # -1.2%


def fstr(x: float) -> str:
    s = f"{x:.3f}".rstrip("0").rstrip(".")
    if "." in s:
        whole, frac = s.split(".")
        s = whole + "." + frac.ljust(2, "0")
    return s.replace(".", ",")


def gmpct(x: float) -> str:
    s = f"{x:.1f}".rstrip("0").rstrip(".")
    return s.replace(".", ",") + "%"


def dec2(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def ebp(disc: float, factor: float, adj: float = 1.0) -> float:
    return 10000 * disc * adj / (FX * factor)


# EU classes (row order = Suzuki). (factor, keep_gm_from_suzuki)
EU = [
    ("C", 0.475),
    ("D", 0.495),
    ("F", 0.555),
    ("J", 0.555),
    ("M", 0.50),
    ("P", 0.44),
    ("V", 0.56),
    ("EV >100K", 0.68),   # EV kept as Suzuki
    ("EV 100k", 0.518),   # EV kept as Suzuki
]


def eu_rows(adj: float, suffix: str):
    out = {"formula": [], "gm": [], "ebp": []}
    for _name, factor in EU:
        gm = (1 - factor / adj) * 100
        out["formula"].append(
            f"Base price * discount 0,62 (JP) or 0,611 (TH) / exchange rate / "
            f"{fstr(factor)}{suffix}"
        )
        out["gm"].append(gmpct(gm))
        out["ebp"].append(f"{dec2(ebp(DJ, factor, adj))} JP / {dec2(ebp(DT, factor, adj))} TH")
    return out


# Israel: (label, multiplier, gm_pct). GM taken from the file's Gm column (weighted, blended J+TH).
UTI = [
    ("C", 1.10, 43.6),
    ("D", 1.22, 49.2),
    ("F", 1.03, 39.8),
    ("J", 1.07, 42.0),
    ("M", 1.08, 42.6),
    ("P", 1.10, 43.6),
    ("V", 0.95, 34.7),
]
UMI = [
    ("C", 1.25, 49.5),
    ("D", 1.25, 51.0),
    ("F", 1.00, 38.8),
    ("J", 1.02, 39.4),
    ("M", 1.10, 44.5),
    ("P", 1.08, 43.4),
    ("V", 0.92, 33.5),
]


def israel_rows(rows):
    out = {"formula": [], "gm": [], "ebp": []}
    for _name, m, gm in rows:
        ms = fstr(m) if m != 1.0 else "1"
        out["formula"].append(f"Base price / Exchange rate * {ms}")
        out["gm"].append(gmpct(gm))
        out["ebp"].append(f"{dec2(10000 * m / FX)} JP & TH")
    return out


def set_cell(cell, text: str) -> None:
    tf = cell.text_frame
    first = None
    align = None
    for p in tf.paragraphs:
        if align is None:
            align = p.alignment
        for r in p.runs:
            first = r
            break
        if first:
            break
    size = bold = name = None
    if first is not None:
        size = first.font.size
        bold = first.font.bold
        name = first.font.name
    cell.text = text
    p = tf.paragraphs[0]
    p.alignment = align
    for r in p.runs:
        if size is not None:
            r.font.size = size
        if bold is not None:
            r.font.bold = bold
        if name:
            r.font.name = name


def update_table(slide, col_map: dict[int, list[str]], n_rows: int) -> None:
    for shape in slide.shapes:
        if not shape.has_table:
            continue
        tbl = shape.table
        for ri in range(1, min(n_rows + 1, len(tbl.rows))):
            for ci, texts in col_map.items():
                if ri - 1 < len(texts):
                    set_cell(tbl.cell(ri, ci), texts[ri - 1])
        return


def apply(prs, slide_idx, col_map, n_rows):
    update_table(prs.slides[slide_idx], col_map, n_rows)


def replace_date(prs) -> None:
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for p in shape.text_frame.paragraphs:
                    for r in p.runs:
                        if "20 June 2025" in r.text:
                            r.text = r.text.replace("20 June 2025", "20 August 2026")


def main() -> int:
    prs = Presentation(str(SRC))

    # Slide 2 = EU standard
    e = eu_rows(1.0, "")
    apply(prs, 1, {1: e["formula"], 2: e["gm"], 3: e["ebp"]}, len(EU))

    # Slide 3 = UK (-2.4%)
    uk = eu_rows(UK_ADJ, " -2,4%")
    apply(prs, 2, {1: uk["formula"], 2: uk["gm"], 3: uk["ebp"]}, len(EU))

    # Slide 4 = Iceland/Norway (-1.2%)
    isl = eu_rows(ISL_ADJ, " -1,2%")
    apply(prs, 3, {1: isl["formula"], 2: isl["gm"], 3: isl["ebp"]}, len(EU))

    # Slide 5 = UTI (multiplier + GM + EBP)
    uti = israel_rows(UTI)
    apply(prs, 4, {1: uti["formula"], 2: uti["gm"], 3: uti["ebp"]}, len(UTI))

    # Slide 6 = UMI
    umi = israel_rows(UMI)
    apply(prs, 5, {1: umi["formula"], 2: umi["gm"], 3: umi["ebp"]}, len(UMI))

    # Slide 7 = CIS (0.40 -> 60%)
    n_cis = 7
    cis_formula = "Base price * discount 0,62 (JP) or 0,611 (TH) / exchange rate / 0,40"
    jp = dec2(ebp(DJ, 0.40))
    th = dec2(ebp(DT, 0.40))
    apply(prs, 6,
          {1: [cis_formula] * n_cis, 2: ["60%"] * n_cis,
           3: [f"{jp} JP / {th} TH"] * n_cis},
          n_cis)

    replace_date(prs)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    cmd = OUT.with_suffix(".cmd")
    cmd.write_text(f'@echo off\r\nstart "" "%~dp0{OUT.name}"\r\n', encoding="utf-8")
    print("wrote", OUT)
    print("wrote", cmd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
