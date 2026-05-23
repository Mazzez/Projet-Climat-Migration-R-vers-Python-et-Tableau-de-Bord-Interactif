"""Phase 2 — 08 — Tests de causalité de Granger climat ↔ CO2 (lag = 6 mois)
sur deux représentations en parallèle (résidus + d12).

Migration de 08_granger.R.
"""
from __future__ import annotations
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, plots                                            # noqa: E402
from climat.stats import grangertest_pvalue                                 # noqa: E402

OUT = config.OUT_PHASE2
PLOT = OUT / "plots"
plots.setup_theme()

LAG = 6
clim_vars = config.CLIM_VARS + ["CRE_SW", "CRE_LW", "CRE_net"]

with open(OUT / "series_transformed.pkl", "rb") as fh:
    ds = pickle.load(fh)


def run_granger(d_x: pd.DataFrame, co2_series: np.ndarray, label: str) -> pd.DataFrame:
    rows = []
    for v in clim_vars:
        x = d_x[v].to_numpy()
        ok = ~np.isnan(x) & ~np.isnan(co2_series)
        if ok.sum() < 50:
            continue
        F1, p1 = grangertest_pvalue(co2_series[ok], x[ok], lag=LAG)   # X -> CO2
        F2, p2 = grangertest_pvalue(x[ok], co2_series[ok], lag=LAG)   # CO2 -> X
        rows.append({
            "repr": label, "var": v,
            "F_x_to_co2": F1, "p_x_to_co2": p1,
            "F_co2_to_x": F2, "p_co2_to_x": p2,
        })
    return pd.DataFrame(rows)


gr_resid = run_granger(ds["resid"], ds["resid"]["co2_trend"].to_numpy(), "resid")
gr_d12   = run_granger(ds["d12"],   ds["d12"]["co2_avg"].to_numpy(),     "d12")
gr = pd.concat([gr_resid, gr_d12], ignore_index=True)

gr["sig_x_to_co2"] = gr["p_x_to_co2"] < 0.05
gr["sig_co2_to_x"] = gr["p_co2_to_x"] < 0.05
def _sens(row):
    if row["sig_x_to_co2"] and row["sig_co2_to_x"]: return "bidirectionnel"
    if row["sig_x_to_co2"]: return "X -> CO2"
    if row["sig_co2_to_x"]: return "CO2 -> X"
    return "aucun"
gr["sens"] = gr.apply(_sens, axis=1)
gr = gr.sort_values(["repr", "p_x_to_co2"]).reset_index(drop=True)

print(f"=== Granger causality (lag = {LAG} mois) — RÉSIDUS ===\n")
print(gr[gr["repr"] == "resid"][["var", "p_x_to_co2", "p_co2_to_x", "sens"]].to_string(index=False))
print(f"\n=== Granger causality (lag = {LAG} mois) — d12 (taux annuel) ===\n")
print(gr[gr["repr"] == "d12"][["var", "p_x_to_co2", "p_co2_to_x", "sens"]].to_string(index=False))
gr.to_csv(OUT / "granger_results.csv", index=False)

print("\n=== Synthèse sens du lien (p < 0.05) par représentation ===")
print(gr.groupby(["repr", "sens"]).size().reset_index(name="n"))

# Visualisation : -log10(p) dans les 2 sens, par représentation
gr_long = gr.melt(id_vars=["repr", "var"], value_vars=["p_x_to_co2", "p_co2_to_x"],
                  var_name="direction", value_name="p")
gr_long["direction"] = gr_long["direction"].map({"p_x_to_co2": "X -> CO2",
                                                  "p_co2_to_x": "CO2 -> X"})
gr_long["nlogp"] = -np.log10(gr_long["p"].clip(lower=1e-300))

fig, axes = plt.subplots(1, 2, figsize=(11, 8), sharey=True)
import seaborn as sns
for ax, repr_name in zip(axes, ["resid", "d12"]):
    sub = gr_long[gr_long["repr"] == repr_name].copy()
    order = (sub.groupby("var")["nlogp"].max().sort_values().index.tolist())
    sub["var"] = pd.Categorical(sub["var"], categories=order, ordered=True)
    sns.barplot(data=sub, y="var", x="nlogp", hue="direction",
                palette={"X -> CO2": "tomato", "CO2 -> X": "steelblue"},
                ax=ax, orient="h")
    ax.axvline(-np.log10(0.05), ls="--", color="darkred")
    ax.set_title(repr_name); ax.set_xlabel("−log10(p)"); ax.set_ylabel(None)
    if repr_name == "resid": ax.legend(loc="upper right", title="Sens")
    else: ax.get_legend().remove() if ax.get_legend() else None
fig.suptitle(f"Tests de causalité de Granger (lag = {LAG} mois)\n"
             "Comparaison résidus (anomalies détendrées) vs d12 (taux annuel)\n"
             "Ligne rouge = seuil p = 0.05")
plots.save(fig, PLOT / "08_granger.png", w=11, h=8, dpi=130)

print("\n=== Sauvegardes ===")
print(" - granger_results.csv")
print(" - plots/08_granger.png")
