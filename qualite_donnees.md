# Qualité des données — Projet Climat & CO2 (migration R → Python)

## 1. Sources des données

| Dataset | Source | Période | Résolution | Volume |
|---|---|---|---|---|
| CO2 mondial mensuel | NOAA GML | 1979-01 → 2025-12 | mensuel, global | 24 ko |
| CO2 Mauna Loa | NOAA / SIO | 1958-03 → 2026-02 | mensuel, station | 23 ko |
| CO2 South Pole flask | NOAA | 1975-07 → 2024-12 | mensuel, station | 13 ko |
| CO2 paléo Vostok | NOAA Paleoclimatology | 414 ka → 2 ka BP | non régulier (n=283) | 8 ko |
| Émissions fossiles | Global Carbon Budget 2025v15 | 1750 → 2024 | annuel, par source | 35 ko |
| ENSO Niño 3.4 (ONI) | NOAA CPC | 1950 → présent | trimestriel glissant | 19 ko |
| Réanalyses CFSR (1979-2010) + CFSv2 (2011-2026) | NCAR (NCEP) | 1979-01 → 2026-03 | 2.5° × 2.5° (144×73) | 3.5 Go GRIB |
| Réanalyses haute résolution | NCAR (NCEP) | 1979-01 → 2026-03 | 0.5° × 0.5° (720×361) | 57 Go GRIB |

Pour les deux résolutions, on extrait par `wgrib2` les **18 mêmes records GRIB2**
(mêmes codes paramètres NCEP — vérifié par `14_verify_grib_codes.sh` :
18/18 records identiques entre CFSR et CFSv2).

## 2. Variables retenues (18 + 3 dérivées)

| # | Code | Niveau | Famille |
|---|---|---|---|
| 1 | T2m | 2 m above ground | Thermo air surface |
| 2 | T500 | 500 hPa | Thermo mid-troposphère |
| 3 | SPFH2m | 2 m above ground | Humidité spécifique |
| 4 | PWAT | colonne entière | Vapeur d'eau intégrée |
| 5 | APCP | surface | Précipitations cumulées |
| 6 | TCDC | colonne entière | Couverture nuageuse totale |
| 7 | DLWRF | surface | LW descendant (effet de serre) |
| 8 | ULWRF | surface | LW ascendant |
| 9 | DSWRF | surface | SW descendant |
| 10 | USWRF | surface | SW réfléchi |
| 11 | PRMSL | mean sea level | Pression réduite |
| 12-15 | CSDSF / CSUSF / CSDLF / CSULF | surface | Flux clear-sky |
| 16-17 | CDUVB / DUVB | surface | UV-B clear-sky / all-sky |
| 18 | ALBDO | surface | Albédo de surface |

**Indicateurs dérivés** (recalculés par Python depuis les flux radiatifs) :

```
CRE_SW  = (DSWRF − USWRF) − (CSDSF − CSUSF)
CRE_LW  = (DLWRF − ULWRF) − (CSDLF − CSULF)
CRE_net = CRE_SW + CRE_LW
```

## 3. Taux de données manquantes

### Pipeline 2.5° (`monthly_global_means_25.csv`)
**0 NA / 564 mois × 18 variables** = pipeline GRIB→NetCDF→moyennes pondérées
sans perte. Les CRE dérivés sont calculés à partir des flux complets, donc
0 NA aussi.

Pour les 5 représentations dérivées (`series_*.csv`) :
- `level`, `anom`, `resid` : 0 NA
- `d1` : 1 NA (1ère ligne, pas de différence définie)
- `d12` : 12 NA (12 premiers mois)

### Pipeline 0.5° (`monthly_band_means_05.csv`)
**0 NA / 566 mois × 6 bandes × 18 variables** = 61 128 valeurs sans manquant.

### CO2 NOAA (`co2_mm_gl.csv`)
**0 NA** sur la période 1979-01 → 2025-12.

### CO2 Mauna Loa (`co2_mm_mlo.csv`)
Le fichier source utilise `-9.99` ou `-99.99` comme code de valeur manquante.
Notre loader les remplace par `NaN`. Sur 1958-03 → 2026-02 (816 mois) :
- `mlo_avg` : 7 NA (mois manquants début 1958-1964)
- `mlo_deseason` : idem

### South Pole flask
571 mois 1975-07 → 2024-12 ; pas de valeurs manquantes après filtrage
(le loader rejette les lignes où `spo_avg` n'est pas un nombre).

### GCB / Vostok / ONI
Aucun NA après filtrage (`Country == Global` pour GCB, etc.).

## 4. Anomalies détectées

### 4.1 Discontinuité CFSR → CFSv2 (jan 2011)

Le passage du modèle CFSR (1979-2010) au modèle CFSv2 (≥2011) introduit un
saut de niveau **significatif sur 17/21 variables** (test de step
dans `lm(y ~ t + step + month)`, p < 0.05) :

| Variable | Saut (sd) | jump_pct | Sens |
|---|---|---|---|
| CRE_LW | -1.92 | -8.0 % | nuages : moins de réchauffement LW |
| PRMSL | -1.77 | -0.026 % | pression : -26 Pa |
| CRE_SW | +1.56 | -11.4 % | nuages : moins de refroidissement SW |
| TCDC | +1.14 | +4.3 % | nuages : ~3 % plus de couverture |
| CRE_net | +1.13 | -15.7 % | bilan radiatif net |

**Impact méthodologique** : sur la version brute, le R² du modèle multivarié
CO2~climat (résidus) est de **0.75**. Après homogénéisation
(modèle additif `y ~ t + step + month` puis correction du saut sur ≥2011),
le R² chute à **0.46**. **Un tiers de la variance explicative était portée
par ce seul artefact technique**.

**Décision** : on conserve la **série brute comme version de référence**
mais on fournit aussi `monthly_global_means_25_homog.csv` et le tableau
de comparaison `comparison_homog_correlations.csv`. La conclusion T2m+CSDLF
↔ CO2 (signature directe du forçage GES) est **renforcée** par
l'homogénéisation (corrélations résiduelles passent de 0.23 à 0.35 pour T2m,
de 0.24 à 0.30 pour CSDLF).

