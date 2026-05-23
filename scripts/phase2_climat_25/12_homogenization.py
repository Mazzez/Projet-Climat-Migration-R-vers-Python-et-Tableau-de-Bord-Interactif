"""Phase 2 — 12 — Détection et correction du saut CFSR (≤2010) → CFSv2 (≥2011)
sur 21 variables, modèle additif `y ~ t + step + month`.

Migration de 12_homogenization.R.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, plots                                            # noqa: E402
from climat.preprocess import add_cre                                       # noqa: E402

OUT = config.OUT_PHASE2
PLOT = OUT / "plots"
plots.setup_theme()

clim = pd.read_csv(OUT / "monthly_global_means_25.csv", parse_dates=["date"])
clim = add_cre(clim)
clim["t"] = (clim["date"] - pd.Timestamp("1979-01-01")).dt.days / 365.25
clim["step"] = (clim["date"] >= pd.Timestamp("2011-01-01")).astype(int)

all_vars = config.CLIM_VARS + ["CRE_SW", "CRE_LW", "CRE_net"]

# ============================================================
# 1. Estimation du saut par variable
# ============================================================
month_dummies = pd.get_dummies(clim["month"], prefix="m", drop_first=True).astype(float)
X_design = pd.concat([clim[["t", "step"]].astype(float), month_dummies], axis=1)
X_design = sm.add_constant(X_design)

jumps_rows = []
for v in all_vars:
    y = clim[v].to_numpy(dtype=float)
    fit = sm.OLS(y, X_design).fit()
    jump = float(fit.params["step"])
    se = float(fit.bse["step"])
    p = float(fit.pvalues["step"])
    ci = fit.conf_int(alpha=0.05).loc["step"]
    trend_per_yr = float(fit.params["t"])
    mean_v = float(np.mean(y))
    sd_v = float(np.std(y, ddof=1))
    jumps_rows.append({
        "var": v, "jump": jump, "se": se, "p_value": p,
        "ci_lo": float(ci[0]), "ci_hi": float(ci[1]),
        "trend_per_yr": trend_per_yr,
        "mean_var": mean_v, "sd_var": sd_v,
        "jump_pct": jump / mean_v * 100 if mean_v != 0 else np.nan,
    })

J = pd.DataFrame(jumps_rows)
J["significant"] = J["p_value"] < 0.05
J["jump_in_sd"] = J["jump"] / J["sd_var"]

J_sorted = J.assign(abs_sd=J["jump_in_sd"].abs()).sort_values("abs_sd", ascending=False).drop(columns="abs_sd")
print("=== Saut estimé CFSR -> CFSv2 (jan 2011) par variable ===")
print(J_sorted[["var", "jump", "jump_pct", "jump_in_sd", "p_value", "significant"]].round(3).to_string(index=False))
J.to_csv(OUT / "cfsr_to_cfsv2_jumps.csv", index=False)

print("\n=== Synthèse ===")
print(f"Variables avec saut significatif (p < 0.05) : {int(J['significant'].sum())} / {len(J)}")
print("Top 5 plus gros sauts (en sd) :")
print(J_sorted.head(5)[["var", "jump", "jump_pct", "jump_in_sd", "p_value"]].round(3).to_string(index=False))

# ============================================================
# 2. Construction de la version homogénéisée (saut retiré aux ≥ 2011)
# ============================================================
homog = clim.copy()
for v in all_vars:
    j = float(J.loc[J["var"] == v, "jump"].iloc[0])
    homog.loc[homog["step"] == 1, v] = homog.loc[homog["step"] == 1, v] - j
homog = homog.drop(columns=["t", "step"])
homog.to_csv(OUT / "monthly_global_means_25_homog.csv", index=False)

# ============================================================
# 3. Bar plot des sauts en sd
# ============================================================
fig, ax = plt.subplots(figsize=(10, 8))
J_plot = J.sort_values("jump_in_sd")
colors = ["tomato" if s else "grey" for s in J_plot["significant"]]
ax.barh(J_plot["var"], J_plot["jump_in_sd"], color=colors)
for i, val in enumerate(J_plot["jump_in_sd"]):
    ax.text(val, i, f"{val:+.2f}",
            ha="left" if val > 0 else "right", va="center", fontsize=8)
ax.axvline(0, color="black", lw=0.4)
ax.set_xlabel("Saut / écart-type")
ax.set_title("Saut CFSR → CFSv2 (jan 2011) par variable\n"
             "Estimé par lm(y ~ t + step + month) ; valeur en écarts-type")
# Légende custom
import matplotlib.patches as mpatches
ax.legend(handles=[
    mpatches.Patch(color="tomato", label="p < 0.05"),
    mpatches.Patch(color="grey",   label="non sig."),
], loc="lower right")
plots.save(fig, PLOT / "12a_jumps_bar.png", w=10, h=8, dpi=130)

# ============================================================
# 4. Avant/après pour les 4 variables les plus impactées
# ============================================================
top4 = J_sorted.head(4)["var"].tolist()
print(f"\nVariables visualisées avant/après : {top4}")

fig, axes = plt.subplots(2, 2, figsize=(12, 8))
for ax, v in zip(axes.flat, top4):
    ax.plot(clim["date"], clim[v], color="steelblue", lw=0.5, alpha=0.7,
            label="Brute (avec saut)")
    ax.plot(homog["date"], homog[v], color="tomato", lw=0.5, alpha=0.7,
            label="Homogénéisée")
    ax.axvline(pd.Timestamp("2011-01-01"), ls="--", color="darkred")
    ax.set_title(v); ax.set_ylabel(None)
axes[0, 0].legend(loc="upper left")
fig.suptitle("Avant / après homogénéisation — top 4 variables\n"
             "Ligne pointillée rouge : transition CFSR → CFSv2 (jan 2011)")
plots.save(fig, PLOT / "12b_before_after.png", w=12, h=8, dpi=130)

# ============================================================
# 5. Magnitude × significativité
# ============================================================
J_plot2 = J.assign(abs_sd=J["jump_in_sd"].abs(),
                   nlogp=-np.log10(J["p_value"].clip(lower=1e-300)))
J_plot2 = J_plot2.sort_values("abs_sd")
fig, ax = plt.subplots(figsize=(10, 8))
norm = plt.Normalize(vmin=J_plot2["nlogp"].min(), vmax=J_plot2["nlogp"].max())
cmap = plt.get_cmap("magma_r")
for i, row in enumerate(J_plot2.itertuples()):
    ax.barh(row.var, row.abs_sd, color=cmap(norm(row.nlogp)))
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
fig.colorbar(sm, ax=ax, label="−log10(p)")
ax.set_xlabel("|Saut| / écart-type")
ax.set_title("Magnitude absolue du saut + significativité\n"
             "Couleur = -log10(p) ; un saut peut être grand mais non significatif si la variance est élevée")
plots.save(fig, PLOT / "12c_significance_grid.png", w=10, h=8, dpi=130)

print("\n=== Sauvegardes ===")
print(" - cfsr_to_cfsv2_jumps.csv")
print(" - monthly_global_means_25_homog.csv")
print(" - plots/12a_jumps_bar.png, 12b_before_after.png, 12c_significance_grid.png")
