#!/usr/bin/env bash
# Lance toute la chaîne de traitement Python (3 phases) + dashboard.
# Suppose que les NetCDF subsets sont déjà générés sous Data/processed/.
#
# Durées attendues (Linux, SSD, 16 Go RAM, Python 3.12) :
#   Phase 1 (CO2)         ~3 min
#   Phase 2 (Climat 2.5°) ~10 min
#   Phase 3 (Climat 0.5°) ~30-60 min (cartes pixel-par-pixel)
#   Validation Python/R   <1 min
#
# Stop dès qu'une étape échoue.

set -euo pipefail

PROJ_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJ_DIR"

if [[ ! -d venv ]]; then
  echo "Création du venv (Python 3.12 requis via pyenv ou système)..."
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
else
  source venv/bin/activate
fi

echo "==================== PHASE 1 — CO2 ===================="
python scripts/phase1_co2/01_co2_basic.py
python scripts/phase1_co2/02_co2_extended.py
python scripts/phase1_co2/03_co2_methodology.py

echo "==================== PHASE 2 — Climat 2.5° ===================="
python scripts/phase2_climat_25/02_global_means.py
python scripts/phase2_climat_25/03_validation.py
python scripts/phase2_climat_25/04_merge_with_co2.py
python scripts/phase2_climat_25/05_preparation.py
python scripts/phase2_climat_25/06_correlations.py
python scripts/phase2_climat_25/07_regressions.py
python scripts/phase2_climat_25/08_granger.py
python scripts/phase2_climat_25/09_synthese.py
python scripts/phase2_climat_25/10_per_variable_analysis.py
python scripts/phase2_climat_25/11_trends_summary.py
python scripts/phase2_climat_25/12_homogenization.py
python scripts/phase2_climat_25/13_phase3_homog_comparison.py

echo "==================== PHASE 3 — Climat 0.5° ===================="
python scripts/phase3_climat_05/02_band_means.py
python scripts/phase3_climat_05/03_validation.py
python scripts/phase3_climat_05/04_05_trend_and_corr_maps.py
python scripts/phase3_climat_05/06_hotspot_analysis.py
python scripts/phase3_climat_05/07_compare_with_25deg.py

echo "==================== Rapport qualité ===================="
python scripts/validation_quality.py

echo "==================== Validation Python vs R ===================="
python tests/validate_vs_r.py

echo ""
echo "Pipeline terminé. Pour lancer le dashboard :"
echo "  source venv/bin/activate"
echo "  python dashboard/app.py"
echo "  → http://127.0.0.1:8050"
