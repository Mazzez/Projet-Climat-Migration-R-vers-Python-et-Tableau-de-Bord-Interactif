# Trame de soutenance — Climat & CO₂ (Migration R → Python + Dashboard interactif)

> **Format :** 10 min de présentation + 5 min de questions.
> **Trois supports, dans cet ordre :**
> 1. **SOUTENANCE.pptx** — présenter sources, variables, pipeline, résultats clés (5 min)
> 2. **Dashboard v2** (http://127.0.0.1:8088) — démonstration interactive (4 min)
> 3. **Notebooks Jupyter** — preuve technique R ↔ Python (1 min ou Q/R)

---

## ⏱️ Timeline détaillé (10 min)

| Temps | Support | Contenu |
|---|---|---|
| 0:00 → 0:30 | PPTX 01 | Titre + question scientifique |
| 0:30 → 2:00 | PPTX 02-03 | **Sources & formats** + **18 variables + 3 CRE** |
| 2:00 → 3:00 | PPTX 04 | Pipeline R→Python (équivalences + validation 10⁻¹³) |
| 3:00 → 5:30 | PPTX 05-07 | Phases 1 (CO₂), 2 (climat 2.5°), 3 (climat 0.5° + hotspots) |
| 5:30 → 6:30 | PPTX 08 | Regard critique — saut CFSR→CFSv2 |
| 6:30 → 9:00 | **Dashboard v2** | Démonstration live des 6 sections cinématiques |
| 9:00 → 9:30 | Notebooks | Ouvrir 1 notebook si Q technique (validation, MK, Lasso) |
| 9:30 → 10:00 | PPTX 10 | Take-away : 3 résultats robustes + limites |

---

## 🎯 Question scientifique

**À l'échelle globale, sur 1979-2025, quelle est la nature du lien statistique entre le climat de surface et la concentration atmosphérique de CO₂ ?**

- **Échelle séculaire** : trend monotone partagée → corrélations brutes fortes mais en partie spurieuses.
- **Échelle interannuelle** : signal propre. Question : qui précède qui ?

**Hypothèse testée** : à l'échelle interannuelle, le climat précède le CO₂ (et non l'inverse). Validée par tests de Granger (lag = 6 mois).

---

## 📊 Phase 1 — Présentation PowerPoint (`SOUTENANCE.pptx`)

Ouvrir avec LibreOffice Impress ou PowerPoint. Slides en format 16:9, palette cosmic climate cohérente avec le dashboard.

### Slide 01 — Titre
- Migration R → Python + Tableau de bord interactif
- Question scientifique en sous-titre

### Slide 02 — Sources & formats (point clé du cahier des charges)
- **8 sources** : NOAA GML, Mauna Loa, Vostok, GCB, ENSO, CFSR/CFSv2 (2.5°), CFSR/CFSv2 (0.5°)
- **4 formats** : CSV, GRIB2 (60 Go au total), NetCDF (issu de wgrib2), Pickle
- 0 NA après filtrage sur les 18 variables × 564 mois

### Slide 03 — Variables retenues
- **18 variables brutes** CFSR/CFSv2 (T2m, T500, SPFH2m, PWAT, APCP, TCDC, DLWRF, ULWRF, DSWRF, USWRF, PRMSL, CSDSF/CSUSF/CSDLF/CSULF, CDUVB, DUVB, ALBDO)
- **3 indicateurs dérivés** Cloud Radiative Effect (CRE_SW, CRE_LW, CRE_net) — formules explicites
- Cohérence physique : T2m global = 287.9 K, CRE_net = -19.7 W/m² (conforme IPCC -20 W/m²)

### Slide 04 — Pipeline R → Python
- 8 équivalences clés (dplyr→pandas, ggplot→matplotlib, forecast→statsmodels, glmnet→sklearn, …)
- **Validation** : `tests/validate_vs_r.py` → précision relative max **10⁻¹³** sur tous les CSV
- 3× plus rapide que R sur la phase 2.5°

### Slide 05 — Phase 1 (CO₂)
- Pente Sen **+1.881 ppm/an** [IC95 bootstrap 1.78 – 1.97]
- **+89 ppm cumulés** sur 47 ans (336.86 → 425.64 ppm)
- Modèle exponentiel privilégié par AIC (doublement à 137 ans)
- Hausse moderne **30× plus rapide** que tout pic paléo Vostok (414 ka BP)
- Effet COVID-19 : -0.4 ppm cumulé, marginal (fraction airborne ≈ 53 % stable)

### Slide 06 — Phase 2 (Climat 2.5°)
- 5 représentations temporelles : `level` / `anom` / `resid` / `d1` / `d12`
- Top 5 corrélations résidus : CRE_LW −0.523, CRE_SW +0.489, DSWRF +0.437, CRE_net +0.432, PRMSL −0.394
- **Granger d12 lag 6 mois : 15/21 X → CO₂ significatifs**
- **R² = 0.748** sur modèle multivarié Newey-West (12 variables)
- **CSDLF +7.84 W/m² sur 47 ans** = signature directe du forçage GES

