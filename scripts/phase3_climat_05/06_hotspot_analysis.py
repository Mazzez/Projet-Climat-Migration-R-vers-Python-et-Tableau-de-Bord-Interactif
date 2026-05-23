"""Phase 3 — 06 — Analyse des 4 hotspots régionaux (Amazonie, Indonésie,
Sibérie, Sahel) sur 4 variables clés (T2m, PWAT, APCP, TCDC).

Migration de 06_hotspot_analysis.R.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, io, plots                                        # noqa: E402
from climat.preprocess import cos_lat_weights                               # noqa: E402
from climat.stats import sens_slope_and_mk                                  # noqa: E402

NC_BASE = config.NC_05
OUT = config.OUT_PHASE3
PLOT = OUT / "plots"
PLOT.mkdir(parents=True, exist_ok=True)
plots.setup_theme()

KEY_VARS_NC = {
    "TMP_2maboveground":                                "T2m",
    "PWAT_entireatmosphere_consideredasasinglelayer_": "PWAT",
    "APCP_surface":                                     "APCP",
    "TCDC_entireatmosphere_consideredasasinglelayer_": "TCDC",
}

files = io.list_nc_files(NC_BASE)
lon, lat = io.get_grid(NC_BASE)
nx, ny, nt = len(lon), len(lat), len(files)

dates = pd.DatetimeIndex([io.date_from_filename(f) for f in files])
months = dates.month.to_numpy()
years = dates.year.to_numpy()
t_yrs = ((dates - dates[0]).days / 365.25).to_numpy(dtype=float)

w_lat = cos_lat_weights(lat)


def make_region_mask(reg: dict) -> tuple[np.ndarray, np.ndarray]:
    mask_lat = (lat >= reg["lat"][0]) & (lat <= reg["lat"][1])
    if reg["lon"][1] > 360:
        mask_lon = (lon >= reg["lon"][0]) | (lon <= (reg["lon"][1] - 360))
    else:
        mask_lon = (lon >= reg["lon"][0]) & (lon <= reg["lon"][1])
    return mask_lat, mask_lon


def extract_region_series(nc_var: str, mask_lat: np.ndarray,
                          mask_lon: np.ndarray) -> np.ndarray:
    series = np.empty(nt, dtype=np.float64)
    w_sub = w_lat[mask_lat]
    for i, f in enumerate(files):
        with io.open_month(f) as ds:
            arr = np.squeeze(ds[nc_var].values)
            if arr.shape == (ny, nx):
                arr = arr.T
            sub = arr[np.ix_(mask_lon, mask_lat)]
            ok = ~np.isnan(sub)
            w_grid = np.broadcast_to(w_sub[None, :], sub.shape)
            n = float(np.sum(w_grid * ok))
            series[i] = float(np.sum(np.where(ok, sub, 0) * w_grid)) / n
    return series


# CO2 résidus
co2 = io.load_co2_global()[["date", "trend"]].rename(columns={"trend": "co2_trend"})
co2_aligned = co2.set_index("date").reindex(dates)["co2_trend"].to_numpy(dtype=float)
co2_clim_m = pd.Series(co2_aligned).groupby(months).transform("mean").to_numpy()
co2_anom = co2_aligned - co2_clim_m
ok_co2 = ~np.isnan(co2_anom)
p = np.polyfit(t_yrs[ok_co2], co2_anom[ok_co2], 1)
co2_resid = co2_anom - np.polyval(p, t_yrs)

# Boucle principale : extraction
t0 = time.time()
all_series: dict[str, np.ndarray] = {}
for rname, reg in config.REGIONS.items():
    mask_lat, mask_lon = make_region_mask(reg)
    print(f"\n[{rname}] {reg['label']}")
    print(f"  cellules : {mask_lat.sum()} (lat) × {mask_lon.sum()} (lon) = "
          f"{mask_lat.sum() * mask_lon.sum()}")
    for nc_var, short in KEY_VARS_NC.items():
        print(f"  - {short} ...")
        all_series[f"{rname}_{short}"] = extract_region_series(nc_var, mask_lat, mask_lon)
print(f"\nDurée extraction : {time.time() - t0:.1f} s")

df = pd.DataFrame({"date": dates, "year": years, "month": months})
for col, ser in all_series.items():
    df[col] = ser
df.to_csv(OUT / "hotspots_series.csv", index=False)
print(f"\nCSV sauvegardé : hotspots_series.csv")

# Plot 1 : T2m anomalies par hotspot (LOESS)
from statsmodels.nonparametric.smoothers_lowess import lowess
df_anom = df.copy()
for rname in config.REGIONS:
    col = f"{rname}_T2m"
    clim = df_anom.groupby("month")[col].transform("mean")
    df_anom[col] = df_anom[col] - clim

fig, ax = plt.subplots(figsize=(12, 6))
palette = sns.color_palette("Set1", len(config.REGIONS))
for rname, color in zip(config.REGIONS, palette):
    col = f"{rname}_T2m"
    sub = df_anom.sort_values("date")
    ax.plot(sub["date"], sub[col], color=color, alpha=0.3, lw=0.3)
    sm_v = lowess(sub[col], (sub["date"] - sub["date"].min()).dt.days,
                  frac=0.15, return_sorted=False)
    ax.plot(sub["date"], sm_v, color=color, lw=1.2, label=rname)
ax.axhline(0, ls="--", color="grey", lw=0.5)
ax.legend(loc="upper left")
ax.set_ylabel("Anomalie T2m (K)")
ax.set_title("Anomalies T2m sur 4 hotspots (0.5°)\n"
             "Anomalie = T2m − climatologie mensuelle ; lissage LOESS")
plots.save(fig, PLOT / "06a_T2m_hotspots.png", w=12, h=6, dpi=130)

# Plot 2 : 4 variables × 4 hotspots
key_vars = list(KEY_VARS_NC.values())
fig, axes = plt.subplots(2, 2, figsize=(14, 8))
for ax, v in zip(axes.flat, key_vars):
    for rname, color in zip(config.REGIONS, palette):
        col = f"{rname}_{v}"
        ax.plot(df["date"], df[col], color=color, alpha=0.5, lw=0.4,
                label=rname if v == key_vars[0] else None)
    ax.set_title(v)
fig.legend(*axes.flat[0].get_legend_handles_labels(), loc="lower center",
           ncol=len(config.REGIONS), bbox_to_anchor=(0.5, -0.02))
fig.suptitle("4 variables × 4 hotspots (0.5°)\nSéries mensuelles brutes")
plots.save(fig, PLOT / "06b_4vars_hotspots.png", w=14, h=8, dpi=130)

# Tableau récap : Sen + corrélation avec CO2 résiduel
results_rows = []
for rname in config.REGIONS:
    for v in key_vars:
        x = df[f"{rname}_{v}"].to_numpy()
        sen = sens_slope_and_mk(x).sen_per_year
        mk_p = sens_slope_and_mk(x).mk_p
        x_clim = pd.Series(x).groupby(months).transform("mean").to_numpy()
        x_anom = x - x_clim
        ok = ~np.isnan(x_anom)
        p2 = np.polyfit(t_yrs[ok], x_anom[ok], 1)
        x_resid = x_anom - np.polyval(p2, t_yrs)
        ok2 = ~np.isnan(x_resid) & ~np.isnan(co2_resid)
        r = float(np.corrcoef(x_resid[ok2], co2_resid[ok2])[0, 1])
        results_rows.append({
            "region": rname, "var": v,
            "sen_per_year": sen, "mk_pvalue": mk_p,
            "r_with_co2_resid": r,
        })
res_df = pd.DataFrame(results_rows)
print("\n=== Hotspots — Sen + r(CO2 résid) ===")
print(res_df.round(3).to_string(index=False))
res_df.to_csv(OUT / "hotspots_summary.csv", index=False)

print("\n=== Hotspots terminés. Fichiers :")
print(" - outputs/hotspots_series.csv")
print(" - outputs/hotspots_summary.csv")
print(" - outputs/plots/06a_T2m_hotspots.png")
print(" - outputs/plots/06b_4vars_hotspots.png")
