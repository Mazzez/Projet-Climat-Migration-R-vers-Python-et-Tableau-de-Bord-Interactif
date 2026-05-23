"""Phase 2 — 03 — Sanity checks + plots des 18 séries + Cloud Radiative
Effects + transition CFSR↔CFSv2 + climatologie saisonnière.

Migration de 03_validation.R.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, plots                                            # noqa: E402
from climat.preprocess import add_cre                                       # noqa: E402

OUT = config.OUT_PHASE2
PLOT = OUT / "plots"
PLOT.mkdir(parents=True, exist_ok=True)
plots.setup_theme()

df = pd.read_csv(OUT / "monthly_global_means_25.csv", parse_dates=["date"])
print(f"Dimensions : {df.shape}")
print(f"Plage      : {df['date'].min().date()} -> {df['date'].max().date()}\n")

vars_ = config.CLIM_VARS  # 18 variables

# ============================================================
# 1. Statistiques descriptives par variable
# ============================================================
stats = (df[vars_].agg(["min", "mean", "max", "std"]).T
         .reset_index().rename(columns={"index": "var", "std": "sd"}))
print(stats)

# Sanity check
exp_df = pd.DataFrame([(v, lo, hi) for v, (lo, hi) in config.EXPECTED_RANGES.items()],
                      columns=["var", "lo", "hi"])
sanity = stats.merge(exp_df, on="var", how="left")
sanity["status"] = np.where(
    (sanity["mean"] < sanity["lo"]) | (sanity["mean"] > sanity["hi"]),
    "ALERTE", "OK"
)
print("\n=== Sanity check (moyennes globales) ===")
print(sanity[["var", "mean", "lo", "hi", "status"]])

# ============================================================
# 2. Plot 18 séries temporelles
# ============================================================
fig, axes = plt.subplots(5, 4, figsize=(16, 10), sharex=True)
for ax, v in zip(axes.flat, vars_):
    ax.plot(df["date"], df[v], color="steelblue", lw=0.5)
    ax.set_title(v, fontsize=10)
    ax.tick_params(labelsize=7)
# Cacher les axes vides
for ax in axes.flat[len(vars_):]:
    ax.set_visible(False)
fig.suptitle(
    "Moyennes globales mensuelles pondérées cos(lat) — 18 variables\n"
    "1979-01 → 2025-12 (résolution 2.5° × 2.5°)",
    fontsize=12,
)
plots.save(fig, PLOT / "01_series_18_variables.png", w=16, h=10, dpi=130)

# ============================================================
# 3. Cloud Radiative Effects
# ============================================================
df_cre = add_cre(df)[["date", "year", "month", "CRE_SW", "CRE_LW", "CRE_net"]]
print("\n=== Statistiques Cloud Radiative Effects (W/m²) ===")
print(df_cre[["CRE_SW", "CRE_LW", "CRE_net"]].agg(["mean", "std"]))

df_cre.to_csv(OUT / "cre_monthly_25.csv", index=False)

fig, axes = plt.subplots(3, 1, sharex=True, figsize=(12, 10))
for ax, comp, color in zip(axes,
                            ["CRE_SW", "CRE_LW", "CRE_net"],
                            ["steelblue", "tomato", "purple"]):
    ax.plot(df_cre["date"], df_cre[comp], color=color, lw=0.7)
    ax.axhline(0, ls="--", color="grey", lw=0.5)
    ax.set_title(comp); ax.set_ylabel("W/m²")
fig.suptitle("Cloud Radiative Effects à la surface\n"
             "CRE_SW (refroidissement par les nuages), CRE_LW (réchauffement par les nuages), net")
plots.save(fig, PLOT / "02_cloud_radiative_effects.png", w=12, h=10, dpi=130)

# ============================================================
# 4. Vérification continuité CFSR → CFSv2 (transition fin 2010)
# ============================================================
df_zoom = df[(df["year"] >= 2008) & (df["year"] <= 2013)]
fig, axes = plt.subplots(2, 2, figsize=(12, 7))
for ax, v in zip(axes.flat, ["T2m", "PWAT", "DSWRF", "TCDC"]):
    ax.plot(df_zoom["date"], df_zoom[v], color="steelblue", lw=0.7)
    ax.axvline(pd.Timestamp("2011-01-01"), ls="--", color="darkred", lw=0.7)
    ax.set_title(v)
fig.suptitle("Continuité CFSR (≤ 2010) → CFSv2 (≥ 2011)\n"
             "Pas de saut visible attendu — 4 variables témoins")
plots.save(fig, PLOT / "03_transition_cfsr_cfsv2.png", w=12, h=7, dpi=130)

# ============================================================
# 5. Climatologie saisonnière (6 variables clés)
# ============================================================
key6 = ["T2m", "PWAT", "DSWRF", "APCP", "TCDC", "ALBDO"]
fig, axes = plt.subplots(2, 3, figsize=(12, 7))
for ax, v in zip(axes.flat, key6):
    cm = (df.groupby("month")[v].agg(mean="mean", sd="std").reset_index())
    ax.fill_between(cm["month"], cm["mean"] - cm["sd"], cm["mean"] + cm["sd"],
                    alpha=0.2, color="steelblue")
    ax.plot(cm["month"], cm["mean"], color="steelblue", lw=1)
    ax.scatter(cm["month"], cm["mean"], color="steelblue", s=8)
    ax.set_xticks(range(1, 13))
    ax.set_title(v)
fig.suptitle("Climatologie saisonnière mondiale\n"
             "Moyenne mensuelle 1979-2025 ± 1 sd")
plots.save(fig, PLOT / "04_climatologie_saisonniere.png", w=12, h=7, dpi=130)

print(f"\n=== Plots sauvegardés dans : {PLOT} ===")
