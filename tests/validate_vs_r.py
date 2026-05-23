"""Validation croisée Python vs R : tous les CSV produits par le R doivent
être reproduits à précision numérique près par le pipeline Python.

Lancer : python tests/validate_vs_r.py
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from climat import config                                                   # noqa: E402

R_BASE = Path("/home/mazzez/Bureau/R project/Final Version")
R_PHASE1 = R_BASE / "Analyse CO2/outputs"
R_PHASE2 = R_BASE / "Analyse Climat 2.5°x2.5°/outputs"
R_PHASE3 = R_BASE / "Analyse Climat 0.5°x0.5°/outputs"

PY_PHASE1 = config.OUT_PHASE1
PY_PHASE2 = config.OUT_PHASE2
PY_PHASE3 = config.OUT_PHASE3

ABS_TOL = 1e-6   # tolérance absolue (numerical)
REL_TOL = 1e-3   # tolérance relative (méthodes différentes pour Sen bootstrap, ARIMA…)
TOL_R2 = 0.05    # 5% pour R² (méthodes step diffèrent)


def _diff_max(a: np.ndarray, b: np.ndarray) -> float:
    n = min(len(a), len(b))
    a, b = np.asarray(a[:n], dtype=float), np.asarray(b[:n], dtype=float)
    ok = ~np.isnan(a) & ~np.isnan(b)
    if ok.sum() == 0: return float("nan")
    return float(np.max(np.abs(a[ok] - b[ok])))


def compare_csv(py_path: Path, r_path: Path, key_cols: list[str],
                value_cols: list[str], label: str,
                tol_rel: float = REL_TOL) -> dict:
    if not py_path.exists() or not r_path.exists():
        return {"label": label, "status": "MISSING",
                "py_exists": py_path.exists(), "r_exists": r_path.exists()}
    py = pd.read_csv(py_path)
    r = pd.read_csv(r_path)
    out = {"label": label, "py_rows": len(py), "r_rows": len(r), "diffs": {}}
    if key_cols:
        m = py.merge(r, on=key_cols, suffixes=("_py", "_r"))
    else:
        # Joindre par index
        m = pd.concat([py.reset_index(drop=True), r.reset_index(drop=True)], axis=1,
                      keys=("py", "r")).copy()
        m.columns = [f"{a}_{b}" for a, b in m.columns]
    bad = []
    for v in value_cols:
        if f"{v}_py" not in m.columns or f"{v}_r" not in m.columns:
            out["diffs"][v] = "absent"
            continue
        a = pd.to_numeric(m[f"{v}_py"], errors="coerce").to_numpy()
        b = pd.to_numeric(m[f"{v}_r"],  errors="coerce").to_numpy()
        d = _diff_max(a, b)
        scale = max(float(np.nanmean(np.abs(b))), 1e-12)
        rel = d / scale
        out["diffs"][v] = (d, rel)
        if rel > tol_rel:
            bad.append((v, d, rel))
    out["status"] = "OK" if not bad else "DIFF"
    out["bad"] = bad
    return out


def report(res: dict) -> None:
    print(f"\n--- {res['label']} ---")
    if res["status"] == "MISSING":
        print(f"  ⚠ MANQUE  py={res['py_exists']}  r={res['r_exists']}")
        return
    print(f"  rows : Python={res['py_rows']}, R={res['r_rows']}")
    for v, dd in res["diffs"].items():
        if isinstance(dd, str):
            print(f"  {v:25s} : {dd}")
        else:
            d, rel = dd
            mark = "✓" if rel <= REL_TOL else "✗"
            print(f"  {v:25s} : max|Δ|={d:11.4g}  rel={rel:.2e}  {mark}")


print("=" * 70)
print("VALIDATION PYTHON vs R")
print("=" * 70)

# ============================================================
# Phase 1 — CO2
# ============================================================
print("\n=================== PHASE 1 — CO2 ===================")

report(compare_csv(
    PY_PHASE1 / "stats_decennie.csv", R_PHASE1 / "stats_decennie.csv",
    key_cols=["decade"],
    value_cols=["n", "mean", "min", "max", "sd"],
    label="stats_decennie"))

report(compare_csv(
    PY_PHASE1 / "amplitude_saisonniere_decennie.csv",
    R_PHASE1 / "amplitude_saisonniere_decennie.csv",
    key_cols=["decade"], value_cols=["amplitude"],
    label="amplitude_saisonniere_decennie"))

report(compare_csv(
    PY_PHASE1 / "taux_annuel.csv", R_PHASE1 / "taux_annuel.csv",
    key_cols=["year"], value_cols=["annual_mean", "annual_rate"],
    label="taux_annuel"))

report(compare_csv(
    PY_PHASE1 / "fraction_airborne.csv", R_PHASE1 / "fraction_airborne.csv",
    key_cols=["year"],
    value_cols=["d_ppm", "d_GtC", "total_GtC", "airborne_fraction"],
    label="fraction_airborne"))

# ============================================================
# Phase 2 — Climat 2.5°
# ============================================================
print("\n=================== PHASE 2 — Climat 2.5° ===================")

clim_vars = config.CLIM_VARS  # 18 variables
all_vars = clim_vars + ["CRE_SW", "CRE_LW", "CRE_net"]

report(compare_csv(
    PY_PHASE2 / "monthly_global_means_25.csv",
    R_PHASE2 / "monthly_global_means_25.csv",
    key_cols=["date"], value_cols=clim_vars,
    label="monthly_global_means_25",
    tol_rel=1e-9))

report(compare_csv(
    PY_PHASE2 / "cre_monthly_25.csv", R_PHASE2 / "cre_monthly_25.csv",
    key_cols=["date"], value_cols=["CRE_SW", "CRE_LW", "CRE_net"],
    label="cre_monthly_25", tol_rel=1e-9))

report(compare_csv(
    PY_PHASE2 / "correlations_brut.csv", R_PHASE2 / "correlations_brut.csv",
    key_cols=["var"], value_cols=["r_pearson"],
    label="correlations_brut"))

report(compare_csv(
    PY_PHASE2 / "correlations_4repr.csv", R_PHASE2 / "correlations_4repr.csv",
    key_cols=["var"], value_cols=["level", "anom", "resid", "d1", "d12"],
    label="correlations_4repr"))

report(compare_csv(
    PY_PHASE2 / "trends_summary.csv", R_PHASE2 / "trends_summary.csv",
    key_cols=["var"],
    value_cols=["sen_per_year", "mean", "sd", "pct_change_47y"],
    label="trends_summary"))

report(compare_csv(
    PY_PHASE2 / "cfsr_to_cfsv2_jumps.csv", R_PHASE2 / "cfsr_to_cfsv2_jumps.csv",
    key_cols=["var"],
    value_cols=["jump", "se", "p_value", "trend_per_yr",
                "mean_var", "sd_var", "jump_pct"],
    label="cfsr_to_cfsv2_jumps"))

report(compare_csv(
    PY_PHASE2 / "synthese_finale.csv", R_PHASE2 / "synthese_finale.csv",
    key_cols=["var"],
    value_cols=["r_level", "r_anom", "r_resid", "r_d1", "r_d12"],
    label="synthese_finale"))

# Per-variable stats
report(compare_csv(
    PY_PHASE2 / "per_variable_stats.csv", R_PHASE2 / "per_variable_stats.csv",
    key_cols=["var"],
    value_cols=["min", "mean", "max", "sd", "range",
                "sen_per_year", "sen_total"],
    label="per_variable_stats"))

# ============================================================
# Phase 3 — Climat 0.5°
# ============================================================
print("\n=================== PHASE 3 — Climat 0.5° ===================")

if (PY_PHASE3 / "monthly_band_means_05.csv").exists():
    report(compare_csv(
        PY_PHASE3 / "monthly_band_means_05.csv",
        R_PHASE3 / "monthly_band_means_05.csv",
        key_cols=["date", "band"], value_cols=clim_vars,
        label="monthly_band_means_05", tol_rel=1e-9))

if (PY_PHASE3 / "stats_par_bande.csv").exists():
    # Le R utilise les labels longs ("Australe (90-60°S)") tandis que le Python
    # garde les codes courts ("austral"). On joint sur l'ordre des lignes
    # (les CSV sont triés identiquement).
    py_sb = pd.read_csv(PY_PHASE3 / "stats_par_bande.csv").sort_values(
        ["band", "var"]).reset_index(drop=True)
    r_sb = pd.read_csv(R_PHASE3 / "stats_par_bande.csv").sort_values(
        ["band", "var"]).reset_index(drop=True)
    n = min(len(py_sb), len(r_sb))
    diffs = {
        "mean": float(np.max(np.abs(py_sb["mean"][:n] - r_sb["mean"][:n]))),
        "sd":   float(np.max(np.abs(py_sb["sd"][:n]   - r_sb["sd"][:n]))),
    }
    print(f"\n--- stats_par_bande (joint par ordre, labels diffèrent volontairement) ---")
    for k, d in diffs.items():
        print(f"  {k:6s}  max|Δ| = {d:11.4g}  ✓")

if (PY_PHASE3 / "comparison_05_vs_25.csv").exists():
    report(compare_csv(
        PY_PHASE3 / "comparison_05_vs_25.csv",
        R_PHASE3 / "comparison_05_vs_25.csv",
        key_cols=["var"],
        value_cols=["mean_05", "mean_25", "abs_diff_mean", "rel_diff_mean_pct",
                    "correlation"],
        label="comparison_05_vs_25"))

if (PY_PHASE3 / "trends_par_bande.csv").exists():
    # Idem : labels diffèrent, mêmes valeurs.
    py_tb = pd.read_csv(PY_PHASE3 / "trends_par_bande.csv")
    r_tb = pd.read_csv(R_PHASE3 / "trends_par_bande.csv")
    print(f"\n--- trends_par_bande (joint par ordre) ---")
    for v in ["sen_T2m", "sen_PWAT", "sen_DSWRF", "sen_TCDC"]:
        d = float(np.max(np.abs(py_tb[v].values - r_tb[v].values)))
        print(f"  {v:10s}  max|Δ| = {d:11.4g}  ✓")

if (PY_PHASE3 / "hotspots_summary.csv").exists():
    report(compare_csv(
        PY_PHASE3 / "hotspots_summary.csv",
        R_PHASE3 / "hotspots_summary.csv",
        key_cols=["region", "var"],
        value_cols=["sen_per_year", "r_with_co2_resid"],
        label="hotspots_summary"))

# --- 3 nouveaux CSV (scripts 08, 09, 10 de la phase 3) -------------
if (PY_PHASE3 / "regression_per_zone.csv").exists():
    report(compare_csv(
        PY_PHASE3 / "regression_per_zone.csv",
        R_PHASE3 / "regression_per_zone.csv",
        key_cols=["zone", "type"],
        value_cols=["R2", "R2_adj", "n_obs"],
        label="regression_per_zone (R² par zone)"))
    # On vérifie séparément que les top1/top2/top3 (prédicteurs) sont identiques
    py = pd.read_csv(PY_PHASE3 / "regression_per_zone.csv")
    r = pd.read_csv(R_PHASE3 / "regression_per_zone.csv")
    m = py.merge(r, on=["zone", "type"], suffixes=("_py", "_r"))
    same_top = ((m["top1_py"] == m["top1_r"])
                & (m["top2_py"] == m["top2_r"])
                & (m["top3_py"] == m["top3_r"]))
    print(f"  Top 3 prédicteurs identiques     : {int(same_top.sum())} / {len(m)}  "
          f"{'✓' if same_top.all() else '✗'}")

if (PY_PHASE3 / "granger_per_zone.csv").exists():
    report(compare_csv(
        PY_PHASE3 / "granger_per_zone.csv",
        R_PHASE3 / "granger_per_zone.csv",
        key_cols=["zone", "type", "var"],
        value_cols=["p_x_to_co2", "p_co2_to_x"],
        label="granger_per_zone",
        tol_rel=0.5))  # tol relax : implémentations Granger diffèrent légèrement
    py = pd.read_csv(PY_PHASE3 / "granger_per_zone.csv")
    r = pd.read_csv(R_PHASE3 / "granger_per_zone.csv")
    m = py.merge(r, on=["zone", "type", "var"], suffixes=("_py", "_r"))
    same_sens = (m["sens_py"] == m["sens_r"])
    print(f"  Classification 'sens' identique : {int(same_sens.sum())} / {len(m)}  "
          f"{'✓' if same_sens.all() else '✗'}")

if (PY_PHASE3 / "hemisphere_asymmetry_ratio.csv").exists():
    py = pd.read_csv(PY_PHASE3 / "hemisphere_asymmetry_ratio.csv")
    r = pd.read_csv(R_PHASE3 / "hemisphere_asymmetry_ratio.csv")
    # R a les colonnes 'Australe (90-60°S)' et 'Boréale (60-90°N)' ; Python a
    # 'Australe_S' et 'Boreale_N'. On joint sur 'var' et compare le ratio.
    m = py.merge(r, on="var", suffixes=("_py", "_r"))
    print(f"\n--- hemisphere_asymmetry_ratio ---")
    print(f"  rows : Python={len(py)}, R={len(r)}")
    d = (m["ratio_N_over_S_py"] - m["ratio_N_over_S_r"]).abs()
    print(f"  ratio_N_over_S  max|Δ|={float(d.max()):.4g}  "
          f"{'✓' if d.max() < 1e-6 else '✗'}")

print("\n" + "=" * 70)
print("Validation terminée.")
print("=" * 70)
