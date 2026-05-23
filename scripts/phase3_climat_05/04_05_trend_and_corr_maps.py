"""Phase 3 — 04 + 05 (combiné) — Cartes pixel-par-pixel pour les 18
variables, en chargant chaque cube UNE seule fois :
  * pente locale (régression sur anomalies désaisonnées) → 04_trend_<VAR>.png
  * Mann-Kendall p-value sur sous-échantillon
  * corrélation pixel-par-pixel avec CO2 résiduel  → 05_corr_<VAR>.png

Cette version remplace la pair 04_trend_maps.py + 05_correlation_maps.py
fidèles au R d'origine, en évitant de re-lire les 4 Go de NetCDF deux fois.

Sauvegarde aussi : trend_grids.pkl + correlation_grids.pkl
"""
from __future__ import annotations
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pymannkendall as pmk

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, io, plots                                        # noqa: E402

NC_BASE = config.NC_05
OUT = config.OUT_PHASE3
MAPS = OUT / "maps"
MAPS.mkdir(parents=True, exist_ok=True)
plots.setup_theme()

files = io.list_nc_files(NC_BASE)
print(f"Fichiers NetCDF : {len(files)}")
lon, lat = io.get_grid(NC_BASE)
nx, ny, nt = len(lon), len(lat), len(files)
print(f"Grille : {nx} × {ny} × {nt} = {nx*ny*nt:,} pixels-mois")

dates = pd.DatetimeIndex([io.date_from_filename(f) for f in files])
months = dates.month.to_numpy()
t_yrs = ((dates - dates[0]).days / 365.25).to_numpy(dtype=float)

# ---- CO2 résidus (pour les corrélations)
co2 = io.load_co2_global()[["date", "trend"]].rename(columns={"trend": "co2_trend"})
co2_aligned = co2.set_index("date").reindex(dates)["co2_trend"].to_numpy(dtype=float)
co2_clim = pd.Series(co2_aligned).groupby(months).transform("mean").to_numpy()
co2_anom = co2_aligned - co2_clim
ok_co2 = ~np.isnan(co2_anom)
p_co2 = np.polyfit(t_yrs[ok_co2], co2_anom[ok_co2], 1)
co2_resid = co2_anom - np.polyval(p_co2, t_yrs)
print(f"CO2 aligné : {ok_co2.sum()} / {nt} valeurs non-NA")


def load_cube(nc_var: str) -> np.ndarray:
    """Cube (nx, ny, nt) en float32 ; lecture efficace via xarray."""
    cube = np.full((nx, ny, nt), np.nan, dtype=np.float32)
    for i, f in enumerate(files):
        with io.open_month(f) as ds:
            if nc_var in ds.data_vars:
                arr = np.squeeze(ds[nc_var].values).astype(np.float32)
                if arr.shape == (ny, nx):
                    arr = arr.T
                if arr.shape == (nx, ny):
                    cube[:, :, i] = arr
    return cube


