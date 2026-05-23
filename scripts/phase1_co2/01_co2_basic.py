"""Phase 1 — Analyse CO2 mondial NOAA GML, sections 1 à 8.

Migration de Final Version/Analyse CO2/scripts/co2_analysis.R.

Sections :
  1. Chargement & nettoyage
  2. Statistiques descriptives (global + par décennie)
  3. Décomposition STL
  4. Cycle saisonnier détaillé (climatologie + amplitude par décennie)
  5. Tendance long-terme (LM linéaire/quadratique/cubique, MK, Sen)
  6. Analyse de l'accélération (taux annuel, ruptures CUSUM/Bai-Perron)
  7. Prévision ARIMA (24 mois)
  8. Visualisations de synthèse

Sortie : outputs/phase1_co2/*.png + 3 CSV (stats_decennie, amplitude, taux_annuel).
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Permettre l'exécution depuis n'importe où
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, io, plots                                    # noqa: E402
from climat.stats import sens_slope_and_mk                              # noqa: E402

from statsmodels.tsa.seasonal import STL                                # noqa: E402
from statsmodels.tsa.arima.model import ARIMA                           # noqa: E402
import pymannkendall as pmk                                              # noqa: E402
import ruptures as rpt                                                   # noqa: E402

OUT = config.OUT_PHASE1
plots.setup_theme()


# ============================================================
# 1. Chargement & nettoyage
# ============================================================
print("\n========== 1. Chargement & nettoyage ==========")
co2 = io.load_co2_global()

print(f"Dimensions       : {co2.shape}")
print(f"Plage temporelle : {co2['date'].min().date()} -> {co2['date'].max().date()}")
print(f"Plage average    : {co2['average'].min():.2f} -> {co2['average'].max():.2f} ppm")
print(f"NA dans average  : {co2['average'].isna().sum()}")
diffs = co2['date'].diff().dropna().dt.days
print(f"Pas de temps régulier ? {diffs.between(28, 31).all()}")

# ============================================================
# 2. Statistiques descriptives
# ============================================================
print("\n========== 2. Statistiques descriptives ==========")
stats_global = co2["average"].agg(["count", "min", "max", "mean", "median", "std"])
stats_global["range"] = stats_global["max"] - stats_global["min"]
print(stats_global)

stats_decade = (co2.groupby("decade")["average"]
                .agg(n="count", mean="mean", min="min", max="max", sd="std")
                .reset_index())
print(stats_decade)
stats_decade.to_csv(OUT / "stats_decennie.csv", index=False)

total_rise = co2["average"].iloc[-1] - co2["average"].iloc[0]
years_span = co2["decimal"].iloc[-1] - co2["decimal"].iloc[0]
avg_rate = total_rise / years_span
print(f"\nHausse totale: {total_rise:.2f} ppm sur {years_span:.2f} ans  (~{avg_rate:.3f} ppm/an)")

# ============================================================
# 3. Décomposition saisonnière (STL)
# ============================================================
print("\n========== 3. Décomposition saisonnière (STL) ==========")
co2_idx = co2.set_index("date")
stl = STL(co2_idx["average"], period=12, robust=True).fit()

stl_df = pd.DataFrame({
    "date":    co2_idx.index,
    "observed": co2_idx["average"].values,
    "trend":    stl.trend.values,
    "seasonal": stl.seasonal.values,
    "remainder": stl.resid.values,
}).reset_index(drop=True)

amp_seasonal = stl_df["seasonal"].max() - stl_df["seasonal"].min()
print(f"Amplitude moyenne du cycle saisonnier (STL) : {amp_seasonal:.3f} ppm")

fig, axes = plt.subplots(2, 1, sharex=True)
axes[0].plot(stl_df["date"], stl_df["observed"], color="steelblue", lw=0.7)
axes[0].set_ylabel("ppm"); axes[0].set_title("observed")
axes[1].plot(stl_df["date"], stl_df["trend"], color="steelblue", lw=0.9)
axes[1].set_ylabel("ppm"); axes[1].set_title("trend")
fig.suptitle("Décomposition STL du CO2 mondial (observed + trend)\n"
             "Source : NOAA GML, moyennes mensuelles globales")
plots.save(fig, OUT / "03_stl_decomposition.png", w=10, h=5)

# ============================================================
# 4. Cycle saisonnier détaillé
# ============================================================
print("\n========== 4. Cycle saisonnier détaillé ==========")
co2_anom = co2.assign(anomaly=co2["average"] - co2["trend"])

clim_month = (co2_anom.groupby("month")["anomaly"]
              .agg(mean_anom="mean", sd_anom="std").reset_index())
print(clim_month)

fig, ax = plt.subplots()
ax.bar(clim_month["month"], clim_month["mean_anom"], color="steelblue")
ax.errorbar(clim_month["month"],
            clim_month["mean_anom"],
            yerr=clim_month["sd_anom"],
            fmt="none", color="black", capsize=3)
ax.set_xticks(range(1, 13))
ax.set_xlabel("Mois"); ax.set_ylabel("Anomalie (ppm)")
ax.set_title("Cycle saisonnier moyen du CO2 mondial (1979-2025)\n"
             "Anomalie = average - trend désaisonnalisé NOAA")
plots.save(fig, OUT / "04a_cycle_saisonnier_moyen.png")

amp_dec = (co2_anom.groupby("decade")["anomaly"]
           .agg(amplitude=lambda s: s.max() - s.min()).reset_index())
print(amp_dec)
amp_dec.to_csv(OUT / "amplitude_saisonniere_decennie.csv", index=False)

fig, ax = plt.subplots()
ax.bar(amp_dec["decade"], amp_dec["amplitude"], color="tomato")
for i, v in enumerate(amp_dec["amplitude"]):
    ax.text(i, v, f"{v:.2f}", ha="center", va="bottom")
ax.set_ylabel("Amplitude max-min (ppm)")
ax.set_title("Amplitude saisonnière du CO2 par décennie")
plots.save(fig, OUT / "04b_amplitude_par_decennie.png")

fig, ax = plt.subplots()
years = sorted(co2_anom["year"].unique())
norm = plt.Normalize(vmin=min(years), vmax=max(years))
cmap = plt.get_cmap("viridis")
for y, sub in co2_anom.groupby("year"):
    ax.plot(sub["month"], sub["anomaly"], color=cmap(norm(y)), alpha=0.5)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
fig.colorbar(sm, ax=ax, label="Année")
ax.set_xticks(range(1, 13))
ax.set_xlabel("Mois"); ax.set_ylabel("Anomalie (ppm)")
ax.set_title("Cycles saisonniers superposés (une ligne par année)")
plots.save(fig, OUT / "04c_cycles_superposes.png")

# ============================================================
# 5. Tendance long-terme
# ============================================================
print("\n========== 5. Tendance long-terme ==========")
x = co2["decimal"].to_numpy()
y = co2["average"].to_numpy()
p1 = np.polyfit(x, y, 1)
p2 = np.polyfit(x, y, 2)
p3 = np.polyfit(x, y, 3)
yhat1 = np.polyval(p1, x); yhat2 = np.polyval(p2, x); yhat3 = np.polyval(p3, x)


def aic_ols(y, yhat, k):
    """AIC d'un modèle OLS gaussien : 2k + n*log(SSE/n)."""
    n = len(y)
    sse = float(np.sum((y - yhat) ** 2))
    return 2 * k + n * np.log(sse / n)


