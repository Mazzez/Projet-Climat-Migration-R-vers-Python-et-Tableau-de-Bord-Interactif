"""Phase 2 — 06 — Corrélations climat ↔ CO2 sur 5 représentations
+ heatmap matrice résiduelle + analyse en lag du top 6.

Migration de 06_correlations.R.
"""
from __future__ import annotations
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, plots                                            # noqa: E402
from climat.stats import lag_correlation                                    # noqa: E402

OUT = config.OUT_PHASE2
PLOT = OUT / "plots"
plots.setup_theme()

with open(OUT / "series_transformed.pkl", "rb") as fh:
    ds = pickle.load(fh)

clim_vars = config.CLIM_VARS + ["CRE_SW", "CRE_LW", "CRE_net"]
CO2_TREND = "co2_trend"
CO2_AVG = "co2_avg"


def co2_target(repr_name: str) -> str:
    """level/anom/resid → co2_trend ; d1/d12 → co2_avg (= série brute, plus
    naturelle pour les diff)."""
    return CO2_AVG if repr_name in ("d1", "d12") else CO2_TREND


# ============================================================
# 1. Corrélations sur les 5 représentations
# ============================================================
rows = []
for repr_name, d in ds.items():
    y = d[co2_target(repr_name)].to_numpy()
    for v in clim_vars:
        x = d[v].to_numpy()
        ok = ~np.isnan(x) & ~np.isnan(y)
        r = float(np.corrcoef(x[ok], y[ok])[0, 1]) if ok.sum() >= 2 else np.nan
        rows.append({"repr": repr_name, "var": v, "r": r})

cor_repr = pd.DataFrame(rows)
cor_wide = cor_repr.pivot(index="var", columns="repr", values="r")
cor_wide = cor_wide.reindex(clim_vars)
cor_wide["abs_resid"] = cor_wide["resid"].abs()
cor_wide = cor_wide.sort_values("abs_resid", ascending=False).drop(columns="abs_resid")
cor_wide = cor_wide[["level", "anom", "resid", "d1", "d12"]]

print("=== Corrélations climat ↔ CO2 sur les 5 représentations ===")
print(" level : niveaux bruts (dominé par tendance commune)")
print(" anom  : anomalies désaisonnées (cycle saisonnier retiré, tendance conservée)")
print(" resid : anomalies désaisonnées ET détendrées (signal interannuel pur)  <-- KEY")
print(" d1    : différences mensuelles (capture surtout la saisonnalité)")
print(" d12   : différences annuelles (taux d'évolution interannuel)\n")
print(cor_wide.round(3))
cor_wide.reset_index().to_csv(OUT / "correlations_4repr.csv", index=False)

# Plot comparatif
order_vars = cor_wide.index.tolist()
fig, ax = plt.subplots(figsize=(11, 8))
reprs = ["level", "anom", "resid", "d1", "d12"]
colors = sns.color_palette("Set1", len(reprs))
y_pos = np.arange(len(order_vars))
W = 0.16
for i, rp in enumerate(reprs):
    ax.barh(y_pos + (i - 2) * W, cor_wide[rp].values, height=W,
            color=colors[i], label=rp)
ax.set_yticks(y_pos); ax.set_yticklabels(order_vars)
ax.axvline(0, color="black", lw=0.4)
ax.invert_yaxis()
ax.legend(loc="lower right", title="Représentation")
ax.set_xlabel("r (Pearson)")
ax.set_title("Corrélations climat ↔ CO2 — comparaison des 5 représentations\n"
             "level/anom/resid : vs co2_trend ;  d1/d12 : vs Δco2")
plots.save(fig, PLOT / "06b_corr_climat_co2.png", w=11, h=8, dpi=130)

# ============================================================
# 2. Heatmap matrice de corrélation sur RÉSIDUS
# ============================================================
all_vars = ["co2_trend"] + clim_vars
M = ds["resid"][all_vars].corr()
fig, ax = plt.subplots(figsize=(13, 12))
sns.heatmap(M, annot=True, fmt=".2f", annot_kws={"fontsize": 7},
            cmap=sns.diverging_palette(220, 20, as_cmap=True),
            center=0, vmin=-1, vmax=1, square=True, ax=ax,
            cbar_kws={"shrink": 0.8})
ax.set_title("Matrice de corrélation sur résidus (anomalies désaisonnées + détendrées)")
plots.save(fig, PLOT / "06a_corr_heatmap.png", w=13, h=12, dpi=130)

# ============================================================
# 3. Lag correlation sur top 6 (sur résidus)
# ============================================================
top6 = cor_wide.head(6).index.tolist()
print(f"\n=== Top 6 variables (résidus) pour lag analysis ===\n{top6}")

co2_resid = ds["resid"]["co2_trend"].to_numpy()
lag_rows = []
for v in top6:
    x = ds["resid"][v].to_numpy()
    lag_df = lag_correlation(x, co2_resid, max_lag=12)
    lag_df["var"] = v
    lag_rows.append(lag_df)

lag_results = pd.concat(lag_rows, ignore_index=True)
lag_results.to_csv(OUT / "lag_correlations.csv", index=False)

print("\n=== Pic absolu de corrélation par variable (sur résidus) ===")
peaks = (lag_results.assign(abs_r=lag_results["r"].abs())
         .sort_values(["var", "abs_r"], ascending=[True, False])
         .groupby("var", as_index=False).first()
         .drop(columns="abs_r"))
print(peaks)

fig, axes = plt.subplots(2, 3, figsize=(12, 8), sharex=True)
for ax, v in zip(axes.flat, top6):
    sub = lag_results[lag_results["var"] == v]
    ax.plot(sub["lag"], sub["r"], color="steelblue", marker="o", lw=0.8, ms=3)
    ax.axhline(0, ls="--", color="grey", lw=0.5)
    ax.axvline(0, ls="--", color="grey", lw=0.5)
    ax.set_title(v)
    ax.set_xlabel("Lag (mois)")
    ax.set_ylabel("r")
fig.suptitle("Corrélations climat ↔ CO2 en fonction du lag (sur résidus)\n"
             "Lag > 0 : la variable précède le CO2  |  Lag < 0 : le CO2 précède la variable")
plots.save(fig, PLOT / "06c_lag_correlations.png", w=12, h=8, dpi=130)

print(f"\n=== Plots et CSV sauvegardés dans : {OUT} ===")