def trend_and_resid(cube: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Renvoie (slope per year, resid_cube) en une passe.

    Méthode vectorisée : désaisonnage par climato mensuelle pixel,
    puis pente OLS = sum((y-y_mean)*(t-t_mean)) / sum((t-t_mean)^2).
    Le résidu est anom - (anom_mean + slope * t_centered).
    """
    clim = np.full((nx, ny, 12), np.nan, dtype=np.float32)
    for m in range(1, 13):
        idx = np.where(months == m)[0]
        clim[:, :, m - 1] = np.nanmean(cube[:, :, idx], axis=2)
    anom = cube - clim[:, :, months - 1]
    t_centered = (t_yrs - t_yrs.mean()).astype(np.float32)
    var_t = float(np.sum(t_centered ** 2))
    anom_mean = np.nanmean(anom, axis=2, keepdims=True)
    cov = np.nansum((anom - anom_mean) * t_centered[None, None, :], axis=2)
    slope = cov / var_t
    resid = anom - anom_mean - slope[:, :, None] * t_centered[None, None, :]
    return slope, resid


def corr_with_co2(resid_cube: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Corrélation Pearson pixel-par-pixel avec un vecteur 1D y."""
    ok = ~np.isnan(y)
    yc = (y[ok] - y[ok].mean()).astype(np.float32)
    sub = resid_cube[:, :, ok]
    n_ok = len(yc)
    y_var = float(np.sum(yc ** 2) / (n_ok - 1))
    x_mean = np.nanmean(sub, axis=2, keepdims=True)
    x_var = np.nanvar(sub, axis=2, ddof=1)
    cov_xy = np.nansum((sub - x_mean) * yc[None, None, :], axis=2) / (n_ok - 1)
    return cov_xy / np.sqrt(x_var * y_var)


def mk_subsample(cube: np.ndarray, step: int = 4) -> np.ndarray:
    """Mann-Kendall sur 1 pixel sur step² (rapide)."""
    pval = np.full((nx, ny), np.nan, dtype=np.float32)
    ix = np.arange(0, nx, step)
    iy = np.arange(0, ny, step)
    for i in ix:
        for j in iy:
            v = cube[i, j, :]
            if np.sum(~np.isnan(v)) > 100:
                try:
                    pval[i, j] = pmk.original_test(v).p
                except Exception:
                    pass
    return pval


def plot_trend(grid: np.ndarray, var: str, out_path: Path) -> None:
    lim = float(np.nanquantile(np.abs(grid), 0.99))
    pic_99 = float(np.nanquantile(grid, 0.995) - np.nanquantile(grid, 0.005))
    fig, ax = plt.subplots(figsize=(11, 5.5))
    sc = ax.pcolormesh(lon, lat, grid.T, cmap="RdBu_r", shading="auto",
                       vmin=-lim, vmax=lim)
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude (°)"); ax.set_ylabel("Latitude (°)")
    fig.colorbar(sc, ax=ax, label="/ an")
    ax.set_title(f"{var} — pente locale (régression sur anomalies)\n"
                 f"Unité / an, sur 1979-2025 ; Δ pic-vallée à 99 % : {pic_99:.4g}")
    plots.save(fig, out_path, w=11, h=5.5, dpi=130)


def plot_corr(grid: np.ndarray, var: str, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 5.5))
    sc = ax.pcolormesh(lon, lat, grid.T, cmap="RdBu_r", shading="auto",
                       vmin=-1, vmax=1)
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude (°)"); ax.set_ylabel("Latitude (°)")
    fig.colorbar(sc, ax=ax, label="r")
    ax.set_title(f"Corrélation locale {var} ↔ CO2_trend (résidus)\n"
                 "Anomalies désaisonnées et détendrées 1979-2025 (signal interannuel propre)")
    plots.save(fig, out_path, w=11, h=5.5, dpi=130)


# ============================================================
# Boucle principale — UNE seule lecture du cube par variable
# ============================================================
trend_results: dict[str, dict] = {}
corr_results: dict[str, np.ndarray] = {}
already_done = []

t0 = time.time()
for k, (nc_var, short) in enumerate(config.VAR_MAP_05.items(), 1):
    trend_path = MAPS / f"04_trend_{short}.png"
    corr_path  = MAPS / f"05_corr_{short}.png"
    if trend_path.exists() and corr_path.exists():
        already_done.append(short)
        print(f"[{k:2d}/{len(config.VAR_MAP_05)}] {short:7s}  déjà calculé — skip")
        continue
    elapsed = time.time() - t0
    eta = elapsed * (len(config.VAR_MAP_05) - k + 1) / max(k - len(already_done), 1)
    print(f"[{k:2d}/{len(config.VAR_MAP_05)}] {short:7s}  load cube...   "
          f"  elapsed={elapsed:.0f}s  eta≈{eta:.0f}s", flush=True)
    cube = load_cube(nc_var)
    slope, resid = trend_and_resid(cube)
    pval = mk_subsample(cube, step=4)
    r_grid = corr_with_co2(resid, co2_resid)
    trend_results[short] = {"slope": slope, "pval": pval}
    corr_results[short] = r_grid
    plot_trend(slope, short, trend_path)
    plot_corr(r_grid, short, corr_path)
    del cube, resid, slope, r_grid, pval

print(f"\nDurée totale : {time.time() - t0:.1f} s")

if trend_results:
    # On ne sauve les pickles que si on a refait au moins une variable
    if len(already_done) < len(config.VAR_MAP_05):
        with open(OUT / "trend_grids.pkl", "wb") as fh:
            pickle.dump(trend_results, fh)
        with open(OUT / "correlation_grids.pkl", "wb") as fh:
            pickle.dump(corr_results, fh)
        print("Pickles sauvegardés (trend_grids.pkl, correlation_grids.pkl)")

print(f"\n=== Cartes sauvegardées dans : {MAPS} ===")
print(f"   trend : 04_trend_<VAR>.png  ({len(already_done) + len(trend_results)} variables)")
print(f"   corr  : 05_corr_<VAR>.png   ({len(already_done) + len(corr_results)} variables)")
