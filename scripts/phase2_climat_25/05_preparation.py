"""Phase 2 — 05 — Construction des 5 représentations temporelles
(level, anom, resid, d1, d12) pour 21 variables (18 climat + 3 CRE)
+ co2_avg + co2_trend.

Migration de 05_preparation.R. Sauvegarde un .pkl (analogue de
series_transformed.rds) + 5 CSV.
"""
from __future__ import annotations
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config                                                   # noqa: E402

OUT = config.OUT_PHASE2

df = pd.read_csv(OUT / "climate_co2_monthly.csv", parse_dates=["date"]).sort_values("date").reset_index(drop=True)

target_vars = config.CLIM_VARS + ["CRE_SW", "CRE_LW", "CRE_net",
                                  "co2_avg", "co2_trend"]
print(f"Variables à traiter : {len(target_vars)}")
print(f"Période             : {df['date'].min().date()} -> {df['date'].max().date()}\n")

months = df["month"].to_numpy()
dates = df["date"]
t = (dates - dates.iloc[0]).dt.days.to_numpy(dtype=float)


def make_transformations(values: np.ndarray) -> dict[str, np.ndarray]:
    """5 représentations : level, anom (climato mensuelle retirée),
    resid (anom + détendrage linéaire), d1 (diff lag 1), d12 (diff lag 12)."""
    level = values.copy()
    # anom = level - clim mensuelle (sur l'ensemble de la période)
    s = pd.Series(level)
    clim = s.groupby(months).transform("mean").to_numpy()
    anom = level - clim
    # resid = anom détendré linéairement vs t
    p = np.polyfit(t, anom, 1)
    fit = np.polyval(p, t)
    resid = anom - fit
    # d1, d12
    d1 = np.full_like(level, np.nan); d1[1:] = np.diff(level, n=1)
    d12 = np.full_like(level, np.nan); d12[12:] = level[12:] - level[:-12]
    return {"level": level, "anom": anom, "resid": resid, "d1": d1, "d12": d12}


trans = {v: make_transformations(df[v].to_numpy(dtype=float)) for v in target_vars}


def build_wide(repr_name: str) -> pd.DataFrame:
    cols = {v: trans[v][repr_name] for v in target_vars}
    out = pd.DataFrame(cols)
    out.insert(0, "month", df["month"].values)
    out.insert(0, "year",  df["year"].values)
    out.insert(0, "date",  df["date"].values)
    return out


ds = {repr_name: build_wide(repr_name)
      for repr_name in ["level", "anom", "resid", "d1", "d12"]}

for k, d in ds.items():
    na_pct = d[target_vars].isna().mean().mean() * 100
    print(f"[{k:5s}]  dim = {d.shape[0]} x {d.shape[1]}   NA(%) = {na_pct:.1f}")

def _preview(df_in: pd.DataFrame, cols_num: list[str]) -> pd.DataFrame:
    """Ne round que les colonnes numériques (laisse les datetime tels quels)."""
    out = df_in.copy()
    out[cols_num] = out[cols_num].round(3)
    return out


print("\nAperçu anomalies (3 premières lignes) :")
print(_preview(ds["anom"][["date", "T2m", "PWAT", "co2_avg"]].head(3),
               ["T2m", "PWAT", "co2_avg"]))

print("\nAperçu différences premières (lignes 2-4) :")
print(_preview(ds["d1"][["date", "T2m", "PWAT", "co2_avg"]].iloc[1:4],
               ["T2m", "PWAT", "co2_avg"]))

# Pickle (analogue rds)
with open(OUT / "series_transformed.pkl", "wb") as fh:
    pickle.dump(ds, fh)

# CSV pour inspection
for k, d in ds.items():
    d.to_csv(OUT / f"series_{k}.csv", index=False)

print("\n=== Fichiers sauvegardés ===")
print(" - series_transformed.pkl")
print(" - series_level.csv, series_anom.csv, series_resid.csv, series_d1.csv, series_d12.csv")
