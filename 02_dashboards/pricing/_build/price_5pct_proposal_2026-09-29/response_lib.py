"""Shared loaders + estimators for the ITUK dealer-demand elasticity test."""
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"


def z10(s):
    return s.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(10)


def load_ituk_monthly():
    files = ["dealer_sellout_long_ITUK_CY2023.csv", "dealer_sellout_long_ITUK_CY2024.csv",
             "dealer_sellout_long_ITUK_network_CY2025.csv", "dealer_sellout_long_ITUK_CY2026YTD.csv"]
    out = []
    for f in files:
        x = pd.read_csv(D / f, dtype={"part_number": str, "period": str})
        x = x[x.period_grain == "month"]
        out.append(x[["part_number", "period", "qty", "description"]])
    m = pd.concat(out, ignore_index=True)
    m["pn"] = z10(m.part_number)
    m["ym"] = pd.PeriodIndex(m.period, freq="M")
    return m.groupby(["pn", "ym"], as_index=False).agg(qty=("qty", "sum"), description=("description", "first"))


def load_lists():
    lists = {}
    for y in (2023, 2024, 2025):
        h = pd.read_parquet(D / f"pricing_pr00_ie40_{y}.parquet")
        h["pn"] = z10(h.Material.astype("Int64"))
        lists[y] = h[h.Price_EUR > 0].groupby("pn").Price_EUR.max()
    cur = pd.read_parquet(D / "pricing_pr00_ie40.parquet")
    cur = cur[(cur.price_condition == "PR00") & (cur.sp_eur > 0)].copy()
    cur["pn"] = z10(cur.part_number)
    lists[2026] = cur.groupby("pn").sp_eur.max()
    sup = cur[cur.part_number != cur.newest_pn]
    superseded = set(z10(sup.part_number)) | set(z10(sup.newest_pn))
    origin = cur.groupby("pn").country_of_origin.first()
    return lists, superseded, origin


def load_family():
    c = pd.read_csv(D / "pr00_classification.csv", dtype=str)
    c["pn"] = z10(c.pn_norm)
    c = c.drop_duplicates("pn").set_index("pn")
    a = pd.read_csv(D / "aim_master_v2.csv", dtype=str,
                    usecols=["part_number", "aim_l1", "aim_l2", "aim_l3", "price_class_iml", "cat_pms_flag"])
    a["pn"] = z10(a.part_number)
    a = a.drop_duplicates("pn").set_index("pn")
    return c, a


def window_qty(m, start, end):
    s = m[(m.ym >= pd.Period(start, "M")) & (m.ym <= pd.Period(end, "M"))]
    return s.groupby("pn").qty.sum()


def fe_logit(y_share, n, x, groups, clusters, iters=60):
    """Two-period Poisson with PN fixed effects == binomial logit on post share.
    y_share = q_post/(q_pre+q_post), n = q_pre+q_post, x = regressor matrix (k),
    groups = family x event dummies. Returns beta, cluster-robust SE."""
    x = np.atleast_2d(np.asarray(x, float))
    if x.shape[0] != len(y_share):
        x = x.T
    G = pd.get_dummies(pd.Series(groups).astype(str)).to_numpy(float)
    X = np.hstack([x, G])
    k = x.shape[1]
    b = np.zeros(X.shape[1])
    y = np.asarray(y_share, float)
    w0 = np.asarray(n, float)
    for _ in range(iters):
        eta = X @ b
        p = 1 / (1 + np.exp(-eta))
        W = w0 * p * (1 - p)
        z = eta + (y - p) / np.clip(p * (1 - p), 1e-9, None)
        XtW = X.T * W
        H = XtW @ X + 1e-8 * np.eye(X.shape[1])
        bn = np.linalg.solve(H, XtW @ z)
        if np.max(np.abs(bn - b)) < 1e-10:
            b = bn
            break
        b = bn
    p = 1 / (1 + np.exp(-(X @ b)))
    W = w0 * p * (1 - p)
    H = (X.T * W) @ X + 1e-8 * np.eye(X.shape[1])
    Hinv = np.linalg.inv(H)
    sc = X * (w0 * (y - p))[:, None]
    cl = pd.Series(clusters).astype(str).to_numpy()
    S = pd.DataFrame(sc).groupby(cl).sum().to_numpy()
    V = Hinv @ (S.T @ S) @ Hinv
    return b[:k], np.sqrt(np.diag(V)[:k])


def fe_wls(y, x, groups, w, clusters):
    """WLS of y on x with group fixed effects (within transform), cluster-robust SE."""
    df = pd.DataFrame({"y": y, "g": groups, "w": w})
    x = np.atleast_2d(np.asarray(x, float))
    if x.shape[0] != len(df):
        x = x.T
    k = x.shape[1]
    for j in range(k):
        df[f"x{j}"] = x[:, j]
    cols = ["y"] + [f"x{j}" for j in range(k)]
    wm = df.groupby("g").apply(lambda d: pd.Series({c: np.average(d[c], weights=d.w) for c in cols}),
                               include_groups=False)
    dm = df[cols] - wm.loc[df.g].to_numpy()
    Y = dm.y.to_numpy()
    Xd = dm[[f"x{j}" for j in range(k)]].to_numpy()
    W = df.w.to_numpy()
    XtW = Xd.T * W
    Hinv = np.linalg.inv(XtW @ Xd)
    b = Hinv @ (XtW @ Y)
    e = Y - Xd @ b
    sc = Xd * (W * e)[:, None]
    S = pd.DataFrame(sc).groupby(pd.Series(clusters).astype(str).to_numpy()).sum().to_numpy()
    V = Hinv @ (S.T @ S) @ Hinv
    return b, np.sqrt(np.diag(V))
