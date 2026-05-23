"""Transformations standard : climatologie, anomalies, résidus, diff lag."""
from __future__ import annotations
import numpy as np
import pandas as pd


def monthly_climatology(values: np.ndarray, months: np.ndarray) -> np.ndarray:
    """Renvoie un vecteur de la même taille où chaque entrée est la moyenne
    de `values` sur tous les mois identiques."""
    s = pd.Series(values).groupby(months).transform("mean").to_numpy()
    return s


def deseasonalize(values: np.ndarray, months: np.ndarray) -> np.ndarray:
    """Anomalie = valeur - climatologie mensuelle."""
    return values - monthly_climatology(values, months)


def detrend_linear(y: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Retire la régression linéaire de y vs t. Préserve les NaN."""
    ok = ~np.isnan(y) & ~np.isnan(t)
    if ok.sum() < 2:
        return y.copy()
    # OLS pente/ordonnée à l'origine via polyfit
    p = np.polyfit(t[ok], y[ok], 1)
    fitted = np.polyval(p, t)
    return y - fitted


def build_residuals(values: np.ndarray, dates: pd.DatetimeIndex) -> np.ndarray:
    """Pipeline complet : (1) désaisonnement par climato mensuelle,
    (2) détendrage linéaire vs t (en jours depuis la 1ère date)."""
    months = np.asarray(dates.month)
    anom = deseasonalize(np.asarray(values, dtype=float), months)
    t = (dates - dates[0]).days.to_numpy(dtype=float)
    return detrend_linear(anom, t)


def diff_lag(values: np.ndarray, lag: int = 1) -> np.ndarray:
    """X_t - X_{t-lag} avec NaN sur les `lag` premiers points."""
    out = np.full_like(np.asarray(values, dtype=float), np.nan)
    out[lag:] = np.asarray(values, dtype=float)[lag:] - np.asarray(values, dtype=float)[:-lag]
    return out


def cos_lat_weights(lat: np.ndarray) -> np.ndarray:
    """Vecteur 1D des poids cos(lat) (lat en degrés)."""
    return np.cos(np.deg2rad(lat))


def weighted_mean_2d(arr: np.ndarray, w_lat: np.ndarray,
                     mask: np.ndarray | None = None) -> float:
    """Moyenne pondérée d'un champ 2D (nlon, nlat) par cos(lat).

    `mask` (booléen, même shape) restreint la zone si fourni.
    """
    nlon, nlat = arr.shape
    # Matrice de poids (nlon, nlat) : un cos(lat[j]) répété sur chaque lon
    w_grid = np.broadcast_to(w_lat[None, :], (nlon, nlat))
    valid = ~np.isnan(arr)
    if mask is not None:
        valid = valid & mask
    w_eff = w_grid * valid
    s = np.sum(arr * w_eff)
    n = np.sum(w_eff)
    return float(s / n) if n > 0 else float("nan")


def add_cre(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute CRE_SW, CRE_LW, CRE_net à un DataFrame contenant les flux radiatifs.

    CRE = (all-sky net) - (clear-sky net), à la surface :
        CRE_SW  = (DSWRF - USWRF) - (CSDSF - CSUSF)
        CRE_LW  = (DLWRF - ULWRF) - (CSDLF - CSULF)
        CRE_net = CRE_SW + CRE_LW
    """
    out = df.copy()
    out["CRE_SW"] = (out["DSWRF"] - out["USWRF"]) - (out["CSDSF"] - out["CSUSF"])
    out["CRE_LW"] = (out["DLWRF"] - out["ULWRF"]) - (out["CSDLF"] - out["CSULF"])
    out["CRE_net"] = out["CRE_SW"] + out["CRE_LW"]
    return out
