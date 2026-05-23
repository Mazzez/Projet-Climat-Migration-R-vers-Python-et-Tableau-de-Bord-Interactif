"""Phase 2 — 02 — Moyennes globales pondérées cos(lat) des 18 variables
(résolution 2.5° × 2.5°), 1979-01 → 2025-12.

Migration de 02_global_means.R.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, io                                              # noqa: E402
from climat.preprocess import cos_lat_weights, weighted_mean_2d             # noqa: E402

NC_BASE = config.NC_25
OUT_FILE = config.OUT_PHASE2 / "monthly_global_means_25.csv"

config.ensure_dirs()

files = io.list_nc_files(NC_BASE)
print(f"Fichiers NetCDF trouvés : {len(files)}")
if not files:
    raise SystemExit(f"Aucun .nc sous {NC_BASE}")

# Grille (constante sur tous les mois) + poids
lon, lat = io.get_grid(NC_BASE)
nx, ny = len(lon), len(lat)
print(f"Grille : {nx} x {ny}   lat range = {lat.min()} à {lat.max()}")
w_lat = cos_lat_weights(lat)
print(f"Somme des poids : {round(nx * w_lat.sum(), 4)}  (= {nx} * sum(cos(lat)))\n")


def field2d(ds: xr.Dataset, name: str) -> np.ndarray:
    """Récupère un champ 2D (nlon, nlat) en gérant les dim time/plevel résiduelles."""
    arr = ds[name].values
    arr = np.squeeze(arr)
    # Convention dims dans les NetCDF wgrib2 : (latitude, longitude). On
    # transpose pour avoir (nlon, nlat) attendu par weighted_mean_2d.
    if arr.shape == (ny, nx):
        arr = arr.T
    if np.issubdtype(arr.dtype, np.floating):
        arr = np.where(np.isnan(arr), np.nan, arr)
    else:
        arr = arr.astype(float)
    return arr


t0 = time.time()
rows: list[dict] = []
for i, f in enumerate(tqdm(files, desc="months")):
    date = io.date_from_filename(f)
    row = {"year": date.year, "month": date.month, "date": date.strftime("%Y-%m-%d")}
    with io.open_month(f) as ds:
        for nc_name, short in config.VAR_MAP_25.items():
            if nc_name in ds.data_vars:
                arr = field2d(ds, nc_name)
                row[short] = weighted_mean_2d(arr, w_lat)
            else:
                row[short] = np.nan
                tqdm.write(f"  {date.strftime('%Y%m')} : variable manquante {nc_name}")
    rows.append(row)

print(f"\nDurée totale : {time.time() - t0:.1f} s")

df = pd.DataFrame(rows)
df = df.sort_values("date").reset_index(drop=True)
print(f"Dimensions du tableau final : {df.shape}")
print(f"Plage temporelle : {df['date'].min()} -> {df['date'].max()}")
print("\nNombre de NA par variable :")
print(df.drop(columns=["year", "month", "date"]).isna().sum())

print("\nAperçu (3 premières lignes) :")
print(df.head(3))
print("\nAperçu (3 dernières lignes) :")
print(df.tail(3))

df.to_csv(OUT_FILE, index=False)
print(f"\n=== CSV sauvegardé : {OUT_FILE} ===")
