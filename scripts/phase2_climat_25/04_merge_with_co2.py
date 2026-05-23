"""Phase 2 — 04 — Fusion 18 variables climat + CO2 NOAA, calcul CRE,
corrélations brutes (vue de premier ordre).

Migration de 04_merge_with_co2.R.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, io, plots                                        # noqa: E402
from climat.preprocess import add_cre                                       # noqa: E402

OUT = config.OUT_PHASE2
PLOT = OUT / "plots"
plots.setup_theme()

clim = pd.read_csv(OUT / "monthly_global_means_25.csv", parse_dates=["date"])
co2 = io.load_co2_global()[["date", "average", "trend"]].rename(
    columns={"average": "co2_avg", "trend": "co2_trend"})

print(f"Climat   : {clim.shape}, {clim['date'].min().date()} -> {clim['date'].max().date()}")
print(f"CO2 NOAA : {co2.shape}, {co2['date'].min().date()} -> {co2['date'].max().date()}")

df = clim.merge(co2, on="date", how="inner")
df = add_cre(df)
print(f"\nTableau fusionné : {df.shape}")
print(f"Plage commune    : {df['date'].min().date()} -> {df['date'].max().date()}")

df.to_csv(OUT / "climate_co2_monthly.csv", index=False)
print("\n=== Sauvegardé : climate_co2_monthly.csv ===")

# Corrélations brutes (Pearson) sur niveaux
clim_vars = config.CLIM_VARS + ["CRE_SW", "CRE_LW", "CRE_net"]
cor_brut = pd.DataFrame({
    "var": clim_vars,
    "r_pearson": [df[v].corr(df["co2_trend"]) for v in clim_vars],
}).sort_values("r_pearson", key=abs, ascending=False)

print("\n=== Corrélations brutes Pearson( var, CO2_trend ) ===")
print(cor_brut)
cor_brut.to_csv(OUT / "correlations_brut.csv", index=False)

# Bar plot
fig, ax = plt.subplots()
ordered = cor_brut.sort_values("r_pearson")
colors = ["tomato" if r > 0 else "steelblue" for r in ordered["r_pearson"]]
ax.barh(ordered["var"], ordered["r_pearson"], color=colors)
ax.axvline(0, color="black", lw=0.5)
ax.set_xlabel("r")
ax.set_title("Corrélations brutes (Pearson) climat ↔ CO2 trend\n"
             "Niveaux non désaisonnés ni dé-tendance — vue de premier ordre seulement")
plots.save(fig, PLOT / "05_correlations_brut.png", w=10, h=8, dpi=130)

print("\n=== Plot : 05_correlations_brut.png ===")
