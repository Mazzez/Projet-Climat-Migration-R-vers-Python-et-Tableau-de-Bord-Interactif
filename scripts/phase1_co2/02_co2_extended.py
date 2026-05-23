"""Phase 1 — Sections 9 à 11 : Mauna Loa + GCB + Vostok.

Migration de Final Version/Analyse CO2/scripts/co2_analysis_extended.R.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, io, plots                                    # noqa: E402

OUT = config.OUT_PHASE1
plots.setup_theme()


# ============================================================
# 9. Comparaison Global (NOAA GML) vs Mauna Loa
# ============================================================
print("\n========== 9. Global vs Mauna Loa ==========")

co2_gl = io.load_co2_global()[["date", "year", "month", "average", "trend"]]
co2_gl = co2_gl.rename(columns={"average": "gl_avg", "trend": "gl_trend"})

co2_mlo = io.load_co2_mauna_loa()[["date", "mlo_avg", "mlo_deseason"]]

both = co2_gl.merge(co2_mlo, on="date", how="inner")
both = both.assign(
    diff=both["mlo_avg"] - both["gl_avg"],
    diff_trend=both["mlo_deseason"] - both["gl_trend"],
)
print(f"Période commune : {both['date'].min().date()} -> "
      f"{both['date'].max().date()} ({len(both)} mois)")
print(f"Diff brut    (MLO - Global) : moyenne = {both['diff'].mean():.2f} ppm "
      f"; sd = {both['diff'].std():.2f} ppm")
print(f"Diff trend   (MLO - Global) : moyenne = {both['diff_trend'].mean():.2f} ppm "
      f"; sd = {both['diff_trend'].std():.2f} ppm")

fig, ax = plt.subplots()
ax.plot(both["date"], both["gl_avg"],  color="steelblue", lw=0.8, label="Global (NOAA GML)")
ax.plot(both["date"], both["mlo_avg"], color="tomato",    lw=0.8, label="Mauna Loa")
ax.legend(loc="lower right"); ax.set_ylabel("ppm")
ax.set_title("CO2 mensuel : Global vs Mauna Loa")
plots.save(fig, OUT / "09a_global_vs_mlo.png")

fig, ax = plt.subplots()
ax.plot(both["date"], both["diff"], color="purple", alpha=0.6, lw=0.8)
import seaborn as sns
sns.regplot(x=pd.to_datetime(both["date"]).map(pd.Timestamp.toordinal),
            y=both["diff"], lowess=True, scatter=False, ax=ax,
            color="black", line_kws={"linewidth": 0.7})
ax.axhline(0, ls="--", color="grey", lw=0.6)
ax.set_ylabel("MLO - Global (ppm)")
ax.set_title("Écart mensuel Mauna Loa - Global\n"
             "Surplus systématique de l'hémisphère nord")
plots.save(fig, OUT / "09b_diff_mlo_global.png")

# Cycle saisonnier comparé
clim_global = (both
               .assign(anomaly=both["gl_avg"] - both["gl_trend"], source="Global")
               .assign(month_n=both["date"].dt.month))
clim_mlo = (both
            .assign(anomaly=both["mlo_avg"] - both["mlo_deseason"], source="Mauna Loa")
            .assign(month_n=both["date"].dt.month))
clim_cmp = pd.concat([clim_global, clim_mlo], ignore_index=True)
clim_cmp = (clim_cmp.groupby(["source", "month_n"])
            .agg(mean_anom=("anomaly", "mean"),
                 sd_anom=("anomaly", "std")).reset_index())

fig, ax = plt.subplots()
months = list(range(1, 13))
w = 0.4
sub_g = clim_cmp[clim_cmp["source"] == "Global"]
sub_m = clim_cmp[clim_cmp["source"] == "Mauna Loa"]
ax.bar(np.array(months) - w / 2, sub_g["mean_anom"], width=w,
       label="Global", color="steelblue",
       yerr=sub_g["sd_anom"], capsize=2)
ax.bar(np.array(months) + w / 2, sub_m["mean_anom"], width=w,
       label="Mauna Loa", color="tomato",
       yerr=sub_m["sd_anom"], capsize=2)
ax.set_xticks(months); ax.legend()
ax.set_xlabel("Mois"); ax.set_ylabel("Anomalie (ppm)")
ax.set_title("Cycle saisonnier moyen : Global vs Mauna Loa\n"
             "Mauna Loa amplifie le signal hémisphérique nord (~3x)")
plots.save(fig, OUT / "09c_cycle_compare.png")

amp_gl = sub_g["mean_anom"].max() - sub_g["mean_anom"].min()
amp_mlo = sub_m["mean_anom"].max() - sub_m["mean_anom"].min()
print(f"Amplitude saisonnière moyenne : Global = {amp_gl:.2f} ppm | "
      f"Mauna Loa = {amp_mlo:.2f} ppm | ratio = {amp_mlo / amp_gl:.2f}")

# ============================================================
# 10. Émissions mondiales (GCB) et fraction airborne
# ============================================================
print("\n========== 10. Émissions et fraction airborne ==========")

gcb = io.load_gcb()
gcb["total_GtC"] = gcb["total_MtCO2"] * config.MTCO2_TO_GTC
print(f"GCB Global : période = {gcb['year'].min()} -> {gcb['year'].max()}")
print(f"Émissions 2024 : {gcb['total_MtCO2'].iloc[-1] / 1000:.2f} GtCO2 "
      f"({gcb['total_GtC'].iloc[-1]:.2f} GtC)")

co2_annual = (co2_gl.groupby("year")
              .agg(annual_mean=("gl_avg", "mean"),
                   n=("gl_avg", "count")).reset_index())
co2_annual = co2_annual[co2_annual["n"] >= 6].copy()
co2_annual["d_ppm"] = co2_annual["annual_mean"].diff()
co2_annual["d_GtC"] = co2_annual["d_ppm"] * config.PPM_TO_GTC

af = (co2_annual.dropna(subset=["d_GtC"])
      .merge(gcb[["year", "total_GtC"]], on="year", how="inner"))
af["airborne_fraction"] = af["d_GtC"] / af["total_GtC"]
print(f"Fraction airborne moyenne : {af['airborne_fraction'].mean():.3f} "
      f" (médiane : {af['airborne_fraction'].median():.3f})")
print(f"Plage des fractions       : {af['airborne_fraction'].min():.3f} - "
      f"{af['airborne_fraction'].max():.3f}")
af.to_csv(OUT / "fraction_airborne.csv", index=False)

# Émissions par source (1900-2024)
sub = gcb[gcb["year"] >= 1900].copy()
fig, ax = plt.subplots()
sources = ["coal", "oil", "gas", "cement", "flaring", "other"]
colors = sns.color_palette("Set2", len(sources))
ax.stackplot(sub["year"],
             *[sub[s].fillna(0) / 1000 for s in sources],
             labels=sources, colors=colors)
ax.legend(loc="upper left"); ax.set_ylabel("GtCO2 / an")
ax.set_title("Émissions mondiales de CO2 par source (1900-2024)\n"
             "Source : Global Carbon Budget 2025v15")
plots.save(fig, OUT / "10a_emissions_par_source.png")

fig, ax = plt.subplots()
ax.plot(af["year"], af["total_GtC"], color="darkred",  lw=1, label="Émissions fossiles")
ax.plot(af["year"], af["d_GtC"],     color="steelblue", lw=1, label="Accroissement atmosphérique")
ax.legend(); ax.set_ylabel("GtC / an")
ax.set_title("Émissions fossiles vs accroissement atmosphérique\n"
             "Période 1980-2024, en GtC/an")
plots.save(fig, OUT / "10b_emissions_vs_accroissement.png")

fig, ax = plt.subplots()
ax.bar(af["year"], af["airborne_fraction"], color="steelblue")
ax.axhline(af["airborne_fraction"].mean(), ls="--", color="darkred", lw=1)
sns.regplot(x=af["year"], y=af["airborne_fraction"], lowess=True,
            scatter=False, color="black", ax=ax, line_kws={"linewidth": 0.7})
from matplotlib.ticker import PercentFormatter
ax.yaxis.set_major_formatter(PercentFormatter(1.0))
ax.set_title(f"Fraction airborne du CO2 fossile (1980-2024)\n"
             f"Moyenne = {100*af['airborne_fraction'].mean():.1f} % (ligne rouge)")
ax.set_ylabel(r"$\Delta CO_2^{atm} / \mathrm{Emissions}$")
plots.save(fig, OUT / "10c_fraction_airborne.png")

# Régression d_GtC ~ total_GtC
ok = af.dropna(subset=["d_GtC", "total_GtC"])
beta1, beta0 = np.polyfit(ok["total_GtC"], ok["d_GtC"], 1)
print(f"\n--- Régression d_GtC ~ total_GtC ---")
print(f"  d_GtC = {beta0:.3f} + {beta1:.3f} * total_GtC")
print(f"Pente (~ fraction airborne implicite) : {beta1:.3f}")

# ============================================================
# 11. Perspective paléoclimatique (Vostok)
# ============================================================
print("\n========== 11. Vostok (paléo) ==========")
vostok = io.load_vostok()
print(f"Vostok : âge max = {vostok['gas_ageBP'].max():.0f} ans BP")
print(f"CO2 plage paléo : {vostok['CO2'].min():.1f} -> {vostok['CO2'].max():.1f} ppm "
      f"(n = {len(vostok)})")

co2_now = co2_gl["gl_avg"].iloc[-1]

fig, ax = plt.subplots()
ax.plot(vostok["gas_ageBP"] / 1000, vostok["CO2"], color="steelblue", lw=0.8)
ax.axhline(co2_now, ls="--", color="darkred", lw=1)
ax.text(vostok["gas_ageBP"].max() / 1000 * 0.6, co2_now + 8,
        f"Niveau actuel : {co2_now:.0f} ppm (2025)", color="darkred")
ax.invert_xaxis()
ax.set_xlabel("Milliers d'années avant 1950 (BP)")
ax.set_ylabel("CO2 (ppm)")
ax.set_title("CO2 atmosphérique sur 414 000 ans (Vostok)\n"
             "4 cycles glaciaires-interglaciaires ; le niveau actuel dépasse tous les pics paléo")
plots.save(fig, OUT / "11a_vostok_full.png")

# Taux paléo vs taux moderne
vostok_rates = vostok.copy()
vostok_rates["d_age"] = vostok_rates["gas_ageBP"].diff()
vostok_rates["d_co2"] = vostok_rates["CO2"].diff()
vostok_rates["rate_ppm_per_century"] = (
    -vostok_rates["d_co2"] / vostok_rates["d_age"] * 100
)
max_paleo_rate = vostok_rates["rate_ppm_per_century"].max()
modern_rate = 1.85 * 100   # 1.85 ppm/an = 185 ppm/siècle
print(f"Taux paléo maximal       : {max_paleo_rate:.2f} ppm/siècle")
print(f"Taux moderne (1979-2025) : {modern_rate:.2f} ppm/siècle")
print(f"Ratio moderne / paléo    : {modern_rate / max_paleo_rate:.1f}x plus rapide")

recent_paleo = vostok[vostok["gas_ageBP"] <= 20000]
modern_annual = (co2_gl.groupby("year")["gl_avg"].mean().reset_index())
modern_annual["gas_ageBP"] = 1950 - modern_annual["year"]

fig, ax = plt.subplots()
ax.plot(recent_paleo["gas_ageBP"], recent_paleo["CO2"],
        color="steelblue", lw=1, label="Paléo (Vostok)")
ax.plot(modern_annual["gas_ageBP"], modern_annual["gl_avg"],
        color="darkred", lw=1.5, label="Moderne (NOAA)")
ax.invert_xaxis(); ax.legend()
ax.set_xlabel("Années avant 1950 (BP)")
ax.set_ylabel("CO2 (ppm)")
ax.set_title("CO2 sur 20 000 ans : paléo (Vostok, bleu) + moderne (NOAA, rouge)\n"
             "La hausse moderne est sans précédent dans cette fenêtre")
plots.save(fig, OUT / "11b_vostok_20k_zoom.png")

print(f"\n=== Sections 9-11 sauvegardées dans : {OUT} ===")
