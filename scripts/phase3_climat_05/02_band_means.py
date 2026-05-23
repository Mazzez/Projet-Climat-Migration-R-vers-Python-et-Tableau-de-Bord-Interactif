"""Phase 3 — 02 — Moyennes pondérées cos(lat) des 18 variables par bande
de latitude (5 bandes + global), résolution 0.5°.

Migration de 02_band_means.R.
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
from climat.preprocess import cos_lat_weights, weighted_mean_2d            # noqa: E402

NC_BASE = config.NC_05
OUT_FILE = config.OUT_PHASE3 / "monthly_band_means_05.csv"
config.ensure_dirs()

files = io.list_nc_files(NC_BASE)
print(f"Fichiers NetCDF trouvés : {len(files)}")
if not files:
    raise SystemExit(f"Aucun .nc sous {NC_BASE}")

lon, lat = io.get_grid(NC_BASE)
nx, ny = len(lon), len(lat)
print(f"Grille : {nx} x {ny}")
print(f"lat range : {lat.min()} à {lat.max()}\n")

w_lat = cos_lat_weights(lat)

# Masques (booléen 1D sur lat) — intervalles non-chevauchants
band_masks_lat = {b: pred(lat) for b, pred in config.BAND_PREDICATES.items()}

# Vérification : les 5 bandes zonales partitionnent exactement les 361 lignes
zone_masks = {b: m for b, m in band_masks_lat.items() if b != "global"}
n_membership = sum(m.astype(int) for m in zone_masks.values())
assert (n_membership == 1).all(), \
    f"Les bandes ne forment pas une partition de lat (n_membership = {np.unique(n_membership)})"

print("Cellules par bande :")
total = nx * ny
for b, m in band_masks_lat.items():
    n_cells = nx * int(m.sum())
    print(f"  {b:12s} : {n_cells} cellules ({100 * n_cells / total:.1f} %)")


def field2d(ds: xr.Dataset, name: str) -> np.ndarray:
    arr = np.squeeze(ds[name].values)
    if arr.shape == (ny, nx):
        arr = arr.T
    if not np.issubdtype(arr.dtype, np.floating):
        arr = arr.astype(float)
    return arr


t0 = time.time()
rows = []
for f in tqdm(files, desc="months"):
    date = io.date_from_filename(f)
    with io.open_month(f) as ds:
        for b, mask_lat in band_masks_lat.items():
            row = {"year": date.year, "month": date.month,
                   "date": date.strftime("%Y-%m-%d"), "band": b}
            mask_2d = np.broadcast_to(mask_lat[None, :], (nx, ny))
            for nc_name, short in config.VAR_MAP_05.items():
                if nc_name in ds.data_vars:
                    arr = field2d(ds, nc_name)
                    if arr.shape != (nx, ny):
                        row[short] = np.nan; continue
                    row[short] = weighted_mean_2d(arr, w_lat, mask=mask_2d)
                else:
                    row[short] = np.nan
            rows.append(row)

print(f"\nDurée totale : {time.time() - t0:.1f} s")

df = pd.DataFrame(rows).sort_values(["date", "band"]).reset_index(drop=True)
print(f"Dimensions du tableau final : {df.shape}")
print(f"Plage temporelle : {df['date'].min()} -> {df['date'].max()}")

print("\nNA par variable :")
print(df[config.CLIM_VARS].isna().sum())

print("\nAperçu (6 premières lignes - une par bande) :")
print(df.head(6))

df.to_csv(OUT_FILE, index=False)
print(f"\n=== CSV sauvegardé : {OUT_FILE} ===")
