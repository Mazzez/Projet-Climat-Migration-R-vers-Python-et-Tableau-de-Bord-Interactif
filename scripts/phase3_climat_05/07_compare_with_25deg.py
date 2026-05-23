"""Phase 3 — 07 — Validation croisée moyennes globales 0.5° vs 2.5°.

Migration de 07_compare_with_25deg.R.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from climat import config, plots                                            # noqa: E402

OUT_05 = config.OUT_PHASE3
OUT_25 = config.OUT_PHASE2
PLOT = OUT_05 / "plots"
plots.setup_theme()

d05 = (pd.read_csv(OUT_05 / "monthly_band_means_05.csv", parse_dates=["date"])
       .query("band == 'global'").drop(columns=["band"]))
d25 = pd.read_csv(OUT_25 / "monthly_global_means_25.csv", parse_dates=["date"])
print(f"0.5° global  : {d05.shape}")
print(f"2.5° global  : {d25.shape}")

vars_ = config.CLIM_VARS
both = d05.merge(d25, on=["date", "year", "month"], suffixes=("_05", "_25"))
print(f"\nPériode commune : {both['date'].min().date()} -> "
      f"{both['date'].max().date()} ({len(both)} mois)\n")

rows = []
for v in vars_:
    v05 = both[f"{v}_05"]; v25 = both[f"{v}_25"]
    diff = v05 - v25
    rel = diff / v25 * 100
    rows.append({
        "var": v,
        "mean_05": float(v05.mean()),
        "mean_25": float(v25.mean()),
        "abs_diff_mean": float(diff.abs().mean()),
        "abs_diff_max":  float(diff.abs().max()),
        "rel_diff_mean_pct": float(rel.abs().mean()),
        "correlation": float(v05.corr(v25)),
    })
gap = pd.DataFrame(rows)
print("=== Comparaison 0.5° vs 2.5° (moyennes globales) ===")
print(gap.round(4).to_string(index=False))
gap.to_csv(OUT_05 / "comparison_05_vs_25.csv", index=False)

# Plot superposition pour 4 variables clés
key = ["T2m", "PWAT", "DSWRF", "TCDC"]
fig, axes = plt.subplots(2, 2, figsize=(14, 8))
for ax, v in zip(axes.flat, key):
    ax.plot(both["date"], both[f"{v}_25"], color="steelblue", alpha=0.7, lw=0.5, label="2.5°")
    ax.plot(both["date"], both[f"{v}_05"], color="tomato",    alpha=0.7, lw=0.5, label="0.5°")
    ax.set_title(v)
axes[0, 0].legend()
fig.suptitle("Moyennes globales : 0.5° vs 2.5°\nValidation croisée des deux pipelines")
plots.save(fig, PLOT / "07_comparison.png", w=14, h=8, dpi=130)

print("\n=== Plot : 07_comparison.png ===")
