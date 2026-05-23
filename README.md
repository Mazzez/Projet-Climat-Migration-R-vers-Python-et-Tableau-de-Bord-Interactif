# Projet Climat & CO2 — Migration R → Python + Dashboard interactif

> ESSAI 1A — Programmation Mathématique 2025-2026 .

Migration **exhaustive** du pipeline R climat & CO2 du premier semestre vers
un environnement Python (pandas / numpy / xarray / statsmodels / scikit-learn)
et exposition des résultats dans un **tableau de bord Dash interactif**.

## ✅ Ce que fait ce projet

- **Phase 1 — CO2** (`scripts/phase1_co2/`) : analyse statistique complète
  du CO2 NOAA GML 1979-2025 (23 sections, 30 PNG + 7 CSV). Comparaison
  Mauna Loa, GCB, Vostok, ENSO. Modèles : STL, ARIMA, modèle exponentiel,
  state-space (Kalman), Mann-Kendall + Sen + bootstrap, ruptures.
- **Phase 2 — Climat 2.5°** (`scripts/phase2_climat_25/`) : extraction
  18 variables × 564 mois depuis CFSR/CFSv2, moyennes globales pondérées
  cos(lat), 5 représentations temporelles, corrélations multivariées,
  régression stepwise + lasso, Granger, homogénéisation CFSR→CFSv2.
- **Phase 3 — Climat 0.5°** (`scripts/phase3_climat_05/`) : moyennes par
  5 bandes de latitude, **cartes pixel-par-pixel** de tendance Sen + corr
  CO2 résiduel, **4 hotspots régionaux** (Amazonie, Indonésie, Sibérie,
  Sahel), validation croisée vs le 2.5°.
- **Dashboard Dash** (`dashboard/app.py`) : 6 onglets interactifs avec
  filtre temporel, sélecteur de variable, graphiques Plotly, indicateurs.
- **Validation croisée** (`tests/validate_vs_r.py`) : précision numérique
  ~10⁻¹³ vs les CSV R sur **toutes** les sorties intermédiaires.

## 🎯 Question scientifique

> **À l'échelle globale et sur la période 1979-2025, quelle est la nature
> du lien statistique entre les variables climatiques de surface
> (température, humidité, flux radiatifs, nuages) et la concentration
> atmosphérique de CO2 ?**

**Trois résultats principaux :**
1. **Les corrélations brutes sont trompeuses** : 11 variables sur 21 ont
   |r| > 0.4 sur les niveaux mais perdent ce lien sur les résidus
   (anomalies désaisonnées + détendrées). Elles partagent simplement la
   trend séculaire commune.
2. **À l'échelle interannuelle** (résidus + d12), seules **5 variables**
   ont un lien réel : CRE_LW (-0.52), CRE_SW (+0.49), DSWRF (+0.44),
   CRE_net (+0.43), PRMSL (-0.39). **15/21 variables causent
   significativement le CO2** au sens de Granger (lag 6 mois) — sens
   dominant : **climat → CO2**.
3. **Une partie des corrélations brutes est artefactuelle** : le
   changement de modèle CFSR→CFSv2 en jan 2011 introduit un saut
   significatif sur 17/21 variables. Après homogénéisation, le R² du
   modèle multivarié passe de 0.75 à 0.46. Les variables thermo (T2m,
   CSDLF) **gagnent** au contraire en corrélation après correction →
   signature directe du forçage GES démasquée.

## 📁 Structure

