"""Phase 2 — 07 — Régressions multivariées CO2 ~ climat sur RÉSIDUS :
- multicolinéarité (top 10 corrélations entre prédicteurs)
- régression complète (OLS)
- sélection AIC stepwise (backward)
- Lasso CV (LassoCV) + path

Migration de 07_regressions.R.
"""
from __future__ import annotations
import io as _io
import pickle
import sys
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, plots                                            # noqa: E402

import statsmodels.api as sm                                                # noqa: E402
from sklearn.linear_model import LassoCV, Lasso                             # noqa: E402
from sklearn.preprocessing import StandardScaler                            # noqa: E402

OUT = config.OUT_PHASE2
PLOT = OUT / "plots"
plots.setup_theme()

with open(OUT / "series_transformed.pkl", "rb") as fh:
    ds = pickle.load(fh)

clim_vars = config.CLIM_VARS + ["CRE_SW", "CRE_LW", "CRE_net"]
X = ds["resid"][clim_vars].copy()
y = ds["resid"]["co2_trend"].to_numpy()

print(f"Régression sur résidus : {len(X)} obs, {X.shape[1]} prédicteurs\n")

# ============================================================
# 1. Multicolinéarité — top 10 corrélations
# ============================================================
print("=== Top 10 corrélations entre prédicteurs (multicolinéarité) ===")
M = X.corr()
pairs = []
for i, a in enumerate(M.columns):
    for j, b in enumerate(M.columns):
        if i < j:
            pairs.append({"Var1": a, "Var2": b, "r": M.iloc[i, j]})
pairs_df = (pd.DataFrame(pairs)
            .assign(abs_r=lambda d: d["r"].abs())
            .sort_values("abs_r", ascending=False)
            .drop(columns="abs_r")
            .head(10))
print(pairs_df.round(3).to_string(index=False))

# ============================================================
# Détection des colonnes redondantes (rank-deficiency)
#
# CRE_SW, CRE_LW, CRE_net sont des combinaisons linéaires EXACTES des flux
# radiatifs (DSWRF/USWRF/CSDSF/CSUSF/...), donc inclure les 21 vars rend X
# rank-deficient. R `lm()` les détecte automatiquement et met leurs coefs
# à NA. statsmodels ne le fait pas, ce qui produit des coefs gigantesques
# (~1e+12) par pseudo-inversion. On reproduit le comportement R en pivotant
# par QR pour identifier les colonnes redondantes et les retirer.
# ============================================================
def drop_aliased_cols(X: pd.DataFrame, tol: float = 1e-9) -> list[str]:
    """Retourne la liste des colonnes redondantes (alias de combinaisons
    linéaires des précédentes) en utilisant la décomposition QR pivotée.
    """
    n, p = X.shape
    A = X.to_numpy(dtype=float)
    # SciPy QR avec pivot pour identifier les colonnes de faible norme dans R
    from scipy.linalg import qr
    Q, R, piv = qr(A, mode="economic", pivoting=True)
    diag = np.abs(np.diag(R))
    rank = int(np.sum(diag > tol * diag.max()))
    # Les colonnes "indépendantes" sont piv[:rank], les autres piv[rank:]
    dropped_idx = piv[rank:]
    return [X.columns[i] for i in dropped_idx]


aliased = drop_aliased_cols(X)
if aliased:
    print(f"\n⚠ Colonnes redondantes détectées (rank-deficiency) : {aliased}")
    print("  → exclues du modèle linéaire (équivalent R lm() qui produit NA).")
X_full = X.drop(columns=aliased)

# ============================================================
# 2. Régression complète (OLS) sur le sous-ensemble indépendant
# ============================================================
X_const = sm.add_constant(X_full)
fit_full = sm.OLS(y, X_const).fit()
print(f"\n=== Régression complète (y = co2_trend résid) ===")
sumcap = fit_full.summary().as_text()
print(sumcap)
r2_full = fit_full.rsquared

# ============================================================
# 3. Sélection AIC stepwise (backward) — sur le X "propre"
# ============================================================
def aic_ols(model: sm.regression.linear_model.RegressionResults) -> float:
    return float(model.aic)


def step_backward(X: pd.DataFrame, y: np.ndarray) -> sm.regression.linear_model.RegressionResults:
    """Élimination backward basée sur AIC (équivalent step(direction='backward'))."""
    cols = list(X.columns)
    cur = sm.OLS(y, sm.add_constant(X[cols])).fit()
    cur_aic = aic_ols(cur)
    while len(cols) > 1:
        candidates = []
        for c in cols:
            sub = [x for x in cols if x != c]
            f = sm.OLS(y, sm.add_constant(X[sub])).fit()
            candidates.append((aic_ols(f), c, f))
        candidates.sort(key=lambda t: t[0])
        best_aic, drop_c, best_fit = candidates[0]
        if best_aic >= cur_aic:
            break
        cur, cur_aic = best_fit, best_aic
        cols.remove(drop_c)
    return cur


fit_step = step_backward(X_full, y)
sumstep = fit_step.summary().as_text()
print("\n=== Modèle stepwise AIC (backward) ===")
print(sumstep)
kept = [c for c in fit_step.params.index if c != "const"]
print(f"\nVariables retenues : {', '.join(kept)}")

