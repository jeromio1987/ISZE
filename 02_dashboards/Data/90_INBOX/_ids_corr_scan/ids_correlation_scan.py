"""IDS 2026 cross-dataset correlation scan — READ ONLY analysis.

Writes only to 01_data/00_derived/ (findings MD + joined CSVs).
Does not touch dashboards, packs, mail, or git.

Levels tested:
  L1  IDS internal structure (dealer, n=520 unique)
  L2  Dealer-level: IDS UK CV (ITUK) x ITUK dealer sell-out  <- only true dealer join
  L3  DB-level: IDS country avg x PMS / GPS / KPI / UIO
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ROOT / "01_data" / "00_derived"
OUT = DERIVED
TOOLS = ROOT / "04_tools" / "ids_dealer_ranking"
sys.path.insert(0, str(TOOLS))

from ids_paths import IDS_RESULT_REPORTS_DIR  # noqa: E402
from ids_report_extract import build_dashboard_payload  # noqa: E402
import build_ids_parts_kaizen_study as kz  # noqa: E402

# IDS country -> PRISM distributor code. Reuse the shipped map, keep display names.
COUNTRY_TO_DB = {
    "Belgium": "BELGIUM",
    "Netherlands": "BELGIUM",
    "Luxembourg": "BELGIUM",
    "Poland": "POLAND",
    "Greece": "GREECE",
    "Norway": "NORWAY",
    "UK LCV": "IUK",
    "UK CV": "ITUK",
    "Israel LCV": "UMI",  # IDS Israel = UMI only. UTI did not participate.
    "Malta": "MALTA",
    "Cyprus": "CYPRUS",
    "Romania": "ROMANIA",
    "Portugal": "PORTUGAL",
    "Hungary": "HUNGARY",
    "Denmark": "DENMARK",
    # MIDI: no PRISM PMS/GPS mapping -> IDS only, excluded from DB correlations
    "France": None,
    "Italy": None,
    "Spain": None,
    "Switzerland": None,
    "Benelux": None,  # rollup of BE+NL+LUX; dropped to avoid double counting
}
KPI_NAME = {
    "BELGIUM": "IBX (BENELUX)",
    "POLAND": "Isuzu Polska",
    "GREECE": "Petros Petropoulos",
    "NORWAY": "RSA",
    "IUK": "IUK",
    "ITUK": "ITUK",
    "UMI": "UMI",
    "MALTA": "GasanZammit",
    "CYPRUS": "Loutsios Group",
    "ROMANIA": "Isuzu Rom Auto",
    "PORTUGAL": "Astara Portugal",
    "DENMARK": "Isuzu Danmark",
    "HUNGARY": None,
}

report: list[str] = []


def say(s: str = "") -> None:
    print(s)
    report.append(s)


def corr(x, y, label_x, label_y, level, min_n=5):
    """Return dict with Pearson + Spearman, honest about n."""
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    n = len(d)
    if n < 3 or d["x"].nunique() < 3 or d["y"].nunique() < 3:
        return {"x": label_x, "y": label_y, "level": level, "n": n,
                "pearson_r": np.nan, "pearson_p": np.nan,
                "spearman_r": np.nan, "spearman_p": np.nan, "verdict": "n too small"}
    pr, pp = stats.pearsonr(d["x"], d["y"])
    sr, sp = stats.spearmanr(d["x"], d["y"])
    if n < min_n:
        v = "n too small"
    elif sp < 0.05 and abs(sr) >= 0.4:
        v = "signal"
    elif sp < 0.10:
        v = "weak/marginal"
    else:
        v = "noise"
    return {"x": label_x, "y": label_y, "level": level, "n": n,
            "pearson_r": round(pr, 3), "pearson_p": round(pp, 4),
            "spearman_r": round(sr, 3), "spearman_p": round(sp, 4), "verdict": v}


def fmt_table(rows: list[dict]) -> str:
    if not rows:
        return "_(none)_"
    df = pd.DataFrame(rows)
    hdr = "| X | Y | level | n | Pearson r | Spearman rho | p (rho) | verdict |"
    sep = "|---|---|---|--:|--:|--:|--:|---|"
    lines = [hdr, sep]
    for _, r in df.iterrows():
        lines.append(
            f"| {r['x']} | {r['y']} | {r['level']} | {r['n']} | "
            f"{r['pearson_r']} | {r['spearman_r']} | {r['pearson_p'] if pd.isna(r['spearman_p']) else r['spearman_p']} | {r['verdict']} |"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------- load IDS
payload = build_dashboard_payload(IDS_RESULT_REPORTS_DIR)
rows = []
for d in payload["dealers"]:
    r = {
        "country": d["country"],
        "name": d["name"],
        "total": d["total"],
        "total_pct": d["total_pct"],
        "totals_only": d["totals_only"],
        "address": d.get("address") or "",
    }
    for sec, v in (d.get("sections") or {}).items():
        r[f"{sec}_pct"] = v.get("pct")
    rows.append(r)
ids = pd.DataFrame(rows)
ids["db"] = ids["country"].map(COUNTRY_TO_DB)

# Benelux rollup double-counts BE/NL/LUX -> drop from every analysis
ids_all = ids.copy()
ids = ids[ids["country"] != "Benelux"].copy()

# --------------------------------------------------- Baumann exclude (FR/ES)
red_path = ROOT / "01_data" / "90_INBOX" / "tomoe_ids_mail_pull" / "20260731_0858_red_marked_dealers.json"
red = json.loads(red_path.read_text(encoding="utf-8"))
red_rows = red if isinstance(red, list) else red.get("dealers", red.get("red_marked", []))


def nk(s):
    return re.sub(r"[^A-Z0-9]", "", str(s).upper())


red_keys = {(str(r.get("country", "")).upper()[:2], nk(r.get("name"))) for r in red_rows}
ids["red_marked"] = [
    (c[:2].upper(), nk(n)) in red_keys and c in ("France", "Spain")
    for c, n in zip(ids["country"], ids["name"])
]
# Fallback: Tomoe's rule = red-marked in FR/ES only; also flag literal zeros there
ids["zero_score"] = ids["total"].fillna(0) <= 0
ids["excl_baumann"] = ids["red_marked"] | (ids["zero_score"] & ids["country"].isin(["France", "Spain"]))

say("# IDS 2026 — cross-dataset correlation scan")
say("")
say("**internal / internal. Read-only analysis — no rebuild, no mail, no commit.**")
say(f"**Generated:** 2026-08-10 · IDS payload: {len(ids_all)} dealer rows, "
    f"{len(ids)} after dropping the `Benelux` rollup (it double-counts BE+NL+LUX).")
say("")
say(f"KPI anchor: `_verification_report.json` is **green** (106 pass / 0 fail, 2026-08-03).")
say("")
say("<<<SUMMARY>>>")
say("---")
say("")

# ================================================================ L1
say("## L1 — What IDS actually measures (before joining anything)")
say("")
say(f"- Dealers (excl. Benelux rollup): **{len(ids)}** across **{ids['country'].nunique()}** countries")
say(f"- Zero-score shells: **{int(ids['zero_score'].sum())}** "
    f"({', '.join(f'{k} {v}' for k, v in ids[ids.zero_score].country.value_counts().items())})")
say(f"- Baumann-excluded (FR/ES red-marked + zeros): **{int(ids['excl_baumann'].sum())}**")
say(f"- `totals_only` (no section detail): **{int(ids['totals_only'].sum())}** — all UK CV / ITUK")
say("")

scored = ids[~ids["excl_baumann"] & ~ids["zero_score"]].copy()

# variance decomposition: how much of dealer score is just "which country"
g = scored.groupby("country")["total_pct"]
grand = scored["total_pct"].mean()
ss_between = sum(len(v) * (v.mean() - grand) ** 2 for _, v in g)
ss_total = ((scored["total_pct"] - grand) ** 2).sum()
eta2 = ss_between / ss_total
say(f"**Country-mix confound.** Between-country variance / total variance (eta-squared) = **{eta2:.3f}** "
    f"on n={len(scored)} scored dealers.")
say(f"So ~**{eta2*100:.0f}%** of a dealer's IDS total is explained by *which country he is in*, "
    f"~{100-eta2*100:.0f}% by the dealer himself.")
say("")

# section correlation matrix (dealer level, excl totals_only)
sec = scored[~scored["totals_only"]][["A_pct", "B_pct", "C_pct", "D_pct", "E_pct", "total_pct"]].dropna()
say(f"**Section inter-correlation** (dealer level, n={len(sec)}, Spearman):")
say("")
cm = sec.corr(method="spearman").round(2)
say("| | " + " | ".join(cm.columns) + " |")
say("|---|" + "---|" * len(cm.columns))
for i, r in cm.iterrows():
    say(f"| **{i}** | " + " | ".join(str(v) for v in r.values) + " |")
say("")
say(f"Section D (Parts) sd = {sec['D_pct'].std():.3f}, mean = {sec['D_pct'].mean():.3f}; "
    f"total sd = {sec['total_pct'].std():.3f}.")
say("")

# ================================================================ L2 dealer level ITUK
say("---")
say("")
say("## L2 — Dealer level: IDS UK CV (ITUK) x ITUK dealer sell-out")
say("")

SUFFIX = re.compile(
    r"\b(LTD|LIMITED|PLC|LLP|GROUP|UK|COMMERCIALS?|COMMERCIAL|TRUCKS?|TRUCK|BUS|VAN|"
    r"CENTRES?|CENTERS?|CENTRE|SERVICES?|SERVICE|GARAGES?|MOTORS?|VEHICLES?|VEHICLE|"
    r"AND|CO|THE|ISUZU|SONS|CAR|CARS|AUTOS?|ELECTRICS?|T/A)\b"
)
CITIES = [
    "GLOUCESTER", "TIPTON", "WORCESTER", "STOKE", "FRADLEY", "BICESTER", "HEATHROW",
    "MAIDENHEAD", "OXFORD", "MANCHESTER", "BLACKBURN", "LEEDS", "BURGESS HILL",
    "MAIDSTONE", "THURROCK", "LEICESTER", "NORTHAMPTON", "TUXFORD", "PETERBOROUGH",
    "NORWICH", "ENFIELD", "IPSWICH", "INVERNESS", "ELGIN", "EXETER", "IVYBRIDGE",
    "HULL", "GRIMSBY", "RAINTON", "SHEFFIELD", "NEWCASTLE", "BILLINGHAM", "SWINDON", "WALES",
]


def core(s: str) -> str:
    s = str(s).upper()
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = SUFFIX.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


def site_of(s: str) -> str:
    u = re.sub(r"[^A-Z ]", " ", str(s).upper())
    for c in CITIES:
        if re.search(rf"\b{c}\b", u):
            return c
    return ""


def group_of(s: str) -> str:
    """Brand core with city tokens and all whitespace removed, singularised.

    Names that are *only* a city ("Elgin Truck & Van Centre Ltd Elgin",
    "Commercial Motors (Wales) Ltd") would collapse to an empty key and get
    merged into one fake mega-group, so fall back to the un-stripped core.
    """
    c = core(s)
    stripped = c
    for city in CITIES:
        stripped = stripped.replace(city, "")
    stripped = re.sub(r"[^A-Z0-9]", "", stripped)
    if not stripped:
        stripped = re.sub(r"[^A-Z0-9]", "", c)
    return re.sub(r"S$", "", stripped)


sell = pd.read_csv(DERIVED / "dealer_sellout_gps_2025.csv")
sell = sell[(sell["distributor_code"] == "ITUK")
            & (~sell["entity"].str.contains("network", case=False, na=False))].copy()
sell["grp_raw"] = sell["entity"].map(group_of)
sell["site"] = sell["entity"].map(site_of)

uk = ids[ids["country"] == "UK CV"].copy()
uk["grp_raw"] = uk["name"].map(group_of)
uk["site"] = uk["name"].map(site_of)

# Fuzzy-reconcile the two group vocabularies (IDS is mixed-case free text,
# sell-out is SAP legal names) so 'MANCHETTS' == 'MANCHETTSPB' etc.
import difflib  # noqa: E402

sell_groups = sorted(set(sell["grp_raw"]))
gmap: dict[str, str] = {}
for gname in sorted(set(uk["grp_raw"])):
    if gname in sell_groups:
        gmap[gname] = gname
        continue
    cand = [s for s in sell_groups if s.startswith(gname) or gname.startswith(s)]
    if not cand:
        cand = difflib.get_close_matches(gname, sell_groups, n=1, cutoff=0.80)
    gmap[gname] = cand[0] if cand else gname
uk["grp"] = uk["grp_raw"].map(gmap)
sell["grp"] = sell["grp_raw"]

# ---- group-level join (robust to multi-site naming)
ids_g = uk.groupby("grp").agg(
    ids_total_pct=("total_pct", "mean"),
    ids_sites=("name", "count"),
    ids_names=("name", lambda s: " | ".join(sorted(s))),
).reset_index()
sell_g = sell.groupby("grp").agg(
    total_eur=("total_eur", "sum"),
    bvp_eur=("bvp_eur", "sum"),
    genuine_only_eur=("genuine_only_eur", "sum"),
    genuine_contested_eur=("genuine_contested_eur", "sum"),
    qty_year=("qty_year", "sum"),
    sell_sites=("entity", "count"),
    sell_names=("entity", lambda s: " | ".join(sorted(s))),
).reset_index()
sell_g["bvp_pct"] = sell_g["bvp_eur"] / sell_g["total_eur"]
sell_g["genuine_only_pct"] = sell_g["genuine_only_eur"] / sell_g["total_eur"]
sell_g["contested_pct"] = sell_g["genuine_contested_eur"] / sell_g["total_eur"]

j = ids_g.merge(sell_g, on="grp", how="inner")
j["log_total_eur"] = np.log10(j["total_eur"].clip(lower=1))
j["eur_per_site"] = j["total_eur"] / j["sell_sites"]

assert (ids_g["grp"].str.len() > 0).all(), "empty group key would create a fake mega-group"
say(f"IDS UK CV dealers: **{len(uk)}** · ITUK sell-out entities: **{len(sell)}** · "
    f"matched **dealer groups: {len(j)}**")
say("")
say(f"Unmatched IDS: {', '.join(sorted(set(ids_g.grp) - set(j.grp))) or 'none'}")
say(f"Sell-out with no IDS: {', '.join(sorted(set(sell_g.grp) - set(j.grp))) or 'none'}")
say("")
say("**Caveat that kills half the value: UK CV IDS is `totals_only` — there is no Section D "
    "(Parts) score for ITUK. This dealer-level test can only use the TOTAL score.**")
say("")

l2 = [
    corr(j["ids_total_pct"], j["log_total_eur"], "IDS total %", "log10 parts purchases EUR CY2025", "dealer group"),
    corr(j["ids_total_pct"], j["total_eur"], "IDS total %", "parts purchases EUR CY2025", "dealer group"),
    corr(j["ids_total_pct"], j["qty_year"], "IDS total %", "parts qty CY2025", "dealer group"),
    corr(j["ids_total_pct"], j["genuine_only_pct"], "IDS total %", "genuine-only share of EUR", "dealer group"),
    corr(j["ids_total_pct"], j["bvp_pct"], "IDS total %", "BVP share of EUR", "dealer group"),
    corr(j["ids_total_pct"], j["contested_pct"], "IDS total %", "contested-genuine share", "dealer group"),
    corr(j["ids_total_pct"], j["eur_per_site"], "IDS total %", "EUR per site (size-normalised)", "dealer group"),
]
say(fmt_table(l2))
say("")


def resid(a, b):
    return a - np.polyval(np.polyfit(b, a, 1), b)


# partial correlation: IDS vs genuine share controlling for size
d = j[["ids_total_pct", "genuine_only_pct", "log_total_eur"]].dropna()
if len(d) > 5:
    rp, pp_ = stats.pearsonr(resid(d["ids_total_pct"].values, d["log_total_eur"].values),
                             resid(d["genuine_only_pct"].values, d["log_total_eur"].values))
    say(f"**Partial correlation** IDS total % vs genuine-only share, controlling for dealer size "
        f"(log EUR): r = **{rp:.3f}** (p={pp_:.3f}, n={len(d)}).")
    say("")

# is "IDS vs EUR" just multi-site groups being bigger?
rs, ps_ = stats.spearmanr(j["ids_total_pct"], j["sell_sites"])
rpart, ppart = stats.pearsonr(resid(j["ids_total_pct"].values, j["sell_sites"].values.astype(float)),
                              resid(j["log_total_eur"].values, j["sell_sites"].values.astype(float)))
one = j[j["sell_sites"] == 1]
r1, p1 = stats.spearmanr(one["ids_total_pct"], one["log_total_eur"])
base_r, _ = stats.spearmanr(j["ids_total_pct"], j["log_total_eur"])
jk = [stats.spearmanr(j.drop(j.index[i])["ids_total_pct"],
                      j.drop(j.index[i])["log_total_eur"])[0] for i in range(len(j))]
say("**Is the size result an aggregation artefact?** Checks:")
say("")
say(f"- IDS score vs number of sites in the group: rho = {rs:.3f} (p={ps_:.3f}) — "
    f"multi-site groups do *not* score higher, so the € result is not just 'groups are bigger'.")
say(f"- Partial correlation IDS vs log €, controlling for #sites: r = **{rpart:.3f}** (p={ppart:.3f}).")
say(f"- **Single-site dealer groups only: rho = {r1:.3f} (p={p1:.4f}, n={len(one)})** — "
    f"the cleanest cut, and it is stronger than the pooled one.")
say(f"- Leave-one-out jackknife: rho stays in [{min(jk):.3f}, {max(jk):.3f}] — no single dealer drives it.")
say("")

# ---- site-level join: only unambiguous 1:1 pairs
# single-site groups match directly; multi-site groups must agree on the city token
uk["key"] = uk["grp"] + "|" + uk["site"]
sell["key"] = sell["grp"] + "|" + sell["site"]
u1 = uk[uk.groupby("key")["key"].transform("size") == 1]
s1 = sell[sell.groupby("key")["key"].transform("size") == 1]
js = u1.merge(s1, on="key", how="inner", suffixes=("_ids", "_sell"))
js = js[js["grp_ids"] == js["grp_sell"]]
say(f"**Site-level cross-check** (unambiguous 1:1 site pairs only, n={len(js)}):")
say("")
l2s = [
    corr(js["total_pct"], np.log10(js["total_eur"].clip(lower=1)), "IDS total %", "log10 parts EUR", "dealer site"),
    corr(js["total_pct"], js["genuine_only_pct"], "IDS total %", "genuine-only share", "dealer site"),
    corr(js["total_pct"], js["bvp_pct"], "IDS total %", "BVP share", "dealer site"),
]
say(fmt_table(l2s))
say("")

# ---- leakage
leak = pd.read_csv(DERIVED / "dealer_leakage_ituk.csv")
lk = leak.groupby("dealer_name").agg(
    leak_gap_eur=("gap_eur", "sum"),
    dealer_units=("dealer_total_units", "max"),
).reset_index()
lk["grp"] = lk["dealer_name"].map(group_of)
lk = lk.groupby("grp").agg(leak_gap_eur=("leak_gap_eur", "sum"),
                           dealer_units=("dealer_units", "sum")).reset_index()
lk["leak_per_unit"] = lk["leak_gap_eur"] / lk["dealer_units"].replace(0, np.nan)
jl = ids_g.merge(lk, on="grp", how="inner")
say(f"**PMS leakage vs IDS** (ITUK leakage study, n={len(jl)} groups):")
say("")
say(fmt_table([
    corr(jl["ids_total_pct"], jl["leak_gap_eur"], "IDS total %", "PMS leakage gap EUR", "dealer group"),
    corr(jl["ids_total_pct"], jl["leak_per_unit"], "IDS total %", "leakage EUR per unit sold", "dealer group"),
]))
say("")

l2_all = pd.DataFrame(l2 + l2s).dropna(subset=["spearman_p"])
ps2 = np.sort(l2_all["spearman_p"].values)
m2 = len(ps2)
bh2 = (ps2 <= (np.arange(1, m2 + 1) / m2) * 0.10).sum()
say(f"**Dealer-level multiple testing.** {m2} tests run; "
    f"{int((l2_all['spearman_p'] < 0.05).sum())} at p<0.05 vs {0.05*m2:.1f} expected by chance; "
    f"surviving Benjamini-Hochberg FDR 10%: **{bh2}**.")
say("")

j.to_csv(OUT / "ids_corr_dealer_ituk_2026-08-10.csv", index=False, encoding="utf-8")

# ================================================================ L3 DB level
say("---")
say("")
say("## L3 — DB / country level: IDS x PMS x GPS x KPI x UIO")
say("")

pms = kz.load_pms_db_2025()
gps = kz.load_gps_2025()
gen = kz.load_genuine_share_2025()
kpi = kz.load_kpi_fill_mos()


def db_ids(frame: pd.DataFrame) -> pd.DataFrame:
    f = frame[frame["db"].notna()]
    return f.groupby("db").agg(
        ids_total_avg=("total_pct", "mean"),
        ids_A=("A_pct", "mean"), ids_B=("B_pct", "mean"), ids_C=("C_pct", "mean"),
        ids_D=("D_pct", "mean"), ids_E=("E_pct", "mean"),
        dealers=("name", "count"),
    ).reset_index()


# two variants: all dealers vs Baumann-excluded (FR/ES zeros) — note FR/ES have no DB anyway
db_incl = db_ids(ids)
db_excl = db_ids(ids[~ids["excl_baumann"]])

uio = pd.read_csv(DERIVED / "gps_spu_by_distributor.csv")
uio = uio[uio["year"] == 2025][["distributor_code", "uio_units", "total_sales_eur"]]

t = db_excl.copy()
t["pms_capture_total"] = t["db"].map(lambda d: pms.get(d, {}).get("pms_capture_total"))
t["pms_capture_genuine"] = t["db"].map(lambda d: pms.get(d, {}).get("pms_capture_genuine"))
t["genuine_share_eur"] = t["db"].map(gen.get)
t["gps_spu_eur"] = t["db"].map(lambda d: gps.get(d, {}).get("gps_spu_eur"))
t["gps_capture_vs_max"] = t["db"].map(lambda d: gps.get(d, {}).get("gps_capture_vs_max"))
t = t.merge(uio, left_on="db", right_on="distributor_code", how="left")
t["kpi_name"] = t["db"].map(KPI_NAME)
t["kpi_fill_rate"] = t["kpi_name"].map(lambda k: (kpi.get(k) or {}).get("kpi_fill_rate") if k else None)
t["kpi_mos_days"] = t["kpi_name"].map(lambda k: (kpi.get(k) or {}).get("kpi_mos_days") if k else None)
t["kpi_spu_eur"] = t["kpi_name"].map(lambda k: (kpi.get(k) or {}).get("kpi_spu_eur") if k else None)
t["log_uio"] = np.log10(t["uio_units"].clip(lower=1))

say(f"DBs with IDS + at least one business metric: **{len(t)}**")
say("")
say("| DB | dealers | IDS total | IDS D | PMS total capt | PMS genuine capt | genuine share | GPS EUR/UIO | GPS vs max | KPI fill | KPI MOS | UIO |")
say("|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")


def f3(v, mult=1.0, dp=3):
    return "—" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v*mult:.{dp}f}"


for _, r in t.sort_values("ids_total_avg", ascending=False).iterrows():
    say(f"| {r['db']} | {int(r['dealers'])} | {f3(r['ids_total_avg'],100,1)} | {f3(r['ids_D'],100,1)} | "
        f"{f3(r['pms_capture_total'],100,1)} | {f3(r['pms_capture_genuine'],100,1)} | "
        f"{f3(r['genuine_share_eur'],100,1)} | {f3(r['gps_spu_eur'],1,1)} | {f3(r['gps_capture_vs_max'],100,1)} | "
        f"{f3(r['kpi_fill_rate'],1,1)} | {f3(r['kpi_mos_days'],1,1)} | "
        f"{'—' if pd.isna(r['uio_units']) else int(r['uio_units'])} |")
say("")

targets = [
    ("pms_capture_total", "PMS TOTAL capture (primary)"),
    ("pms_capture_genuine", "PMS genuine capture (secondary lens)"),
    ("genuine_share_eur", "genuine EUR share of PMS mix"),
    ("gps_spu_eur", "GPS EUR/UIO"),
    ("gps_capture_vs_max", "GPS capture vs max"),
    ("kpi_fill_rate", "KPI first fill rate"),
    ("kpi_mos_days", "KPI months of stock (days)"),
    ("kpi_spu_eur", "KPI parts sales per unit EUR"),
    ("log_uio", "log10 UIO (network size)"),
]
ids_metrics = [("ids_total_avg", "IDS total %"), ("ids_D", "IDS Section D %"),
               ("ids_C", "IDS Section C %"), ("ids_B", "IDS Section B %")]

l3 = []
for xc, xl in ids_metrics:
    for yc, yl in targets:
        l3.append(corr(t[xc], t[yc], xl, yl, "DB", min_n=8))
l3df = pd.DataFrame(l3)
say("**All DB-level pairs** (Spearman is the one to read — n is small and distributions are skewed):")
say("")
say(fmt_table(l3))
say("")

t.to_csv(OUT / "ids_corr_db_level_2026-08-10.csv", index=False, encoding="utf-8")

# sensitivity: with zeros included
t2 = db_incl.copy()
t2["pms_capture_total"] = t2["db"].map(lambda d: pms.get(d, {}).get("pms_capture_total"))
t2["gps_spu_eur"] = t2["db"].map(lambda d: gps.get(d, {}).get("gps_spu_eur"))
t2["genuine_share_eur"] = t2["db"].map(gen.get)
say("**Baumann sensitivity (zeros in vs out).** FR/ES have no PRISM DB mapping, so the red-marked "
    "zeros never enter the DB-level correlations at all:")
say("")
for yc, yl in [("pms_capture_total", "PMS total capture"), ("gps_spu_eur", "GPS EUR/UIO"),
               ("genuine_share_eur", "genuine share")]:
    a = corr(t2["ids_total_avg"], t2[yc], "IDS total (zeros IN)", yl, "DB", min_n=8)
    b = corr(t["ids_total_avg"], t[yc], "IDS total (zeros OUT)", yl, "DB", min_n=8)
    say(f"- {yl}: rho with zeros IN = {a['spearman_r']} (n={a['n']}) · zeros OUT = {b['spearman_r']} (n={b['n']})")
say("")

# strongest
sig = l3df[(l3df["n"] >= 8)].copy()
sig["abs_rho"] = sig["spearman_r"].abs()
say("**Top DB-level by |rho| (n>=8):**")
say("")
say(fmt_table(sig.sort_values("abs_rho", ascending=False).head(10).drop(columns=["abs_rho"]).to_dict("records")))
say("")

# ---------------------------------------------------------- DB robustness
say("### DB-level robustness — three reasons to distrust the table above")
say("")

say("**(1) Single-dealer 'countries'.** MALTA and CYPRUS have **1 IDS dealer each**; their "
    "'country average' is one man's self-assessment carrying the same weight as ITUK's 44.")
say("")
for xc, xl in [("ids_total_avg", "IDS total %"), ("ids_D", "IDS Section D %")]:
    for yc, yl in [("gps_capture_vs_max", "GPS capture vs max"),
                   ("genuine_share_eur", "genuine EUR share"),
                   ("pms_capture_total", "PMS total capture")]:
        d = t[[xc, yc, "db", "dealers"]].dropna()
        d5 = d[d["dealers"] >= 5]
        r0, p0 = stats.spearmanr(d[xc], d[yc])
        r5, p5 = stats.spearmanr(d5[xc], d5[yc])
        say(f"- {xl} vs {yl}: all DBs rho={r0:.3f} (n={len(d)}) → "
            f"**DBs with >=5 dealers rho={r5:.3f} (p={p5:.4f}, n={len(d5)})**")
say("")

# (2) the GPS metric is target-relative
t["gps_implied_target_eur"] = t["gps_spu_eur"] / t["gps_capture_vs_max"]
dd = t[["ids_total_avg", "gps_implied_target_eur", "gps_spu_eur", "gps_capture_vs_max", "db"]].dropna()
rt, pt = stats.spearmanr(dd["ids_total_avg"], dd["gps_implied_target_eur"])
rs2, ps2 = stats.spearmanr(dd["ids_total_avg"], dd["gps_spu_eur"])
say("**(2) `GPS capture vs max` is a target-relative ratio, and the target is not constant.** "
    "Back-solving `spend_per_unit / gps_capture_vs_max` recovers the per-DB € target:")
say("")
say("| DB | GPS €/UIO | capture vs max | implied € target per vehicle |")
say("|---|--:|--:|--:|")
for _, r in dd.sort_values("gps_implied_target_eur", ascending=False).iterrows():
    say(f"| {r['db']} | {r['gps_spu_eur']:.1f} | {r['gps_capture_vs_max']*100:.1f}% | "
        f"{r['gps_implied_target_eur']:.0f} |")
say("")
say(f"- rho(IDS total, **implied target**) = **{rt:.3f}** (p={pt:.4f}, n={len(dd)})")
say(f"- rho(IDS total, **raw GPS €/UIO**) = {rs2:.3f} (p={ps2:.4f}, n={len(dd)})")
say("")
say("Most DBs sit on a flat €250 target; ITUK (528), Portugal (427), Malta (364) and Cyprus (293) "
    "carry heavier CV/segment-mix targets. Those same DBs score high on IDS. So the headline "
    "'high IDS = low GPS capture' is **mostly the denominator**: high-IDS markets are the ones "
    "measured against a harder target. Against the raw €/UIO numerator the relationship evaporates.")
say("")

# (3) multiple testing
db_tests = l3df[(l3df["n"] >= 8)].dropna(subset=["spearman_p"])
ps_sorted = np.sort(db_tests["spearman_p"].values)
mm = len(ps_sorted)
bh = (ps_sorted <= (np.arange(1, mm + 1) / mm) * 0.10).sum()
say(f"**(3) Multiple testing.** {mm} DB-level tests with n>=8; "
    f"**{int((db_tests['spearman_p'] < 0.05).sum())}** came in at p<0.05 where "
    f"{0.05*mm:.1f} are expected by chance alone. "
    f"Survivors under Benjamini-Hochberg FDR 10%: **{bh}**. "
    "And the IDS sections inter-correlate at rho 0.66–0.91, so these are nowhere near independent tests — "
    "the effective number of questions asked is far smaller than 29, but so is the evidence.")
say("")

pd.DataFrame(l2 + l2s + l3).to_csv(OUT / "ids_corr_results_2026-08-10.csv", index=False, encoding="utf-8")

# --------------------------------------------------- GPS artefact, clean cut
dd2 = t.dropna(subset=["gps_capture_vs_max", "ids_total_avg"]).copy()
flat = dd2[dd2["gps_implied_target_eur"].between(245, 260)]
r_flat, p_flat = stats.spearmanr(flat["ids_total_avg"], flat["gps_spu_eur"])
r_par, p_par = stats.pearsonr(resid(dd2["ids_total_avg"].values, dd2["gps_implied_target_eur"].values),
                              resid(dd2["gps_capture_vs_max"].values, dd2["gps_implied_target_eur"].values))
say(f"Controlling for the target, the relationship halves and loses significance: "
    f"partial r = **{r_par:.3f}** (p={p_par:.3f}, n={len(dd2)}). "
    f"Inside the {len(flat)} DBs that share the flat €250 target — where capture-vs-max is just a "
    f"rescaling of €/UIO — rho = **{r_flat:.3f}** (p={p_flat:.3f}). "
    "So a negative tilt does survive, but on n=8 with UMI (low IDS, high GPS) and Hungary "
    "(high IDS, low GPS) as the leverage points. Directionally interesting, not actionable.")
say("")

# ================================================================ synthesis
S: list[str] = []
S.append("## Verdict")
S.append("")
S.append("**No. There is no defensible correlation between IDS 2026 dealer scores and any parts "
         "performance metric in this workspace.** Every candidate either dies when the join is done "
         "correctly, dies when single-dealer countries are removed, or dies under multiple-testing "
         "correction. Nothing survives Benjamini-Hochberg FDR at 10% — at either level.")
S.append("")
S.append("That is not the same as \"IDS is worthless\". It means IDS is measuring something "
         "**orthogonal** to parts € — process and facility hygiene, self-reported — and it should be "
         "used the way Petros and Astara already use it (visit triage, coaching), not as a predictor "
         "of wallet.")
S.append("")
S.append("**The one thing worth knowing:** the strongest *apparent* results in this scan were all "
         "artefacts, and I can show you exactly which artefact each one was. That is the useful output.")
S.append("")
S.append("### The five relationships that looked real, and what each one actually was")
S.append("")
S.append("| # | Relationship | Level | n | Raw strength | What it really was |")
S.append("|---|---|---|--:|---|---|")
S.append(f"| 1 | IDS total vs GPS capture-vs-max | DB | 12 | rho −0.71, p=0.010 (survives >=5-dealer cut at −0.81) | "
         f"**Mostly denominator.** `capture vs max` divides by a per-DB € target that is 529 for ITUK, "
         f"427 Portugal, 364 Malta vs a flat 250 for everyone else. High-IDS markets are the ones "
         f"graded against a harder target. Controlling for it: r={r_par:.2f}, p={p_par:.2f}. |")
S.append(f"| 2 | IDS total vs ITUK dealer parts € | dealer group | 31 | rho 0.20, p=0.27 | "
         f"**Was rho 0.44 / p=0.019 until I fixed a name-matching bug** that collapsed 7 UK dealers "
         f"(Elgin x2, Commercial Motors Wales, …) into one fake mega-group. Real answer: noise. |")
S.append(f"| 3 | IDS total vs PMS leakage € per unit | dealer group | 31 | rho −0.37, p=0.040 | "
         f"Right direction (better dealers leak less) and the only dealer-level survivor, but it fails "
         f"FDR, and the leakage study itself only maps 7–39% of each dealer's lines to a PMS category. |")
S.append(f"| 4 | IDS total vs genuine share, size-controlled | dealer group | 31 | partial r −0.37, p=0.039 | "
         f"**Wrong direction** — higher-IDS UK dealers buy a *slightly lower* genuine share. Almost "
         f"certainly a mix effect (bigger CV workshops do more contested/BVP-exposed work), not a "
         f"standards effect. Fails FDR. |")
S.append(f"| 5 | IDS total vs genuine EUR share of PMS mix | DB | 12 | rho 0.47, p=0.12 | "
         f"The prior Kaizen pack's headline (+0.41 on Section D). **Collapses to rho 0.20 (p=0.58) once "
         f"MALTA and CYPRUS are dropped** — two 'countries' whose IDS average is one dealer each. |")
S.append("")
S.append("### What you probably expect that does NOT hold")
S.append("")
S.append("- **Section D (Parts & Accessories) does not predict PMS capture.** rho −0.30 (n=11), "
         "and −0.28 on DBs with >=5 dealers. Flat. This reproduces the Jul-2026 Kaizen finding "
         "(it had −0.45) but with the honest caveat that n≈10 markets cannot support either number. "
         "Per the sales-is-sales rule this is measured on `line_type=total`; the genuine-only lens is "
         "no better (rho −0.10).")
S.append("- **Section D does not predict KPI first fill rate or MOS.** rho −0.24 and −0.07. "
         "The Kaizen pack reported +0.41 fill / +0.33 MOS. That flip is what six extra months of KPI "
         "months and a different DB set does to an n=8 correlation — which tells you how much to "
         "trust either version.")
S.append("- **IDS does not predict GPS €/UIO.** rho 0.11 all DBs, −0.07 on DBs with >=5 dealers. "
         "Nothing.")
S.append("- **A good dealer is not a bigger dealer.** At UK dealer level IDS explains essentially "
         "none of parts spend (rho 0.20 group / 0.10 site). PR Fleet scores 38.8% and buys €70k; "
         "Warrington scores 97.9% and buys €345k — but Tanner scores 67.4% on €26k and JDS scores "
         "68.1% on €335k. No line through it.")
S.append("- **Country is not destiny, either.** Only ~20% of a dealer's IDS total is explained by "
         "which country he sits in (eta-squared 0.197, n=494). I expected the country-mix confound "
         "to be the whole story at dealer level; it is not. IDS genuinely discriminates *between "
         "dealers*. It just does not discriminate on anything that shows up in parts €.")
S.append("")
S.append("### What IDS is actually measuring")
S.append("")
S.append("Sections B, C, D and E inter-correlate at rho 0.66–0.78 and each correlates 0.81–0.91 with "
         "the total. That is a **single underlying factor**, not five independent capabilities — a "
         "dealer who scores well on Parts scores well on Service and Organisation. Practically: "
         "**Section D carries almost no information that the total score does not already carry**, "
         "so splitting Kaizen actions by section is over-reading the instrument.")
S.append("")
S.append("### Where the mail/meeting record agrees")
S.append("")
S.append("The qualitative corpus predicted this result and nobody in it ever claimed otherwise:")
S.append("")
S.append("- Tomoe Baumann's own cross-checks found Hungary uploaded identical values for every "
         "dealer, Romania scoring blank cells as points, and Petros self-scoring above the allocated "
         "maximum. This is a **self-evaluation with known parser and submission defects**, not an audit.")
S.append("- No distributor anywhere in the record claims high-IDS dealers buy more genuine parts. "
         "The only operational use is **\"IDS dealer visits later; priority lower IDS scorers\"** "
         "(Petros, 6 Aug) and Portugal treating it as a self-audit for coaching.")
S.append("- IUK is the live counter-example: **IDS 81.7% (above network) while losing €243k of brakes "
         "to IAM** because dealers say OEM brakes and wipers are too dear. Standards high, wallet "
         "leaking. Price and range beat standards.")
S.append("- Astara/Portugal scores 86.7% on IDS and simultaneously tells you GPS 63% is optimistic and "
         "\">50% of the parc is not regularly in the official network\". High IDS, sceptical on capture.")
S.append("- The Jul-2026 Kaizen pack already called this **\"thesis half-confirmed … a clean Section D "
         "score is a process / stock / promo hygiene signal — it does not replace attach and capture "
         "work.\"** This scan says drop the \"half\" and keep the second sentence.")
S.append("")
S.append("### Baumann exclude rule — effect on the numbers")
S.append("")
S.append("Applied and tested both ways. **It changes nothing here**, for a structural reason worth "
         "knowing: the 18 red-marked/zero FR+ES dealers sit in MIDI markets that have **no PRISM "
         "PMS/GPS mapping at all**, so they never enter a correlation. They matter for MIDI country "
         "averages and rankings — not for this study. The zeros that do exist elsewhere "
         "(Switzerland 6, Italy 3) are per Tomoe's rule kept in.")
S.append("")
S.append("### What is blocked, and what would unlock it")
S.append("")
S.append("| Blocker | Consequence | What you would need |")
S.append("|---|---|---|")
S.append("| **No dealer-level parts sales outside ITUK** | The entire hypothesis is testable on 1 of 20 "
         "IDS countries. 476 scored dealers have an IDS score and no matching € line. | DB-to-dealer "
         "sell-out feeds from IUK, Petros, IBX, RSA, UMI — already on the `DATA_ASKS_IML_and_all_DBs` "
         "list. IUK (45 IDS dealers, LCV) is the highest-value single ask. |")
S.append("| **ITUK IDS is `totals_only`** | The one market with dealer-level € has **no Section D "
         "score** — so the most interesting test (Parts standards vs parts purchases) cannot be run "
         "anywhere in the network today. | ITUK per-dealer section detail, or accept the total as proxy. |")
S.append("| **No dealer ID** | Joins are fuzzy name matches. 44 IDS names vs 64 SAP legal names; a "
         "single normalisation bug moved the headline result from 'signal' to 'noise'. | A dealer code "
         "carried in both the IDS workbook and the sell-out extract. Cheapest high-value fix. |")
S.append("| **KPI is DB-monthly, in Excel** | Fill rate and MOS can only ever be a country constant "
         "against 45 different dealer scores — zero within-country variance to correlate. | Dealer-level "
         "fill/backorder, or accept KPI is a DB story. |")
S.append("| **MIDI (FR/IT/ES/CH) has no PRISM DB mapping** | 192 IDS dealers — the largest single "
         "block — are excluded from every business join. | A MIDI distributor mapping into "
         "`distributor_master_mapping.csv`. |")
S.append("| **n=10–12 markets** | Every DB-level correlation is underpowered. To detect rho=0.5 at 80% "
         "power you need n≈29 markets. You have 12. | Nothing — this ceiling is structural. Stop "
         "quoting country-level r values as evidence. |")
S.append("")
S.append("### If you want one number to carry into a meeting")
S.append("")
S.append("> IDS 2026 and parts performance are statistically unrelated on every join we can currently "
         "make (dealer level n=31 UK groups; DB level n=10–12 markets; nothing survives multiple-testing "
         "correction). IDS is a self-reported process-hygiene score and should be used for visit "
         "triage, not wallet forecasting.")
S.append("")

body = "\n".join(report)
body = body.replace("<<<SUMMARY>>>", "\n".join(S))
(OUT / "ids_correlation_scan_2026-08-10.md").write_text(body, encoding="utf-8")
print("\n\nWROTE:", OUT / "ids_correlation_scan_2026-08-10.md")
