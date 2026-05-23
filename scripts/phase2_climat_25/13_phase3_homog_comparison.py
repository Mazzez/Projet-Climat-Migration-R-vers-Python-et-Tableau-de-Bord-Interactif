"""Phase 2 — 13 — Comparaison phase 3 brute vs homogénéisée.

Migration de 13_phase3_homog_comparison.R.
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

from climat import config, io, plots                                        # noqa: E402
from climat.preprocess import add_cre, build_residuals                      # noqa: E402

OUT = config.OUT_PHASE2
PLOT = OUT / "plots"
plots.setup_theme()

co2 = io.load_co2_global()[["date", "average", "trend"]].rename(
    columns={"average": "co2_avg", "trend": "co2_trend"})

clim_vars = config.CLIM_VARS + ["CRE_SW", "CRE_LW", "CRE_net"]


def _drop_aliased_cols(X: pd.DataFrame, tol: float = 1e-9) -> list[str]:
    """QR-pivoting pour détecter les colonnes redondantes (mimique R lm())."""
    from scipy.linalg import qr
    Q, R, piv = qr(X.to_numpy(dtype=float), mode="economic", pivoting=True)
    diag = np.abs(np.diag(R))
    rank = int(np.sum(diag > tol * diag.max()))
    return [X.columns[i] for i in piv[rank:]]


def step_backward_r2(X: pd.DataFrame, y: np.ndarray) -> tuple[float, float, int]:
    """Élimination AIC backward avec gestion du rank-deficiency.
    Renvoie (R²_complet, R²_step, n_step)."""
    # Retirer les colonnes aliasées (= NA coefficients en R)
    aliased = _drop_aliased_cols(X)
    X = X.drop(columns=aliased)

    cols = list(X.columns)
    full = sm.OLS(y, sm.add_constant(X[cols])).fit()
    cur = full
    cur_aic = float(full.aic)
    while len(cols) > 1:
        cands = []
        for c in cols:
            sub = [x for x in cols if x != c]
            f = sm.OLS(y, sm.add_constant(X[sub])).fit()
            cands.append((float(f.aic), c, f))
        cands.sort(key=lambda t: t[0])
        a, drop_c, fbest = cands[0]
        if a >= cur_aic: break
        cur, cur_aic = fbest, a
        cols.remove(drop_c)
    return float(full.rsquared), float(cur.rsquared), len(cols)


def analyse_version(file_path: Path, label: str) -> dict:
    d = pd.read_csv(file_path, parse_dates=["date"]).merge(co2, on="date", how="inner")
    if "CRE_SW" not in d.columns:
        d = add_cre(d)
    dates = pd.DatetimeIndex(d["date"])
    co2_resid = build_residuals(d["co2_trend"].to_numpy(), dates)
    cor_rows = []
    X_cols = {}
    for v in clim_vars:
        r = build_residuals(d[v].to_numpy(), dates)
        X_cols[v] = r
        cor_rows.append({"version": label, "var": v,
                         "r": float(np.corrcoef(r, co2_resid)[0, 1])})
    cor_rows.append({"version": label, "var": "co2_trend", "r": 1.0})
    X = pd.DataFrame(X_cols)
    r2_full, r2_step, n_step = step_backward_r2(X, co2_resid)
    return {
        "cor": pd.DataFrame(cor_rows),
        "r2": {"version": label, "r2_full": r2_full, "r2_step": r2_step, "n_step": n_step},
    }


print("=== Analyse version BRUTE ===")
res_brut  = analyse_version(OUT / "monthly_global_means_25.csv",       "brute")
print(f"R² complet : {res_brut['r2']['r2_full']:.3f}   "
      f"R² stepwise : {res_brut['r2']['r2_step']:.3f}   "
      f"vars retenues : {res_brut['r2']['n_step']}\n")

print("=== Analyse version HOMOGÉNÉISÉE ===")
res_homog = analyse_version(OUT / "monthly_global_means_25_homog.csv", "homog")
print(f"R² complet : {res_homog['r2']['r2_full']:.3f}   "
      f"R² stepwise : {res_homog['r2']['r2_step']:.3f}   "
      f"vars retenues : {res_homog['r2']['n_step']}\n")

cmp = (pd.concat([res_brut["cor"], res_homog["cor"]], ignore_index=True)
       .query("var != 'co2_trend'")
       .pivot(index="var", columns="version", values="r")
       .reset_index())
cmp["diff"] = cmp["homog"] - cmp["brute"]
cmp = cmp.sort_values("diff", key=lambda c: c.abs(), ascending=False)
print("=== Variations des corrélations (sur résidus) ===")
print(cmp.round(3).to_string(index=False))
cmp.to_csv(OUT / "comparison_homog_correlations.csv", index=False)

# Scatter brute vs homog
fig, ax = plt.subplots(figsize=(10, 9))
ax.plot([-1, 1], [-1, 1], ls="--", color="grey")
ax.axhline(0, ls=":", color="grey"); ax.axvline(0, ls=":", color="grey")
mask = cmp["diff"].abs() > 0.1
ax.scatter(cmp.loc[~mask, "brute"], cmp.loc[~mask, "homog"], color="grey", s=40)
ax.scatter(cmp.loc[mask,  "brute"], cmp.loc[mask,  "homog"], color="tomato", s=40)
for _, row in cmp.iterrows():
    ax.annotate(row["var"], (row["brute"], row["homog"]),
                xytext=(3, 3), textcoords="offset points", fontsize=8)
ax.set_xlabel("r (version brute)"); ax.set_ylabel("r (version homogénéisée)")
ax.set_title("Corrélations climat ↔ CO2 sur résidus\n"
             "Comparaison : version brute vs version homogénéisée\nDiagonale = pas de changement")
plots.save(fig, PLOT / "13a_correlations_homog_vs_brut.png", w=10, h=9, dpi=130)

# R² comparatif
r2_df = pd.DataFrame([
    {"version": "Brute",        "model": "Complet",  "r2": res_brut["r2"]["r2_full"]},
    {"version": "Brute",        "model": "Stepwise", "r2": res_brut["r2"]["r2_step"]},
    {"version": "Homogénéisée", "model": "Complet",  "r2": res_homog["r2"]["r2_full"]},
    {"version": "Homogénéisée", "model": "Stepwise", "r2": res_homog["r2"]["r2_step"]},
])
fig, ax = plt.subplots(figsize=(8, 6))
sns.barplot(data=r2_df, x="model", y="r2", hue="version",
            palette={"Brute": "steelblue", "Homogénéisée": "tomato"}, ax=ax)
for c in ax.containers:
    ax.bar_label(c, fmt="%.3f", padding=3, fontsize=9)
ax.set_ylim(0, 1); ax.set_ylabel("R²")
ax.set_title("R² des modèles de régression CO2_trend ~ climat\n"
             "Variables sur résidus (anom désaisonnée + détendrée)")
plots.save(fig, PLOT / "13b_R2_homog_vs_brut.png", w=8, h=6, dpi=130)

print("\n=== Sauvegardes ===")
print(" - comparison_homog_correlations.csv")
print(" - plots/13a_correlations_homog_vs_brut.png, 13b_R2_homog_vs_brut.png")
