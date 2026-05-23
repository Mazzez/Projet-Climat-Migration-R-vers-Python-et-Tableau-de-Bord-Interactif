"""Phase 3 — 04 — Cartes pixel-par-pixel de la pente Sen + Mann-Kendall
sur sous-échantillon, pour les 18 variables (résolution 0.5°).

Migration de 04_trend_maps.R. La régression linéaire vectorisée
remplace Sen pour rester rapide ; MK est calculé sur un sous-échantillon
(1 pixel sur 16) pour la p-value.
"""
from __future__ import annotations
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import pymannkendall as pmk
from tqdm import tqdm

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

dates = pd.DatetimeIndex([io.date_from_filename(f) for f in files])
months = dates.month.to_numpy()
years = dates.year.to_numpy()
t_yrs = ((dates - dates[0]).days / 365.25).to_numpy(dtype=float)


def load_cube(nc_var: str) -> np.ndarray:
    """Charge un cube (nx, ny, nt) en mémoire."""
    cube = np.full((nx, ny, nt), np.nan, dtype=np.float32)
    for i, f in enumerate(files):
        with io.open_month(f) as ds:
            if nc_var in ds.data_vars:
                arr = np.squeeze(ds[nc_var].values)
                if arr.shape == (ny, nx):
                    arr = arr.T
                if arr.shape == (nx, ny):
                    cube[:, :, i] = arr
    return cube


def trend_grid(cube: np.ndarray) -> np.ndarray:
    """Pente locale (per year) de la régression linéaire des anomalies
    désaisonnées vs t_yrs. Vectorisé sur les pixels."""
    # Climatologie mensuelle pixel par pixel : (nx, ny, 12)
    clim = np.full((nx, ny, 12), np.nan, dtype=np.float32)
    for m in range(1, 13):
        idx = np.where(months == m)[0]
        clim[:, :, m - 1] = np.nanmean(cube[:, :, idx], axis=2)
    # Anomalies (nx, ny, nt) — broadcasting
    anom = cube - clim[:, :, months - 1]
    # Régression : slope = sum((y - y_mean) * (t - t_mean)) / sum((t - t_mean)^2)
    t_centered = t_yrs - t_yrs.mean()
    var_t = float(np.sum(t_centered ** 2))
    anom_mean = np.nanmean(anom, axis=2, keepdims=True)
    cov = np.nansum((anom - anom_mean) * t_centered[None, None, :], axis=2)
    slope = cov / var_t   # unité / an
    return slope


def mk_subsample(cube: np.ndarray, step: int = 4) -> np.ndarray:
    """Mann-Kendall sur 1 pixel sur step². Renvoie une grille NaN-padded
    avec la p-value MK."""
    pval = np.full((nx, ny), np.nan, dtype=np.float32)
    ix = np.arange(0, nx, step)
    iy = np.arange(0, ny, step)
    n_total = len(ix) * len(iy)
    for i in tqdm(ix, desc="MK", leave=False):
        for j in iy:
            v = cube[i, j, :]
            if np.sum(~np.isnan(v)) > 100:
                try:
                    pval[i, j] = pmk.original_test(v).p
                except Exception:
                    pass
    return pval


def plot_map(grid: np.ndarray, title: str, subtitle: str, unit: str,
             out_path: Path) -> None:
    df = pd.DataFrame({"lon": np.repeat(lon, ny),
                       "lat": np.tile(lat, nx),
                       "value": grid.flatten()})
    lim = float(np.nanquantile(np.abs(df["value"]), 0.99))
    fig, ax = plt.subplots(figsize=(11, 5.5))
    sc = ax.pcolormesh(lon, lat, grid.T, cmap="RdBu_r", shading="auto",
                       vmin=-lim, vmax=lim)
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude (°)"); ax.set_ylabel("Latitude (°)")
    fig.colorbar(sc, ax=ax, label=unit)
    ax.set_title(f"{title}\n{subtitle}")
    plots.save(fig, out_path, w=11, h=5.5, dpi=130)


# Boucle principale
trend_results = {}
t0 = time.time()
for nc_var, short in config.VAR_MAP_05.items():
    print(f"\n[{short}] chargement du cube...")
    cube = load_cube(nc_var)
    print(f"[{short}] tendance pixel par pixel...")
    slope = trend_grid(cube)
    print(f"[{short}] p-value Mann-Kendall (sous-échantillon 1/16)...")
    pval = mk_subsample(cube, step=4)
    trend_results[short] = {"slope": slope, "pval": pval}

    pic_99 = float(np.nanquantile(slope, 0.995) - np.nanquantile(slope, 0.005))
    plot_map(slope,
             title=f"{short} — pente locale (régression sur anomalies)",
             subtitle=f"Unité / an, sur 1979-2025 ; Δ pic-vallée à 99 % : {pic_99:.4g}",
             unit="/an",
             out_path=MAPS / f"04_trend_{short}.png")
    del cube

print(f"\nDurée totale : {time.time() - t0:.1f} s")

# Sauvegarde pickle (analogue rds)
with open(OUT / "trend_grids.pkl", "wb") as fh:
    pickle.dump(trend_results, fh)

print(f"\n=== 18 cartes de tendance sauvegardées dans : {MAPS} ===")
