"""IDS 2026 charts from the country roll-up workbooks (real scores, no invention)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpr_charts as C  # noqa: E402

SHEETS = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IDS_2026_SharePoint_drop\IDS_dealer_sheets")


def read_rollup(p: Path) -> dict | None:
    try:
        xl = pd.ExcelFile(p)
    except Exception:  # noqa: BLE001
        return None
    if "Network overview" not in xl.sheet_names:
        return None
    df = pd.read_excel(p, sheet_name="Network overview", header=None)
    out = {"file": p.name, "market": p.parent.name}
    for _, row in df.iterrows():
        key = str(row[0]).strip().lower() if not pd.isna(row[0]) else ""
        val = row[1] if len(row) > 1 else None
        if key.startswith("network average"):
            out["avg"] = float(val) if not pd.isna(val) else None
        elif key.startswith("dealers evaluated"):
            out["dealers"] = int(val) if not pd.isna(val) else None
        elif key.startswith("average points"):
            out["points"] = float(val) if not pd.isna(val) else None
        elif key == "good":
            out["good"] = float(row[2]) if len(row) > 2 and not pd.isna(row[2]) else None
        elif key == "medium":
            out["medium"] = float(row[2]) if len(row) > 2 and not pd.isna(row[2]) else None
        elif key.startswith("needs improvement"):
            out["needs"] = float(row[2]) if len(row) > 2 and not pd.isna(row[2]) else None
        elif key.startswith("a ") or key.startswith("a -") or "premises" in key:
            out.setdefault("sections", {})["A Premises"] = (float(val) if not pd.isna(val) else None,
                                                            float(row[2]) if len(row) > 2 and not pd.isna(row[2]) else None,
                                                            int(row[3]) if len(row) > 3 and not pd.isna(row[3]) else 0)
        elif "organisation" in key or key.startswith("b "):
            out.setdefault("sections", {})["B Organisation"] = (float(val) if not pd.isna(val) else None,
                                                                float(row[2]) if len(row) > 2 and not pd.isna(row[2]) else None,
                                                                int(row[3]) if len(row) > 3 and not pd.isna(row[3]) else 0)
        elif key.startswith("c ") or "service" in key:
            if "service" in key and not key.startswith("c"):
                pass
            out.setdefault("sections", {})["C Service"] = (float(val) if not pd.isna(val) else None,
                                                           float(row[2]) if len(row) > 2 and not pd.isna(row[2]) else None,
                                                           int(row[3]) if len(row) > 3 and not pd.isna(row[3]) else 0)
        elif key.startswith("d ") or "parts" in key:
            out.setdefault("sections", {})["D Parts"] = (float(val) if not pd.isna(val) else None,
                                                         float(row[2]) if len(row) > 2 and not pd.isna(row[2]) else None,
                                                         int(row[3]) if len(row) > 3 and not pd.isna(row[3]) else 0)
        elif key.startswith("e ") or "vehicle sales" in key:
            out.setdefault("sections", {})["E Vehicle sales"] = (float(val) if not pd.isna(val) else None,
                                                                 float(row[2]) if len(row) > 2 and not pd.isna(row[2]) else 0,
                                                                 int(row[3]) if len(row) > 3 and not pd.isna(row[3]) else 0)
    return out


def main():
    files = sorted(SHEETS.rglob("IDS_2026_DB_Rollup_*_v0.4.xlsx"))
    rows = []
    for f in files:
        r = read_rollup(f)
        if r and r.get("avg") is not None:
            rows.append(r)
    print(f"rollups found {len(files)}, usable {len(rows)}")
    if not rows:
        (HERE / "_ids_scores_SKIPPED.md").write_text(
            "# IDS scores — not built\n\nNo country roll-up workbook with a readable "
            "'Network overview' sheet was found.\n", encoding="utf-8")
        return

    (HERE / "_ids_numbers.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")

    df = pd.DataFrame([{"market": r["market"], "avg": r["avg"] * 100,
                        "dealers": r.get("dealers") or 0,
                        "good": (r.get("good") or 0) * 100,
                        "needs": (r.get("needs") or 0) * 100} for r in rows])
    df = df.sort_values("avg", ascending=False)
    net = (df.avg * df.dealers).sum() / df.dealers.sum()
    C.ranked_bar(
        [f"{m}  ({int(d)} dealers)" for m, d in zip(df.market, df.dealers)],
        df.avg.tolist(),
        "_ids_country_scores.png",
        title="Dealer standard assessment: how each country scored in 2026",
        subtitle=(
            f"Dealer average score as a percentage of the 280-point standard, from the country roll-up "
            f"workbooks (v0.4). Network dealer-weighted average {net:.1f}% across "
            f"{int(df.dealers.sum())} dealers. Bands: good 80% and above."
        ),
        value_fmt="{:,.1f}%",
        reference=net,
        reference_label=f"network {net:.0f}%",
        hot_below=True,
        figsize=(9.8, 5.8),
    )

    band = df.sort_values("needs", ascending=False).head(10)
    C.ranked_bar(
        [f"{m}" for m in band.market],
        band.needs.tolist(),
        "_ids_sections.png",
        title="Where the weakest dealers are concentrated",
        subtitle=(
            "Share of each country's dealers in the lowest band (needs improvement), country roll-up "
            "workbooks v0.4. A country with a single dealer is highly sensitive to that one score."
        ),
        value_fmt="{:,.1f}%",
        hot_below=False,
        figsize=(9.6, 4.8),
    )

    # Section A-E, dealer-weighted across the network. The workbooks carry the
    # section averages, so this is a measured view rather than a re-derivation.
    order = ["A Premises", "B Organisation", "C Service", "D Parts", "E Vehicle sales"]
    sec_pct, sec_dealers, sec_max = {}, {}, {}
    for r in rows:
        for name, (mx, avg, n) in (r.get("sections") or {}).items():
            if avg is None or not n:
                continue
            sec_pct.setdefault(name, []).append((avg * 100, n))
            sec_dealers[name] = sec_dealers.get(name, 0) + n
            sec_max[name] = mx
    sec_rows = []
    for name in order:
        if name not in sec_pct:
            continue
        pairs = sec_pct[name]
        w = sum(v * n for v, n in pairs) / sum(n for _, n in pairs)
        sec_rows.append((name, w, sec_max.get(name), sec_dealers.get(name, 0)))
    if sec_rows:
        C.ranked_bar(
            [f"{n}  (max {int(mx)} pts)" for n, _, mx, _ in sec_rows],
            [w for _, w, _, _ in sec_rows],
            "_ids_section_scores.png",
            title="Dealer standard by section: where the network is weakest",
            subtitle=(
                "Dealer-weighted average per section as a percentage of that section's maximum, 2026 country "
                "roll-up workbooks. The weakest section constrains the others, so it is the one to fix first."
            ),
            value_fmt="{:,.1f}%",
            hot_below=True,
            reference=sum(w for _, w, _, _ in sec_rows) / len(sec_rows),
            reference_label="section mean",
            figsize=(9.6, 4.4),
        )
        (HERE / "_ids_sections.json").write_text(
            json.dumps([{"section": n, "pct": w, "max_points": mx, "dealers": d}
                        for n, w, mx, d in sec_rows], indent=1), encoding="utf-8")
        print("section chart written:", [(n, round(w, 1)) for n, w, _, _ in sec_rows])
    print("IDS charts written")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
