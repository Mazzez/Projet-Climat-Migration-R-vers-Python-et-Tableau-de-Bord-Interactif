"""Stats : pente de Sen, Mann-Kendall, bootstrap, Granger, lag-corr."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
import pymannkendall as pmk
from statsmodels.tsa.stattools import grangercausalitytests


@dataclass
class TrendResult:
    sen_per_step: float        # pente Sen par pas (souvent par mois)
    sen_per_year: float        # pente Sen × 12
    mk_tau: float
    mk_p: float
    sen_lo95: float | None = None
    sen_hi95: float | None = None


def sens_slope_and_mk(x: np.ndarray) -> TrendResult:
    """Pente de Sen + statistique Mann-Kendall (basée sur pymannkendall)."""
    x = np.asarray(x, dtype=float)
    res = pmk.original_test(x)
    return TrendResult(
        sen_per_step=float(res.slope),
        sen_per_year=float(res.slope) * 12.0,
        mk_tau=float(res.Tau),
        mk_p=float(res.p),
    )


def bootstrap_sen(x: np.ndarray, n_boot: int = 500,
                  seed: int = 42) -> tuple[float, float, float]:
    """Bootstrap par ré-échantillonnage avec replacement de Sen.

    On garde l'ordre temporel sur le sous-échantillon (sort des indices
    tirés) pour rester cohérent avec le R `boot_sen` du projet.
    Retourne (sen_per_year, lo95_per_year, hi95_per_year) avec IC
    percentile.
    """
    x = np.asarray(x, dtype=float)
    rng = np.random.default_rng(seed)
    n = len(x)
    estimates = np.empty(n_boot)
    for i in range(n_boot):
        idx = np.sort(rng.integers(0, n, size=n))
        estimates[i] = pmk.original_test(x[idx]).slope
    # Sen sur la série originale × 12 = pente annuelle
    sen0 = pmk.original_test(x).slope * 12.0
    lo, hi = np.quantile(estimates * 12.0, [0.025, 0.975])
    return sen0, float(lo), float(hi)


def lag_correlation(x: np.ndarray, y: np.ndarray,
                    max_lag: int = 12) -> pd.DataFrame:
    """Corrélation à différents lags.

    Convention identique au R du projet :
      * lag > 0 : x précède y de `lag` pas (cor(x[:-lag], y[lag:]))
      * lag < 0 : y précède x de |lag| pas (cor(x[|lag|:], y[:-|lag|]))
      * lag = 0 : corrélation simple
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    rows = []
    for L in range(-max_lag, max_lag + 1):
        if L > 0:
            xa = x[:-L]
            ya = y[L:]
        elif L < 0:
            xa = x[-L:]
            ya = y[:L]
        else:
            xa, ya = x, y
        ok = ~np.isnan(xa) & ~np.isnan(ya)
        if ok.sum() < 2:
            r = np.nan
        else:
            r = float(np.corrcoef(xa[ok], ya[ok])[0, 1])
        rows.append({"lag": L, "r": r})
    return pd.DataFrame(rows)


def grangertest_pvalue(y: np.ndarray, x: np.ndarray,
                       lag: int = 6) -> tuple[float, float]:
    """Reproduit la sortie de lmtest::grangertest(y ~ x, order = lag).

    Modèle restreint : y_t ~ y_{t-1..t-lag}
    Modèle complet   : y_t ~ y_{t-1..t-lag} + x_{t-1..t-lag}
    H0 : x ne cause pas y au sens de Granger.

    Retourne (F_stat, p_value) du test F sur l'ajout des lags de x.
    """
    arr = np.column_stack([
        np.asarray(y, dtype=float),
        np.asarray(x, dtype=float),
    ])
    arr = arr[~np.isnan(arr).any(axis=1)]
    if len(arr) < lag + 5:
        return float("nan"), float("nan")
    # statsmodels.grangercausalitytests teste la colonne 0 causée par la colonne 1.
    # `verbose` est déprécié depuis statsmodels 0.14 ; les versions récentes
    # ne le passent plus du tout (l'impression est désactivée par défaut quand
    # on capture la sortie). On essaie sans, puis fallback verbose=False.
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        try:
            res = grangercausalitytests(arr, maxlag=[lag])
        except TypeError:
            res = grangercausalitytests(arr, maxlag=[lag], verbose=False)
    f_stat, p_val, _, _ = res[lag][0]["ssr_ftest"]
    return float(f_stat), float(p_val)


def percentile_quantile(x: np.ndarray, q: tuple[float, float]) -> tuple[float, float]:
    return tuple(np.nanquantile(x, q))  # type: ignore[return-value]
