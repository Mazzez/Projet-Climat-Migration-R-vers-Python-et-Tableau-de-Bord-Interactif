"""Phase 3 — 09 — Tests de causalité Granger climat ↔ CO2 par zone
(5 bandes + 4 hotspots), représentation d12, lag 6 mois.

Migration de 09_granger_per_zone.R.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, io                                                # noqa: E402
from climat.stats import grangertest_pvalue                                  # noqa: E402

OUT = config.OUT_PHASE3
LAG = 6

bands_df = pd.read_csv(OUT / "monthly_band_means_05.csv", parse_dates=["date"]).sort_values("date")
hot_df = pd.read_csv(OUT / "hotspots_series.csv", parse_dates=["date"]).sort_values("date")

co2 = io.load_co2_global()[["date", "trend"]].rename(columns={"trend": "co2_trend"})

dates = pd.DatetimeIndex(sorted(bands_df["date"].unique()))
co2_v = co2.set_index("date").reindex(dates)["co2_trend"].to_numpy(dtype=float)


def d12(x: np.ndarray) -> np.ndarray:
    """X_t - X_{t-12} — 12 NaN au début."""
    out = np.full_like(x, np.nan, dtype=float)
    out[12:] = x[12:] - x[:-12]
    return out


co2_d12 = d12(co2_v)


def granger_xy(x: np.ndarray, y: np.ndarray, lag: int = LAG) -> tuple[float, float]:
    """Retourne (p_x_to_y, p_y_to_x)."""
    ok = ~np.isnan(x) & ~np.isnan(y)
    if int(ok.sum()) < 50:
        return float("nan"), float("nan")
    xc, yc = x[ok], y[ok]
    _, p_xy = grangertest_pvalue(yc, xc, lag=lag)  # x -> y
    _, p_yx = grangertest_pvalue(xc, yc, lag=lag)  # y -> x
    return float(p_xy), float(p_yx)


def classify(p_xy: float, p_yx: float) -> str:
    if not np.isnan(p_xy) and p_xy < 0.05 and not np.isnan(p_yx) and p_yx < 0.05:
        return "bidirectional"
    if not np.isnan(p_xy) and p_xy < 0.05:
        return "X -> CO2"
    if not np.isnan(p_yx) and p_yx < 0.05:
        return "CO2 -> X"
    return "none"


# ============================================================
# Bandes de latitude
# ============================================================
clim_vars = config.CLIM_VARS
bands_list = list(bands_df["band"].unique())

rows: list[dict] = []
for b in bands_list:
    sub = bands_df[bands_df["band"] == b].sort_values("date").reset_index(drop=True)
    for v in clim_vars:
        x_d12 = d12(sub[v].to_numpy(dtype=float))
        p_xy, p_yx = granger_xy(x_d12, co2_d12, lag=LAG)
        rows.append({
            "zone": b, "type": "bande", "var": v,
            "p_x_to_co2": p_xy, "p_co2_to_x": p_yx,
            "sens": classify(p_xy, p_yx),
        })

# ============================================================
# Hotspots
# ============================================================
hot_vars = ["T2m", "PWAT", "APCP", "TCDC"]
regions = ["Amazonie", "Indonesie", "Siberie", "Sahel"]

for r in regions:
    for v in hot_vars:
        x_d12 = d12(hot_df[f"{r}_{v}"].to_numpy(dtype=float))
        p_xy, p_yx = granger_xy(x_d12, co2_d12, lag=LAG)
        rows.append({
            "zone": r, "type": "hotspot", "var": v,
            "p_x_to_co2": p_xy, "p_co2_to_x": p_yx,
            "sens": classify(p_xy, p_yx),
        })

gr = pd.DataFrame(rows)
gr.to_csv(OUT / "granger_per_zone.csv", index=False)

# Synthèse : nb variables significatives par zone
synth = (gr.assign(
            sig_x_to_co2=lambda d: (d["p_x_to_co2"] < 0.05).fillna(False),
            sig_co2_to_x=lambda d: (d["p_co2_to_x"] < 0.05).fillna(False))
         .groupby(["zone", "type"])
         .agg(n_vars=("var", "count"),
              n_x_to_co2_sig=("sig_x_to_co2", "sum"),
              n_co2_to_x_sig=("sig_co2_to_x", "sum"))
         .reset_index()
         .sort_values(["type", "n_x_to_co2_sig"], ascending=[True, False]))

print("=== Synthèse Granger par zone (d12, lag 6) ===")
print(synth.to_string(index=False))

print(f"\n=== Détail sauvegardé : {OUT / 'granger_per_zone.csv'} ===")
