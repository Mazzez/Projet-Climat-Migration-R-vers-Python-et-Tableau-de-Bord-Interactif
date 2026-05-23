"""Phase 3 — 05 — Cartes pixel-par-pixel de corrélation
climat ↔ CO2_trend sur résidus (anomalies désaisonnées + détendrées).

Migration de 05_correlation_maps.R.
"""
from __future__ import annotations
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, io, plots                                        # noqa: E402

NC_BASE = config.NC_05
OUT = config.OUT_PHASE3
MAPS = OUT / "maps"
MAPS.mkdir(parents=True, exist_ok=True)
plots.setup_theme()

files = io.list_nc_files(NC_BASE)
lon, lat = io.get_grid(NC_BASE)
nx, ny, nt = len(lon), len(lat), len(files)

dates = pd.DatetimeIndex([io.date_from_filename(f) for f in files])
months = dates.month.to_numpy()
t_yrs = ((dates - dates[0]).days / 365.25).to_numpy(dtype=float)

# CO2 → résidus (désaisonné + détendré linéaire)
co2 = io.load_co2_global()[["date", "trend"]].rename(columns={"trend": "co2_trend"})
co2_aligned = co2.set_index("date").reindex(dates)["co2_trend"].to_numpy(dtype=float)
co2_clim_m = pd.Series(co2_aligned).groupby(months).transform("mean").to_numpy()
co2_anom = co2_aligned - co2_clim_m
ok_co2 = ~np.isnan(co2_anom)
p = np.polyfit(t_yrs[ok_co2], co2_anom[ok_co2], 1)
co2_resid = co2_anom - np.polyval(p, t_yrs)
print(f"CO2 aligné : {ok_co2.sum()} / {nt} valeurs non-NA\n")


def load_resid_cube(nc_var: str) -> np.ndarray:
    """Charge un cube et calcule les résidus (anomalies désaisonnées + détendrées)
    en chaque pixel — vectorisé sur les pixels."""
    cube = np.full((nx, ny, nt), np.nan, dtype=np.float32)
    for i, f in enumerate(files):
        with io.open_month(f) as ds:
            if nc_var in ds.data_vars:
                arr = np.squeeze(ds[nc_var].values)
                if arr.shape == (ny, nx):
                    arr = arr.T
                if arr.shape == (nx, ny):
                    cube[:, :, i] = arr
    # Désaisonnage par climato mensuelle pixel
    clim = np.full((nx, ny, 12), np.nan, dtype=np.float32)
    for m in range(1, 13):
        idx = np.where(months == m)[0]
        clim[:, :, m - 1] = np.nanmean(cube[:, :, idx], axis=2)
    anom = cube - clim[:, :, months - 1]
    # Détendrage linéaire pixel par pixel
    t_centered = t_yrs - t_yrs.mean()
    var_t = float(np.sum(t_centered ** 2))
    anom_mean = np.nanmean(anom, axis=2, keepdims=True)
    cov = np.nansum((anom - anom_mean) * t_centered[None, None, :], axis=2)
    slope = cov / var_t
    resid = anom - anom_mean - slope[:, :, None] * t_centered[None, None, :]
    return resid


def corr_grid(resid_cube: np.ndarray, y_resid: np.ndarray) -> np.ndarray:
    """Corrélation Pearson pixel-par-pixel entre resid_cube et y_resid (vecteur 1D)."""
    ok = ~np.isnan(y_resid)
    y = y_resid[ok]
    cube = resid_cube[:, :, ok]
    n_ok = len(y)
    yc = y - y.mean()
    y_var = float(np.sum(yc ** 2) / (n_ok - 1))
    x_mean = np.nanmean(cube, axis=2, keepdims=True)
    x_var = np.nanvar(cube, axis=2, ddof=1)
    cov_xy = np.nansum((cube - x_mean) * yc[None, None, :], axis=2) / (n_ok - 1)
    return cov_xy / np.sqrt(x_var * y_var)


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


corr_results = {}
t0 = time.time()
for nc_var, short in config.VAR_MAP_05.items():
    print(f"\n[{short}] chargement et résidus...")
    resid_cube = load_resid_cube(nc_var)
    print(f"[{short}] corrélation avec CO2 résiduel...")
    r_grid = corr_grid(resid_cube, co2_resid)
    corr_results[short] = r_grid
    print(f"[{short}] médiane |r| = {float(np.nanmedian(np.abs(r_grid))):.3f}, "
          f"max |r| = {float(np.nanmax(np.abs(r_grid))):.3f}")
    plot_corr(r_grid, short, MAPS / f"05_corr_{short}.png")
    del resid_cube

print(f"\nDurée totale : {time.time() - t0:.1f} s")
with open(OUT / "correlation_grids.pkl", "wb") as fh:
    pickle.dump(corr_results, fh)
print(f"\n=== 18 cartes de corrélation sauvegardées dans : {MAPS} ===")