print(f"--- Régression linéaire ---     coefs = {p1[::-1]}")
print(f"--- Régression quadratique ---  coefs = {p2[::-1]}")
print(f"--- Régression cubique ---      coefs = {p3[::-1]}")
print(f"AIC linéaire    : {aic_ols(y, yhat1, 2):.2f}")
print(f"AIC quadratique : {aic_ols(y, yhat2, 3):.2f}")
print(f"AIC cubique     : {aic_ols(y, yhat3, 4):.2f}")

print("\n--- Mann-Kendall (non-paramétrique) ---")
mk_full = pmk.original_test(y)
print(f"  tau = {mk_full.Tau:.4f},  p = {mk_full.p:.3g}")

print("\n--- Pente de Sen ---")
res = sens_slope_and_mk(y)
print(f"Sen (mensuel)   : {res.sen_per_step:.4f} ppm/mois")
print(f"Sen (annualisé) : {res.sen_per_year:.4f} ppm/an")

co2 = co2.assign(lm1_fit=yhat1, lm2_fit=yhat2, lm3_fit=yhat3)

fig, ax = plt.subplots()
ax.scatter(co2["date"], co2["average"], s=3, alpha=0.3, color="grey")
ax.plot(co2["date"], yhat1, color="blue",      label="Linéaire", lw=1)
ax.plot(co2["date"], yhat2, color="red",       label="Quadratique", lw=1)
ax.plot(co2["date"], yhat3, color="darkgreen", label="Cubique", lw=1)
ax.legend()
ax.set_ylabel("ppm")
ax.set_title("Tendance long-terme du CO2 mondial")
plots.save(fig, OUT / "05_tendance_polynomes.png")

# ============================================================
# 6. Analyse de l'accélération
# ============================================================
print("\n========== 6. Analyse de l'accélération ==========")
annual = (co2.groupby("year")
          .agg(annual_mean=("average", "mean"),
               n_months=("average", "count"))
          .reset_index())
