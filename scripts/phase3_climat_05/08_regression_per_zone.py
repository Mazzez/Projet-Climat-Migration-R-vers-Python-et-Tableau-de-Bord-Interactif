"""Phase 3 — 08 — Régression multivariée du CO2 résiduel par zone
(5 bandes + 4 hotspots) — répond à : où le lien climat→CO2 est-il
le plus fort géographiquement ?

Migration de 08_regression_per_zone.R.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, io                                                # noqa: E402

OUT = config.OUT_PHASE3

bands_df = pd.read_csv(OUT / "monthly_band_means_05.csv", parse_dates=["date"])
hot_df = pd.read_csv(OUT / "hotspots_series.csv", parse_dates=["date"])

co2 = io.load_co2_global()[["date", "trend"]].rename(columns={"trend": "co2_trend"})

dates = sorted(bands_df["date"].unique())
dates = pd.DatetimeIndex(dates)
months = dates.month.to_numpy()
t_yrs = ((dates - dates[0]).days / 365.25).to_numpy(dtype=float)

# CO2 aligné → résidus
co2_v = co2.set_index("date").reindex(dates)["co2_trend"].to_numpy(dtype=float)
co2_clim = pd.Series(co2_v).groupby(months).transform("mean").to_numpy()
co2_anom = co2_v - co2_clim
ok_co2 = ~np.isnan(co2_anom)
p_co2 = np.polyfit(t_yrs[ok_co2], co2_anom[ok_co2], 1)
co2_resid = co2_anom - np.polyval(p_co2, t_yrs)
mask_co2 = ~np.isnan(co2_resid)


def to_resid(x: np.ndarray) -> np.ndarray:
    """Désaisonner + détendrer linéairement (signal interannuel)."""
    if np.all(np.isnan(x)):
        return np.full_like(x, np.nan, dtype=float)
    s = pd.Series(x, dtype=float)
    clim = s.groupby(months).transform("mean").to_numpy()
    anom = x - clim
    ok = ~np.isnan(anom)
    p = np.polyfit(t_yrs[ok], anom[ok], 1)
    return anom - np.polyval(p, t_yrs)


def fit_summary(X: pd.DataFrame, y: np.ndarray) -> dict:
    """Régression OLS multivariée + top 3 prédicteurs par |t|."""
    Xc = sm.add_constant(X)
    fit = sm.OLS(y, Xc).fit()
    tvals = fit.tvalues.drop("const")
    top3 = tvals.abs().sort_values(ascending=False).index.tolist()[:3]
    return {
        "R2": round(float(fit.rsquared), 3),
        "R2_adj": round(float(fit.rsquared_adj), 3),
        "n_obs": int(len(X)),
        "top1": top3[0] if len(top3) > 0 else None,
        "top2": top3[1] if len(top3) > 1 else None,
        "top3": top3[2] if len(top3) > 2 else None,
    }


# ============================================================
# 1. Régression par bande de latitude
# ============================================================
clim_vars = config.CLIM_VARS  # 18 variables 0.5°
bands_list = list(bands_df["band"].unique())

results: list[dict] = []
for b in bands_list:
    sub = bands_df[bands_df["band"] == b].sort_values("date").reset_index(drop=True)
    resid_cols = {v: to_resid(sub[v].to_numpy(dtype=float)) for v in clim_vars}
    X = pd.DataFrame(resid_cols)
    X = X.loc[mask_co2].reset_index(drop=True)
    y = co2_resid[mask_co2]
    res = fit_summary(X, y)
    res.update({"zone": b, "type": "bande"})
    results.append(res)

# ============================================================
# 2. Régression par hotspot (4 vars : T2m, PWAT, APCP, TCDC)
# ============================================================
hot_vars = ["T2m", "PWAT", "APCP", "TCDC"]
regions = ["Amazonie", "Indonesie", "Siberie", "Sahel"]

for r in regions:
    resid_cols = {v: to_resid(hot_df[f"{r}_{v}"].to_numpy(dtype=float))
                  for v in hot_vars}
    X = pd.DataFrame(resid_cols)
    X = X.loc[mask_co2].reset_index(drop=True)
    y = co2_resid[mask_co2]
    res = fit_summary(X, y)
    res.update({"zone": r, "type": "hotspot"})
    results.append(res)

# ============================================================
# 3. Tableau final
# ============================================================
final = pd.DataFrame(results)[
    ["zone", "type", "R2", "R2_adj", "n_obs", "top1", "top2", "top3"]
]
print(final.to_string(index=False))
final.to_csv(OUT / "regression_per_zone.csv", index=False)

print(f"\n=== Régression par zone terminée : {OUT / 'regression_per_zone.csv'} ===")
