"""Phase 3 — 10 — Asymétrie hémisphérique du cycle saisonnier T2m,
PWAT, DSWRF, TCDC — comparé au ratio CO2 MLO/SPO = 5.6× (phase 1).

Migration de 10_hemisphere_asymmetry.R.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, plots                                            # noqa: E402

OUT = config.OUT_PHASE3
PLOT = OUT / "plots"
PLOT.mkdir(parents=True, exist_ok=True)
plots.setup_theme()

BAND_ORDER = ["austral", "temperate_S", "tropical", "temperate_N", "boreal", "global"]
BAND_LABELS = {
    "austral":     "Australe (90-60°S)",
    "temperate_S": "Tempérée S (60-30°S)",
    "tropical":    "Tropicale (30°S-30°N)",
    "temperate_N": "Tempérée N (30-60°N)",
    "boreal":      "Boréale (60-90°N)",
    "global":      "Global",
}

df = pd.read_csv(OUT / "monthly_band_means_05.csv", parse_dates=["date"])
df["band_lbl"] = df["band"].map(BAND_LABELS)
df["band_lbl"] = pd.Categorical(df["band_lbl"],
                                 categories=[BAND_LABELS[b] for b in BAND_ORDER],
                                 ordered=True)

vars_ = ["T2m", "PWAT", "DSWRF", "TCDC"]

# ============================================================
# 1. Climatologie mensuelle par bande × variable
# ============================================================
clim_long = (df.query("band != 'global'")
             .melt(id_vars=["band", "band_lbl", "month"],
                   value_vars=vars_, var_name="var", value_name="value")
             .groupby(["band", "band_lbl", "var", "month"], observed=True)
             .agg(mean_clim=("value", "mean"))
             .reset_index())

# ============================================================
# 2. Amplitude saisonnière = max(clim) - min(clim) par bande × var
# ============================================================
amp = (clim_long.groupby(["band", "band_lbl", "var"], observed=True)
       .agg(amplitude=("mean_clim", lambda s: s.max() - s.min()))
       .reset_index())

amp_wide = amp.pivot(index="var", columns="band_lbl", values="amplitude")
print(amp_wide.round(4))

# Ratio Boréale / Australe (équivalent climat de MLO/SPO)
ratio_rows = []
for v in vars_:
    boreal_amp = float(amp.query("var == @v and band == 'boreal'")["amplitude"].iloc[0])
    austral_amp = float(amp.query("var == @v and band == 'austral'")["amplitude"].iloc[0])
    ratio_rows.append({
        "var": v,
        "Boreale_N": boreal_amp,
        "Australe_S": austral_amp,
        "ratio_N_over_S": boreal_amp / austral_amp,
    })
ratio = pd.DataFrame(ratio_rows)

print("\n=== Ratio amplitude saisonnière Boréale / Australe ===")
print(ratio.to_string(index=False))

ratio_co2_mlo_spo = 5.6
print(f"\nRéférence phase 1 : MLO/SPO CO2 saisonnier = {ratio_co2_mlo_spo:.1f}×")

# ============================================================
# 3. Sauvegarde CSV
# ============================================================
amp[["band", "var", "amplitude"]].to_csv(
    OUT / "hemisphere_asymmetry.csv", index=False)
ratio.to_csv(OUT / "hemisphere_asymmetry_ratio.csv", index=False)

# ============================================================
# 4. Plot : 2 panneaux empilés
# ============================================================
# Panneau 1 : cycles saisonniers superposés (T2m anomalie / moyenne bande)
clim_t2m = clim_long.query("var == 'T2m'").copy()
clim_t2m["anom"] = (clim_t2m.groupby("band_lbl", observed=True)["mean_clim"]
                    .transform(lambda x: x - x.mean()))

fig, axes = plt.subplots(2, 1, figsize=(12, 10),
                         gridspec_kw={"height_ratios": [1, 1]})

palette = sns.color_palette("Set1", 5)
for color, b in zip(palette, [BAND_LABELS[b] for b in BAND_ORDER if b != "global"]):
    sub = clim_t2m[clim_t2m["band_lbl"] == b].sort_values("month")
    axes[0].plot(sub["month"], sub["anom"], color=color, lw=1.2, marker="o",
                 ms=5, label=b)
axes[0].axhline(0, ls="--", color="grey", lw=0.5)
axes[0].set_xticks(range(1, 13))
axes[0].set_xticklabels(list("JFMAMJJASOND"))
axes[0].set_xlabel("Mois"); axes[0].set_ylabel("Anomalie T2m (K)")
axes[0].legend(loc="lower center", ncol=3,
               bbox_to_anchor=(0.5, -0.18), frameon=False)
axes[0].set_title("Cycle saisonnier de T2m par bande de latitude\n"
                  "Anomalie par rapport à la moyenne annuelle de chaque bande — 1979-2025",
                  fontsize=11)

# Panneau 2 : amplitudes T2m par bande
amp_t2m = amp.query("var == 'T2m'").copy()
amp_t2m["band_lbl"] = pd.Categorical(
    amp_t2m["band_lbl"],
    categories=[BAND_LABELS["boreal"], BAND_LABELS["temperate_N"],
                BAND_LABELS["tropical"],
                BAND_LABELS["temperate_S"], BAND_LABELS["austral"]],
    ordered=True,
)
amp_t2m = amp_t2m.sort_values("band_lbl")
colors2 = sns.color_palette("Set1", 5)
bars = axes[1].bar(amp_t2m["band_lbl"].astype(str), amp_t2m["amplitude"],
                   color=colors2, width=0.7)
for bar, val in zip(bars, amp_t2m["amplitude"]):
    axes[1].text(bar.get_x() + bar.get_width() / 2, val + 0.5,
                 f"{val:.1f} K", ha="center", va="bottom", fontweight="bold")
r_NS = ratio.query("var == 'T2m'")["ratio_N_over_S"].iloc[0]
axes[1].set_title(
    f"Amplitude saisonnière T2m par bande — ratio N/S = {r_NS:.2f}×\n"
    f"À comparer au ratio CO2 saisonnier MLO/SPO de la phase 1 = {ratio_co2_mlo_spo:.1f}×",
    fontsize=11,
)
axes[1].set_ylabel("Amplitude saisonnière (K)")
plt.setp(axes[1].get_xticklabels(), rotation=20, ha="right", fontweight="bold")

plots.save(fig, PLOT / "08_hemisphere_asymmetry.png", w=12, h=10, dpi=140)

print(f"\n=== Plot sauvegardé : {PLOT / '08_hemisphere_asymmetry.png'} ===")
