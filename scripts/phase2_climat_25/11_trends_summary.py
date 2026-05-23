"""Phase 2 — 11 — Bilan des tendances 21 variables : Sen + MK + bootstrap
+ grille de heatmaps + grille de STL trends.

Migration de 11_trends_summary.R.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, plots                                            # noqa: E402
from climat.stats import sens_slope_and_mk, bootstrap_sen                   # noqa: E402

from statsmodels.tsa.seasonal import STL                                    # noqa: E402

OUT = config.OUT_PHASE2
PLOT = OUT / "plots"
plots.setup_theme()

df = pd.read_csv(OUT / "climate_co2_monthly.csv", parse_dates=["date"])
all_vars = config.CLIM_VARS + ["CRE_SW", "CRE_LW", "CRE_net"]

# ============================================================
# 1. Sen + bootstrap + MK pour chaque variable
# ============================================================
print("Calcul des tendances + bootstrap Sen (R=500) pour 21 variables...")
t0 = time.time()
results = []
for v in all_vars:
    x = df[v].to_numpy()
    sen = sens_slope_and_mk(x)
    sen_year, lo, hi = bootstrap_sen(x, n_boot=500, seed=42)
    mean_v = float(np.mean(x))
    pct_change_47y = (sen_year * 47) / mean_v * 100 if mean_v != 0 else np.nan
    results.append({
        "var": v,
        "sen_per_year": sen_year,
        "sen_lo95": lo, "sen_hi95": hi,
        "mk_tau": sen.mk_tau, "mk_pvalue": sen.mk_p,
        "mean": mean_v, "sd": float(np.std(x, ddof=1)),
        "pct_change_47y": pct_change_47y,
    })
print(f"Durée : {time.time() - t0:.1f} s")

trends = pd.DataFrame(results)
trends["significant"] = trends["mk_pvalue"] < 0.05
print("\n=== Tendances Sen annualisées (avec IC bootstrap 95%) ===")
print(trends.round(4).to_string(index=False))
trends.to_csv(OUT / "trends_summary.csv", index=False)

# ============================================================
# 2. Vitesses normalisées (% du moyen / an)
# ============================================================
trends_pct = trends.copy()
trends_pct["pct_per_year"] = trends_pct["sen_per_year"] / trends_pct["mean"] * 100
trends_pct = trends_pct.sort_values("pct_per_year")

fig, ax = plt.subplots(figsize=(11, 8))
colors = ["tomato" if v > 0 else "steelblue" for v in trends_pct["pct_per_year"]]
ax.barh(trends_pct["var"], trends_pct["pct_per_year"], color=colors)
for i, val in enumerate(trends_pct["pct_per_year"]):
    ax.text(val, i, f"{val:+.3f}",
            ha="left" if val > 0 else "right", va="center", fontsize=9)
ax.axvline(0, color="black", lw=0.5)
ax.set_xlabel("% / an")
ax.set_title("Vitesses d'évolution normalisées des 21 variables (1979-2025)\n"
             "Pente de Sen / valeur moyenne, en % par an")
plots.save(fig, PLOT / "11a_trends_sen.png", w=11, h=8, dpi=130)

# ============================================================
# 3. -log10(p) Mann-Kendall
# ============================================================
trends_p = trends.copy()
trends_p["nlogp"] = -np.log10(trends_p["mk_pvalue"].clip(lower=1e-300))
trends_p = trends_p.sort_values("nlogp")

fig, ax = plt.subplots(figsize=(11, 8))
colors = ["darkgreen" if v > -np.log10(0.05) else "grey" for v in trends_p["nlogp"]]
ax.barh(trends_p["var"], trends_p["nlogp"], color=colors)
ax.axvline(-np.log10(0.05), ls="--", color="darkred")
ax.set_xlabel("−log10(p)")
ax.set_title("Significativité des tendances (Mann-Kendall)\n"
             "Ligne rouge = seuil p = 0.05 ; vert = tendance significative")
plots.save(fig, PLOT / "11b_trends_significance.png", w=11, h=8, dpi=130)

# ============================================================
# 4. Heatmap grille mois × année des anomalies (21 vars)
# ============================================================
fig, axes = plt.subplots(4, 6, figsize=(14, 10))
for ax, v in zip(axes.flat, all_vars):
    val = df[v].to_numpy()
    clim = pd.Series(val).groupby(df["month"]).transform("mean").to_numpy()
    anom = val - clim
    sd = float(np.std(anom, ddof=1))
    z = anom / sd if sd > 0 else anom
    pivot = (pd.DataFrame({"year": df["year"], "month": df["month"], "z": z})
             .pivot(index="year", columns="month", values="z"))
    sns.heatmap(pivot, cmap=sns.diverging_palette(220, 20, as_cmap=True),
                center=0, vmin=-3, vmax=3, ax=ax, cbar=False)
    ax.set_title(v, fontsize=9, weight="bold")
    ax.set_xticks([0.5, 5.5, 11.5]); ax.set_xticklabels(["J", "J", "D"], fontsize=7)
    ax.set_yticks([]); ax.set_xlabel(""); ax.set_ylabel("")
    ax.invert_yaxis()
for ax in axes.flat[len(all_vars):]:
    ax.set_visible(False)
fig.suptitle("Heatmaps mois × année des anomalies — 21 variables\n"
             "Anomalies z-score (= (val - climato) / sd), même échelle pour comparaison")
plots.save(fig, PLOT / "11c_grid_heatmaps.png", w=14, h=10, dpi=130)

# ============================================================
# 5. Grille des STL trends (21 vars)
# ============================================================
fig, axes = plt.subplots(4, 6, figsize=(14, 9), sharex=True)
s_idx = pd.PeriodIndex(df["date"], freq="M").to_timestamp()
for ax, v in zip(axes.flat, all_vars):
    s = pd.Series(df[v].values, index=s_idx)
    stl = STL(s, period=12, robust=True).fit()
    ax.plot(s.index, s.values, color="grey", alpha=0.6, lw=0.3)
    ax.plot(s.index, stl.trend.values, color="darkred", lw=0.7)
    ax.set_title(v, fontsize=9, weight="bold")
    ax.tick_params(labelsize=6)
for ax in axes.flat[len(all_vars):]:
    ax.set_visible(False)
fig.suptitle("Trend STL extraite — 21 variables\n"
             "Gris : série observée ; rouge : composante trend STL")
plots.save(fig, PLOT / "11d_grid_stl_trends.png", w=14, h=9, dpi=130)

# ============================================================
# Bilan textuel
# ============================================================
print(f"\n=== Synthèse ===")
print(f"Variables avec tendance significative (p < 0.05) : "
      f"{int(trends['significant'].sum())} / {len(trends)}")
print("Top 5 plus rapides en %/an :")
top5 = (trends_pct.assign(abs_pct=trends_pct["pct_per_year"].abs())
        .sort_values("abs_pct", ascending=False)
        .head(5)[["var", "sen_per_year", "pct_per_year", "mk_pvalue"]])
print(top5.round(4).to_string(index=False))

print("\n=== Sauvegardes ===")
print(" - trends_summary.csv")
print(" - plots/11a_trends_sen.png, 11b_trends_significance.png")
print(" - plots/11c_grid_heatmaps.png, 11d_grid_stl_trends.png")
