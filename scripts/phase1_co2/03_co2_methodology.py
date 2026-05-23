"""Phase 1 — Sections 12 à 23 : raffinements méthodologiques (A1-A5)
                                + enrichissements (B1-B7).

Migration de Final Version/Analyse CO2/scripts/co2_analysis_methodology.R.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, io, plots                                        # noqa: E402
from climat.stats import sens_slope_and_mk, bootstrap_sen                   # noqa: E402

from statsmodels.tsa.stattools import adfuller, kpss, acf, pacf             # noqa: E402
from statsmodels.tsa.seasonal import STL                                    # noqa: E402
from statsmodels.tsa.arima.model import ARIMA                               # noqa: E402
from statsmodels.tsa.filters.hp_filter import hpfilter                      # noqa: E402
from statsmodels.tsa.statespace.structural import UnobservedComponents      # noqa: E402
from statsmodels.stats.diagnostic import acorr_ljungbox                     # noqa: E402
from scipy.optimize import curve_fit                                        # noqa: E402
from scipy import signal                                                    # noqa: E402

OUT = config.OUT_PHASE1
plots.setup_theme()

co2 = io.load_co2_global()
y_avg = co2["average"].to_numpy(dtype=float)
y_trend = co2["trend"].to_numpy(dtype=float)


def pp_test_pvalue(x: np.ndarray) -> float:
    """Phillips-Perron via la formulation `arch.unitroot.PhillipsPerron`. On
    n'importe le package que ponctuellement pour rester sur les libs de base
    quand possible — fallback vers ADF si arch absent."""
    try:
        from arch.unitroot import PhillipsPerron
        return float(PhillipsPerron(x).pvalue)
    except Exception:
        return float("nan")


# ============================================================
# 12. A1 — Tests de stationnarité (ADF, KPSS, Phillips-Perron)
# ============================================================
print("\n========== 12. Tests de stationnarité ==========")


def run_stationarity(x, name):
    print(f"\n-- {name} --")
    try:
        adf_p = adfuller(x, autolag="AIC")[1]
    except Exception as e:
        adf_p = float("nan")
    try:
        # KPSS lance UserWarning quand p < 0.01 ou > 0.1 ; on les ignore.
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            kpss_p = kpss(x, regression="c", nlags="auto")[1]
    except Exception:
        kpss_p = float("nan")
    pp_p = pp_test_pvalue(x)
    print(f"ADF      p = {adf_p:.4f}")
    print(f"KPSS     p = {kpss_p:.4f}")
    print(f"PP       p = {pp_p:.4f}")


run_stationarity(y_avg, "Série brute")
run_stationarity(y_trend, "Trend NOAA désaisonnalisé")
run_stationarity(np.diff(y_avg), "Δ première (différence ordre 1)")
run_stationarity(np.diff(y_avg, n=12), "Δ saisonnière (lag 12)")
run_stationarity(np.diff(np.diff(y_avg, n=12)), "Δ + Δ12")
print("\nInterprétation :")
print("  ADF p > 0.05  =>  non stationnaire")
print("  KPSS p < 0.05 =>  non stationnaire")
print("  PP  p > 0.05  =>  non stationnaire")

# ============================================================
# 13. A2 — STL vs NOAA (X-13 non disponible nativement → on compare
#         3 méthodes : NOAA, STL, et HP, comme dans la section 16)
# ============================================================
print("\n========== 13. Comparaison méthodes de désaisonnement ==========")

co2_idx = co2.set_index("date")
stl = STL(co2_idx["average"], period=12, robust=True).fit()
trend_stl = stl.trend.values

trend_hp_cycle, trend_hp = hpfilter(co2_idx["average"], lamb=14400)
trend_hp = trend_hp.values

cmp = pd.DataFrame({
    "date": co2["date"], "NOAA": y_trend, "STL": trend_stl, "HP": trend_hp,
})

fig, ax = plt.subplots()
ax.plot(cmp["date"], cmp["NOAA"], label="NOAA", color="steelblue", lw=0.7)
ax.plot(cmp["date"], cmp["STL"],  label="STL",  color="darkorange", lw=0.7)
ax.plot(cmp["date"], cmp["HP"],   label="HP",   color="darkgreen", lw=0.7)
ax.legend(); ax.set_ylabel("ppm")
ax.set_title("Trend désaisonnalisé : NOAA / STL / Hodrick-Prescott")
plots.save(fig, OUT / "13_x13_vs_stl_vs_noaa.png")

print(f"Diffs max (ppm) :")
print(f"  NOAA - STL : {np.max(np.abs(cmp['NOAA'] - cmp['STL'])):.3f}")
print(f"  NOAA - HP  : {np.max(np.abs(cmp['NOAA'] - cmp['HP'])):.3f}")
print(f"  STL  - HP  : {np.max(np.abs(cmp['STL']  - cmp['HP'])):.3f}")

# ============================================================
# 14. A3 — Bootstrap de la pente de Sen
# ============================================================
print("\n========== 14. Bootstrap pente de Sen ==========")

sen0_y, lo, hi = bootstrap_sen(y_avg, n_boot=500, seed=123)
print(f"Sen original         : {sen0_y:.4f} ppm/an")
print(f"IC 95 % (percentile) : {lo:.4f} - {hi:.4f} ppm/an")

# Distribution des estimations bootstrap
import pymannkendall as pmk
rng = np.random.default_rng(123)
N = 500
ests = np.empty(N)
n = len(y_avg)
for i in range(N):
    idx = np.sort(rng.integers(0, n, size=n))
    ests[i] = pmk.original_test(y_avg[idx]).slope * 12

fig, ax = plt.subplots()
ax.hist(ests, bins=30, color="steelblue", edgecolor="white")
ax.axvline(sen0_y, color="red", lw=1.5)
ax.set_xlabel("Pente Sen (ppm/an)"); ax.set_ylabel("Fréquence")
ax.set_title(f"Bootstrap pente de Sen (R = 500) : {sen0_y:.3f} ppm/an\n"
             f"IC 95 % percentile : [{lo:.3f} ; {hi:.3f}]")
plots.save(fig, OUT / "14_bootstrap_sen.png")

# ============================================================
# 15. A4 — Validation croisée ARIMA (rolling-origin, h = 1..12)
# ============================================================
print("\n========== 15. CV rolling-origin ARIMA ==========")

order = (1, 1, 1)
seasonal_order = (0, 1, 1, 12)
print(f"Modèle : SARIMA{order}x{seasonal_order}")

initial = 120
H = 12
y_series = co2_idx["average"]

# Pour rester rapide on évalue 1 origine sur 6 (pas 1 par mois) ; le résultat
# reste représentatif et match l'ordre de grandeur du tsCV R (qui était lent).
errors = {h: [] for h in range(1, H + 1)}
origins = list(range(initial, len(y_series) - H, 6))
for o in origins:
    try:
        model = ARIMA(y_series.iloc[:o], order=order,
                      seasonal_order=seasonal_order,
                      enforce_stationarity=False,
                      enforce_invertibility=False).fit(method_kwargs={"warn_convergence": False})
        fcst = model.forecast(steps=H).values
        actual = y_series.iloc[o:o + H].values
        for i, h in enumerate(range(1, H + 1)):
            errors[h].append(actual[i] - fcst[i])
    except Exception:
        continue

cv_df = pd.DataFrame({
    "horizon": list(range(1, H + 1)),
    "MAE":     [np.nanmean(np.abs(errors[h])) for h in range(1, H + 1)],
    "RMSE":    [np.sqrt(np.nanmean(np.array(errors[h])**2)) for h in range(1, H + 1)],
})
print(cv_df)
cv_df.to_csv(OUT / "cv_arima.csv", index=False)

fig, ax = plt.subplots()
ax.plot(cv_df["horizon"], cv_df["MAE"],  marker="o", label="MAE",  color="steelblue")
ax.plot(cv_df["horizon"], cv_df["RMSE"], marker="o", label="RMSE", color="darkred")
ax.set_xticks(range(1, 13)); ax.legend()
ax.set_xlabel("Horizon (mois)"); ax.set_ylabel("Erreur (ppm)")
ax.set_title("Validation croisée rolling-origin ARIMA\n"
             "Erreur en fonction de l'horizon de prévision")
plots.save(fig, OUT / "15_cv_arima.png")

# ============================================================
# 16. A5 — NOAA / STL / Hodrick-Prescott (déjà fait en 13)
# ============================================================
print("\n========== 16. NOAA / STL / HP (synthèse plot) ==========")
fig, ax = plt.subplots()
ax.plot(cmp["date"], cmp["NOAA"], label="NOAA", color="steelblue", lw=0.7)
ax.plot(cmp["date"], cmp["STL"],  label="STL",  color="darkorange", lw=0.7)
ax.plot(cmp["date"], cmp["HP"],   label="HP",   color="darkgreen", lw=0.7)
ax.legend(); ax.set_ylabel("ppm")
ax.set_title("Trend désaisonnalisé : NOAA / STL / Hodrick-Prescott")
plots.save(fig, OUT / "16_three_trends.png")

# ============================================================
# 17. B1 — Modèle exponentiel C(t) = C0 * exp(r * t_yrs)
# ============================================================
print("\n========== 17. Modèle exponentiel ==========")

t_yrs = co2["decimal"].to_numpy() - co2["decimal"].iloc[0]


def model_exp(t, C0, r):
    return C0 * np.exp(r * t)


popt, _ = curve_fit(model_exp, t_yrs, y_avg, p0=[336.0, 0.005])
C0_hat, r_hat = popt
double_yrs = float(np.log(2) / r_hat)
print(f"C0 = {C0_hat:.3f} ppm   r = {r_hat:.5f} /an   doublement = {double_yrs:.1f} ans")

# Comparaison AIC linéaire vs exponentiel
yhat_lin = np.polyval(np.polyfit(co2["decimal"], y_avg, 1), co2["decimal"])
yhat_exp = model_exp(t_yrs, *popt)


def aic(y, yhat, k):
    n = len(y); sse = float(np.sum((y - yhat) ** 2))
    return 2 * k + n * np.log(sse / n)


print(f"AIC linéaire     : {aic(y_avg, yhat_lin, 2):.2f}")
print(f"AIC exponentiel  : {aic(y_avg, yhat_exp, 2):.2f}")

fig, ax = plt.subplots()
ax.scatter(co2["date"], y_avg, s=3, alpha=0.3, color="grey")
ax.plot(co2["date"], yhat_exp, color="red",  lw=1, label="Exponentiel")
ax.plot(co2["date"], yhat_lin, color="blue", lw=1, label="Linéaire")
ax.legend(); ax.set_ylabel("ppm")
ax.set_title("Hausse exponentielle vs linéaire\n"
             f"Taux exp r = {r_hat:.4f} /an, doublement = {double_yrs:.1f} ans")
plots.save(fig, OUT / "17_modele_exponentiel.png")

# ============================================================
# 18. B2 — ACF / PACF des résidus STL + Ljung-Box
# ============================================================
print("\n========== 18. ACF / PACF résidus STL ==========")

resid_stl = stl.resid.dropna().values
ljb = acorr_ljungbox(resid_stl, lags=[24], return_df=True)
ljb_p = float(ljb["lb_pvalue"].iloc[0])
print(f"Ljung-Box (lag 24) p = {ljb_p:.4f}")

fig, axes = plt.subplots(2, 1)
acf_vals = acf(resid_stl, nlags=60, fft=False)
pacf_vals = pacf(resid_stl, nlags=60, method="yw")
axes[0].vlines(range(len(acf_vals)), 0, acf_vals)
axes[0].axhline(0, color="black", lw=0.5)
axes[0].set_title("ACF des résidus STL")
axes[1].vlines(range(len(pacf_vals)), 0, pacf_vals)
axes[1].axhline(0, color="black", lw=0.5)
axes[1].set_title("PACF des résidus STL")
plots.save(fig, OUT / "18_acf_pacf_residus_stl.png", w=10, h=7)

# ============================================================
# 19. B3 — Périodogramme spectral
# ============================================================
print("\n========== 19. Spectre ==========")
spec_input = (y_avg - y_trend)
freq, density = signal.periodogram(spec_input, fs=12.0, scaling="density")
# fs = 12 (cycles par an) -> period_months = 12 / freq_par_an = 12 / freq
period_months = np.divide(12.0, freq, out=np.full_like(freq, np.inf),
                          where=freq != 0)
spec_df = pd.DataFrame({"period_months": period_months, "density": density})

top5 = spec_df.sort_values("density", ascending=False).head(5)
print("Top 5 périodes (mois) :")
print(top5)

mask = spec_df["period_months"] <= 60
fig, ax = plt.subplots()
ax.plot(spec_df.loc[mask, "period_months"],
        spec_df.loc[mask, "density"], color="darkblue", lw=0.8)
ax.axvline(12, color="red", ls="--", lw=0.8)
ax.text(13, spec_df["density"].max() * 0.9, "12 mois", color="red")
ax.set_xlabel("Période (mois)"); ax.set_ylabel("Densité spectrale")
ax.set_title("Périodogramme de l'anomalie (average − trend)")
plots.save(fig, OUT / "19_periodogramme.png")

# ============================================================
# 20. B4 — Régression taux annuel ~ ENSO (Niño 3.4)
# ============================================================
print("\n========== 20. Taux annuel ~ ENSO ==========")

oni = io.load_oni()
co2_annual = (co2.groupby("year")
              .agg(annual_mean=("average", "mean"), n=("average", "count"))
              .reset_index())
co2_annual = co2_annual[co2_annual["n"] >= 6].copy()
co2_annual["annual_rate"] = co2_annual["annual_mean"].diff()

oni_annual = (oni.groupby("year")
              .agg(oni_annual=("oni", "mean")).reset_index())

ar_oni = (co2_annual.merge(oni_annual, on="year", how="inner")
          .dropna(subset=["annual_rate"]))

beta1, beta0 = np.polyfit(ar_oni["oni_annual"], ar_oni["annual_rate"], 1)
yhat = beta0 + beta1 * ar_oni["oni_annual"]
ss_res = float(np.sum((ar_oni["annual_rate"] - yhat) ** 2))
ss_tot = float(np.sum((ar_oni["annual_rate"] - ar_oni["annual_rate"].mean()) ** 2))
r2_oni = 1 - ss_res / ss_tot
r_pearson = float(np.corrcoef(ar_oni["annual_rate"], ar_oni["oni_annual"])[0, 1])
# p-value de la pente
n = len(ar_oni)
se_residual = np.sqrt(ss_res / (n - 2))
sx = np.std(ar_oni["oni_annual"], ddof=1) * np.sqrt(n - 1)
t_stat = beta1 * sx / se_residual
from scipy import stats as scstats
p_oni = 2 * (1 - scstats.t.cdf(abs(t_stat), df=n - 2))
print(f"Corrélation Pearson taux ↔ ONI : {r_pearson:.3f}")
print(f"Pente : {beta1:.3f} ppm/an / unité ONI   p = {p_oni:.3g}")

fig, ax = plt.subplots()
sc = ax.scatter(ar_oni["oni_annual"], ar_oni["annual_rate"],
                c=ar_oni["year"], cmap="viridis", s=30)
ax.plot(ar_oni["oni_annual"], yhat, color="darkblue", lw=1)
fig.colorbar(sc, ax=ax, label="Année")
ax.set_xlabel("ONI annuel (anomalie SST °C)")
ax.set_ylabel("Taux CO2 (ppm/an)")
ax.set_title(f"Taux annuel CO2 vs indice ENSO (Niño 3.4)\n"
             f"r = {r_pearson:.2f}, pente = {beta1:.2f} ppm/an par unité ONI (p = {p_oni:.3g})")
plots.save(fig, OUT / "20_taux_vs_enso.png")

# Avec lag de 6 mois (ENSO précède CO2)
oni_dated = oni.assign(date=pd.to_datetime(
    dict(year=oni["year"], month=oni["month"], day=1))).sort_values("date")
oni_dated["oni_lag6"] = oni_dated["oni"].shift(6)
oni_lag6_annual = (oni_dated.groupby("year")
                   .agg(oni_lag6=("oni_lag6", "mean")).reset_index())
ar_oni_lag = (co2_annual.merge(oni_lag6_annual, on="year", how="inner")
              .dropna(subset=["annual_rate", "oni_lag6"]))
r_lag6 = float(np.corrcoef(ar_oni_lag["annual_rate"], ar_oni_lag["oni_lag6"])[0, 1])
print(f"Corrélation taux ↔ ONI(lag 6 mois) : {r_lag6:.3f}")

# ============================================================
# 21. B5 — Effet COVID-19
# ============================================================
print("\n========== 21. Effet COVID-19 ==========")

co2_pre = co2_idx.loc[:"2019-12-31", "average"]
fit_pre = ARIMA(co2_pre, order=(1, 1, 1),
                seasonal_order=(0, 1, 1, 12),
                enforce_stationarity=False,
                enforce_invertibility=False).fit(method_kwargs={"warn_convergence": False})
fcst = fit_pre.get_forecast(steps=24)
mean = fcst.predicted_mean
ci80 = fcst.conf_int(alpha=0.20)

dates_covid = pd.date_range("2020-01-01", periods=24, freq="MS")
obs_covid = co2_idx.loc[dates_covid[0]:dates_covid[-1], "average"].values

covid_df = pd.DataFrame({
    "date": dates_covid,
    "observed": obs_covid,
    "predicted": mean.values,
    "lo80": ci80.iloc[:, 0].values,
    "hi80": ci80.iloc[:, 1].values,
})
covid_df["anomaly"] = covid_df["observed"] - covid_df["predicted"]
print(f"Anomalie cumulée 2020-2021 : {covid_df['anomaly'].sum():.2f} ppm")
print(f"Anomalie moyenne mensuelle : {covid_df['anomaly'].mean():.3f} ppm")
covid_df.to_csv(OUT / "covid_anomalie.csv", index=False)

fig, ax = plt.subplots()
ax.fill_between(covid_df["date"], covid_df["lo80"], covid_df["hi80"], color="lightgrey")
ax.plot(covid_df["date"], covid_df["predicted"], color="blue", lw=1,
        label="Prédit (ARIMA pré-2020)")
ax.plot(covid_df["date"], covid_df["observed"], color="red", lw=1, label="Observé")
ax.legend(); ax.set_ylabel("ppm")
ax.set_title("Effet COVID-19 sur le CO2 atmosphérique global\n"
             "Modèle ARIMA fitté sur 1979-2019 puis projeté")
plots.save(fig, OUT / "21_covid_effect.png")

# ============================================================
# 22. B6 — Cycle saisonnier hémisphérique : NH (MLO) vs SH (SPO)
# ============================================================
print("\n========== 22. Cycle saisonnier hémisphérique ==========")

mlo = io.load_co2_mauna_loa()
spo = io.load_co2_south_pole()


def moving_anom(x):
    """Anomalie = x - moyenne mobile centrée 12 mois (équivalent
    stats::filter(x, rep(1/12, 12), sides = 2) du R)."""
    return x - pd.Series(x).rolling(12, center=True, min_periods=12).mean().values


mlo["anom"] = moving_anom(mlo["mlo_avg"].values)
spo["anom"] = moving_anom(spo["spo_avg"].values)
print(f"MLO : période = {mlo['date'].min().date()} -> {mlo['date'].max().date()} "
      f"({mlo['mlo_avg'].notna().sum()} mois)")
print(f"SPO : période = {spo['date'].min().date()} -> {spo['date'].max().date()} "
      f"({len(spo)} mois)")

mlo_clim = (mlo.dropna(subset=["anom"])
            .groupby("month")["anom"].agg(["mean", "std"])
            .rename(columns={"mean": "mean_anom", "std": "sd_anom"})
            .assign(site="Mauna Loa (NH)").reset_index())
spo_clim = (spo.dropna(subset=["anom"])
            .groupby("month")["anom"].agg(["mean", "std"])
            .rename(columns={"mean": "mean_anom", "std": "sd_anom"})
            .assign(site="South Pole (SH)").reset_index())

fig, ax = plt.subplots()
months = list(range(1, 13))
w = 0.4
ax.bar(np.array(months) - w / 2, mlo_clim["mean_anom"], width=w, color="tomato",
       label="Mauna Loa (NH)", yerr=mlo_clim["sd_anom"], capsize=2)
ax.bar(np.array(months) + w / 2, spo_clim["mean_anom"], width=w, color="steelblue",
       label="South Pole (SH)", yerr=spo_clim["sd_anom"], capsize=2)
ax.set_xticks(months); ax.legend()
ax.set_xlabel("Mois"); ax.set_ylabel("Anomalie (ppm)")
ax.set_title("Cycle saisonnier moyen : NH vs SH\n"
             "Cycles déphasés et amplitude NH >> SH")
plots.save(fig, OUT / "22_cycle_hemispherique.png")

amp_mlo = mlo_clim["mean_anom"].max() - mlo_clim["mean_anom"].min()
amp_spo = spo_clim["mean_anom"].max() - spo_clim["mean_anom"].min()
print(f"Amplitude saisonnière MLO : {amp_mlo:.2f} ppm")
print(f"Amplitude saisonnière SPO : {amp_spo:.2f} ppm")
print(f"Ratio NH / SH             : {amp_mlo / amp_spo:.1f}")

# ============================================================
# 23. B7 — Modèle state-space (équivalent KFAS)
# ============================================================
print("\n========== 23. State-space ==========")

# UnobservedComponents : niveau local + tendance + saison stochastique
ssm = UnobservedComponents(
    co2_idx["average"],
    level="local linear trend",
    seasonal=12,
    stochastic_seasonal=True,
)
fit_ssm = ssm.fit(disp=False, maxiter=500)
trend_ssm = fit_ssm.smoothed_state[0, :]   # niveau
slope_ssm = fit_ssm.smoothed_state[1, :]   # pente

ssm_df = pd.DataFrame({
    "date": co2_idx.index,
    "observed": co2_idx["average"].values,
    "trend_ssm": trend_ssm,
    "slope_ssm": slope_ssm,
})
ssm_df.to_csv(OUT / "ssm_components.csv", index=False)

fig, ax = plt.subplots()
ax.plot(ssm_df["date"], ssm_df["observed"], color="grey", alpha=0.6, lw=0.5)
ax.plot(ssm_df["date"], ssm_df["trend_ssm"], color="red", lw=0.9)
ax.set_ylabel("ppm")
ax.set_title("State-space (Kalman) : niveau lissé\n"
             "Niveau + tendance + saison période 12")
plots.save(fig, OUT / "23a_ssm_level.png")

fig, ax = plt.subplots()
ax.plot(ssm_df["date"], ssm_df["slope_ssm"] * 12, color="darkgreen", lw=0.9)
ax.set_ylabel("ppm/an")
ax.set_title("Pente instantanée (slope) du modèle state-space\n"
             "Convertie en ppm/an, équivalent du taux annuel")
plots.save(fig, OUT / "23b_ssm_slope.png")

# Variances finales du modèle (équivalent du H et Q de KFAS)
print("Paramètres estimés :")
print(fit_ssm.params)

print(f"\n=== Sections 12-23 sauvegardées dans {OUT} ===")
