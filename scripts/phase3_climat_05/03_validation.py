"""Phase 3 — 03 — Validation 0.5° : stats par bande + plots des séries
+ anomalies T2m par bande + tendances Sen.

Migration de 03_validation.R.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, plots                                            # noqa: E402
from climat.stats import sens_slope_and_mk                                  # noqa: E402

OUT = config.OUT_PHASE3
PLOT = OUT / "plots"
PLOT.mkdir(parents=True, exist_ok=True)
plots.setup_theme()

df = pd.read_csv(OUT / "monthly_band_means_05.csv", parse_dates=["date"])

BAND_ORDER = ["austral", "temperate_S", "tropical", "temperate_N", "boreal", "global"]
df["band"] = pd.Categorical(df["band"], categories=BAND_ORDER, ordered=True)

print(f"Tableau chargé : {df.shape}")
print(f"Bandes         : {[config.BAND_LABELS[b] for b in BAND_ORDER]}\n")

vars_ = config.CLIM_VARS

# ============================================================
# 1. Statistiques descriptives par bande
# ============================================================
stats = (df.melt(id_vars=["date", "year", "month", "band"],
                 value_vars=vars_, var_name="var", value_name="value")
         .groupby(["band", "var"], observed=True)["value"]
         .agg(mean="mean", sd="std").reset_index())

print("=== Moyennes par bande (extrait) ===")
key = stats[stats["var"].isin(["T2m", "PWAT", "DSWRF", "TCDC"])]
pivot = key.pivot(index="band", columns="var", values=["mean", "sd"])
print(pivot.round(4))
stats.to_csv(OUT / "stats_par_bande.csv", index=False)

# ============================================================
# 2. Séries T2m, PWAT, DSWRF, TCDC par bande
# ============================================================
key_vars = ["T2m", "PWAT", "DSWRF", "TCDC"]
fig, axes = plt.subplots(2, 2, figsize=(14, 8))
palette = sns.color_palette("Set1", len(BAND_ORDER))
for ax, v in zip(axes.flat, key_vars):
    for b, color in zip(BAND_ORDER, palette):
        sub = df[df["band"] == b]
        ax.plot(sub["date"], sub[v], color=color, alpha=0.7, lw=0.4,
                label=config.BAND_LABELS[b] if v == "T2m" else None)
    ax.set_title(v)
fig.legend(*axes.flat[0].get_legend_handles_labels(), loc="lower center", ncol=6)
fig.suptitle("Variables climatiques par bande de latitude (0.5°)\n"
             "Moyennes pondérées cos(lat) — 1979 → 2025")
plots.save(fig, PLOT / "01_series_par_bande.png", w=14, h=8, dpi=130)

# ============================================================
# 3. Toutes les 18 variables, série globale 0.5°
# ============================================================
df_global = df[df["band"] == "global"]
fig, axes = plt.subplots(5, 4, figsize=(16, 10), sharex=True)
for ax, v in zip(axes.flat, vars_):
    ax.plot(df_global["date"], df_global[v], color="steelblue", lw=0.4)
    ax.set_title(v, fontsize=10)
    ax.tick_params(labelsize=7)
for ax in axes.flat[len(vars_):]:
    ax.set_visible(False)
fig.suptitle("Moyennes globales 0.5° des 18 variables\n"
             "Pour comparaison directe avec le 2.5°")
plots.save(fig, PLOT / "02_series_18_global_05.png", w=16, h=10, dpi=130)

# ============================================================
# 4. Anomalies T2m par bande (sans Global) — réchauffement amplifié
# ============================================================
df_t2m = df[df["band"] != "global"].copy()
clim = (df_t2m.groupby(["band", "month"], observed=True)["T2m"]
        .mean().reset_index().rename(columns={"T2m": "clim_T2m"}))
df_anom = df_t2m.merge(clim, on=["band", "month"])
df_anom["anom"] = df_anom["T2m"] - df_anom["clim_T2m"]

from statsmodels.nonparametric.smoothers_lowess import lowess
fig, ax = plt.subplots(figsize=(12, 7))
for b, color in zip(BAND_ORDER[:-1], sns.color_palette("Set1", 5)):
    sub = df_anom[df_anom["band"] == b].sort_values("date")
    ax.plot(sub["date"], sub["anom"], color=color, alpha=0.3, lw=0.3)
    sm_v = lowess(sub["anom"], (sub["date"] - sub["date"].min()).dt.days,
                  frac=0.15, return_sorted=False)
    ax.plot(sub["date"], sm_v, color=color, lw=1.2, label=config.BAND_LABELS[b])
ax.axhline(0, ls="--", color="grey", lw=0.5)
ax.legend(loc="lower right")
ax.set_ylabel("Anomalie T2m (K)")
ax.set_title("Anomalie de T2m par bande de latitude (lissage LOESS)\n"
             "Réchauffement amplifié attendu en bande boréale (Arctic amplification)")
plots.save(fig, PLOT / "03_T2m_anomaly_par_bande.png", w=12, h=7, dpi=130)

# ============================================================
# 5. Tendances Sen annualisées par bande
# ============================================================
band_trends_rows = []
for b in BAND_ORDER[:-1]:
    sub = df[df["band"] == b]
    row = {"band": b}
    for v in ["T2m", "PWAT", "DSWRF", "TCDC"]:
        sen = sens_slope_and_mk(sub[v].to_numpy())
        row[f"sen_{v}"] = sen.sen_per_year
    band_trends_rows.append(row)
band_trends = pd.DataFrame(band_trends_rows)
print("\n=== Tendances Sen annualisées par bande ===")
print(band_trends.round(4))
band_trends.to_csv(OUT / "trends_par_bande.csv", index=False)

print(f"\n=== Plots sauvegardés dans : {PLOT} ===")
