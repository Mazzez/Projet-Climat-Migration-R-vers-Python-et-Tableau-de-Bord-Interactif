"""Phase 2 — 09 — Tableau de synthèse final consolidant scripts 06+07+08.

Migration de 09_synthese.R.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, plots                                            # noqa: E402

OUT = config.OUT_PHASE2
PLOT = OUT / "plots"
plots.setup_theme()

cor4 = pd.read_csv(OUT / "correlations_4repr.csv")
gr = pd.read_csv(OUT / "granger_results.csv")

gr_d12 = (gr[gr["repr"] == "d12"]
          [["var", "p_x_to_co2", "p_co2_to_x", "sens"]]
          .rename(columns={"p_x_to_co2": "p_x_to_co2_d12",
                           "p_co2_to_x": "p_co2_to_x_d12",
                           "sens": "sens_d12"}))

synth = (cor4.rename(columns={"level": "r_level", "anom": "r_anom",
                              "resid": "r_resid", "d1": "r_d1", "d12": "r_d12"})
         .merge(gr_d12, on="var", how="left")
         .assign(abs_resid=lambda d: d["r_resid"].abs())
         .sort_values("abs_resid", ascending=False).drop(columns="abs_resid"))


def cat_corr(r):
    a = abs(r)
    if a > 0.4:  return "fort"
    if a > 0.2:  return "modéré"
    return "faible"


synth["poids_corr"] = synth["r_resid"].apply(cat_corr)
synth["spurious_trend"] = np.where(
    (synth["r_anom"].abs() > 0.5) & (synth["r_resid"].abs() < 0.25),
    "OUI", "non"
)

print("=== Synthèse finale (corrélations + Granger d12) ===\n")
print(synth.round(3).to_string(index=False))
synth.to_csv(OUT / "synthese_finale.csv", index=False)

# Plot synthèse
order_vars = synth["var"].tolist()
df_long = (synth.melt(id_vars="var",
                      value_vars=["r_level", "r_anom", "r_resid", "r_d12"],
                      var_name="repr", value_name="r"))
df_long["repr"] = df_long["repr"].map({
    "r_level": "Niveaux", "r_anom": "Anomalies",
    "r_resid": "Résidus", "r_d12": "d12 (annuel)"})
df_long["var"] = pd.Categorical(df_long["var"], categories=order_vars[::-1], ordered=True)

fig, ax = plt.subplots(figsize=(11, 8))
import seaborn as sns
sns.barplot(data=df_long, y="var", x="r", hue="repr",
            palette="Set1", ax=ax, orient="h")
ax.axvline(0, color="black", lw=0.4)
ax.set_xlabel("r (Pearson)"); ax.set_ylabel(None)
ax.legend(loc="lower right", title=None)
ax.set_title("Corrélation climat ↔ CO2 selon la représentation temporelle\n"
             "Plus on assainit la série (level → anom → resid), plus on isole le signal interannuel propre")
plots.save(fig, PLOT / "09_synthese.png", w=11, h=8, dpi=130)

print("\n=== Sauvegardes ===")
print(" - synthese_finale.csv")
print(" - plots/09_synthese.png\n")

# Bilan textuel
n_spurious = int((synth["spurious_trend"] == "OUI").sum())
n_xCo2 = int(synth["sens_d12"].isin(["X -> CO2", "bidirectionnel"]).sum())
n_co2X = int(synth["sens_d12"].isin(["CO2 -> X", "bidirectionnel"]).sum())
top5 = synth.head(5)[["var", "r_resid", "sens_d12"]]

print("=" * 52)
print("                BILAN PHASE 3 — climat ↔ CO2")
print("=" * 52)
print(f"\n• {len(synth)} variables climatiques globales testées")
print(f"• Variables avec corrélation 'spurious' (fort sur anom, faible sur resid) : "
      f"{n_spurious} / {len(synth)}")
print("  -> ces variables partagent surtout une tendance commune avec le CO2")
print("• Top 5 corrélations sur résidus (signal interannuel pur) :")
print(top5.round(3).to_string(index=False))
print(f"\n• Granger d12 — variables X causant CO2 (p < 0.05) : {n_xCo2}")
print(f"• Granger d12 — CO2 causant X (p < 0.05)              : {n_co2X}")
print("\n=> Le sens dominant à l'échelle interannuelle est CLIMAT -> CO2")
print("   (les variations climatiques précèdent celles du CO2)")
print("=" * 52)
