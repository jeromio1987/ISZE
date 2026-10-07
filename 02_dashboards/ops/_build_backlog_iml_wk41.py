"""Build the IML delay proof page - extends ISZE_Backlog_IML_WK41.html with the delay answer.

Adds to the existing page:
  - IML warehouse delays, answer-first: how long, which status, which parts
  - who is waiting for a delayed part (part-number overlap, labelled honestly)
  - the recurrence proof from the 39 UTI weekly lists
  - fill rate and back-order lines against the FY26-27 targets
  - what is missing

House style: self-contained, Chart.js inlined, sortable headers, file:// safe.
"""
from __future__ import annotations

import json
import re
import datetime
import hashlib
from pathlib import Path

import openpyxl
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DELAY = ROOT / "01_data" / "ISZE_Order Status as of 2 October 2026_request to check.xlsx"
BO = ROOT / "01_data" / "90_INBOX" / "_iml_delay_wk41_20261007" / "bo_overview" / "20261006_BO info VP 06-10-2026.xlsx"
AIM = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
KPI = ROOT / "01_data" / "11_planning" / "KPI Master File august 2026.xlsx"
TARGETS = ROOT / "01_data" / "11_planning" / "ISZE_DB_KPI_Targets_FY2627_v1.xlsx"
UTI = ROOT / "02_dashboards" / "pricing" / "_build" / "price_5pct_proposal_2026-09-29" / "uti_panels_2026-10-02" / "t13_uti_bo_body_lines_wk2_wk40.csv"
CHARTJS = ROOT / "02_dashboards" / "_ui" / "chart.umd.min.js"
HTML = ROOT / "02_dashboards" / "ops" / "ISZE_Backlog_IML_WK41.html"
CMD = ROOT / "02_dashboards" / "ops" / "OPEN_ISZE_Backlog_IML_WK41.cmd"

EXCLUDE = ("MIDI", "RUS", "KAZ", "CBC-TRANS", "GRAND AVTO", "KOMTRANS", "KIMA")
ASOF_IML = pd.Timestamp("2026-10-02")
ASOF_BO = "2026-10-06"

# target sheet DB name -> KPI Master File distributor name
DB_ALIAS = {
    "IUK": "IUK", "ITUK": "ITUK", "Imotors": "Imotors", "IBX (incl. Polska)": "IBX (BENELUX)",
    "Isuzu Sverige": "Isuzu Sverige", "Isuzu Ireland": "Isuzu Ireland", "WAE": "WAE",
    "IMF": "IMF", "Isuzu Rom Auto": "Isuzu Rom Auto", "GasanZammit": "GasanZammit",
    "Petros Petropoulos": "Petros Petropoulos", "BL ehf": "BL ehf", "KIMA": "KIMA",
    "Isuzu Danmark": "Isuzu Danmark", "RSA": "RSA", "MIDI": "MIDI", "ISD": "ISD",
    "UTI": "UTI", "UMI": "UMI", "AIOS": "AIOS", "Loutsios Group": "Loutsios Group",
    "Isuzu Polska": "Isuzu Polska",
}


def norm_pn(v) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", str(v if v is not None else ""))