### Slide 07 — Phase 3 (Climat 0.5°)
- Cartes pixel-par-pixel : 259 920 pixels × 564 mois × 18 vars
- **Amplification arctique 4×** (Sen boréal 0.052 K/an vs global 0.017 K/an)
- 4 hotspots : Sahel, Sibérie centrale, Amazonie, Indonésie
- R² par zone : global 0.75, tropical 0.69, boréal 0.28, Amazonie 0.04
- **Validation 0.5° vs 2.5°** : corrélations 0.9999-1.0000

### Slide 08 — Regard critique
- Saut CFSR→CFSv2 (jan 2011) **affecte 17/21 variables** (p < 0.05)
- Top jumps : CRE_LW -1.92 sd, PRMSL -1.77 sd, CRE_SW +1.56 sd, TCDC +1.14 sd
- **R² 0.748 → 0.46** après homogénéisation
- **Mais T2m et CSDLF gagnent en corrélation** → signature GES démasquée

### Slide 09 — Dashboard v2
- Stack : React 18 + Three.js 0.158 + Babel in-browser, pas de bundler
- 6 sections cinématiques, globe NASA Blue Marble interactif
- 36 grilles scientifiques réelles exportées du pipeline (18 vars × 2 modes)

### Slide 10 — Conclusions
- 3 résultats robustes + limites + perspectives

---

## 🌐 Phase 2 — Démonstration Dashboard v2

### Lancement (à faire avant la soutenance)

```bash
cd "/home/mazzez/Bureau/ESSAI/1er année/Programmation Mathematique/Projet/dashboard-v2"
python3 -m http.server 8088
# Ouvrir http://127.0.0.1:8088
```

### Scénario de démo (4 min, 6 sections)

#### Section 01 — Hero (30 s)
- Globe 3D fullscreen avec texture NASA Blue Marble
- 4 KPI vivants : **+1.881 ppm/an** · **+0.78 K** · **4.0× amplif arctique** · **30× vs paléo**
- Titre : **+89 ppm en 47 ans**

#### Section 02 — Trajectoire CO₂ (40 s)
- Courbe NOAA GML 1979-2025 (vraies 564 valeurs)
- 3 modèles superposés (linéaire / quadratique / cubique) — montrer toggle
- Timeline événements cliquable : Pinatubo, El Niño 97, Kyoto, Paris, COVID, Hunga Tonga

#### Section 03 — Earth 3D interactif (60 s, **temps fort**)
- Sélecteur 18 variables × 2 modes (Sen / Corr CO₂)
- **Badge RÉEL** confirme que les données viennent du pipeline 0.5°
- Démos rapides : T2m (amplification arctique) → PRMSL (déformation pressions) → CSDLF (forçage GES)
- Cliquer un hotspot → drawer avec Granger + R² + tendances par variable

#### Section 04 — Lien climat ↔ CO₂ (45 s)
- Heatmap 21 vars × 5 représentations — onglet `Résidus` pour révéler le top 5
- Sankey Granger : 10 X→CO₂, 5 bidirectionnels, 3 CO₂→X, 3 aucun
- Panneau pédagogie : différence entre level (trend partagée) et resid (signal réel)

#### Section 05 — Hotspots & amplification (30 s)
- 4 mini-globes positionnés sur Sahel / Sibérie / Amazonie / Indonésie
- Thermomètre amplification arctique par bande latitude
- Radar R² par zone : tropical/boreal forts, Amazonie/Sahel faibles

#### Section 06 — Critique (35 s)
- Timeline interactive saut CFSR/CFSv2 (cliquer les 5 lignes)
- 3 cartes limites : détendrage, échelle globale, instruments
- Sources bibliographiques

---

## 📓 Phase 3 — Notebooks (preuve technique)

4 notebooks Jupyter dans `notebooks/` + 4 PDFs correspondants :

| Notebook | Contenu | Quand l'ouvrir |
|---|---|---|
| `01_preprocessing.ipynb` | Pipeline pré-traitement + QA + détection NA | Q sur la qualité des données |
| `02_phase1_co2.ipynb` | Caractérisation CO₂ : STL, ARIMA, Mann-Kendall, bootstrap | Q sur les méthodes statistiques |
| `03_phase2_climat_25.ipynb` | Climat global 2.5°, 5 représentations, Granger, Lasso, Newey-West | Q sur les corrélations / causalité |
| `04_phase3_climat_05.ipynb` | Climat régional 0.5°, cartes pixel, hotspots, validation 0.5°↔2.5° | Q sur les cartes / la résolution |

Les PDFs sont prêts à présenter (mise en page propre, figures incluses).

---

## ❓ Q/R fréquentes