annual = annual[annual["n_months"] >= 6].copy()
annual["annual_rate"] = annual["annual_mean"].diff()
print(annual.tail(15))
annual.to_csv(OUT / "taux_annuel.csv", index=False)

ar = annual.dropna(subset=["annual_rate"])
fig, ax = plt.subplots()
ax.bar(ar["year"], ar["annual_rate"], color="darkorange")
sns.regplot(x=ar["year"], y=ar["annual_rate"], lowess=True,
            scatter=False, color="black", ax=ax,
            line_kws={"linewidth": 0.8})
ax.set_ylabel("ppm/an")
ax.set_title("Taux annuel de croissance du CO2 mondial\n"
             "Différence des moyennes annuelles successives")
plots.save(fig, OUT / "06a_taux_annuel.png")

print("\n--- Détection de ruptures (algorithm: PELT, modèle linéaire) ---")
trend_arr = co2["trend"].to_numpy()
# Détection sur la pente : on régresse trend ~ time et cherche les ruptures
# de niveau dans la pente locale via l'algorithme Pelt sur la dérivée 1ère
# (proche de strucchange::breakpoints).
algo = rpt.Pelt(model="rbf", min_size=24).fit(np.diff(trend_arr))
n_pen = max(1, int(0.001 * len(trend_arr)))
breaks = algo.predict(pen=n_pen)
break_idx = [b for b in breaks if b < len(trend_arr) - 1]
brk_dates = co2["date"].iloc[break_idx].tolist()
print("Dates de rupture détectées :")
for d in brk_dates:
    print(f"  {d.date()}")

if brk_dates:
    fig, ax = plt.subplots()
    ax.plot(co2["date"], co2["trend"], color="darkred", lw=0.8)
    for d in brk_dates:
        ax.axvline(d, ls="--", color="grey", lw=0.8)
    ax.set_ylabel("ppm")
    ax.set_title("Trend désaisonnalisé NOAA et ruptures détectées\n"
                 "Lignes pointillées = changements de régime")
    plots.save(fig, OUT / "06b_ruptures.png")

# ============================================================
# 7. Prévision ARIMA (24 mois)
# ============================================================
print("\n========== 7. Prévision ARIMA ==========")
# Sélection automatique simple : SARIMA(1,1,1)(0,1,1,12), proche de auto.arima
# par défaut sur ce signal (forte tendance + saison annuelle).
order = (1, 1, 1)
seasonal_order = (0, 1, 1, 12)
fit_arima = ARIMA(co2.set_index("date")["average"],
                  order=order,
                  seasonal_order=seasonal_order,
                  enforce_stationarity=False,
                  enforce_invertibility=False).fit()
print(fit_arima.summary().tables[0])
print(fit_arima.summary().tables[1])

fcst_res = fit_arima.get_forecast(steps=24)
mean = fcst_res.predicted_mean
ci80 = fcst_res.conf_int(alpha=0.20)

fig, ax = plt.subplots()
ax.plot(co2["date"], co2["average"], color="steelblue", lw=0.6, label="Observé")
ax.plot(mean.index, mean, color="darkred", lw=1, label="Prévision (24 mois)")
ax.fill_between(mean.index, ci80.iloc[:, 0], ci80.iloc[:, 1],
                color="red", alpha=0.2, label="IC 80 %")
ax.set_ylabel("ppm"); ax.legend()
ax.set_title(f"Prévision CO2 mondial (24 mois)\n"
             f"Modèle : SARIMA{order}x{seasonal_order}")
plots.save(fig, OUT / "07_prevision_arima.png")

# ============================================================
# 8. Visualisations de synthèse
# ============================================================
print("\n========== 8. Synthèse ==========")
fig, ax = plt.subplots()
ax.plot(co2["date"], co2["average"], color="grey", alpha=0.6, lw=0.7, label="brut")
ax.plot(co2["date"], co2["trend"],   color="darkred", lw=1, label="trend désais. NOAA")
ax.legend()
ax.set_ylabel("ppm")
ax.set_title("CO2 atmosphérique mondial 1979-2025\n"
             "Série brute (gris) et tendance désaisonnalisée NOAA (rouge)")
plots.save(fig, OUT / "08a_serie_complete.png")

fig, ax = plt.subplots()
ax.plot(co2["date"], co2["average"], color="steelblue", lw=0.7)
ax.set_ylabel("ppm")
ax.set_title("CO2 mondial - série mensuelle brute")
plots.save(fig, OUT / "08b_serie_brute_zoom.png")

print(f"\n=== Tous les outputs sauvegardés dans : {OUT} ===")