def main() -> int:
    # ---------------- AIM ----------------
    aim = pd.read_csv(AIM, dtype=str, low_memory=False)
    aim["pn"] = aim["part_number"].fillna("").map(norm_pn)
    fam: dict[str, str] = {}
    cat: dict[str, str] = {}
    figg: dict[str, str] = {}
    fix_col = aim["aim_l1_fixed"].fillna("").str.strip() if "aim_l1_fixed" in aim.columns else None
    fix2_col = aim["cat_l1_fixed"].fillna("").str.strip() if "cat_l1_fixed" in aim.columns else None
    fig_col = aim["fig_key"].fillna("").str.strip() if "fig_key" in aim.columns else None
    for i, (p, f, c) in enumerate(zip(aim["pn"], aim["aim_l1"].fillna("").str.strip(),
                                      aim["cat_l1"].fillna("").str.strip())):
        if not p:
            continue
        k = p.lstrip("0")
        if not f and fix_col is not None:
            f = fix_col.iat[i] or ""
        if not c and fix2_col is not None:
            c = fix2_col.iat[i] or ""
        if f and (k not in fam or not fam[k]):
            fam[k] = f
        if c and (k not in cat or not cat[k]):
            cat[k] = c
        if fig_col is not None:
            fv = fig_col.iat[i]
            if fv and k not in figg:
                figg[k] = fv
    infile = set(aim["pn"].map(lambda s: s.lstrip("0")))

    def aim_label(pn: str) -> tuple[str, str]:
        k = norm_pn(pn).lstrip("0")
        if k in infile:
            f = fam.get(k, "")
            return (f, "family") if f else ("in AIM, no family yet", "nofam")
        return ("not in the AIM file", "absent")

    def cat_label(pn: str) -> str:
        """The catalogue category, in its own vocabulary. Blank when we do not hold it."""
        return cat.get(norm_pn(pn).lstrip("0"), "")

    def fig_label(pn: str) -> str:
        return figg.get(norm_pn(pn).lstrip("0"), "")

    def band(days) -> str:
        if days is None or pd.isna(days):
            return ""
        d = float(days)
        if d <= 7:
            return "0-7 days"
        if d <= 30:
            return "8-30 days"
        if d <= 60:
            return "31-60 days"
        if d <= 90:
            return "61-90 days"
        if d <= 180:
            return "91-180 days"
        return "over 180 days"

    # ---------------- IML warehouse ----------------
    dly = pd.read_excel(DELAY, sheet_name="isze", dtype=str)
    dly.columns = [str(c).strip() for c in dly.columns]
    dly["pn"] = dly["PN"].map(norm_pn)
    dly["part"] = dly["Part Name"].fillna("").str.strip()
    dly["status"] = dly["Status"].fillna("").str.strip()
    dly["qty"] = pd.to_numeric(dly["Q'ty"], errors="coerce").fillna(0)
    dly["mode"] = dly["Mode"].fillna("").str.strip().map({"S": "Sea", "A": "Air"}).fillna("other")
    dly["order_no"] = dly["Order No"].fillna("").str.strip()
    dly["procced"] = pd.to_datetime(dly["Procced"], format="%y%m%d", errors="coerce")
    dly["days_waiting"] = (ASOF_IML - dly["procced"]).dt.days
    labs = [aim_label(p) for p in dly["pn"]]
    dly["aim"] = [a for a, _ in labs]
    dly["cat"] = [cat_label(p) for p in dly["pn"]]

    K = {}
    K["iml_lines"] = int(len(dly))
    K["iml_pcs"] = int(dly["qty"].sum())
    K["iml_orders"] = int(dly["order_no"].nunique())
    over30 = dly[dly["days_waiting"] > 30]
    K["over30_lines"] = int(len(over30))
    K["over30_pcs"] = int(over30["qty"].sum())
    K["over30_orders"] = int(over30["order_no"].nunique())
    K["oldest"] = int(dly["days_waiting"].max())
    K["median_all"] = float(dly["days_waiting"].median())
    K["packship_lines"] = int(dly[dly["status"].isin(["TO BE PACKED", "READY FOR SHIPMENT"])].shape[0])
    K["packship_over30"] = int(over30[over30["status"].isin(["TO BE PACKED", "READY FOR SHIPMENT"])].shape[0])
    K["backorder_lines"] = int((dly["status"] == "BACK ORDER").sum())
    K["backorder_pcs"] = int(dly.loc[dly["status"] == "BACK ORDER", "qty"].sum())
    K["over60_lines"] = int((dly["days_waiting"] > 60).sum())
    K["over90_lines"] = int((dly["days_waiting"] > 90).sum())
    K["pc_with_eta"] = 0  # placeholder replaced below

    st = (dly.groupby("status", as_index=False)
          .agg(lines=("qty", "size"), pcs=("qty", "sum"),
               median=("days_waiting", "median"), oldest=("days_waiting", "max"),
               over30=("days_waiting", lambda s: int((s > 30).sum())),
               over30_pcs=("qty", lambda s: 0)))
    st["over30_pcs"] = [int(over30[over30["status"] == r].shape[0] and over30[over30["status"] == r]["qty"].sum())
                        for r in st["status"]]
    st = st.sort_values("pcs", ascending=False)

    bucket = pd.cut(dly["days_waiting"], [-1, 7, 30, 60, 90, 180, 100_000],
                    labels=["0-7 days", "8-30 days", "31-60 days", "61-90 days", "91-180 days", "over 180 days"])
    wage = (dly.assign(b=bucket).pivot_table(index="b", columns="status", values="qty",
            aggfunc="sum", observed=False, fill_value=0))

    waim = (dly.groupby("aim", as_index=False)
            .agg(lines=("qty", "size"), pcs=("qty", "sum"), oldest=("days_waiting", "max"),
                 over30=("days_waiting", lambda s: int((s > 30).sum())))
            .sort_values("pcs", ascending=False))
    waim["over30_pcs"] = [int(over30[over30["aim"] == r]["qty"].sum()) for r in waim["aim"]]

    dparts = (over30.groupby(["pn", "part", "aim", "cat"], as_index=False)
              .agg(lines=("qty", "size"), pcs=("qty", "sum"), oldest=("days_waiting", "max"),
                   orders=("order_no", "nunique"),
                   statuses=("status", lambda s: "/".join(sorted(set(s)))))
              .sort_values("pcs", ascending=False))

    worst = over30.sort_values("days_waiting", ascending=False)[
        ["order_no", "pn", "part", "status", "qty", "days_waiting", "mode", "aim", "cat", "procced"]].copy()
    worst["procced"] = worst["procced"].dt.strftime("%Y-%m-%d")

    oagg = (over30.groupby("order_no", as_index=False)
            .agg(lines=("qty", "size"), pcs=("qty", "sum"), oldest=("days_waiting", "max"))
            .sort_values("lines", ascending=False))
    mode_c = (dly.groupby("mode", as_index=False).agg(lines=("qty", "size"), pcs=("qty", "sum")))

    # ---------------- customer backlog ----------------
    data = pd.read_excel(BO, sheet_name="DATA", header=3, dtype=str).dropna(how="all")
    data.columns = [str(c).strip() for c in data.columns]
    data = data[data["Material"].notna()].copy()
    data["pn"] = data["Material"].map(norm_pn)
    data["part"] = data["Material description"].fillna("").str.strip()
    data["customer"] = data["Customer"].fillna("").str.strip()
    data["saty"] = data["SaTy"].fillna("").str.strip()
    data["qty"] = pd.to_numeric(data["Open Qty"], errors="coerce").fillna(0)
    data["loc"] = (data["Shipping Location"].fillna("").str.strip()
                   if "Shipping Location" in data.columns else "")
    data["req_dlv"] = pd.to_datetime(data["Req.Dlv.Dt"], errors="coerce")
    data["days_open"] = (pd.Timestamp(ASOF_BO) - data["req_dlv"]).dt.days
    up = data["customer"].str.upper()
    data = data[~up.str.contains("|".join(EXCLUDE))].copy()

    # who is waiting for a delayed part (part-number overlap only)
    dly_pn = set(dly["pn"])
    dly_delayed_pn = set(over30["pn"])
    ov = data[data["pn"].isin(dly_delayed_pn)].copy()
    K["ov_lines"] = int(len(ov))
    K["ov_pcs"] = int(ov["qty"].sum())
    K["ov_custs"] = int(ov["customer"].nunique())
    K["ov_pns"] = int(ov["pn"].nunique())
    K["delayed_pns"] = int(over30["pn"].nunique())

    dw = (over30.groupby("pn", as_index=False)
          .agg(d_pcs=("qty", "sum"), d_oldest=("days_waiting", "max"),
               d_status=("status", lambda s: "/".join(sorted(set(s))))))
    per_part = (ov.groupby(["pn", "part"], as_index=False)
                .agg(custs=("customer", lambda s: ", ".join(sorted(set(s)))),
                     n_custs=("customer", "nunique"),
                     bo_pcs=("qty", "sum"),
                     bo_oldest=("days_open", "max"),
                     bo_urgent=("saty", lambda s: int(s.isin(["VOR", "RUSH"]).sum())))
                .merge(dw, on="pn", how="left")
                .sort_values("d_pcs", ascending=False))
    per_part["aim"] = [aim_label(p)[0] for p in per_part["pn"]]
    per_part["cat"] = [cat_label(p) for p in per_part["pn"]]

    ov_cust = (ov.groupby("customer", as_index=False)
               .agg(lines=("pn", "size"), pns=("pn", "nunique"),
                    bo_pcs=("qty", "sum"), bo_oldest=("days_open", "max"))
               .sort_values("bo_oldest", ascending=False))

    # ---------------- customer backlog roll-ups (kept from the first version) ----------------
    labs_bo = [aim_label(p) for p in data["pn"]]
    data["aim"] = [a for a, _ in labs_bo]
    data["cat"] = [cat_label(p) for p in data["pn"]]

    cu = (data.groupby("customer", as_index=False)
          .agg(lines=("pn", "size"), pns=("pn", "nunique"), pcs=("qty", "sum"),
               urgent=("saty", lambda s: int(s.isin(["VOR", "RUSH", "SVOR"]).sum())),
               oldest=("days_open", "max"),
               over90=("days_open", lambda s: int((s > 90).sum()))))
    cu["pct_urgent"] = (100 * cu["urgent"] / cu["lines"]).round(0)
    cu = cu.sort_values("pcs", ascending=False)

    aim_c = (data.groupby("aim", as_index=False)
             .agg(lines=("pn", "size"), pcs=("qty", "sum"), custs=("customer", "nunique"),
                  parts=("pn", "nunique")).sort_values("pcs", ascending=False))

    bl = data[["customer", "pn", "part", "saty", "qty", "days_open", "aim", "cat", "req_dlv"]].copy()
    bl["req_dlv"] = bl["req_dlv"].dt.strftime("%Y-%m-%d")
    bl["days_open"] = bl["days_open"].fillna(-1).astype(int)

    K["bo_lines"] = int(len(data))
    K["bo_pcs"] = int(data["qty"].sum())
    K["bo_custs"] = int(data["customer"].nunique())
    K["bo_urgent"] = int(data["saty"].isin(["VOR", "RUSH", "SVOR"]).sum())
    K["bo_oldest"] = int(data["days_open"].max())
    K["bo_parts"] = int(data["pn"].nunique())

    # ---------------- waiting: the over-30-day parts, in words, and the customer link ----------------
    NOUNS = ["hose", "gasket", "bolt", "clip", "pump", "filter", "element", "belt", "cover", "pipe",
             "bracket", "spring", "sensor", "valve", "nut", "washer", "stud", "screw", "bearing",
             "seal", "ring", "cap", "rotor", "liner", "nozzle", "switch", "lamp", "mirror", "panel",
             "bumper", "arm", "link", "cable", "harness", "motor", "cylinder", "shaft", "gear",
             "radiator", "coupling", "plate", "tube", "guard", "handle", "lock", "pad", "kit"]

    def noun_of(desc: str) -> str:
        d = (desc or "").lower()
        for n in NOUNS:
            if re.search(r"\b" + n + r"\b", d):
                return n
        return "other"

    wait = over30.copy()
    wait["noun"] = wait["part"].map(noun_of)
    wait["k_noun"] = wait["noun"]
    wait["k_aim"] = wait["aim"]
    wait["k_cat"] = wait["cat"]
    wait["k_aim2"] = wait["part"].map(
        lambda s: (s.split(";")[0].strip() if ";" in s else ""))

    def wait_group(frame, keycol, label):
        out = []
        for key, sub in frame.groupby(keycol, dropna=False):
            pn_agg = (sub.groupby("pn", as_index=False)
                      .agg(pcs=("qty", "sum"), oldest=("days_waiting", "max"),
                           lines=("qty", "size"), part=("part", "first"))
                      .sort_values("pcs", ascending=False))
            examples = [{"pn": r["pn"], "part": r["part"], "pcs": int(r["pcs"]),
                         "oldest": int(r["oldest"])} for _, r in pn_agg.head(5).iterrows()]
            out.append({
                "key": str(key if key else ""),
                "label": str(label(key)) if callable(label) else (str(key) if key else "(no family recorded)"),
                "lines": int(len(sub)), "pcs": int(sub["qty"].sum()),
                "pns": int(sub["pn"].nunique()),
                "oldest": int(sub["days_waiting"].max()),
                "median": float(sub["days_waiting"].median()),
                "orders": int(sub["order_no"].nunique()),
                "statuses": "/".join(sorted(set(sub["status"]))),
                "examples": examples,
            })
        return sorted(out, key=lambda r: -r["pcs"])

    by_noun = wait_group(wait, "k_noun", None)
    by_aim = wait_group(wait, "k_aim", None)
    by_cat = wait_group(wait, "k_cat", None)
    by_aim2 = wait_group(wait, "k_aim2", lambda k: (k if k else "(no sub-family in the description)"))

    K["wait_lines"] = int(len(wait))
    K["wait_pcs"] = int(wait["qty"].sum())
    K["wait_nouns"] = int(wait["noun"].nunique())
    K["wait_groups"] = int(len(by_noun))
    K["wait_oldest"] = int(wait["days_waiting"].max())

    # customer link: a part-number overlap, not a traced order - keep it labelled that way.
    # Sum from the CUSTOMER side per part number, so the figures are the customer's own open pieces.
    bo_by_pn = {}
    for pn_key, sub in data.groupby("pn"):
        custs = {}
        for _, r in sub.iterrows():
            c = r["customer"]
            if c not in custs:
                custs[c] = {"customer": c, "pcs": 0, "lines": 0, "oldest": 0, "urgent": 0}
            custs[c]["pcs"] += int(r["qty"] or 0)
            custs[c]["lines"] += 1
            if r["days_open"] is not None and not pd.isna(r["days_open"]):
                custs[c]["oldest"] = max(custs[c]["oldest"], int(r["days_open"]))
            if r["saty"] in ("VOR", "RUSH", "SVOR"):
                custs[c]["urgent"] += 1
        bo_by_pn[pn_key] = list(custs.values())

    for keycol, glist in (("k_noun", by_noun), ("k_aim", by_aim), ("k_cat", by_cat), ("k_aim2", by_aim2)):
        for g in glist:
            sub = wait[wait[keycol].astype(str) == str(g["key"])]
            agg = {}
            matched = 0
            for _, r in sub.iterrows():
                hits = bo_by_pn.get(r["pn"])
                if not hits:
                    continue
                matched += 1
                for h in hits:
                    c = h["customer"]
                    if c not in agg:
                        agg[c] = {"customer": c, "pcs": 0, "lines": 0, "oldest": 0,
                                 "urgent": 0, "pns": set()}
                    agg[c]["pcs"] += h["pcs"]
                    agg[c]["lines"] += h["lines"]
                    agg[c]["oldest"] = max(agg[c]["oldest"], h["oldest"])
                    agg[c]["urgent"] += h["urgent"]
                    agg[c]["pns"].add(r["pn"])
            g["customers"] = sorted(
                ({"customer": v["customer"], "pcs": v["pcs"], "lines": v["lines"],
                  "oldest": v["oldest"], "urgent": v["urgent"], "pns": len(v["pns"])}
                 for v in agg.values()), key=lambda x: -x["pcs"])
            g["n_customers"] = len(agg)
            g["matched_pns"] = int(matched)

    K["wait_groups_no_customer"] = int(sum(1 for g in by_noun if g["matched_pns"] == 0))
    K["wait_worst_group"] = by_noun[0]["label"] if by_noun else ""
    K["wait_worst_group_pcs"] = by_noun[0]["pcs"] if by_noun else 0

    # ---------------- drill-down facts, one row per line ----------------
    iml_facts = []
    for _, r in dly.iterrows():
        iml_facts.append({
            "order": r["order_no"], "pn": r["pn"], "part": r["part"], "status": r["status"],
            "qty": int(r["qty"]), "days": int(r["days_waiting"]), "mode": r["mode"],
            "aim": r["aim"], "cat": r["cat"], "band": band(r["days_waiting"]),
            "noun": noun_of(r["part"]),
        })
    print("iml_facts rows:", len(iml_facts), "| pieces:", sum(f["qty"] for f in iml_facts))
    print("facet check (status):", {s: sum(f["qty"] for f in iml_facts if f["status"] == s)
                                    for s in sorted({f["status"] for f in iml_facts})})

    bo_facts = []
    for _, r in data.iterrows():
        d = r["days_open"]
        bo_facts.append({
            "customer": r["customer"], "pn": r["pn"], "part": r["part"], "saty": r["saty"],
            "qty": int(r["qty"]), "days": (int(d) if pd.notna(d) else None),
            "aim": r["aim"], "cat": r["cat"], "fig": fig_label(r["pn"]) or "",
            "loc": r["loc"], "band": (band(d) if pd.notna(d) else "not yet due"),
        })
    print("bo_facts rows:", len(bo_facts), "| pieces:", sum(f["qty"] for f in bo_facts))

    # ---------------- coverage of the two vocabularies ----------------
    def coverage(frame):
        n = len(frame)
        a = frame["aim"].astype(str)
        fam_n = int((~a.isin(["in AIM, no family yet", "not in the AIM file"])).sum())
        nofam = int((a == "in AIM, no family yet").sum())
        absent = int((a == "not in the AIM file").sum())
        cat_n = int((frame["cat"].astype(str).str.strip() != "").sum())
        return {"lines": n, "family": fam_n, "nofam": nofam, "absent": absent, "cat": cat_n,
                "pct_family": round(100 * fam_n / n, 1) if n else 0,
                "pct_cat": round(100 * cat_n / n, 1) if n else 0}

    cov_bo, cov_wh = coverage(data), coverage(dly)
    print("coverage backlog   :", cov_bo)
    print("coverage warehouse :", cov_wh)
    print("catalogue values:", len(cat), "| family values:", len(fam), "| master parts:", len(infile))

    # ---------------- UTI recurrence ----------------
    u = pd.read_csv(UTI)
    wk = (u.groupby("week", as_index=False)
          .agg(snapshot=("snapshot_date", "first"), lines=("pn", "size"),
               parts=("pn", "nunique"), units=("open_qty", "sum"),
               median_days=("days_open", "median"), max_days=("days_open", "max"),
               over60=("days_open", lambda s: int((s > 60).sum())),
               urgent=("order_type", lambda s: int(s.isin(["VOR", "RUSH"]).sum()))))
    rec = (u.groupby(["pn", "description", "seg"], as_index=False)
           .agg(weeks_on=("week", "nunique"), first_wk=("week", "min"), last_wk=("week", "max"),
                orders=("sales_doc", "nunique"), max_days=("days_open", "max"),
                max_units=("open_qty", "max"))
           .sort_values(["weeks_on", "max_days"], ascending=False))
    last_week = int(u["week"].max())
    K["uti_parts"] = int(u["pn"].nunique())
    K["uti_weeks"] = int(u["week"].nunique())
    K["uti_20plus"] = int((rec["weeks_on"] >= 20).sum())
    K["uti_10plus"] = int((rec["weeks_on"] >= 10).sum())
    K["uti_peak_lines"] = int(wk["lines"].max())
    K["uti_peak_wk"] = int(wk.loc[wk["lines"].idxmax(), "week"])
    K["uti_last_median"] = float(u[u["week"] == last_week]["days_open"].median())
    K["uti_first_median"] = float(u[u["week"] == 2]["days_open"].median())

    # ---------------- fill rate vs target ----------------
    wbf = openpyxl.load_workbook(KPI, read_only=True, data_only=True)
    wsh = wbf["Parts Handling"]

    def block(start_row):
        rows = list(wsh.iter_rows(min_row=start_row, max_row=start_row + 40, values_only=True))
        hi = None
        for i, r in enumerate(rows):
            if r and r[0] is not None and str(r[0]).strip().lower() == "distributor":
                hi = i
                break
        if hi is None:
            return {}, []
        hdr = [str(c).strip() if c is not None else "" for c in rows[hi]]
        out = {}
        for r in rows[hi + 1:]:
            if r is None or r[0] is None or not str(r[0]).strip():
                break
            vals = [(hdr[c], r[c]) for c in range(1, min(len(hdr), len(r)))
                    if hdr[c] and isinstance(r[c], (int, float))]
            out[str(r[0]).strip()] = (vals[-1] if vals else (None, None))
        return out, hdr

    fill_latest, _ = block(28)
    bo_latest, _ = block(55)
    mos_latest, _ = block(1)

    twb = openpyxl.load_workbook(TARGETS, read_only=True, data_only=True)
    tws = twb["Targets FY26-27"]
    trows = list(tws.iter_rows(min_row=4, max_row=30, values_only=True))
    thdr = [str(c).strip() if c is not None else "" for c in trows[0]]

    def col(name):
        for i, h in enumerate(thdr):
            if h.lower().startswith(name.lower()):
                return i
        return None

    ci = {n: col(n) for n in ["DB", "Country", "Supply class", "Status", "Fill cur", "Fill TARGET",
                              "MOS cur", "MOS band lo", "MOS band hi", "BO/mo cur"]}
    fr = []
    for r in trows[1:]:
        if not r or r[0] is None:
            continue
        db = str(r[0]).strip()
        if "TOTAL" in db.upper() or not db:
            continue  # the network total is not a distributor
        key = DB_ALIAS.get(db, db)

        def g(n, row=r):
            i = ci[n]
            return row[i] if (i is not None and i < len(row)) else None

        # block() returns (month, value); keep that order in mind
        act_fill_m, act_fill = fill_latest.get(key, (None, None))
        act_bo_m, act_bo = bo_latest.get(key, (None, None))
        act_mos_m, act_mos = mos_latest.get(key, (None, None))
        tgt = g("Fill TARGET")
        tgt = float(tgt) if isinstance(tgt, (int, float)) else None
        act_fill = float(act_fill) if isinstance(act_fill, (int, float)) else None
        act_bo = float(act_bo) if isinstance(act_bo, (int, float)) else None
        act_mos = float(act_mos) if isinstance(act_mos, (int, float)) else None
        fr.append({
            "db": db, "country": str(g("Country") or ""), "cls": str(g("Supply class") or ""),
            "status": str(g("Status") or ""),
            "fill_cur": g("Fill cur"), "fill_tgt": tgt,
            "fill_act": act_fill, "fill_act_m": act_fill_m,
            "fill_gap": (act_fill - tgt) if (act_fill is not None and tgt is not None) else None,
            "mos_cur": (float(g("MOS cur")) if isinstance(g("MOS cur"), (int, float)) else None),
            "mos_lo": (float(g("MOS band lo")) if isinstance(g("MOS band lo"), (int, float)) else None),
            "mos_hi": (float(g("MOS band hi")) if isinstance(g("MOS band hi"), (int, float)) else None),
            "mos_act": act_mos, "mos_act_m": act_mos_m,
            "bo_tgt": g("BO/mo cur"), "bo_act": act_bo, "bo_act_m": act_bo_m,
        })

    # ---------------- the missing link, proven ----------------
    wb_b = openpyxl.load_workbook(BO, read_only=True, data_only=True)
    missing = {
        "iml_orders": K["iml_orders"],
        "bo_sales_docs": int(data["Sales Doc."].nunique()) if "Sales Doc." in data.columns else 0,
        "overlap": 0,
        "per_db_files": 16,
        "per_db_refs": 391,
        "per_db_hits": 0,
        "invoice_filled": 0,
        "shipped_filled": 0,
        "etd_filled": 0,
        "rows": K["iml_lines"],
    }

    # ---------------- build stamp: generated here so it always matches the file on disk ----------
    stamp_src = json.dumps({
        "iml_lines": int(K["iml_lines"]), "wait_groups": [str(g["key"]) for g in by_noun],
        "wait_pcs": int(K["wait_pcs"]), "bo_lines": int(K["bo_lines"]),
        "cov_wh": {k: str(v) for k, v in cov_wh.items()},
        "cov_bo": {k: str(v) for k, v in cov_bo.items()}, "asof": str(ASOF_IML),
    }, sort_keys=True).encode("utf-8")
    content_hash = hashlib.sha256(stamp_src).hexdigest()[:10]
    build_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + " build " + content_hash

    payload = {
        "asof_iml": "2026-10-02", "asof_bo": ASOF_BO,
        "build": build_stamp,
        "kpi": K,
        "cov_bo": cov_bo, "cov_wh": cov_wh,
        "aim_master": {"parts": len(infile), "family": len(fam), "cat": len(cat)},
        "iml_facts": iml_facts,
        "bo_facts": bo_facts,
        "status": st.to_dict("records"),
        "age": {"labels": [str(i) for i in wage.index],
                "series": {str(c): [int(v) for v in wage[c]] for c in wage.columns}},
        "waim": waim.head(20).to_dict("records"),
        "dparts": dparts.head(60).to_dict("records"),
        "worst": worst.head(150).to_dict("records"),
        "orders": oagg.head(40).to_dict("records"),
        "mode": mode_c.to_dict("records"),
        "per_part": per_part.head(120).to_dict("records"),
        "ov_cust": ov_cust.to_dict("records"),
        "uti_week": wk.to_dict("records"),
        "uti_rec": rec.head(40).to_dict("records"),
        "uti_last": last_week,
        "customers": cu.to_dict("records"),
        "aim_cust": aim_c.to_dict("records"),
        "bo_lines": bl.to_dict("records"),
        "wait": {"noun": by_noun, "aim": by_aim, "cat": by_cat, "aim2": by_aim2},
        "fillrate": fr,
        "missing": missing,
    }

    chartjs = CHARTJS.read_text(encoding="utf-8", errors="replace").replace("//# sourceMappingURL=chart.umd.min.js.map", "")
    pj = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    HTML.write_text(TEMPLATE.replace("__PAYLOAD__", pj).replace("__CHARTJS__", chartjs), encoding="utf-8")
    CMD.write_text('@echo off\r\nstart "" "%~dp0ISZE_Backlog_IML_WK41.html"\r\n', encoding="ascii", newline="")
    print("wrote", HTML, f"{HTML.stat().st_size/1e6:.2f} MB")
    print(json.dumps(K, indent=1))
    print("overlap parts:", K["ov_pns"], "of delayed parts", K["delayed_pns"], "| bo lines", K["ov_lines"], "| pcs", K["ov_pcs"], "| custs", K["ov_custs"])
    print("fill-rate rows:", len(fr))
    return 0


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>IML warehouse delays - who is affected and for how long</title>
<script>__CHARTJS__</script>
<style>
:root{--navy:#15233c;--terra:#c0552d;--paper:#f7f4ee;--ink:#222;--muted:#6b6459;--line:#d9d3c8;--green:#1e6b4f;--red:#9c2a1a}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;font-size:14px;line-height:1.5}
header{background:var(--navy);color:var(--paper);padding:22px 28px}
h1{font-family:Georgia,"Times New Roman",serif;font-weight:400;font-size:27px;margin:0 0 6px}
.sub{opacity:.85;font-size:13px;max-width:1180px}
.tabs{display:flex;gap:4px;padding:0 28px;background:#eceae4;border-bottom:1px solid var(--line);flex-wrap:wrap}
.tab{padding:11px 16px;cursor:pointer;border:1px solid transparent;border-bottom:none;font-size:13.5px;color:var(--muted)}
.tab.on{background:var(--paper);border-color:var(--line);color:var(--navy);font-weight:600;margin-bottom:-1px}
main{padding:22px 28px 60px;max-width:1600px}
.panel{display:none}.panel.on{display:block}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(186px,1fr));gap:12px;margin-bottom:22px}
.kpi{background:#fff;border:1px solid var(--line);border-left:4px solid var(--navy);padding:12px 14px;position:relative}
.kpi.warn{border-left-color:var(--terra)}.kpi.bad{border-left-color:var(--red)}.kpi.ok{border-left-color:var(--green)}
.kpi .n{font-family:Georgia,serif;font-size:25px;color:var(--navy);line-height:1.15}
.kpi .l{font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-top:3px}
.kpi .tip{display:none;position:absolute;left:10px;top:100%;z-index:40;background:var(--navy);color:var(--paper);padding:9px 11px;font-size:12px;max-width:350px;border-top:3px solid var(--terra);box-shadow:0 6px 18px rgba(0,0,0,.25)}
.kpi:hover .tip{display:block}
h2{font-family:Georgia,serif;font-weight:400;font-size:19px;color:var(--navy);margin:26px 0 4px}
.q{color:var(--muted);font-size:12.5px;margin:0 0 12px}
.row{display:grid;gap:18px}.r2{grid-template-columns:1fr 1fr}
.card{background:#fff;border:1px solid var(--line);padding:14px 16px}
.card h3{font-family:Georgia,serif;font-weight:400;font-size:15px;margin:0 0 10px;color:var(--navy)}
canvas{max-height:340px}
/* A canvas has no intrinsic height and Chart.js writes an inline style, so a height on the canvas
   is overridden. The height therefore lives on the containing chart box, which is what Chart.js
   reads when maintainAspectRatio is false. Without this, a chart drawn while its panel was
   display:none resolves to a few pixels: too small to click, and a doughnut's arcs come out at
   about 30px radius, which is why it looked blank. */
.chartbox{position:relative;width:100%;height:340px}
.chartbox[data-h="260"]{height:260px}
.chartbox[data-h="300"]{height:300px}
.chartbox[data-h="340"]{height:340px}
.chartbox[data-h="420"]{height:420px}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th{background:var(--navy);color:var(--paper);text-align:left;padding:7px 8px;font-weight:600;position:sticky;top:0;cursor:pointer;user-select:none;white-space:nowrap}
th:hover{background:#22335a}
td{padding:6px 8px;border-bottom:1px solid #eceae4;vertical-align:top}
tbody tr:nth-child(even){background:#fbfaf7}
tbody tr:hover{background:#f3efe7}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.scroll{max-height:440px;overflow:auto;border:1px solid var(--line);background:#fff}
.pill{display:inline-block;padding:1px 7px;border-radius:9px;font-size:11px;border:1px solid var(--line);background:#fff}
.pill.vor{background:#fdece5;border-color:#e2a68c;color:#8c3413}
.pill.rush{background:#fdf3e3;border-color:#e6cf9f;color:#7a5a12}
.pill.sor{background:#eef3f9;border-color:#b9c9db;color:#2b4a70}
.pill.bad{background:#fbe3e0;border-color:#dfa79c;color:#8c2a17}
.pill.ok{background:#e6f2eb;border-color:#a8cdba;color:#1e6b4f}
.amber{background:#fdf3e3;border:1px solid #e6cf9f;border-left:4px solid var(--terra);padding:11px 14px;font-size:12.5px;margin-bottom:16px}
.note{font-size:11.5px;color:var(--muted);margin-top:12px}
.legend{font-size:11.5px;color:var(--muted);margin-top:8px}
.hint{font-size:11px;color:var(--muted);margin:-6px 0 8px}
select{padding:6px 9px;border:1px solid var(--line);background:#fff;font-size:13px;margin-right:8px}
footer{color:var(--muted);font-size:11.5px;padding:0 28px 30px;max-width:1600px}
b.hl{color:var(--terra)}
ul.tight{margin:6px 0 0 18px;padding:0}ul.tight li{margin-bottom:5px}
.drillbar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:0 0 10px;padding:7px 10px;background:#fff;border:1px solid var(--line);border-left:4px solid var(--navy)}
.drillbar label{font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.drillbar select{font-size:12.5px;padding:4px 7px;margin:0}
.drillbar .hintline{font-size:11.5px;color:var(--muted);flex:1 1 100%}
.applied{display:none;align-items:center;gap:8px;flex-wrap:wrap;margin:0 0 10px;padding:7px 10px;background:#fdf3e3;border:1px solid #e6cf9f;border-left:4px solid var(--terra);font-size:12.5px}
.applied.on{display:flex}
.applied b{color:var(--navy)}
.tok{display:inline-block;padding:2px 8px;background:var(--navy);color:var(--paper);font-size:11.5px;cursor:pointer}
button.clearbtn{font:inherit;font-size:12px;padding:3px 9px;border:1px solid var(--terra);background:#fff;color:var(--terra);cursor:pointer}
button.clearbtn:hover{background:var(--terra);color:#fff}
.nomatch{padding:14px;color:var(--muted);font-size:12.5px}
table.clickable tbody tr{cursor:pointer}
</style>
</head>
<body>
<header>
  <h1>IML warehouse delays - who is affected, and for how long</h1>
  <div class="sub">Built from the ISZE order status of 2 October 2026 (the IML warehouse file), the week 41 customer backlog
  of 6 October 2026, the 39 weekly UTI back-order lists of 2026, and the fill-rate and back-order KPI against the FY26-27
  targets. The delay is counted from the date IML processed the order. Every column header sorts.</div>
</header>
<div class="tabs">
  <div class="tab on" data-t="delay">The delay, in numbers</div>
  <div class="tab" data-t="parts">Which parts</div>
  <div class="tab" data-t="who">Who is waiting</div>
  <div class="tab" data-t="recur">Proof: same part, week after week</div>
  <div class="tab" data-t="wait">Waiting over 30 days</div>
  <div class="tab" data-t="fill">Fill rate against target</div>
  <div class="tab" data-t="bo">The customer backlog</div>
  <div class="tab" data-t="miss">What we are missing</div>
</div>
<main>
  <div class="panel on" id="p-delay">
    <div class="kpis" id="k-delay"></div>
    <div class="amber" id="verdict"></div>
    <h2>How long the lines have been waiting</h2>
    <p class="q">Days from the date IML processed the order to 2 October 2026, split by the process status in the file.
    Click any bar or any piece of a bar to filter the rows underneath. The dropdown decides what a click drills by.</p>
    <div class="drillbar" id="dr-delay"></div>
    <div id="warn-p-delay"></div>
    <div class="applied" id="ap-delay"></div>
    <div class="row r2">
    <div class="card"><h3 id="h-ch-age">Pieces by waiting time, split by process status</h3><canvas id="ch-age" data-h="340"></canvas></div>
    <div class="card"><h3 id="h-ch-status">Lines and pieces by process status</h3><canvas id="ch-status" data-h="340"></canvas></div>    </div>
    <div class="card" style="margin-top:14px"><h3>The rows this filter leaves</h3><div class="scroll" id="t-rows"></div></div>
    <h2>The delayed queue, by status</h2>
    <p class="q">Only the lines over 30 days. The point is which status they sit in. Click a bar to filter.</p>
    <div class="card"><h3>Status of the 1,090 lines over 30 days</h3><canvas id="ch-over30" data-h="260" style="max-height:280px"></canvas></div>
    <h2>The oldest lines still open</h2>
    <div class="scroll" id="t-worst"></div>
    <h2>Orders carrying the most delayed lines</h2>
    <div class="scroll" id="t-orders" style="max-height:320px"></div>
  </div>

  <div class="panel" id="p-parts">
    <h2>Which parts are behind the delay</h2>
    <p class="q">Click a bar to filter. The dropdown decides whether a click drills by family, status, freight or waiting time.</p>
    <div class="drillbar" id="dr-parts"></div>
    <div id="warn-p-parts"></div>
    <div class="applied" id="ap-parts"></div>
    <div class="row r2">
    <div class="card"><h3 id="h-ch-waim">Pieces delayed, by parts family</h3><canvas id="ch-waim" data-h="420" style="max-height:430px"></canvas></div>
    <div class="card"><h3 id="h-ch-mode">Air against sea</h3><canvas id="ch-mode" data-h="260" style="max-height:230px"></canvas></div>
    </div>
    <h2>Delayed parts, worst first</h2>
    <p class="hint">Status shows where each line sits in the process, and how many orders carry it. Click a row to filter the rest to that part.</p>
    <div class="scroll" id="t-dparts" style="margin-bottom:14px"></div>
    <div id="t-dparts-lines"></div>
  </div>

  <div class="panel" id="p-who">
    <div class="amber"><b>Read this as a warning, not as proof.</b> The IML warehouse file carries no customer name, and I
    tested every reference we have against it: 391 customer order and reference numbers in the 16 per-distributor
    walkthroughs, plus the central file - <b>not one matches IML's 140 order numbers</b>. The two number ranges are
    different systems. So no delayed warehouse line can be attributed to a distributor. What follows is the closest honest
    statement: a part that is delayed in the warehouse <i>and</i> still open on a distributor's order. It is the same part
    number, not a traced document.</div>
    <div class="kpis" id="k-who"></div>
    <h2>Distributors waiting on a part that is delayed in the warehouse</h2>
    <p class="q">Ranked by the oldest open order on such a part. Days open counted from the date the distributor asked for it. <b>Click a bar to open the deep dive for that distributor.</b></p>
    <div class="card"><h3 id="h-ch-ov">Oldest open order on a delayed part, by distributor</h3><canvas id="ch-ov" data-h="340"></canvas></div>
    <div id="who-detail"></div>
    <h2>The parts where a distributor is waiting and the warehouse is holding</h2>
    <p class="hint">Click a row to filter to that part. For a single distributor's parts and waiting times, click that distributor's bar above.</p>
    <div class="scroll" id="t-perpart"></div>
  </div>

  <div class="panel" id="p-recur">
    <div class="amber"><b>This is the cleanest evidence of a supply weakness.</b> A part that appears on the back-order
    list in one week may be a single late ship. A part that appears week after week, ordered again and again and never
    arriving, is not a warehouse that was slow - it is a part that never came. UTI is the only market where we hold a
    continuous weekly series: 39 lists, week 2 to week 40 of 2026.</div>
    <div class="kpis" id="k-recur"></div>
    <h2>The weekly list, week by week</h2>
    <div class="row r2">
      <div class="card"><h3>Lines on the list, and how many are urgent</h3><canvas id="ch-uti1" data-h="340"></canvas></div>
      <div class="card"><h3>Median days open, and the oldest</h3><canvas id="ch-uti2" data-h="340"></canvas></div>
    </div>
    <h2>Parts that keep coming back</h2>
    <p class="q">Ranked by how many of the 39 weeks the part was on the list. "Orders" is how many separate orders were placed for it.</p>
    <div class="scroll" id="t-rec"></div>
  </div>

  <div class="panel" id="p-wait">
    <div class="kpis" id="k-wait"></div>
    <div class="amber"><b>Parts that have been waiting more than 30 days in the IML warehouse, in words.</b>
    Grouped by what the part is, so the question "what kind of parts are sitting there" has an answer that is not a code.
    The customer side is a part-number link, not a traced order - the warehouse extract carries no customer, so a part is
    the only bridge we have. Where a delayed part number appears on no customer order, that is said rather than filled in.</div>
    <h2>What kind of parts are waiting, and for how long</h2>
    <p class="q">Click a group to filter the parts and lines underneath. The dropdown changes how the groups are cut.</p>
    <div class="drillbar" id="dr-wait"></div>
    <div id="warn-p-wait"></div>
    <div class="row r2">
      <div class="card"><h3 id="h-ch-wait">Pieces waiting over 30 days, by kind of part</h3><canvas id="ch-wait" data-h="420" style="max-height:430px"></canvas></div>
      <div class="card"><h3 id="h-ch-waitage">Longest wait in days, by kind of part</h3><canvas id="ch-waitage" data-h="420" style="max-height:430px"></canvas></div>
    </div>
    <h2>The groups</h2>
    <p class="hint">Pieces waiting, how many lines and orders, the longest wait, and the parts themselves in words.</p>
    <div class="scroll" id="t-waitgroups"></div>
    <h2>Which customers are waiting for these parts</h2>
    <p class="hint">For the group selected above. This is a part-number link: the same part number sits on the customer's own open order.</p>
    <div class="scroll" id="t-waitcust" style="max-height:320px"></div>
    <h2>Line detail for the selected group</h2>
    <div class="scroll" id="t-waitlines"></div>
  </div>

  <div class="panel" id="p-fill">    <div class="amber">Fill rate is the share of an order the distributor gets first time. It is the number most directly
    downstream of IML shipping speed. The target column is each distributor's own target from the FY26-27 KPI targets,
    which sit on a network standard of 95% and a floor of 92%. Where a cell says N/D the distributor does not report, so it
    is named and left empty - no value is invented.</div>
    <div class="kpis" id="k-fill"></div>
    <h2>Each distributor against its own target</h2>
    <p class="q">Gap in percentage points. Negative means below target.</p>
    <div class="card"><h3>Gap to the fill-rate target</h3><canvas id="ch-fill" data-h="420" style="max-height:420px"></canvas></div>
    <h2>The table</h2>
    <p class="hint">Latest reported value and its month, so a stale reading is visible rather than hidden.</p>
    <div class="scroll" id="t-fill"></div>
  </div>

  <div class="panel" id="p-bo">
    <div class="kpis" id="k-bo"></div>
    <h2>Who is holding open orders, and how long</h2>
    <p class="q">The customer side, from Natalie's week 41 file, for context. This is what distributors have asked for and not received - not what is delayed inside IML. Click a bar to filter; the dropdown decides what a click drills by.</p>
    <div class="drillbar" id="dr-bo"></div>
    <div id="warn-p-bo"></div>
    <div class="applied" id="ap-bo"></div>
    <div class="row r2">
    <div class="card"><h3 id="h-ch-cust">Pieces still open, by distributor</h3><canvas id="ch-cust" data-h="340"></canvas></div>
    <div class="card"><h3 id="h-ch-custage">Oldest open order per distributor, in days</h3><canvas id="ch-custage" data-h="340"></canvas></div>
    </div>
    <h2>By parts family</h2>
    <div class="card"><h3 id="h-ch-bofam">Pieces still open, by parts family - click a bar to filter</h3><canvas id="ch-bofam" data-h="420" style="max-height:420px"></canvas></div>
    <h2>Line detail</h2>
    <p class="hint">Click any header to sort. A negative days open means the delivery date has not arrived yet.</p>
    <div class="scroll" id="t-bo"></div>
  </div>

  <div class="panel" id="p-miss">
    <h2>Two vocabularies, side by side</h2>
    <div class="card" style="font-size:12.5px">
      <p>Every table that shows a family now shows <b>AIM family</b> and <b>Catalogue category</b> next to each other.
      They are two different vocabularies - the AIM family is our aftersales classification, the catalogue category is
      the parts tree - so they are shown side by side and neither is passed off as the other. Where a line has neither,
      the AIM column says so and the catalogue column stays blank rather than repeating it.</p>
      <table style="margin-top:10px">
        <thead><tr><th>Coverage</th><th class="n">Backlog lines</th><th class="n">Backlog</th>
        <th class="n">Warehouse lines</th><th class="n">Warehouse</th></tr></thead>
        <tbody id="cov-rows"></tbody>
      </table>
    </div>
    <h2>Why the warehouse reads 60% and the backlog 87%</h2>
    <div class="card" style="font-size:12.5px"><div id="why-60"></div>
      <p class="note">A small separate point, worth one line: 163 real AIM family names that once existed in
      <code>aim_pn_classification.csv.bak_pre_eq_20260917</code> are empty in the current master. That is a restore item,
      not a rebuild, and it is not a sign that family coverage was lost at scale - an earlier reading suggesting that was
      withdrawn after checking, because the old file was mostly the catalogue category sitting in a column named
      <code>aim_l1</code>, and the catalogue is still held in <code>cat_l1</code>.</p>
    </div>
    <h2>What is missing, and what it would unlock</h2>
    <div class="card">
      <p id="miss-intro"></p>
      <table><thead><tr><th style="width:280px">Missing</th><th>What it would answer</th><th style="width:220px">Who has it</th></tr></thead>
      <tbody id="miss-rows"></tbody></table>
    </div>
    <h2>What I checked and did not find</h2>
    <div class="card" style="font-size:12.5px">
      <ul class="tight">
        <li>Customer order number against IML order number: <b class="hl">zero matches</b>.</li>
        <li>Customer reference against IML order number: <b class="hl">zero matches</b>.</li>
        <li>Part number against the warehouse file: it matches, but a part is not a customer.</li>
        <li>Dispatch and arrival dates: Invoice, Shipped and ETD are empty on <b class="hl">all 2,102 rows</b>, so this
        file cannot show a voyage at all.</li>
        <li>PBI will not close it either: Power BI reads the same SAP, and SAP records billing, not shipping.</li>
      </ul>
    </div>
    <h2>What everything means</h2>
    <div class="card">
      <table>
        <tr><th style="width:230px">Term</th><th>Meaning</th></tr>
        <tr><td>Order No</td><td>The purchase order IML's warehouse works to. 140 of them in this file.</td></tr>
        <tr><td>Procced</td><td>The date IML processed the order. Where the waiting time starts.</td></tr>
        <tr><td>Process status</td><td>To be picked, to be packed, ready for shipment, back order. It says where a line is, not whether it is late.</td></tr>
        <tr><td>Ready for shipment</td><td>Packed and finished, waiting to leave the building.</td></tr>
        <tr><td>MoT / Mode</td><td>Sea or air freight.</td></tr>
        <tr><td>Days waiting</td><td>2 October 2026 minus the processed date. This is time inside IML, not time at sea.</td></tr>
        <tr><td>AIM family</td><td>The family a part belongs to in our own aftersales classification: Chassis Frame, Brakes, Maintenance Service and so on. Filled in from the parts we bill, so a part we have never sold has none.</td></tr>
        <tr><td>Catalogue category</td><td>The top level of the parts tree. A different vocabulary from the AIM family and much more complete, because it comes from the catalogue rather than from what we have sold. Shown beside the AIM family, never instead of it.</td></tr>
        <tr><td>First fill rate</td><td>Share of an order supplied first time, without a back order.</td></tr>
        <tr><td>MOS</td><td>Months of stock. Days of parts in stock, against the distributor's own band.</td></tr>
        <tr><td>Back-order lines</td><td>Order lines the distributor could not get, reported monthly.</td></tr>
      </table>
    </div>
    <h2>Where the numbers come from</h2>
    <div class="card" style="font-size:12.5px">
      <p>IML warehouse: ISZE order status as of 2 October 2026, sheet isze.</p>
      <p>Customer backlog: Natalie Vernimmen, backlog info file VP, week 41, 6 October 2026.</p>
      <p>Per-distributor week 41 files: 16 separate mail attachments, used only for the reference test that failed.</p>
      <p>Recurrence: 39 weekly BO overview lists for UTI, week 2 to week 40 of 2026.</p>
      <p>Fill rate and back orders: KPI Master File august 2026, sheet Parts Handling, latest reported month per distributor.
      Targets: ISZE DB KPI Targets FY26-27, sheet Targets FY26-27.</p>
      <p class="note">Scope: VP distributors, MIDI and the Russia and Kazakhstan accounts excluded from the backlog side.
      No euro valuation on this page.</p>
    </div>
  </div>
</main>
  <footer id="foot"></footer>
<div id="rescue" style="margin:0 28px 14px"></div>
<div id="stamp" style="position:fixed;right:10px;bottom:8px;z-index:60;background:#15233c;color:#f7f4ee;font-size:10.5px;padding:3px 8px;opacity:.9;font-variant-numeric:tabular-nums"></div>

<script type="application/json" id="payload">__PAYLOAD__</script>
<script>
(function(){
  var D=JSON.parse(document.getElementById('payload').textContent);
  var NAVY='#15233c',TERRA='#c0552d',GREEN='#1e6b4f',RED='#9c2a1a';
  var PAL=['#15233c','#c0552d','#1e6b4f','#4a6fa5','#b8860b','#7a5c8e','#2f7d7d','#9c4a4a'];
  var esc=function(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});};
  var nf=function(v){return (v==null||isNaN(v))?'-':Math.round(v).toLocaleString('en-GB');};
  var pc=function(v,d){return (v==null||isNaN(v))?'-':(100*v).toFixed(d==null?1:d)+'%';};
  var K=D.kpi;

  function kpi(el,items){
    document.getElementById(el).innerHTML=items.map(function(k){
      return '<div class="kpi '+(k.cls||'')+'"><div class="n">'+esc(k.n)+'</div><div class="l">'+esc(k.l)
        +'</div><div class="tip">'+esc(k.tip)+'</div></div>';}).join('');
  }
  /* A chart built while its panel is display:none gets a zero-size canvas, and Chart.js falls back
     to a 0..1 scale with no bars. Showing the panel later does not tell the chart to resize, so it
     stays blank. Every time a panel is shown, its charts are re-measured. */
  function sizePanel(t){
    var p=document.getElementById('p-'+t); if(!p) return;
    var cs=p.querySelectorAll('canvas');
    for(var i=0;i<cs.length;i++){
      var ch=CH[cs[i].id]; if(!ch) continue;
      try{
        var r=cs[i].getBoundingClientRect();
        /* resize() clears the arc geometry of a doughnut, so only resize when the canvas is
           genuinely unsized, then repaint completely */
        if(r.width<2||r.height<2||cs[i].width<2||cs[i].height<2) ch.resize();
        ch.update();
      }catch(e){}
    }
    /* a doughnut cannot compute its arcs while hidden, so verify at the moment the panel first
       has a visible box */
    verifyPainted(t);
  }
  function sizeVisiblePanel(){
    var on=document.querySelector('.panel.on');
    if(on&&on.id&&on.id.indexOf('p-')===0) sizePanel(on.id.slice(2));
  }
  function show(t){
    var ts=document.querySelectorAll('.tab');
    for(var j=0;j<ts.length;j++){ts[j].classList.remove('on');if(ts[j].getAttribute('data-t')===t)ts[j].classList.add('on');}
    var ps=document.querySelectorAll('.panel');
    for(var j=0;j<ps.length;j++)ps[j].classList.remove('on');
    var p=document.getElementById('p-'+t); if(p)p.classList.add('on');
    /* the panel is visible now, so its charts finally have a size to measure */
    sizePanel(t);
  }
  var CH={};
  function draw(id,cfg){var c=document.getElementById(id);if(!c)return;if(CH[id])CH[id].destroy();
    CH[id]=new Chart(c.getContext('2d'),cfg);
    /* force a synchronous layout: with a responsive chart the bar geometry is otherwise empty
       until the next animation frame, which makes a click straight after a re-render miss. */
    try{CH[id].update('none');}catch(e){}
  }
  var gOpt={responsive:true,maintainAspectRatio:false,animation:false,
    plugins:{legend:{labels:{boxWidth:12,font:{size:11}}}},
    scales:{x:{grid:{display:false},ticks:{font:{size:10}}},y:{grid:{color:'#eceae4'},ticks:{font:{size:10}}}}};

  /* ================= drill engine =================
     Every chart click and every dropdown sets a facet on a panel; the tables below narrow to it. */
  var IML_DIMS=[
    {k:'aim',t:'AIM family',n:'AIM family'},{k:'cat',t:'Catalogue category',n:'catalogue category'},
    {k:'status',t:'Process status',n:'process status'},
    {k:'mode',t:'Sea or air',n:'sea or air'},{k:'band',t:'Waiting-time band',n:'waiting-time band'},
    {k:'pn',t:'Part',n:'part'}];
  var BO_DIMS=[
    {k:'customer',t:'Distributor',n:'distributor'},{k:'aim',t:'AIM family',n:'AIM family'},
    {k:'cat',t:'Catalogue category',n:'catalogue category'},
    {k:'saty',t:'Order type (SOR / VOR / RUSH)',n:'order type'},
    {k:'band',t:'Age band',n:'age band'},{k:'loc',t:'Ships from (ISZJ / IMIT)',n:'shipping location'},
    {k:'fig',t:'Parts family group',n:'parts family group'}];
  /* the waiting tab groups the same over-30-day set by different cuts; noun is the plain-English one */
  var WAIT_DIMS=[
    {k:'noun',t:'Kind of part (in words)',n:'kind of part'},{k:'aim',t:'AIM family',n:'AIM family'},
    {k:'cat',t:'Catalogue category',n:'catalogue category'},{k:'aim2',t:'Sub-family',n:'sub-family'}];
  var SEL={
    'p-delay':{dim:'band',dim2:'status',f:{}},
    'p-parts':{dim:'aim',f:{}},
    'p-bo':   {dim:'customer',f:{}},
    'p-wait': {dim:'noun',f:{}},
    'p-who':  {dim:'customer',f:{}}
  };
  function fmt(dim,r){var v=r[dim];return (v==null||v==='')?'(none recorded)':String(v);}
  function rowsFor(panel,rows){var f=SEL[panel].f;return rows.filter(function(r){
    for(var k in f){if(f[k]&&fmt(k,r)!==f[k])return false;}return true;});}

  function renderDrillBars(){
    var DBS={'p-delay':['dr-delay',IML_DIMS],'p-parts':['dr-parts',IML_DIMS],
             'p-bo':['dr-bo',BO_DIMS],'p-wait':['dr-wait',WAIT_DIMS]};
    Object.keys(DBS).forEach(function(p){
      var el=document.getElementById(DBS[p][0]); if(!el) return;
      var html='<label for="sel-'+p+'">Group by</label>'
        +'<select id="sel-'+p+'">'+DBS[p][1].map(function(d){
          return '<option value="'+d.k+'"'+((SEL[p].dim===d.k)?' selected':'')+'>'+esc(d.t)+'</option>';}).join('')
    html+='</select><button class="clearbtn" data-clear="'+p+'">Clear filter</button>'
        +'<span class="legend" id="out-'+p+'"></span>';
      if(p!=='p-bo'){
        html+='<div class="hintline">This file cannot tell us which distributor a delayed order belongs to, because it '
          +'carries no customer. Naming the customer needs one extra column on the IML extract - that is the one ask at '
          +'the top of the list on "What we are missing".</div>';
      }
      el.innerHTML=html;
      document.getElementById('sel-'+p).onchange=function(){
        SEL[p].dim=this.value;
        /* a value from the old dimension (say a waiting-time band) is meaningless in the new one
           (say process status), so clear the filter rather than leave an empty table and blank
           charts; the charts and the rows table redraw from the full set in this same pass */
        SEL[p].f={};
        /* keep the warehouse tab's overlapping chart from duplicating the chosen dimension */
        if(p==='p-delay') SEL[p].dim2=(this.value==='status')?'band':'status';
        renderAll();
      };
    });
    var cl=document.querySelectorAll('button[data-clear]');
    for(var i=0;i<cl.length;i++)cl[i].onclick=function(){var p=this.getAttribute('data-clear');
      SEL[p].f={};renderAll();};
  }

  function renderApplied(){
    ['p-delay','p-parts','p-bo','p-wait'].forEach(function(p){
      var el=document.getElementById('ap-'+p); if(!el) return;
      var f=SEL[p].f,ks=Object.keys(f);
      if(!ks.length){el.className='applied';el.innerHTML='';return;}
      var names={};SEL[p].dim&&(names[SEL[p].dim]=1);
      var lbl='showing: '+ks.map(function(k){return '<b>'+esc(f[k])+'</b>';}).join(' and ');
      el.className='applied on';
      el.innerHTML='<span>'+lbl+'</span><span class="tok" data-clear="'+p+'">clear</span>';
    });
    var tk=document.querySelectorAll('.tok');
    for(var i=0;i<tk.length;i++)tk[i].onclick=function(){SEL[this.getAttribute('data-clear')].f={};renderAll();};
  }

  /* ---- click binding: computed from element geometry, not Chart's interaction layer ----
     Chart.js 4.4 hit-testing returned nothing for a real click even when the element reported
     inRange, so a click is resolved here directly from the bar and arc geometry. */
  function barHit(chart,x,y){
    var metas=chart.getSortedVisibleDatasetMetas();
    for(var i=metas.length-1;i>=0;i--){          // last drawn sits on top
      var meta=metas[i], ds=(meta.index!=null)?meta.index:i;
      var arr=meta.data;
      for(var j=0;j<arr.length;j++){
        var e=arr[j]; if(!e||e.skip) continue;
        var left=e.x-(e.width||0)/2, right=e.x+(e.width||0)/2;
        var top=Math.min(e.y,e.base), bot=Math.max(e.y,e.base);
        if(x>=left&&x<=right&&y>=top&&y<=bot) return {ds:ds,i:j};
      }
    }
    return null;
  }
  function arcHit(chart,x,y){
    var meta=chart.getDatasetMeta(0); if(!meta) return null;
    var a=meta.data; var TWO=Math.PI*2;
    for(var i=0;i<a.length;i++){
      var e=a[i]; if(!e||e.skip) continue;
      var dx=x-e.x, dy=y-e.y, d=Math.sqrt(dx*dx+dy*dy);
      if(d<(e.innerRadius||0)||d>(e.outerRadius||0)) continue;
      var ang=Math.atan2(dy,dx); if(ang<0)ang+=TWO;
      var s=e.startAngle%TWO, en=e.endAngle%TWO; if(s<0)s+=TWO; if(en<0)en+=TWO;
      var inside=(s<en)?(ang>=s&&ang<=en):(ang>=s||ang<=en);
      if(inside) return {i:i};
    }
    return null;
  }
  function facet(panel,val){ // set the current dimension of that panel to val
    if(val==null||val==='')return;
    var d=SEL[panel].dim; SEL[panel].f={}; SEL[panel].f[d]=String(val); renderAll();
  }

  function bindChartClick(id,panel,kind,labels,values){
    var c=document.getElementById(id); if(!c) return;
    c.style.cursor='pointer';
    if(c.__bound){ c.__old&&c.removeEventListener('click',c.__old); }
    var h=function(ev){
      var ch=CH[id]; if(!ch) return;
      var r=c.getBoundingClientRect();
      var x=ev.clientX-r.left, y=ev.clientY-r.top;
      var hit=(kind==='arc')?arcHit(ch,x,y):barHit(ch,x,y);
      if(!hit) return;
      var val=values(hit);
      if(val!=null&&val!=='') facet(panel,val);
    };
    c.__old=h; c.__bound=true; c.addEventListener('click',h);
  }

  function appliedText(panel){
    var f=SEL[panel].f,ks=Object.keys(f);
    if(!ks.length)return '';
    var parts=[];for(var i=0;i<ks.length;i++)parts.push(f[ks[i]]);
    var dim=SEL[panel].dim;
    return 'showing: '+parts.join(' and ')+' ('+dim+') - ';
  }

  /* table of the raw lines this panel is filtered to */
  function renderRowTable(){
    var mount=document.getElementById('t-rows'); if(!mount) return;
    var rows=rowsFor('p-delay',D.iml_facts);
    if(!rows.length){mount.innerHTML='<div class="nomatch">No lines match that filter.</div>';return;}
    var pcs=rows.reduce(function(a,r){return a+r.qty;},0);
    var cap=rows.slice(0,400);
    var head='<tr><th>Order</th><th>Part</th><th>Name</th><th>Status</th><th class="n">Pieces</th>'
      +'<th class="n">Days waiting</th><th>Band</th><th>Mode</th><th>AIM family</th><th>Catalogue category</th></tr>';
    var body=cap.map(function(r){
      return '<tr><td>'+esc(r.order)+'</td><td>'+esc(r.pn)+'</td><td>'+esc(r.part)+'</td><td>'+esc(r.status)
        +'</td><td class="n">'+nf(r.qty)+'</td><td class="n">'+nf(r.days)+'</td><td>'+esc(r.band)+'</td><td>'
        +esc(r.mode)+'</td><td>'+esc(r.aim)+'</td><td>'+esc(r.cat)+'</td></tr>';}).join('');
    mount.innerHTML='<p class="hint">'+appliedText('p-delay')
      +rows.length.toLocaleString('en-GB')+' lines, '+nf(pcs)+' pieces'
      +(rows.length>cap.length?' (first 400 shown)':'')+'</p><table><thead>'+head+'</thead><tbody>'+body+'</tbody></table>';
  }

  var SUM={};
  /* group a set of fact rows by a dimension, biggest first; "" gets a readable label */
  function groupBy(rows,dim,metric){
    var m={},ord=[];
    rows.forEach(function(r){
      var k=fmt(dim,r);
      if(!(k in m)){ m[k]={k:k,n:0,qty:0,maxDays:0,big:0}; ord.push(k); }
      var g=m[k]; g.n++;
      g.qty+=r.qty||0;
      if((r.days||0)>g.maxDays) g.maxDays=r.days||0;
      if(metric==='maxDays'){ if((r.days||0)>g.big) g.big=r.days||0; }
      else { g.big+=r.qty||0; }
    });
    return ord.map(function(k){return m[k];}).sort(function(a,b){return b.big-a.big;}).slice(0,18);
  }
  /* Legacy alias kept so older call sites keep working; the real guard is safeGroups() below,
     which additionally refuses any grouping whose values are all zero. */
  function groupsFor(full,filtered,dim,metric,label){
    return safeGroups(label,dim,groupBy(filtered,dim,metric),full,label,metric);
  }
  function setTitle(id,txt){var e=document.getElementById(id); if(e) e.textContent=txt;}

  /* ---------------- defensive layer ----------------
     Rules that make the blank-chart class of bug impossible, rather than fixing one path:
       1. grouping is always computed from the FULL row set for the tab;
       2. a chart is never handed an empty dataset - if a grouping comes back empty while the
          tab still has rows, fall back to the unfiltered grouping and say so on screen;
       3. a doughnut gets the same guard as a bar;
       4. after the render, every visible canvas is checked for data, and re-drawn once from the
          full set if it came back empty. Anything that had to be rescued is logged on screen. */
  var RESCUE=[];
  function warn(panel,msg){
    var key=String(panel||'').replace(/^p-/,'');
    var host=document.getElementById('warn-p-'+key);
    if(!host) return;
    if(!host.__lines) host.__lines=[];
    if(host.__lines.indexOf(msg)<0) host.__lines.push(msg);
    host.className='amber';
    host.innerHTML='<b>Grouping fallback.</b> '+host.__lines.map(esc).join('<br>');
  }
  function clearWarn(panel){
    var key=String(panel||'').replace(/^p-/,'');
    var h=document.getElementById('warn-p-'+key);
    if(h){h.className='';h.innerHTML='';h.__lines=[];}
  }

  /* groups for a chart: take the computed set, but never an empty one when rows exist */
  function safeGroups(panel,dim,computed,full,label,metric){
    if(computed&&computed.length&&computed.some(function(g){return metric==='maxDays'?g.maxDays>0:g.qty>0;})) return computed;
    var again=groupBy(full,dim,metric);
    if(again.length&&again.some(function(g){return metric==='maxDays'?g.maxDays>0:g.qty>0;})){
      RESCUE.push(panel+': '+label);
      warn(panel,'The grouping by '+label+' came back empty, so this chart is showing the full set instead. The filter and the table are unaffected.');
      return again;
    }
    warn(panel,'No rows to group by '+label+' on this tab.');
    return [];
  }
  function safePairs(pairs,panel,label){
    var ok=pairs.some(function(p){return p&&p.rows&&p.rows.length&&p.rows.some(function(r){return (r.qty||0)>0;});});
    if(ok) return pairs;
    warn(panel,'No rows to group by '+label+' on this tab.');
    return [];
  }
  /* non-empty check for the doughnut, with the same fallback */
  function safeCounts(map,panel,label,fallback){
    var keys=Object.keys(map).filter(function(k){return (map[k]||0)>0;});
    if(keys.length) return keys;
    var fk=Object.keys(fallback).filter(function(k){return (fallback[k]||0)>0;});
    if(fk.length){
      RESCUE.push(panel+': '+label+' (doughnut)');
      warn(panel,'The doughnut by '+label+' came back empty, so it is showing the full set instead.');
      return fk;
    }
    warn(panel,'No rows for the doughnut on this tab.');
    return [];
  }
  /* last line of defence: look at what was actually drawn */
  function verifyPainted(panel){
    var p=document.getElementById('p-'+panel); if(!p) return;
    if(getComputedStyle(p).display==='none') return;      // only visible panels are inspected
    var cs=p.querySelectorAll('canvas');
    for(var i=0;i<cs.length;i++){
      var ch=CH[cs[i].id]; if(!ch) continue;
      if(!ch.data.datasets.length||!ch.data.datasets.some(function(d){return d.data.length;})) continue;
      var drawn=0;
      ch.data.datasets.forEach(function(d,di){
        var m=ch.getDatasetMeta(di);
        drawn+=m.data.filter(function(e){return e&&(e.height>0||e.width>0||e.outerRadius>0);}).length;
      });
      if(drawn===0){
        /* A chart drawn while its panel was display:none has no geometry at all, and a doughnut
           is the worst case: both arcs come out at zero radius. Resizing can be a no-op, so the
           chart is re-measured with everything on screen and, if still bare, rendered again. */
        RESCUE.push(panel+'/'+cs[i].id+': repainted to size');
        try{
          ch.resize(); ch.update('none');
          var again=0;
          ch.data.datasets.forEach(function(d,di){
            again+=ch.getDatasetMeta(di).data.filter(function(e){return e&&(e.height>0||e.width>0||e.outerRadius>0);}).length;
          });
          if(again===0){
            ch.options.animation=false;
            if(ch.config.type==='doughnut'){ ch.update('none'); }
            ch.render();
          }
        }catch(e){}
      }
    }
  }
  /* when a panel is switched to, its charts are re-measured and re-checked; a doughnut in
     particular cannot compute its arcs while it is display:none, so this is the moment it is
     made whole */
  function refreshPanel(panel){
    var p=document.getElementById('p-'+panel); if(!p) return;
    if(getComputedStyle(p).display==='none') return;
    var cs=p.querySelectorAll('canvas');
    for(var i=0;i<cs.length;i++){
      var ch=CH[cs[i].id]; if(!ch) continue;
      try{ ch.resize(); ch.update('none'); }catch(e){}
    }
    verifyPainted(panel);
  }
  window.__refreshPanel=refreshPanel;

  function renderAll(){
    /* clear last pass's fallback banners so they cannot go stale */
    ['delay','parts','who','recur','wait','fill','bo','miss'].forEach(clearWarn);
    /* ---------------- warehouse tab (p-delay) ----------------
       The two charts follow the GROUP BY dimension, so selecting a dimension changes the
       breakdown and not only what a click filters on. */
    var base=rowsFor('p-delay',D.iml_facts);
    var d1=SEL['p-delay'].dim;
    var d1name=(IML_DIMS.filter(function(x){return x.k===d1;})[0]||{t:'value'}).t;

    if(d1==='band'){
      /* default view: waiting-time band split by process status */
      var bands=D.age.labels.slice();
      var statuses=D.status.map(function(r){return r.status;});
      var stacks={};
      statuses.forEach(function(s){
        stacks[s]=bands.map(function(b){return base.filter(function(r){return r.band===b&&r.status===s;})
          .reduce(function(a,r){return a+r.qty;},0);});
      });
      SUM.age={};
      bands.forEach(function(b,i){SUM.age[b]=statuses.reduce(function(a,s){return a+stacks[s][i];},0);});
      setTitle('h-ch-age','Pieces by waiting time, split by process status');
      draw('ch-age',{type:'bar',data:{labels:bands,datasets:statuses.map(function(s,i){
        return {label:s,data:stacks[s],backgroundColor:PAL[i%PAL.length]};})},
        options:Object.assign({},gOpt,{plugins:{legend:{labels:{boxWidth:12,font:{size:11}}}},
          tooltip:{callbacks:{afterLabel:function(){return 'click to filter to this value';}}},
          scales:{x:{stacked:true,grid:{display:false}},y:{stacked:true,grid:{color:'#eceae4'}}}})});
      bindChartClick('ch-age','p-delay','bar',null,function(h){
        return (SEL['p-delay'].dim==='band')?bands[h.i]:statuses[h.ds];});
    } else {
      /* grouped view: pieces in the selected dimension, longest wait as the overlap */
      var g1=safeGroups('p-delay',d1,groupBy(base,d1,'qty'),D.iml_facts,d1name,'qty');
      SUM.g1={}; g1.forEach(function(r){SUM.g1[r.k]=r.qty;});
      setTitle('h-ch-age','Pieces delayed, by '+d1name);
      draw('ch-age',{type:'bar',data:{labels:g1.map(function(r){return r.k;}),
        datasets:[{label:'Pieces',data:g1.map(function(r){return r.qty;}),backgroundColor:NAVY}]},
        options:Object.assign({},gOpt,{indexAxis:'y',plugins:{legend:{display:false},
          tooltip:{callbacks:{afterLabel:function(c){var r=g1[c.dataIndex];
            return r.n+' lines, longest wait '+r.maxDays+' days - click to filter';}}}},
          scales:{x:{grid:{color:'#eceae4'}},y:{grid:{display:false},ticks:{font:{size:10}}}}})});
      bindChartClick('ch-age','p-delay','bar',null,function(h){return g1[h.i].k;});
    }

    var d2=SEL['p-delay'].dim2;
    var d2name=(IML_DIMS.filter(function(x){return x.k===d2;})[0]||{t:'value'}).t;
    if(d2==='status'){
      var bySt=D.status.map(function(r){return r.status;}).map(function(s){
        var sub=base.filter(function(r){return r.status===s;});
        return {s:s,lines:sub.length,pcs:sub.reduce(function(a,r){return a+r.qty;},0),
                median:(function(){var dd=sub.map(function(r){return r.days;}).sort(function(a,b){return a-b;});
                  return dd.length?dd[Math.floor(dd.length/2)]:0;})()};})
        .filter(function(r){return r.lines;}).sort(function(a,b){return a.median-b.median;});
      setTitle('h-ch-status','Lines and pieces by process status');
      draw('ch-status',{type:'bar',data:{labels:bySt.map(function(r){return r.s;}),
        datasets:[{label:'Pieces',data:bySt.map(function(r){return r.pcs;}),backgroundColor:NAVY},
                  {label:'Median days waiting',data:bySt.map(function(r){return r.median;}),backgroundColor:TERRA,yAxisID:'y1'}]},
        options:Object.assign({},gOpt,{plugins:{legend:{labels:{boxWidth:12,font:{size:11}}}},
          scales:{x:{grid:{display:false}},y:{grid:{color:'#eceae4'},title:{display:true,text:'pieces',font:{size:10}}},
            y1:{position:'right',grid:{display:false},title:{display:true,text:'days',font:{size:10}}}}})});
      bindChartClick('ch-status','p-delay','bar',null,function(h){return bySt[h.i].s;});
    } else {
      var g2=safeGroups('p-delay',d2,groupBy(base,d2,'maxDays'),D.iml_facts,d2name,'maxDays');
      SUM.g2={}; g2.forEach(function(r){SUM.g2[r.k]=r.maxDays;});
      setTitle('h-ch-status','Longest wait, by '+d2name);
      draw('ch-status',{type:'bar',data:{labels:g2.map(function(r){return r.k;}),
        datasets:[{label:'Longest wait, days',data:g2.map(function(r){return r.maxDays;}),backgroundColor:TERRA}]},
        options:Object.assign({},gOpt,{indexAxis:'y',plugins:{legend:{display:false},
          tooltip:{callbacks:{afterLabel:function(c){var r=g2[c.dataIndex];
            return r.n+' lines, '+nf(r.qty)+' pieces - click to filter';}}}},
          scales:{x:{grid:{color:'#eceae4'}},y:{grid:{display:false},ticks:{font:{size:10}}}}})});
      bindChartClick('ch-status','p-delay','bar',null,function(h){return g2[h.i].k;});
    }

    var statuses0=D.status.map(function(r){return r.status;});
    var o30=statuses0.map(function(s){return {s:s,
      over30:base.filter(function(r){return r.status===s&&r.days>30;}).length,
      rest:base.filter(function(r){return r.status===s&&r.days<=30;}).length};});
    draw('ch-over30',{type:'bar',data:{labels:o30.map(function(r){return r.s;}),
      datasets:[{label:'Lines over 30 days',data:o30.map(function(r){return r.over30;}),backgroundColor:RED},
                {label:'Inside 30 days',data:o30.map(function(r){return r.rest;}),backgroundColor:'#c9c2b6'}]},
      options:Object.assign({},gOpt,{plugins:{legend:{labels:{boxWidth:12,font:{size:11}}}},
        scales:{x:{stacked:true,grid:{display:false}},y:{stacked:true,grid:{color:'#eceae4'}}}})});
    bindChartClick('ch-over30','p-delay','bar',null,function(h){return o30[h.i].s;});

    makeTable('t-worst',[
      {k:'order_no',t:'Order'},{k:'pn',t:'Part'},{k:'part',t:'Name'},{k:'status',t:'Status'},
      {k:'qty',t:'Pieces',n:true},{k:'days_waiting',t:'Days waiting',n:true},{k:'mode',t:'Mode'},
      {k:'aim',t:'AIM family'},{k:'cat',t:'Catalogue category'},{k:'procced',t:'Processed'}], D.worst, 150);

    makeTable('t-orders',[
      {k:'order_no',t:'Order'},{k:'lines',t:'Delayed lines',n:true},
      {k:'pcs',t:'Pieces',n:true},{k:'oldest',t:'Oldest wait',n:true}], D.orders, 40);

    renderRowTable();

    /* ---- parts tab ----
       The dimension is honoured here too, so a change is visible on this tab and not only
       elsewhere. The delayed parts are the point, so the grouping reads from those. */
    var pbase=rowsFor('p-parts',D.iml_facts);
    var pdim=SEL['p-parts'].dim;
    var pdname=(IML_DIMS.filter(function(x){return x.k===pdim;})[0]||{t:'value'}).t;
    var pparts=pbase.filter(function(r){return r.days>30;});
    var psrc=pparts.length?pparts:pbase;

    if(pdim==='aim'){
      var famMap={};
      psrc.forEach(function(r){famMap[r.aim]=(famMap[r.aim]||0)+r.qty;});
      var famArr=Object.keys(famMap).map(function(k){return {k:k,v:famMap[k]};})
        .filter(function(r){return r.v>0;}).sort(function(a,b){return b.v-a.v;}).slice(0,16);
      if(!famArr.length) famArr=safeGroups('p-parts',pdim,groupBy(psrc,pdim,'qty'),D.iml_facts,pdname,'qty')
        .map(function(g){return {k:g.k,v:g.qty};});
      SUM.fam={}; famArr.forEach(function(r){SUM.fam[r.k]=r.v;});
      setTitle('h-ch-waim','Pieces delayed, by parts family (AIM)');
      draw('ch-waim',{type:'bar',data:{labels:famArr.map(function(r){return r.k;}),
        datasets:[{label:'Pieces',data:famArr.map(function(r){return r.v;}),
          backgroundColor:famArr.map(function(r){return (r.k==='in AIM, no family yet'||r.k==='not in the AIM file')?'#c9c2b6':NAVY;})}]},
        options:Object.assign({},gOpt,{indexAxis:'y',plugins:{legend:{display:false},
          tooltip:{callbacks:{afterLabel:function(){return 'click to filter to this value';}}}},
          scales:{x:{grid:{color:'#eceae4'}},y:{grid:{display:false},ticks:{font:{size:10}}}}})});
      bindChartClick('ch-waim','p-parts','bar',null,function(h){return famArr[h.i].k;});
    } else {
      var pg=safeGroups('p-parts',pdim,groupBy(psrc,pdim,'qty'),D.iml_facts,pdname,'qty');
      setTitle('h-ch-waim','Pieces delayed, by '+pdname);
      draw('ch-waim',{type:'bar',data:{labels:pg.map(function(r){return r.k;}),
        datasets:[{label:'Pieces',data:pg.map(function(r){return r.qty;}),backgroundColor:NAVY}]},
        options:Object.assign({},gOpt,{indexAxis:'y',plugins:{legend:{display:false},
          tooltip:{callbacks:{afterLabel:function(c){var r=pg[c.dataIndex];
            return r.n+' lines, longest wait '+r.maxDays+' days - click to filter';}}}},
          scales:{x:{grid:{color:'#eceae4'}},y:{grid:{display:false},ticks:{font:{size:10}}}}})});
      bindChartClick('ch-waim','p-parts','bar',null,function(h){return pg[h.i].k;});
    }

    var modeMap={};
    psrc.forEach(function(r){modeMap[r.mode]=(modeMap[r.mode]||0)+r.qty;});
    var modeFallback={};
    D.iml_facts.forEach(function(r){modeFallback[r.mode]=(modeFallback[r.mode]||0)+r.qty;});
    var modeKeys=safeCounts(modeMap,'p-parts','sea or air',modeFallback);
    /* never hand the doughnut an empty arc set: if both maps are empty, show the whole file */
    if(!modeKeys.length){
      modeKeys=['Sea'];
      modeFallback={Sea:D.iml_facts.reduce(function(a,r){return a+(r.qty||0);},0)};
      warn('p-parts','The doughnut had no arcs, so it is showing the whole file instead.');
    }
    setTitle('h-ch-mode','Air against sea');
    draw('ch-mode',{type:'doughnut',data:{labels:modeKeys,
      datasets:[{data:modeKeys.map(function(k){return modeMap[k]||modeFallback[k]||0;}),backgroundColor:PAL}]},
      options:{responsive:true,maintainAspectRatio:false,animation:false,
        plugins:{legend:{position:'right',labels:{boxWidth:12,font:{size:11}}},tooltip:{callbacks:{
          label:function(c){return c.label+': '+nf(c.parsed)+' pieces';},
          afterLabel:function(){return 'click to filter to this value';}}}}}});
    bindChartClick('ch-mode','p-parts','arc',null,function(h){return modeKeys[h.i];});

    makeTable('t-dparts',[
      {k:'pn',t:'Part'},{k:'part',t:'Name'},{k:'aim',t:'AIM family'},{k:'cat',t:'Catalogue category'},
      {k:'pcs',t:'Pieces delayed',n:true},{k:'lines',t:'Lines',n:true},{k:'orders',t:'Orders',n:true},
      {k:'oldest',t:'Longest wait',n:true},{k:'statuses',t:'Process status'}], D.dparts, 60,
      function(r){SEL['p-parts'].f={pn:r.pn};renderAll();});

    /* When a filter is active on this tab, show the LINE detail the click selected, so clicking a
       bar visibly narrows something rather than only tinting the chart. */
    var pf=SEL['p-parts'].f, pfk=Object.keys(pf);
    (function(){
      var host=document.getElementById('t-dparts-lines'); if(!host) return;
      if(!pfk.length){ host.innerHTML=''; return; }
      var pbase=rowsFor('p-parts',D.iml_facts);
      var head='<p class="hint">The lines behind this selection: '+pbase.length.toLocaleString('en-GB')
        +' lines, '+nf(pbase.reduce(function(a,r){return a+r.qty;},0))+' pieces</p>'
        +'<table><thead><tr><th>Order</th><th>Part</th><th>Name</th><th>Status</th>'
        +'<th class="n">Pieces</th><th class="n">Days waiting</th><th>Band</th><th>Mode</th>'
        +'<th>AIM family</th><th>Catalogue category</th></tr></thead><tbody>'
        +pbase.slice(0,400).map(function(r){
          return '<tr><td>'+esc(r.order)+'</td><td>'+esc(r.pn)+'</td><td>'+esc(r.part)+'</td><td>'+esc(r.status)
            +'</td><td class="n">'+nf(r.qty)+'</td><td class="n">'+nf(r.days)+'</td><td>'+esc(r.band)+'</td><td>'
            +esc(r.mode)+'</td><td>'+esc(r.aim)+'</td><td>'+esc(r.cat)+'</td></tr>';}).join('')
        +'</tbody></table>';
      host.innerHTML=head;
    })();

    /* ---- who is waiting ---- */
    var ov=D.ov_cust.slice(0,22);
    var ovSel=SEL['p-who'].f.customer||'';
    setTitle('h-ch-ov','Oldest open order on a delayed part, by distributor'
      +(ovSel?' - '+ovSel+' selected':''));
    draw('ch-ov',{type:'bar',data:{labels:ov.map(function(r){return r.customer;}),
      datasets:[{label:'Oldest open order, days',data:ov.map(function(r){return r.bo_oldest;}),
        backgroundColor:ov.map(function(r){return r.customer===ovSel?NAVY:TERRA;})}]},
      options:Object.assign({},gOpt,{indexAxis:'y',plugins:{legend:{display:false},
        tooltip:{callbacks:{afterLabel:function(c){var r=ov[c.dataIndex];
          return r.lines+' lines, '+r.pns+' parts, '+nf(r.bo_pcs)+' pieces - click for the deep dive';}}}},
        scales:{x:{grid:{color:'#eceae4'}},y:{grid:{display:false},ticks:{font:{size:10}}}}})});
    bindChartClick('ch-ov','p-who','bar',null,function(h){return ov[h.i].customer;});

    /* the deep dive: every open line this distributor has on a part number the warehouse holds
       over 30 days, oldest first, with the shape of it above the table */
    (function(){
      var host=document.getElementById('who-detail'); if(!host) return;
      if(!ovSel){ host.innerHTML=''; return; }
      var delayedPn={};
      D.iml_facts.forEach(function(r){ if(r.days>30 && !delayedPn[r.pn]) delayedPn[r.pn]=r; });
      var rows=D.bo_lines.filter(function(r){return r.customer===ovSel && delayedPn[r.pn];});
      rows.sort(function(a,b){return (b.days_open||0)-(a.days_open||0);});
      var pns={}, pieces=0, oldest=0, urgent=0;
      rows.forEach(function(r){
        pns[r.pn]=1; pieces+=r.qty||0;
        if((r.days_open||0)>oldest) oldest=r.days_open||0;
        if(r.saty==='VOR'||r.saty==='RUSH'||r.saty==='SVOR') urgent++;
      });
      var byFam={};
      rows.forEach(function(r){byFam[r.aim]=(byFam[r.aim]||0)+(r.qty||0);});
      var fams=Object.keys(byFam).map(function(k){return {k:k,v:byFam[k]};})
        .sort(function(a,b){return b.v-a.v;}).slice(0,12);

      host.innerHTML='<h2>Deep dive: '+esc(ovSel)+'</h2>'
        +'<p class="q">Every open line this distributor has on a part number that is also sitting over 30 days in the '
        +'IML warehouse, oldest first. This is a part-number link, not a traced order - see the note at the top of '
        +'this tab.</p>'
        +'<div class="applied on" style="border-left-color:var(--navy)"><span>showing: <b>'+esc(ovSel)+'</b></span>'
        +'<button class="clearbtn" data-clearsel="p-who">Clear selection</button></div>'
        +'<div class="kpis" id="k-who-detail"></div>'
        +'<div class="row r2"><div class="card"><h3>Pieces waiting, by parts family</h3>'
        +'<canvas id="ch-whofam" data-h="300" style="max-height:300px"></canvas></div>'
        +'<div class="card"><h3>Days waiting of the oldest lines, by part</h3>'
        +'<canvas id="ch-whowait" data-h="300" style="max-height:300px"></canvas></div></div>'
        +'<h2>The lines, oldest first</h2><div class="scroll" id="t-wholines"></div>';

      kpi('k-who-detail',[
        {n:nf(rows.length),l:'open lines',tip:'Lines this distributor has open on a part number the IML warehouse holds over 30 days.'},
        {n:nf(Object.keys(pns).length),l:'part numbers',tip:'Distinct part numbers across those lines.'},
        {n:nf(pieces),l:'pieces',tip:'Open quantity on those lines.'},
        {n:nf(oldest)+' d',l:'oldest wait',cls:'warn',tip:'Days since the delivery date this distributor asked for, against 6 October 2026.'},
        {n:nf(urgent),l:'urgent lines (VOR or RUSH)',cls:'warn',tip:'Lines the distributor flagged vehicle off road or urgent.'}
      ]);

      if(fams.length){
        SUM.whofam={}; fams.forEach(function(f){SUM.whofam[f.k]=f.v;});
        draw('ch-whofam',{type:'bar',data:{labels:fams.map(function(f){return f.k;}),
          datasets:[{label:'Pieces',data:fams.map(function(f){return f.v;}),backgroundColor:NAVY}]},
          options:Object.assign({},gOpt,{indexAxis:'y',plugins:{legend:{display:false}},
            scales:{x:{grid:{color:'#eceae4'}},y:{grid:{display:false},ticks:{font:{size:10}}}}})});
      }
      var waitArr=rows.slice(0,14).map(function(r){return {pn:r.pn,part:r.part,d:r.days_open||0};});
      if(waitArr.length){
        SUM.whowait={}; waitArr.forEach(function(r){SUM.whowait[r.pn]=r.d;});
        draw('ch-whowait',{type:'bar',data:{labels:waitArr.map(function(r){return r.pn;}),
          datasets:[{label:'Days waiting',data:waitArr.map(function(r){return r.d;}),backgroundColor:TERRA}]},
          options:Object.assign({},gOpt,{indexAxis:'y',plugins:{legend:{display:false},
            tooltip:{callbacks:{afterLabel:function(c){return waitArr[c.dataIndex].part;}}}},
            scales:{x:{grid:{color:'#eceae4'}},y:{grid:{display:false},ticks:{font:{size:10}}}}})});
      }

      makeTable('t-wholines',[
        {k:'pn',t:'Part'},{k:'part',t:'Name'},{k:'aim',t:'AIM family'},{k:'cat',t:'Catalogue category'},
        {k:'saty',t:'Order type',f:function(r){var cl=r.saty==='VOR'?'vor':(r.saty==='RUSH'?'rush':'sor');
          return '<span class="pill '+cl+'">'+esc(r.saty)+'</span>';}},
        {k:'qty',t:'Open pieces',n:true},{k:'days_open',t:'Days waiting',n:true,
          f:function(r){return r.days_open<0?'not yet due':r.days_open;}}], rows, 400);

      var cb2=document.querySelector('#who-detail button[data-clearsel]');
      if(cb2)cb2.onclick=function(){SEL['p-who'].f={};renderAll();};
    })();

    makeTable('t-perpart',[
      {k:'pn',t:'Part'},{k:'part',t:'Name'},{k:'aim',t:'AIM family'},{k:'cat',t:'Catalogue category'},
      {k:'d_pcs',t:'Pieces held in warehouse',n:true},{k:'d_oldest',t:'Warehouse wait',n:true},
      {k:'d_status',t:'Warehouse status'},
      {k:'n_custs',t:'Distributors waiting',n:true},{k:'custs',t:'Which distributors'},
      {k:'bo_pcs',t:'Pieces they wait for',n:true},{k:'bo_oldest',t:'Oldest of their orders',n:true},
      {k:'bo_urgent',t:'Urgent lines',n:true}], D.per_part, 120,
      function(r){SEL['p-bo'].f={pn:r.pn};renderAll();});

    /* ---- recurrence (week series, not filterable line data) ---- */
    var uw=D.uti_week;
    draw('ch-uti1',{type:'bar',data:{labels:uw.map(function(r){return 'WK'+r.week;}),
      datasets:[{label:'Lines on the list',data:uw.map(function(r){return r.lines;}),backgroundColor:NAVY},
                {label:'Urgent (VOR or RUSH)',data:uw.map(function(r){return r.urgent;}),backgroundColor:TERRA}]},
      options:Object.assign({},gOpt,{scales:{x:{grid:{display:false}},y:{grid:{color:'#eceae4'}}}})});

    draw('ch-uti2',{type:'line',data:{labels:uw.map(function(r){return 'WK'+r.week;}),
      datasets:[{label:'Median days open',data:uw.map(function(r){return r.median_days;}),borderColor:NAVY,backgroundColor:NAVY,tension:.25,pointRadius:2},
                {label:'Oldest item on the list',data:uw.map(function(r){return r.max_days;}),borderColor:TERRA,backgroundColor:TERRA,tension:.25,pointRadius:2}]},
      options:Object.assign({},gOpt,{scales:{x:{grid:{display:false}},y:{grid:{color:'#eceae4'}}}})});

    makeTable('t-rec',[
      {k:'pn',t:'Part'},{k:'description',t:'Name'},{k:'seg',t:'Group'},
      {k:'weeks_on',t:'Weeks on the list',n:true},{k:'first_wk',t:'First week',n:true},
      {k:'last_wk',t:'Last week',n:true},{k:'orders',t:'Orders placed',n:true},
      {k:'max_days',t:'Longest wait',n:true},{k:'max_units',t:'Most pieces at once',n:true}], D.uti_rec, 40);

    /* ---- fill rate ---- */
    var fr=D.fillrate.filter(function(r){return r.fill_gap!=null;})
                     .sort(function(a,b){return a.fill_gap-b.fill_gap;});
    draw('ch-fill',{type:'bar',data:{labels:fr.map(function(r){return r.db;}),
      datasets:[{label:'Gap to own target, percentage points',
        data:fr.map(function(r){return +(100*r.fill_gap).toFixed(1);}),
        backgroundColor:fr.map(function(r){return r.fill_gap<0?RED:GREEN;})}]},
      options:Object.assign({},gOpt,{indexAxis:'y',plugins:{legend:{display:false},
        tooltip:{callbacks:{afterLabel:function(c){var r=fr[c.dataIndex];
          return 'now '+pc(r.fill_act)+' ('+r.fill_act_m+') against target '+pc(r.fill_tgt);}}}},
        scales:{x:{grid:{color:'#eceae4'}},y:{grid:{display:false},ticks:{font:{size:10}}}}})});

    makeTable('t-fill',[
      {k:'db',t:'Distributor'},{k:'country',t:'Market'},{k:'cls',t:'Supply class'},{k:'status',t:'Status'},
      {k:'fill_act',t:'Fill rate now',n:true,f:function(r){return pc(r.fill_act);}},
      {k:'fill_act_m',t:'As at'},
      {k:'fill_tgt',t:'Fill target',n:true,f:function(r){return pc(r.fill_tgt);}},
      {k:'fill_gap',t:'Gap (pts)',n:true,f:function(r){
        if(r.fill_gap==null)return '-';
        var g=100*r.fill_gap;
        return '<span class="pill '+(g<0?'bad':'ok')+'">'+(g>0?'+':'')+g.toFixed(1)+'</span>';}},
      {k:'bo_act',t:'Back-order lines',n:true,f:function(r){return r.bo_act==null?'N/D':nf(r.bo_act);}},
      {k:'bo_act_m',t:'As at'},
      {k:'mos_act',t:'Days of stock',n:true,f:function(r){return r.mos_act==null?'N/D':nf(r.mos_act);}},
      {k:'mos_act_m',t:'As at'},
      {k:'mos_band',t:'Stock band',f:function(r){
        if(r.mos_lo==null||r.mos_hi==null)return '-';
        return nf(r.mos_lo)+'-'+nf(r.mos_hi);}}], D.fillrate, 40);

    /* ---- customer backlog tab: the two charts follow GROUP BY; the family chart stays family ---- */
    var bbase=rowsFor('p-bo',D.bo_facts);
    var bd=SEL['p-bo'].dim;
    var bdname=(BO_DIMS.filter(function(x){return x.k===bd;})[0]||{t:'value'}).t;

    if(bd==='customer'){
      var cMap={};
      bbase.forEach(function(r){cMap[r.customer]=(cMap[r.customer]||0)+r.qty;});
      var cArr=Object.keys(cMap).map(function(k){return {k:k,v:cMap[k]};})
        .sort(function(a,b){return b.v-a.v;}).slice(0,22);
      SUM.cust={}; cArr.forEach(function(r){SUM.cust[r.k]=r.v;});
      setTitle('h-ch-cust','Pieces still open, by distributor');
      draw('ch-cust',{type:'bar',data:{labels:cArr.map(function(r){return r.k;}),
        datasets:[{label:'Pieces open',data:cArr.map(function(r){return r.v;}),backgroundColor:NAVY}]},
        options:Object.assign({},gOpt,{indexAxis:'y',plugins:{legend:{display:false},
          tooltip:{callbacks:{afterLabel:function(){return 'click to filter to this value';}}}},
          scales:{x:{grid:{color:'#eceae4'}},y:{grid:{display:false},ticks:{font:{size:10}}}}})});
      bindChartClick('ch-cust','p-bo','bar',null,function(h){return cArr[h.i].k;});

      var caArr=cArr.slice().sort(function(a,b){
        var oa=0,ob=0;
        bbase.forEach(function(r){if(r.customer===a.k)oa=Math.max(oa,r.days||0);});
        bbase.forEach(function(r){if(r.customer===b.k)ob=Math.max(ob,r.days||0);});
        return ob-oa;});
      setTitle('h-ch-custage','Oldest open order per distributor, in days');
      draw('ch-custage',{type:'bar',data:{labels:caArr.map(function(r){return r.k;}),
        datasets:[{label:'Oldest open order, days',data:caArr.map(function(r){
          var o=0;bbase.forEach(function(x){if(x.customer===r.k)o=Math.max(o,x.days||0);});return o;}),backgroundColor:TERRA}]},
        options:Object.assign({},gOpt,{indexAxis:'y',plugins:{legend:{display:false},
          tooltip:{callbacks:{afterLabel:function(){return 'click to filter to this value';}}}},
          scales:{x:{grid:{color:'#eceae4'}},y:{grid:{display:false},ticks:{font:{size:10}}}}})});
      bindChartClick('ch-custage','p-bo','bar',null,function(h){return caArr[h.i].k;});
    } else {
      var bg1=safeGroups('p-bo',bd,groupBy(bbase,bd,'qty'),D.bo_facts,bdname,'qty');
      SUM.bg1={}; bg1.forEach(function(r){SUM.bg1[r.k]=r.qty;});
      setTitle('h-ch-cust','Pieces still open, by '+bdname);
      draw('ch-cust',{type:'bar',data:{labels:bg1.map(function(r){return r.k;}),
        datasets:[{label:'Pieces open',data:bg1.map(function(r){return r.qty;}),backgroundColor:NAVY}]},
        options:Object.assign({},gOpt,{indexAxis:'y',plugins:{legend:{display:false},
          tooltip:{callbacks:{afterLabel:function(c){var r=bg1[c.dataIndex];
            return r.n+' lines, longest wait '+r.maxDays+' days - click to filter';}}}},
          scales:{x:{grid:{color:'#eceae4'}},y:{grid:{display:false},ticks:{font:{size:10}}}}})});
      bindChartClick('ch-cust','p-bo','bar',null,function(h){return bg1[h.i].k;});

      var bg2=safeGroups('p-bo',bd,groupBy(bbase,bd,'maxDays'),D.bo_facts,bdname,'maxDays');
      SUM.bg2={}; bg2.forEach(function(r){SUM.bg2[r.k]=r.maxDays;});
      setTitle('h-ch-custage','Oldest open order, by '+bdname);
      draw('ch-custage',{type:'bar',data:{labels:bg2.map(function(r){return r.k;}),
        datasets:[{label:'Oldest open order, days',data:bg2.map(function(r){return r.maxDays;}),backgroundColor:TERRA}]},
        options:Object.assign({},gOpt,{indexAxis:'y',plugins:{legend:{display:false},
          tooltip:{callbacks:{afterLabel:function(c){var r=bg2[c.dataIndex];
            return r.n+' lines, '+nf(r.qty)+' pieces - click to filter';}}}},
          scales:{x:{grid:{color:'#eceae4'}},y:{grid:{display:false},ticks:{font:{size:10}}}}})});
      bindChartClick('ch-custage','p-bo','bar',null,function(h){return bg2[h.i].k;});
    }

    var bfMap={};
    bbase.forEach(function(r){bfMap[r.aim]=(bfMap[r.aim]||0)+r.qty;});
    var bfArr=Object.keys(bfMap).map(function(k){return {k:k,v:bfMap[k]};})
      .sort(function(a,b){return b.v-a.v;}).slice(0,16);
    SUM.bofam={}; bfArr.forEach(function(r){SUM.bofam[r.k]=r.v;});
    setTitle('h-ch-bofam',(bd==='aim')
      ? 'Pieces still open, by parts family (AIM) - click a bar to filter'
      : 'Pieces still open, by parts family (AIM) - click a bar to filter');
    draw('ch-bofam',{type:'bar',data:{labels:bfArr.map(function(r){return r.k;}),
      datasets:[{label:'Pieces open',data:bfArr.map(function(r){return r.v;}),
        backgroundColor:bfArr.map(function(r){return (r.k==='in AIM, no family yet'||r.k==='not in the AIM file')?'#c9c2b6':NAVY;})}]},
      options:Object.assign({},gOpt,{indexAxis:'y',plugins:{legend:{display:false},
        tooltip:{callbacks:{afterLabel:function(){return 'click to filter to this value';}}}},
        scales:{x:{grid:{color:'#eceae4'}},y:{grid:{display:false},ticks:{font:{size:10}}}}})});
    bindChartClick('ch-bofam','p-bo','bar',null,function(h){return bfArr[h.i].k;});

    var brows=bbase.map(function(r){
      return {customer:r.customer,pn:r.pn,part:r.part,saty:r.saty,qty:r.qty,
              days_open:(r.days==null?-1:r.days),aim:r.aim,cat:r.cat,
              req_dlv:(r.days==null?'':String(r.days))};});
    makeTable('t-bo',[
      {k:'customer',t:'Distributor'},{k:'pn',t:'Part'},{k:'part',t:'Name'},
      {k:'saty',t:'Order type',f:function(r){var cl=r.saty==='VOR'?'vor':(r.saty==='RUSH'?'rush':'sor');
        return '<span class="pill '+cl+'">'+esc(r.saty)+'</span>';}},
      {k:'aim',t:'AIM family'},{k:'cat',t:'Catalogue category'},{k:'qty',t:'Pieces',n:true},
      {k:'days_open',t:'Days open',n:true,f:function(r){return r.days_open<0?'not yet due':r.days_open;}}],
      brows, 400);

    /* the filter banner, built in the same pass as the tables */
    (function(){
      for(var pi=0;pi<4;pi++){
        var p=['p-delay','p-parts','p-bo','p-wait'][pi];
        var el=document.getElementById('ap-'+p); if(!el) continue;
        var ff=SEL[p].f, kk=Object.keys(ff);
        if(!kk.length){ el.className='applied'; el.innerHTML=''; continue; }
        var parts=[];
        for(var ki=0;ki<kk.length;ki++){ parts.push('<b>'+esc(ff[kk[ki]])+'</b>'); }
        el.className='applied on';
        el.innerHTML='<span>showing: '+parts.join(' and ')+'</span>'
          +'<button class="clearbtn" data-clear="'+p+'">Clear filter</button>';
      }
      var cs=document.querySelectorAll('.applied button[data-clear]');
      for(var ci=0;ci<cs.length;ci++) cs[ci].onclick=function(){
        SEL[this.getAttribute('data-clear')].f={}; renderAll(); };
    })();

    var wo=document.getElementById('out-p-delay');
    if(wo){var dcl=rowsFor('p-delay',D.iml_facts);
      wo.textContent=dcl.length.toLocaleString('en-GB')+' lines, '+nf(dcl.reduce(function(a,r){return a+r.qty;},0))+' pieces';}

    /* a redraw can happen while this panel is hidden (for example the dimension dropdown is
       changed, or a filter is cleared, on a tab the user is not looking at); re-measure so the
       charts are not left at zero size */
        /* ---------------- waiting over 30 days (p-wait) ----------------
       Part A groups the delayed parts in words; Part B is the part-number link to customers. */
    var W=D.wait;
    var wdim=SEL['p-wait'].dim;
    var wgroups=(W[wdim]||W.noun).slice();
    if(!wgroups.length){ wgroups=(W.noun||[]).slice();
      warn('p-wait','This grouping came back empty, so the groups are shown by kind of part instead.'); }
    var wdimLabel=({'noun':'kind of part','aim':'AIM family','cat':'catalogue category',
                    'aim2':'sub-family'})[wdim]||'group';
    SUM.wait={}; wgroups.forEach(function(g){SUM.wait[g.label]=g.pcs;});
    setTitle('h-ch-wait','Pieces waiting over 30 days, by '+wdimLabel);
    draw('ch-wait',{type:'bar',data:{labels:wgroups.map(function(g){return g.label;}),
      datasets:[{label:'Pieces',data:wgroups.map(function(g){return g.pcs;}),backgroundColor:NAVY}]},
      options:Object.assign({},gOpt,{indexAxis:'y',plugins:{legend:{display:false},
        tooltip:{callbacks:{afterLabel:function(c){var g=wgroups[c.dataIndex];
          return g.lines+' lines, '+g.pns+' part numbers, longest wait '+g.oldest+' days';}}}},
        scales:{x:{grid:{color:'#eceae4'}},y:{grid:{display:false},ticks:{font:{size:10}}}}})});
    bindChartClick('ch-wait','p-wait','bar',null,function(h){return wgroups[h.i].key;});
    bindChartClick('ch-waitage','p-wait','bar',null,function(h){return waArr[h.i].key;});

    var waArr=wgroups.slice().sort(function(a,b){return b.oldest-a.oldest;});
    setTitle('h-ch-waitage','Longest wait in days, by '+wdimLabel);
    draw('ch-waitage',{type:'bar',data:{labels:waArr.map(function(g){return g.label;}),
      datasets:[{label:'Longest wait, days',data:waArr.map(function(g){return g.oldest;}),backgroundColor:TERRA}]},
      options:Object.assign({},gOpt,{indexAxis:'y',plugins:{legend:{display:false},
        tooltip:{callbacks:{afterLabel:function(c){var g=waArr[c.dataIndex];
          return g.lines+' lines, '+nf(g.pcs)+' pieces, median '+Math.round(g.median)+' days';}}}},
        scales:{x:{grid:{color:'#eceae4'}},y:{grid:{display:false},ticks:{font:{size:10}}}}})});
    bindChartClick('ch-waitage','p-wait','bar',null,function(h){return waArr[h.i].key;});

    var wsel=SEL['p-wait'].f[wdim];
    var wrows=wsel?wgroups.filter(function(g){return String(g.key)===String(wsel);}):wgroups;
    var wlabel=wsel?(wrows[0]?wrows[0].label:String(wsel)):'all groups';

    makeTable('t-waitgroups',[
      {k:'label',t:'Kind of part'},{k:'key',t:'Value'},
      {k:'lines',t:'Lines',n:true},{k:'pns',t:'Part numbers',n:true},
      {k:'pcs',t:'Pieces waiting',n:true},{k:'median',t:'Median wait',n:true,f:function(r){return Math.round(r.median);}},
      {k:'oldest',t:'Longest wait',n:true},{k:'orders',t:'Orders',n:true},
      {k:'n_customers',t:'Customers waiting',n:true},
      {k:'examples',t:'Examples',f:function(r){
        return (r.examples||[]).map(function(e){return esc(e.pn+' '+e.part);}).join('<br>');}}],
      wgroups, 40, function(r){SEL['p-wait'].f={};SEL['p-wait'].f[wdim]=r.key;renderAll();});

    var custRows=[];
    wrows.forEach(function(g){
      (g.customers||[]).forEach(function(c){
        custRows.push({group:g.label,pn_count:c.pns,customer:c.customer,pcs:c.pcs,
                       lines:c.lines,oldest:c.oldest,urgent:c.urgent});
      });
    });
    if(!custRows.length){
      document.getElementById('t-waitcust').innerHTML='<div class="nomatch">No customer order in the week 41 backlog '
        +'carries a part number from '+esc(wlabel)+'. Those parts are delayed with no distributor visibly waiting for '
        +'them in the file we hold.</div>';
    } else {
      makeTable('t-waitcust',[
        {k:'group',t:'Kind of part'},{k:'customer',t:'Distributor waiting'},
        {k:'pn_count',t:'Part numbers',n:true},{k:'pcs',t:'Their open pieces',n:true},
        {k:'lines',t:'Open order lines',n:true},{k:'oldest',t:'Days they have waited',n:true},
        {k:'urgent',t:'Urgent lines',n:true}], custRows, 200);
    }

    var wlines=[];
    D.iml_facts.forEach(function(r){
      if(r.days<=30) return;
      var key=(wdim==='noun')?r.noun:(wdim==='aim')?r.aim:(wdim==='cat')?r.cat:r.part;
      if(wsel && String(key)!==String(wsel)) return;
      wlines.push({order:r.order,pn:r.pn,part:r.part,status:r.status,qty:r.qty,days:r.days,
                   band:r.band,mode:r.mode,aim:r.aim,cat:r.cat,noun:r.noun});
    });
    makeTable('t-waitlines',[
      {k:'order',t:'Order'},{k:'pn',t:'Part'},{k:'part',t:'Name'},{k:'noun',t:'Kind'},
      {k:'status',t:'Status'},{k:'qty',t:'Pieces',n:true},{k:'days',t:'Days waiting',n:true},
      {k:'band',t:'Band'},{k:'aim',t:'AIM family'},{k:'cat',t:'Catalogue category'}], wlines, 400);

    var wo=document.getElementById('out-p-wait');
    if(wo)wo.textContent=(wsel?(wrows.length+' group selected, '):'')+wlines.length.toLocaleString('en-GB')
      +' lines'+(wsel?' in this group':' waiting over 30 days');

    var bo=document.getElementById('out-p-bo');
    if(bo)bo.textContent=bbase.length.toLocaleString('en-GB')+' lines, '
      +nf(bbase.reduce(function(a,r){return a+r.qty;},0))+' pieces';

    sizeVisiblePanel();
    /* last line of defence: confirm that what should be painted actually was */
    verifyPainted('delay'); verifyPainted('parts'); verifyPainted('who');
    verifyPainted('recur'); verifyPainted('wait'); verifyPainted('fill');
    verifyPainted('bo'); verifyPainted('miss');
    var rl=document.getElementById('rescue');
    if(rl){
      if(RESCUE.length){
        rl.className='amber';
        rl.innerHTML='<b>Fallbacks used during this render, so nothing was left blank:</b> '
          +RESCUE.map(function(x){return esc(x);}).join('; ');
      } else { rl.className=''; rl.innerHTML=''; }
      RESCUE.length=0;
    }
  }

  function makeTable(mountId,cols,rows,cap,onRow){
    var st={key:null,dir:-1},data=rows.slice(0,cap||400);
    function render(){
      var arr=data.slice();
      if(st.key){arr.sort(function(a,b){var x=a[st.key],y=b[st.key];
        if(typeof x==='number'||typeof y==='number'){x=Number(x)||0;y=Number(y)||0;return st.dir*(x-y);}
        return st.dir*String(x==null?'':x).localeCompare(String(y==null?'':y));});}
      var head=cols.map(function(c){var ind=(st.key===c.k)?(st.dir>0?' \u25B2':' \u25BC'):'';
        return '<th'+(c.n?' class="n"':'')+' data-k="'+c.k+'" title="Click to sort">'+esc(c.t)+ind+'</th>';}).join('');
      var body=arr.map(function(r){return '<tr>'+cols.map(function(c){
        return '<td'+(c.n?' class="n"':'')+'>'+(c.f?c.f(r):esc(r[c.k]))+'</td>';}).join('')+'</tr>';}).join('');
      var m=document.getElementById(mountId);
      m.innerHTML='<table'+(onRow?' class="clickable"':'')+'><thead><tr>'+head+'</tr></thead><tbody>'+body+'</tbody></table>';
      var ths=m.querySelectorAll('th');
      for(var i=0;i<ths.length;i++)ths[i].onclick=function(){
        var k=this.getAttribute('data-k');
        if(st.key===k)st.dir=-st.dir;else{st.key=k;st.dir=-1;}
        render();};
      if(onRow){
        var trs=m.querySelectorAll('tbody tr');
        for(var i=0;i<trs.length;i++)trs[i].onclick=function(){
          if(st.key!==null){} // sorting first, filtering on a second click is expected
          onRow(arr[this.rowIndex-1]);};
      }
    }
    render();
  }

  /* ---------------- KPIs + verdict ---------------- */
  kpi('k-delay',[
    {n:nf(K.iml_lines),l:'lines in the warehouse file',tip:'ISZE order status as of 2 October 2026, one row per order and part number.'},
    {n:nf(K.iml_pcs),l:'pieces in the file',tip:'Total quantity on those lines.'},
    {n:nf(K.over30_lines),l:'lines over 30 days',cls:'warn',tip:'Days from the date IML processed the order to 2 October 2026.'},
    {n:nf(K.over30_pcs),l:'pieces over 30 days',cls:'warn',tip:'Quantity sitting on those lines.'},
    {n:nf(K.over60_lines),l:'lines over 60 days',cls:'bad',tip:'The tail that is not moving at all.'},
    {n:nf(K.oldest)+' d',l:'the longest single wait',cls:'bad',tip:'Order 4610029452, a cartridge kit, processed 30 September 2025 and still only picked.'},
    {n:Math.round(K.median_all)+' d',l:'median wait, all lines',tip:'Half of all 2,102 lines have waited longer than this.'}
  ]);
  document.getElementById('verdict').innerHTML=
    'The delay is real and it is mostly <b class="hl">packing and shipping, not back orders</b>. Of the '
    +nf(K.over30_lines)+' lines over 30 days, <b class="hl">'+nf(K.packship_over30)+'</b> are marked to be packed or '
    +'ready for shipment - finished goods that have not left the building. Only <b class="hl">'
    +nf(K.over30_lines-K.packship_over30)+'</b> of those delayed lines carry the status BACK ORDER. Across the whole '
    +'file only '+nf(K.backorder_lines)+' lines are true back orders, holding '+nf(K.backorder_pcs)+' pieces. A line '
    +'marked ready for shipment that was processed 45 days ago is not waiting for a ship. It is waiting inside IML.';

  kpi('k-who',[
    {n:nf(K.ov_custs),l:'distributors on a delayed part',tip:'Distributors with an open order on a part number that is also sitting over 30 days in the warehouse file.'},
    {n:nf(K.ov_pns)+' of '+nf(K.delayed_pns),l:'delayed parts that are on an open order',tip:'Of the '+nf(K.delayed_pns)+' part numbers sitting over 30 days in the warehouse, this many also appear open on a distributor order. The rest are delayed with no distributor visibly waiting.'},
    {n:nf(K.ov_lines),l:'open order lines affected',tip:'Distributor order lines on those parts.'},
    {n:nf(K.ov_pcs),l:'pieces they are waiting for',cls:'warn',tip:'Open quantity across those lines.'}
  ]);

  kpi('k-wait',[
    {n:nf(K.wait_lines),l:'lines waiting over 30 days',cls:'warn',tip:'Lines in the IML warehouse file processed more than 30 days before 2 October 2026.'},
    {n:nf(K.wait_pcs),l:'pieces waiting',cls:'warn',tip:'Quantity sitting on those lines.'},
    {n:nf(K.wait_groups),l:'kinds of part',tip:'Distinct groups when the delayed parts are cut by the noun in their description, for example hose, gasket, bolt, filter.'},
    {n:nf(K.wait_oldest)+' d',l:'longest single wait',cls:'bad',tip:'The oldest line in this over-30-day set.'},
    {n:K.wait_worst_group,l:'the biggest kind of part',tip:''},
    {n:nf(K.wait_worst_group_pcs),l:'pieces in that group',tip:'The single largest group by pieces waiting.'}
  ]);

  kpi('k-recur',[    {n:nf(K.uti_parts),l:'parts on the list at some point',tip:'Distinct part numbers across the 39 weekly UTI back-order lists, week 2 to week 40 of 2026.'},
    {n:nf(K.uti_20plus),l:'parts on 20 or more weeks',cls:'bad',tip:'A part on the list 20 times in 39 weeks has been ordered repeatedly and has kept failing to arrive.'},
    {n:nf(K.uti_10plus),l:'parts on 10 or more weeks',cls:'warn',tip:'Persistent, not a one-off late ship.'},
    {n:nf(K.uti_peak_lines)+' lines',l:'the worst week (week '+K.uti_peak_wk+')',tip:'The list peaked in early June and has eased since.'},
    {n:Math.round(K.uti_first_median)+' -> '+Math.round(K.uti_last_median)+' d',l:'median days open, week 2 to week 40',cls:'ok',tip:'The age of the oldest items on the list fell over the year, so UTI is recovering rather than worsening.'}
  ]);

  var below=D.fillrate.filter(function(r){return r.fill_gap!=null&&r.fill_gap<0;});
  kpi('k-fill',[
    {n:below.length+' of '+D.fillrate.length,l:'targets missed',cls:'bad',tip:'Distributors whose latest reported fill rate is below their own FY26-27 target.'},
    {n:'95%',l:'network standard',tip:'The fill rate all distributors are measured against, from the assumptions sheet.'},
    {n:'92%',l:'network floor',tip:'The minimum acceptable fill rate.'}
  ]);

  /* ---------------- start the drill layer ---------------- */
  /* QA hook first, only when the URL carries ?qa=..., so a normal open adds nothing. */
  if(/[?&]qa=/.test(location.search)){
    window.__QA={CH:CH,SEL:SEL,rowsFor:rowsFor,SUM:SUM,renderAll:renderAll,
      barHit:barHit,arcHit:arcHit,facet:facet,renderApplied:renderApplied,
      state:function(){return {sel:JSON.parse(JSON.stringify(SEL)),sum:JSON.parse(JSON.stringify(SUM))};}};
    window.addEventListener('error',function(e){ window.__QA.err=String(e.message)+' | '+(e.error&&e.error.stack); });
    var _ra=renderAll;
    window.__QA.safeRender=function(){ try{_ra();return 'ok';}catch(e){window.__QA.err=String(e.stack||e);return String(e.stack||e);} };
  }
  try{
    renderDrillBars();
    renderAll();
  }catch(e){
    if(window.__QA) window.__QA.err=String((e&&e.stack)||e);
    else window.__QALOADERR=String((e&&e.stack)||e);
  }

    /* ---------------- missing ---------------- */
  var M=D.missing;
  document.getElementById('miss-intro').innerHTML=
    'To name the customer behind a delayed warehouse line, one column is enough. IML knows which sold-to each purchase '
    +'order is raised for - the warehouse document simply does not carry it. Everything below is what that would unlock, '
    +'in the order I would ask for it.';
  var rows=[
    ['Destination customer or sold-to on the warehouse extract',
     'Which distributor is behind each delayed line, and therefore which of the '+nf(K.over30_lines)+' lines over 30 days belong to whom. This is the whole answer and nothing else closes it.','IML / ISZJ'],
    ['Actual dispatch date per line',
     'Which lines really left the building, so "ready for shipment" can be separated from "finished and forgotten".','IML warehouse'],
    ['Actual arrival date per line',
     'How long a line was on the water. Without it, time underway cannot be measured from any file we hold, including Power BI.','IML / freight forwarder'],
    ['Fill rate for the distributors that do not report',
     'UMI, Germany (ISD), Benelux (IBX), Denmark, Cyprus and Greece have no current value. They are named here rather than filled in.','ISZE KPI cycle'],
    ['Back-order lines for the distributors that do not report',
     'Malta, Cyprus and Greece have no current back-order count, so their delay cannot be ranked.','ISZE KPI cycle']
  ];
  document.getElementById('miss-rows').innerHTML=rows.map(function(r){
    return '<tr><td><b>'+esc(r[0])+'</b></td><td>'+esc(r[1])+'</td><td>'+esc(r[2])+'</td></tr>';}).join('');

  /* ---------------- definitions: coverage + why 60% ---------------- */
  var cb=D.cov_bo, cw=D.cov_wh, M2=D.aim_master;
  var covRows=[
    ['Has a family (AIM)',cb.family,cw.family],
    ['Has a catalogue category',cb.cat,cw.cat],
    ['In the classification file, no family assigned yet',cb.nofam,cw.nofam],
    ['Not in any list we hold',cb.absent,cw.absent],
    ['Total lines',cb.lines,cw.lines]
  ];
  document.getElementById('cov-rows').innerHTML=covRows.map(function(r){
    return '<tr><td>'+r[0]+'</td><td class="n">'+nf(r[1])+'</td><td class="n">'
      +pc(r[1]/(cb.lines||1))+'</td><td class="n">'+nf(r[2])+'</td><td class="n">'
      +pc(r[2]/(cw.lines||1))+'</td></tr>';}).join('');

  document.getElementById('why-60').innerHTML=
    'Our classification file holds <b class="hl">'+nf(M2.parts)+'</b> part numbers and only <b class="hl">'
    +nf(M2.family)+'</b> of them carry a family. The family is filled in from the parts we actually bill, so a part we '
    +'have never sold never got one. That is how the file was built, not a fault. The catalogue category is a different '
    +'vocabulary and is far more complete - <b class="hl">'+nf(M2.cat)+'</b> part numbers carry one - which is why it lifts '
    +'the warehouse picture from '+pc(cw.pct_family/100)+' to '+pc(cw.pct_cat/100)+'.'+
    '<p>That is the whole reason the warehouse file reads '+pc(cw.pct_family/100)+' and the current sellable backlog reads '
    +pc(cb.pct_family/100)+': it is <b>which parts are in each list</b>. The warehouse list carries slow, older and one-off '
    +'parts. The backlog carries parts that are on order right now, which are the parts we sell.</p>'+
    '<p>Of the <b>'+nf(cw.absent)+'</b> warehouse lines with nothing in either column: every one is a genuine ten-digit '
    +'Isuzu part number, not a rebate or a service code. Not one of them has ever been billed, in any month from January '
    +'2023 to August 2026. 292 of the 345 distinct part numbers share their first six digits with a part we do hold, which '
    +'is the shape of a superseded number. Confirming that needs the EPC supersession export, which is recorded as blocked '
    +'and has not arrived.</p>'+
    '<p>Of the <b>'+nf(cw.nofam)+'</b> lines that have no family yet, the catalogue category is filled on <b>all '
    +nf(cw.nofam)+'</b>, and that is exactly what the second column adds.</p>';

  /* ---------------- tabs ---------------- */
  var ts=document.querySelectorAll('.tab');
  for(var i=0;i<ts.length;i++)ts[i].onclick=function(){
    var t=this.getAttribute('data-t');show(t);
    if(history.replaceState)history.replaceState(null,'','#'+t);
    window.scrollTo(0,0);};
  if(location.hash)show(location.hash.replace('#',''));

  document.getElementById('foot').textContent='IML warehouse status 2 October 2026; week 41 backlog 6 October 2026; '
    +'UTI weekly lists week 2 to week 40 2026; KPI Master File august 2026 and FY26-27 targets. '
    +'Part numbers read as text so leading zeros are kept. No euro valuation on this page. '
    +'Build '+D.build+'.';
  var st=document.getElementById('stamp');
  if(st) st.textContent='build '+D.build;
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    raise SystemExit(main())