# ============================================================
# 4. Lasso (sklearn) avec CV 10 plis
# ============================================================
scaler = StandardScaler()
Xs = scaler.fit_transform(X.values)
np.random.seed(42)
# sklearn ≥1.7 préfère `alphas=<int>` au lieu de `n_alphas=<int>` (déprécié)
cv = LassoCV(cv=10, alphas=200, max_iter=20000, random_state=42)
cv.fit(Xs, y)
lambda_min = cv.alpha_
lasso_min = Lasso(alpha=lambda_min, max_iter=50000).fit(Xs, y)

# Coefs en échelle "standardisée" (sd-basé) pour interprétation comparable
beta_min = lasso_min.coef_  # déjà sur Xs
sd_X = X.std(ddof=0).values   # sd_X dans l'échelle d'origine
nonzero = {clim_vars[i]: beta_min[i] for i in range(len(clim_vars)) if beta_min[i] != 0}
print(f"\n=== Lasso (lambda.min = {lambda_min:.4f}) ===")
print(f"Variables retenues  : {len(nonzero)} / {len(clim_vars)}")
print("\nCoefficients non nuls (standardisés, ppm / sd) :")
for k, v in sorted(nonzero.items(), key=lambda kv: -kv[1]):
    print(f"  {k:8s}  {v:+.4f}")

# Path lasso (parcours du grille de alphas par défaut de sklearn)
alphas = np.logspace(np.log10(cv.alphas_.min()), np.log10(cv.alphas_.max()), 100)
betas = np.zeros((len(alphas), len(clim_vars)))
for i, a in enumerate(alphas):
    m = Lasso(alpha=a, max_iter=50000).fit(Xs, y)
    betas[i] = m.coef_

path_df_rows = []
for j, v in enumerate(clim_vars):
    for i, a in enumerate(alphas):
        path_df_rows.append({"var": v, "lambda": a,
                             "log_lambda": float(np.log(a)),
                             "coef": float(betas[i, j])})
path_df = pd.DataFrame(path_df_rows)
path_df.to_csv(OUT / "lasso_path.csv", index=False)

# Plot path
fig, ax = plt.subplots(figsize=(12, 7))
keep = [v for v in clim_vars if np.max(np.abs(betas[:, clim_vars.index(v)])) > 0.05]
import seaborn as sns
palette = sns.color_palette("tab20", len(keep))
for i, v in enumerate(keep):
    j = clim_vars.index(v)
    ax.plot(np.log(alphas), betas[:, j], label=v, color=palette[i], lw=0.8)
ax.axvline(np.log(lambda_min), ls="--", color="darkred", lw=0.8)
ax.axhline(0, color="grey", lw=0.4)
ax.invert_xaxis()
ax.set_xlabel("log(lambda)  (gauche = sélection forte ; droite = peu de pénalisation)")
ax.set_ylabel("Coefficient standardisé (ppm / sd)")
ax.set_title("Chemin de régularisation Lasso (coefficients standardisés)\n"
             f"Ligne rouge : log(lambda.min) = {np.log(lambda_min):.3f} (lambda.min = {lambda_min:.4f})")
ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), ncol=1, fontsize=8)
plots.save(fig, PLOT / "07a_lasso_path.png", w=12, h=7, dpi=130)

# ============================================================
# 5. Diagnostic stepwise : observed/predicted + résidus
# ============================================================
fitted = fit_step.fittedvalues
resid = fit_step.resid
fig, ax = plt.subplots(figsize=(11, 6))
ax.plot(ds["resid"]["date"], y,      color="steelblue", lw=0.6, label="Observé")
ax.plot(ds["resid"]["date"], fitted, color="tomato",    lw=0.6, label="Prédit")
ax.legend(); ax.set_ylabel("ppm")
ax.set_title(f"Modèle stepwise — R² = {fit_step.rsquared:.3f}\n"
             f"y = co2_trend résiduel (anomalie désaisonnée et détendrée)")
plots.save(fig, PLOT / "07b_stepwise_fit.png", w=11, h=6, dpi=130)

fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(ds["resid"]["date"], resid, color="darkred", lw=0.5)
ax.axhline(0, ls="--", color="black", lw=0.5)
ax.set_ylabel("ppm")
ax.set_title("Résidus du modèle stepwise\nDoit ressembler à un bruit blanc")
plots.save(fig, PLOT / "07c_stepwise_residuals.png", w=11, h=5, dpi=130)

# Résumé texte
with open(OUT / "regression_summary.txt", "w") as fh:
    fh.write("=== Régression complète ===\n\n")
    fh.write(sumcap + "\n\n=== Modèle stepwise AIC (backward) ===\n\n")
    fh.write(sumstep + "\n\n=== Lasso (lambda.min) — coefs non nuls ===\n")
    for k, v in sorted(nonzero.items(), key=lambda kv: -kv[1]):
        fh.write(f"  {k:8s}  {v:+.4f}\n")

print("\n=== Sauvegardes ===")
print(" - regression_summary.txt")
print(" - lasso_path.csv")
print(" - plots/07a_lasso_path.png, 07b_stepwise_fit.png, 07c_stepwise_residuals.png")
print(f"\nR² complet  = {r2_full:.3f}   |   R² stepwise = {fit_step.rsquared:.3f}")