```
Projet/
├── README.md                ← ce fichier
├── qualite_donnees.md       ← sources, NA, anomalies, limites
├── requirements.txt
├── projet_climat_python.md  ← cahier des charges
│
├── climat/                  ← package partagé (loaders, prétraitement, stats, plots)
│   ├── config.py
│   ├── io.py
│   ├── preprocess.py
│   ├── stats.py
│   └── plots.py
│
├── scripts/
│   ├── phase1_co2/
│   │   ├── 01_co2_basic.py            # sections 1-8
│   │   ├── 02_co2_extended.py         # sections 9-11 (MLO, GCB, Vostok)
│   │   └── 03_co2_methodology.py      # sections 12-23 (A1-A5 + B1-B7)
│   ├── phase2_climat_25/
│   │   ├── 01_extract_subset.sh       # GRIB subset → NetCDF
│   │   ├── 02_global_means.py
│   │   ├── 03_validation.py
│   │   ├── 04_merge_with_co2.py
│   │   ├── 05_preparation.py
│   │   ├── 06_correlations.py
│   │   ├── 07_regressions.py
│   │   ├── 08_granger.py
│   │   ├── 09_synthese.py
│   │   ├── 10_per_variable_analysis.py
│   │   ├── 11_trends_summary.py
│   │   ├── 12_homogenization.py
│   │   ├── 13_phase3_homog_comparison.py
│   │   ├── 14_verify_grib_codes.sh
│   │   └── 15_extract_grib_subset.sh
│   └── phase3_climat_05/
│       ├── 01_extract_subset.sh
│       ├── 02_band_means.py
│       ├── 03_validation.py
│       ├── 04_05_trend_and_corr_maps.py  # version combinée optimisée
│       ├── 06_hotspot_analysis.py
│       ├── 07_compare_with_25deg.py
│       └── 15_extract_grib_subset.sh
│
├── outputs/                 ← générés par les scripts
│   ├── phase1_co2/          # 30 PNG + 7 CSV
│   ├── phase2_climat_25/    # ~106 PNG + 19 CSV + plots/ + per_variable/
│   ├── phase3_climat_05/    # 36 cartes + plots/ + 6 CSV + 2 pickles
│   └── validation_quality_report.txt + validation_quality.csv
│
├── dashboard/
│   └── app.py               # Dash, port 8050 — 6 onglets + cartes interactives
│
├── notebooks/
│   ├── 01_preprocessing.ipynb        # Pipeline pré-traitement + QA
│   ├── 02_phase1_co2.ipynb           # Phase 1 : caractérisation CO2 1979-2025
│   ├── 03_phase2_climat_25.ipynb     # Phase 2 : climat global 2.5° ↔ CO2
│   └── 04_phase3_climat_05.ipynb     # Phase 3 : climat régional 0.5° + hotspots
│
└── tests/
    └── validate_vs_r.py     # comparaison avec les CSV R d'origine
```

## 🚀 Lancer

```bash
# 1. Setup
cd Projet
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. (Optionnel — si les NetCDF subsets ne sont pas générés)
bash scripts/phase2_climat_25/15_extract_grib_subset.sh
bash scripts/phase2_climat_25/01_extract_subset.sh
bash scripts/phase3_climat_05/15_extract_grib_subset.sh
bash scripts/phase3_climat_05/01_extract_subset.sh

# 3. Pipelines (peuvent tourner en parallèle, indépendants)
# Phase 1 : ~3 min
python scripts/phase1_co2/01_co2_basic.py
python scripts/phase1_co2/02_co2_extended.py
python scripts/phase1_co2/03_co2_methodology.py

# Phase 2 : ~10 min
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

# Phase 3 : ~30-60 min (cartes pixel-par-pixel)
python scripts/phase3_climat_05/02_band_means.py
python scripts/phase3_climat_05/03_validation.py
python scripts/phase3_climat_05/04_05_trend_and_corr_maps.py
python scripts/phase3_climat_05/06_hotspot_analysis.py
python scripts/phase3_climat_05/07_compare_with_25deg.py

# 4. Dashboard
python dashboard/app.py
# → http://127.0.0.1:8050

# 5. Validation Python vs R
python tests/validate_vs_r.py
```

## 📊 Tableau de bord

Six onglets :
1. **Vue d'ensemble** — CO2 + climat + corrélations + tendances (sélecteur
   variable + slider temporel)
2. **CO2 (Phase 1)** — série complète, taux annuel, perspective Vostok
3. **Climat global 2.5°** — série + MA12, CRE, sauts CFSR/CFSv2
4. **Régional 0.5°** — anomalies T2m par bande, hotspots,
   **cartes interactives** (tendance Sen / corrélation CO2 résiduel) avec
   les 4 hotspots surimposés
5. **Climat ↔ CO2** — corrélations 5 représentations + Granger
6. **Critique / qualité** — sanity checks, limites, sauts

Indicateurs (KPI) : période, hausse CO2, réchauffement T2m, nb variables.

## 🔬 Validation Python vs R

`python tests/validate_vs_r.py` compare chaque CSV produit par Python à
celui produit par R. Précision relative typique : **10⁻¹³** sur les
moyennes pondérées, **10⁻¹⁰** sur les Sen avec bootstrap (différence
inhérente aux RNG).

## 📚 Références

- Cahier des charges : `projet_climat_python.md`
- Sources des données : `qualite_donnees.md`
- Pipeline R d'origine : `/home/mazzez/Bureau/R project/Final Version/`