**Q : Pourquoi 5 représentations temporelles ?**
R : La même paire (X, CO₂) peut avoir 5 corrélations très différentes selon la statistique d'intérêt.
- `level` capte la trend séculaire (souvent spurieuse)
- `anom` retire la saisonnalité
- `resid` retire aussi la trend → c'est le test de robustesse
- `d1` est sensible à la variation mois-à-mois (saisonnalité)
- `d12` est le taux annuel → c'est la base pour les tests de Granger

**Q : Pourquoi la corrélation TCDC ↔ CO₂ = 0.76 sur les niveaux mais 0.08 sur les résidus ?**
R : Cas typique de corrélation spurieuse. Le saut CFSR/CFSv2 sur TCDC (+4.3 % en 2011) coïncide avec la trend CO₂. Une fois désaisonné + détendré + homogénéisé, le lien réel à l'échelle interannuelle est très faible.

**Q : Comment savez-vous que c'est climat → CO₂ et pas l'inverse ?**
R : Test de Granger sur d12 (taux annuel) avec lag 6 mois. **15 variables ont X → CO₂ significatif** (p < 0.05) ; 5 sont bidirectionnelles ; seulement 3 sont CO₂ → X strict. Le sens dominant est confirmé par la corrélation taux annuel CO₂ ↔ ONI (ENSO) à lag 6 mois = +0.28.

**Q : Comment avez-vous validé la migration R → Python ?**
R : Script `tests/validate_vs_r.py` qui compare chaque CSV produit par Python à celui produit par R. Précision relative max **10⁻¹³** sur les moyennes pondérées et corrélations ; **10⁻¹⁰** sur les bootstraps Sen (différence inhérente aux générateurs aléatoires).

**Q : Quelle est la principale limite de ce travail ?**
R : 
1. Détendrage linéaire alors que la trend CO₂ est cubique → courbure résiduelle (amélioration : GAM ou splines).
2. Résolution globale 2.5° qui masque les puits/sources tropicaux (résolu en partie par la Phase 3 à 0.5°).
3. Sauts artefactuels CFSR/CFSv2 documentés mais inévitables (on fournit la version homogénéisée à titre de robustesse).
4. On ne fait pas d'attribution causale physique, seulement statistique au sens de Granger.

**Q : Pourquoi le dashboard v2 utilise React + Three.js sans bundler ?**
R : Pour avoir une démo entièrement statique servie par `python -m http.server`, sans dépendre de `npm install` ou Node.js. Babel transpile les `.jsx` en live dans le navigateur. Le coût (cache miss à chaque modif) est anecdotique pour un dashboard ; le bénéfice (zéro setup pour l'évaluateur) est majeur.

**Q : Comment les grilles affichées sur le globe sont-elles obtenues ?**
R : `scripts/phase3_climat_05/export_grids_for_dashboard.py` lit les pickles `outputs/phase3_climat_05/{trend,correlation}_grids.pkl` (résolution native 720 × 361, float32), fait un block-mean 20 × 20 pour descendre à 36 × 18, calcule les bornes percentile 1/99 symétrisées par variable, et sérialise un seul JSON de 191 KB chargé au démarrage du dashboard. Badge **RÉEL** ↔ **APPROX** indique à l'utilisateur s'il regarde des données pipeline ou une approximation.

---

## 📋 Checklist pré-soutenance

- [ ] `SOUTENANCE.pptx` ouvert dans LibreOffice Impress (ou PowerPoint en backup)
- [ ] Serveur dashboard lancé : `cd dashboard-v2 && python3 -m http.server 8088 &`
- [ ] Navigateur Firefox/Chrome ouvert sur http://127.0.0.1:8088
- [ ] Tester chaque section du dashboard (sélecteur variable, slider année, clic hotspot)
- [ ] 4 notebooks PDFs accessibles dans `notebooks/`
- [ ] Laptop chargé + adaptateur HDMI
- [ ] Transitions répétées (passer du PPTX au dashboard sans switching pénible)
- [ ] Backup : si problème de réseau, la texture NASA Blue Marble du globe ne charge pas. Avoir une capture écran de secours.

---

## 🎯 Take-away final (slide 10)

**Trois résultats robustes :**

1. **Les corrélations brutes sont trompeuses.** 11 variables sur 21 ont |r| > 0.4 sur les niveaux mais perdent ce lien sur les résidus → trend séculaire partagée.

2. **5 variables sont réellement actives** à l'échelle interannuelle (CRE_LW, CRE_SW, DSWRF, CRE_net, PRMSL). 15/21 causent Granger le CO₂ au lag 6 mois — sens dominant **climat → CO₂**.

3. **Une partie est artefact.** Saut CFSR→CFSv2 jan 2011 affecte 17/21 vars. Après homogénéisation, R² 0.75 → 0.46. T2m et CSDLF gagnent en corrélation → signature directe du forçage GES démasquée.

**Migration validée à 10⁻¹³ près. Pipeline reproductible. Dashboard servi en zéro setup.**
