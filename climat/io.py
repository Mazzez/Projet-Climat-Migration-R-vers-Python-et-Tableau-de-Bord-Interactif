"""Lecteurs de données : CO2 NOAA, CSV climat, fichiers NetCDF."""
from __future__ import annotations
from pathlib import Path
import re
import numpy as np
import pandas as pd
import xarray as xr

from .config import DATA_CO2


# ============================================================
# CO2 NOAA / Mauna Loa / GCB / Vostok / ENSO
# ============================================================
def load_co2_global() -> pd.DataFrame:
    """co2_mm_gl.csv (NOAA GML) → DataFrame avec date, year, month, decimal,
    average, trend, decade."""
    path = DATA_CO2 / "co2_mm_gl.csv"
    df = pd.read_csv(path, comment="#")
    df["date"] = pd.to_datetime(
        dict(year=df["year"], month=df["month"], day=1)
    )
    df = df.sort_values("date").reset_index(drop=True)
    df["decade"] = (df["year"] // 10 * 10).astype(int).astype(str) + "s"
    return df


def load_co2_mauna_loa() -> pd.DataFrame:
    """co2_mm_mlo.csv (NOAA / SIO Mauna Loa). Colonnes : year, month, decimal,
    mlo_avg, mlo_deseason, ndays, sdev, unc."""
    path = DATA_CO2 / "co2_mm_mlo.csv"
    # Le fichier a des # de commentaires puis une ligne d'en-tête CSV.
    df = pd.read_csv(path, comment="#")
    df.columns = ["year", "month", "decimal", "mlo_avg", "mlo_deseason",
                  "ndays", "sdev", "unc"]
    df["date"] = pd.to_datetime(
        dict(year=df["year"], month=df["month"], day=1)
    )
    df.loc[df["mlo_avg"] < 0, "mlo_avg"] = np.nan
    df.loc[df["mlo_deseason"] < 0, "mlo_deseason"] = np.nan
    return df.sort_values("date").reset_index(drop=True)


def load_co2_south_pole() -> pd.DataFrame:
    """co2_spo_surface-flask_1_ccgg_month.txt → date, spo_avg."""
    path = DATA_CO2 / "co2_spo_surface-flask_1_ccgg_month.txt"
    rows = []
    with open(path, "r") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            try:
                site = parts[0]
                year = int(parts[1])
                month = int(parts[2])
                spo = float(parts[3])
            except (ValueError, IndexError):
                continue
            rows.append((site, year, month, spo))
    df = pd.DataFrame(rows, columns=["site", "year", "month", "spo_avg"])
    df["date"] = pd.to_datetime(
        dict(year=df["year"], month=df["month"], day=1)
    )
    return df.sort_values("date").reset_index(drop=True)


def load_gcb() -> pd.DataFrame:
    """Global Carbon Budget — émissions globales par source (1750→2024).
    Filtre Country == Global, retourne year + total_MtCO2 + sources."""
    path = DATA_CO2 / "GCB2025v15_MtCO2_flat.csv"
    df = pd.read_csv(path)
    df = df[df["Country"] == "Global"].dropna(subset=["Total"]).copy()
    return df.rename(columns={
        "Year": "year",
        "Total": "total_MtCO2",
        "Coal": "coal", "Oil": "oil", "Gas": "gas",
        "Cement": "cement", "Flaring": "flaring", "Other": "other",
    })[["year", "total_MtCO2", "coal", "oil", "gas",
        "cement", "flaring", "other"]].reset_index(drop=True)


def load_vostok() -> pd.DataFrame:
    """co2nat-noaa.txt — paléoclimat Vostok. Colonnes gas_ageBP, CO2."""
    path = DATA_CO2 / "co2nat-noaa.txt"
    rows = []
    with open(path, "r") as fh:
        for line in fh:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            parts = s.split()
            if len(parts) < 2:
                continue
            try:
                age = float(parts[0])
                co2 = float(parts[1])
                rows.append((age, co2))
            except ValueError:
                continue
    df = pd.DataFrame(rows, columns=["gas_ageBP", "CO2"])
    df = df.dropna()
    df["year_AD"] = 1950 - df["gas_ageBP"]
    return df.sort_values("gas_ageBP").reset_index(drop=True)


def load_oni() -> pd.DataFrame:
    """oni.ascii.txt — indice ENSO Niño 3.4. Colonnes year, month (1-12), oni."""
    path = DATA_CO2 / "oni.ascii.txt"
    df = pd.read_csv(path, sep=r"\s+")
    seas_to_month = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5,
                     "MJJ": 6, "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10,
                     "OND": 11, "NDJ": 12}
    df["month"] = df["SEAS"].map(seas_to_month)
    df = df.rename(columns={"YR": "year", "ANOM": "oni"})
    return df[["year", "month", "oni"]].copy()


# ============================================================
# NetCDF / xarray
# ============================================================
_YYYYMM_RE = re.compile(r"(\d{6})\.nc$")


def list_nc_files(nc_base: Path) -> list[Path]:
    """Liste triée des fichiers NetCDF YYYYMM.nc sous nc_base/YYYY/."""
    return sorted(nc_base.rglob("*.nc"))


def date_from_filename(path: Path) -> pd.Timestamp:
    """Extrait la date YYYY-MM-01 du nom de fichier YYYYMM.nc."""
    m = _YYYYMM_RE.search(path.name)
    if not m:
        raise ValueError(f"Nom de fichier inattendu : {path.name}")
    yyyymm = m.group(1)
    return pd.Timestamp(year=int(yyyymm[:4]), month=int(yyyymm[4:6]), day=1)


def open_month(path: Path) -> xr.Dataset:
    """Ouvre un NetCDF mensuel et collapse la dim time (toujours de taille 1
    après harmonisation par wgrib2)."""
    ds = xr.open_dataset(path, decode_timedelta=False)
    if "time" in ds.dims and ds.sizes["time"] == 1:
        ds = ds.isel(time=0, drop=True)
    return ds


def get_grid(nc_base: Path) -> tuple[np.ndarray, np.ndarray]:
    """Retourne (lon, lat) du premier NetCDF du dossier."""
    files = list_nc_files(nc_base)
    if not files:
        raise FileNotFoundError(f"Aucun .nc sous {nc_base}")
    with xr.open_dataset(files[0], decode_timedelta=False) as ds:
        lon = ds["longitude"].values
        lat = ds["latitude"].values
    return lon, lat