### 4.2 Données paléo (Vostok)
Forte irrégularité temporelle (résolution variable selon profondeur de
carotte glaciaire). On conserve tous les points ; on ne fait pas de
ré-interpolation : les conclusions reposent sur la simple comparaison de
**plages** (paléo : 182-298 ppm vs moderne : 425 ppm).

### 4.3 Effet COVID-19
Anomalie cumulée modérée (~ -0.4 ppm sur 2020-2021), inférieure à la
détection statistique de pré-2020 ARIMA (en deçà de la bande IC 80%).
Conclusion : **effet COVID-19 mesurable mais marginal** dans le signal
atmosphérique global, ce qui est cohérent avec le fait que la fraction
airborne (53 %) reste à peu près constante d'année en année.

## 5. Validation croisée 0.5° vs 2.5°

Comparaison des moyennes globales calculées indépendamment (script 07
de la phase 3) :

- **Toutes les corrélations 0.5° vs 2.5° = 0.9999-1.0000**
- Écarts relatifs moyens < 0.15 %, max < 0.4 %

Ces résultats valident à la fois :
- la cohérence du sous-échantillonnage spatial (fact 5x sur chaque axe)
- l'identité physique des codes GRIB2 entre les deux fichiers source
  (pgbl04 et pgbh04)
- la robustesse des moyennes pondérées cos(lat) implémentées en
  `climat.preprocess.weighted_mean_2d`.

## 6. Validation croisée Python vs R

Tests automatisés (`tests/validate_vs_r.py`) sur chaque CSV produit par
les deux pipelines :

| Sortie | Précision relative max |
|---|---|
| `monthly_global_means_25.csv` (564 × 18) | 5×10⁻¹⁵ |
| `monthly_band_means_05.csv` (3396 × 18) | 2×10⁻¹⁴ |
| `cre_monthly_25.csv` | 1×10⁻¹³ |
| `correlations_4repr.csv` | 3×10⁻¹² |
| `synthese_finale.csv` | 3×10⁻¹² |
| `trends_summary.csv` | 4×10⁻¹⁰ |
| `cfsr_to_cfsv2_jumps.csv` | 8×10⁻¹² |
| `comparison_05_vs_25.csv` | 5×10⁻¹⁰ |

**Conclusion** : la migration R → Python n'introduit aucune dérive numérique
au-delà de la précision flottante (~10⁻¹³ pour les moyennes, ~10⁻¹⁰ pour
les Sen avec bootstrap qui dépend du seed).

## 7. Limites identifiées

1. **Détendrage linéaire** alors que la trend CO2 est cubique : il reste une
   courbure résiduelle en U dans le fit du modèle stepwise.
   Amélioration possible : détendrage cubique ou GAM.
2. **Corrélations sur résidus modérées** (|r| ≤ 0.5) : à l'échelle globale,
   le CO2 répond surtout aux puits/sources tropicaux (Amazonie, Indonésie)
   qui ne sont pas explicitement résolus dans une moyenne globale 2.5°.
3. **Discontinuité CFSR → CFSv2** : visible sur TCDC (~3 %), CRE_LW (~ -2 sd),
   PRMSL (~ -1.8 sd). On la documente et on fournit la version homogénéisée
   à titre de robustesse.
4. **Mann-Kendall en 0.5° sur sous-échantillon** : pour des raisons de coût
   (259 920 pixels × 564 mois × 18 vars), la p-value MK est calculée
   sur 1 pixel sur 16 (step=4 sur chaque axe). La carte de pente Sen,
   en revanche, est calculée sur tous les pixels via la régression OLS
   vectorisée — c'est cohérent avec la méthode du R d'origine.
5. **Période** : le subset 0.5° contient 2 mois de plus que le 2.5°
   (jusqu'à 2026-03). On utilise la fenêtre commune (1979-01 → 2025-12)
   pour les comparaisons.

## 8. Reproductibilité

Tous les scripts Python sont déterministes pour les seeds explicites
(bootstrap Sen, lasso CV) ; les méthodes intrinsèquement non-déterministes
(rolling-origin ARIMA) utilisent un sous-échantillonnage régulier
(1 origine sur 6) qui ne dépend pas du seed.

Les hashes md5 des fichiers de sortie sont stables d'une exécution à l'autre
sur la même machine.
