"""Phase 2 — 10 — Fiches d'analyse par variable (21 vars × 4 plots) :
1) série + LOESS, 2) STL, 3) climato + amplitude/décennie, 4) heatmap mois×année.

Migration de 10_per_variable_analysis.R.
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

from statsmodels.tsa.seasonal import STL                                    # noqa: E402
from statsmodels.nonparametric.smoothers_lowess import lowess               # noqa: E402

OUT = config.OUT_PHASE2
PV = OUT / "per_variable"
PV.mkdir(parents=True, exist_ok=True)
plots.setup_theme()

df = pd.read_csv(OUT / "climate_co2_monthly.csv", parse_dates=["date"])
df["decade"] = (df["year"] // 10 * 10).astype(int).astype(str) + "s"

all_vars = config.CLIM_VARS + ["CRE_SW", "CRE_LW", "CRE_net"]


def analyse_variable(v: str) -> dict:
    unit, long = config.META[v]
    d = df[["date", "year", "month", "decade", v]].rename(columns={v: "value"}).copy()
    vdir = PV / v
    vdir.mkdir(parents=True, exist_ok=True)

    # -- 1. Série + LOESS
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(d["date"], d["value"], color="steelblue", alpha=0.6, lw=0.5)
    sm = lowess(d["value"], (d["date"] - d["date"].min()).dt.days,
                frac=0.2, return_sorted=False)
    ax.plot(d["date"], sm, color="darkred", lw=1)
    ax.set_ylabel(f"{v} ({unit})")
    ax.set_title(f"{v} — série temporelle 1979-2025\n"
                 f"{long} ({unit}) ; lissage LOESS span=0.2 en rouge")
    plots.save(fig, vdir / "01_timeseries_loess.png", w=10, h=5, dpi=130)

    # -- 2. STL
    s = pd.Series(d["value"].values, index=pd.PeriodIndex(d["date"], freq="M").to_timestamp())
    stl = STL(s, period=12, robust=True).fit()
    amp_seasonal = float(stl.seasonal.max() - stl.seasonal.min())

    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(10, 5))
    axes[0].plot(d["date"], d["value"], color="steelblue", lw=0.5)
    axes[0].set_title("observed"); axes[0].set_ylabel(f"{v} ({unit})")
    axes[1].plot(d["date"], stl.trend.values, color="steelblue", lw=0.8)
    axes[1].set_title("trend"); axes[1].set_ylabel(f"{v} ({unit})")
    fig.suptitle(f"{v} — décomposition STL (observed + trend)\n"
                 f"Amplitude saisonnière = {amp_seasonal:.3f} {unit}")
    plots.save(fig, vdir / "02_stl_decomposition.png", w=10, h=5, dpi=130)

    # -- 3. Climatologie + amplitude par décennie
    clim = (d.groupby("month")["value"]
            .agg(mean="mean", sd="std").reset_index())
    amp_dec = (d.groupby("decade")["value"]
               .agg(amp=lambda s: s.max() - s.min()).reset_index())

    fig, axes = plt.subplots(2, 1, figsize=(10, 8),
                             gridspec_kw={"height_ratios": [1, 0.7]})
    axes[0].fill_between(clim["month"], clim["mean"] - clim["sd"], clim["mean"] + clim["sd"],
                         color="steelblue", alpha=0.2)
    axes[0].plot(clim["month"], clim["mean"], color="steelblue", lw=1)
    axes[0].scatter(clim["month"], clim["mean"], color="steelblue", s=15)
    axes[0].set_xticks(range(1, 13))
    axes[0].set_xticklabels(["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
    axes[0].set_title(f"{v} — climatologie mensuelle"); axes[0].set_ylabel(f"{v} ({unit})")

    axes[1].bar(amp_dec["decade"], amp_dec["amp"], color="tomato")
    for i, val in enumerate(amp_dec["amp"]):
        axes[1].text(i, val, f"{val:.3g}", ha="center", va="bottom", fontsize=8)
    axes[1].set_title(f"{v} — amplitude (max-min) par décennie")
    axes[1].set_ylabel(f"{v} ({unit})")
    plots.save(fig, vdir / "03_seasonal_climato.png", w=10, h=8, dpi=130)

    # -- 4. Heatmap mois × année
    anom = d["value"].values - clim["mean"].values[d["month"].values - 1]
    pivot = (pd.DataFrame({"year": d["year"], "month": d["month"], "anom": anom})
             .pivot(index="year", columns="month", values="anom"))
    fig, ax = plt.subplots(figsize=(8, 9))
    sns.heatmap(pivot, cmap=sns.diverging_palette(220, 20, as_cmap=True),
                center=0, ax=ax,
                cbar_kws={"label": f"anom ({unit})"})
    ax.set_xticks(np.arange(12) + 0.5)
    ax.set_xticklabels(["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
    ax.invert_yaxis()
    ax.set_title(f"{v} — heatmap mois × année des anomalies\n"
                 "Anomalie = valeur − climatologie mensuelle")
    plots.save(fig, vdir / "04_heatmap_anomaly.png", w=8, h=9, dpi=130)

    # Stats
    sen = sens_slope_and_mk(d["value"].values)
    n = len(d)
    return {
        "var": v, "long_name": long, "unit": unit, "n_obs": n,
        "min": float(d["value"].min()),
        "mean": float(d["value"].mean()),
        "max": float(d["value"].max()),
        "sd": float(d["value"].std()),
        "range": float(d["value"].max() - d["value"].min()),
        "sen_per_year": sen.sen_per_year,
        "sen_total": sen.sen_per_year * (n / 12),
        "mk_tau": sen.mk_tau,
        "mk_pvalue": sen.mk_p,
        "seasonal_amp_stl": amp_seasonal,
        "amp_decade_first": float(amp_dec["amp"].iloc[0]),
        "amp_decade_last":  float(amp_dec["amp"].iloc[-1]),
    }


print("Génération des fiches par variable :")
all_stats = []
import time
t0 = time.time()
for i, v in enumerate(all_vars, 1):
    print(f"  [{i:2d}/{len(all_vars)}] {v}")
    all_stats.append(analyse_variable(v))
print(f"\nDurée totale : {time.time() - t0:.1f} s")

stats_df = pd.DataFrame(all_stats)
stats_df.to_csv(OUT / "per_variable_stats.csv", index=False)

print("\n=== Statistiques par variable ===")
print(stats_df.round(4).to_string(index=False))
print(f"\nFiches dans : {PV}")
print(f"Stats        : {OUT / 'per_variable_stats.csv'}")
