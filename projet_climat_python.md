# Projet Climat — Migration R → Python & Tableau de Bord Interactif

## ✅ Résumé

Ce projet de **6 semaines** permet à des étudiants de confronter leurs compétences R acquises à un environnement Python, tout en les exposant à une véritable source de données climatiques opérationnelle.

La production d'un tableau de bord valorise leur travail et leur donne une expérience concrète de visualisation interactive. L'évaluation met l'accent sur la **qualité scientifique**, la **robustesse technique** et le **recul critique** sur les données.

> 📅 Les soutenances suivront les créneaux joints (voir fichier PDF).

---

## 🎯 Objectifs du projet

Les étudiants disposent d'un premier semestre de travail sous R (nettoyage, analyse exploratoire, modélisation simple) sur des données climatiques. L'objectif de ce projet est de :

1. **Migrer** l'intégralité du pipeline de R vers Python (`pandas`, `numpy`, `scikit-learn`, etc.) ;
2. **Utiliser** une source de données robuste et standardisée ;
3. **Produire** une visualisation interactive et valorisable via un tableau de bord ;
4. **Développer** un regard critique sur la qualité des données, leur acquisition, et les choix méthodologiques.

---

## 🗓️ Planning prévisionnel

| Semaine | Objectif principal | Livrable intermédiaire |
|---------|--------------------|------------------------|
| **1** | Choix de la question scientifique, acquisition des données, première lecture en Python | Notebook Jupyter + question validée |
| **2** | Nettoyage, gestion des valeurs manquantes et aberrantes (Python) | Script de preprocessing propre |
| **3** | Transformation, agrégation temporelle, *features engineering* | Dataset final prêt à analyser |
| **4** | Analyse exploratoire avancée et premières visualisations statiques | Figures et statistiques clés |
| **5** | Construction du tableau de bord interactif | Version locale fonctionnelle |
| **6** | Finalisation, test utilisateur, préparation de la soutenance | Soutenance orale (10 + 5 min) |

---

## ❓ Étape 1 — Question scientifique

Les étudiants doivent formuler une question **claire, vérifiable et spatialement/temporellement située**.

**Exemples :**

- Les vagues de chaleur sont-elles devenues plus longues et plus intenses en Europe de l'Ouest depuis 1980 ?
- Comment l'humidité du sol et la température interagissent-elles avant un épisode pluvieux extrême en Méditerranée ?

> ✅ **Critère d'évaluation :** pertinence scientifique et originalité relative.

---

## 📦 Étape 2 — Acquisition des données

- **Variables possibles :** température (2 m), précipitations, humidité relative, rayonnement solaire, vitesse du vent, pression, humidité du sol, couverture neigeuse, etc.

### Exigences techniques

- Téléchargement en **NetCDF** ou **GRIB**.
- Au moins **3 variables climatiques** différentes.
- Une **série temporelle continue** sur une zone géographique cohérente.

> ⚠️ Les étudiants doivent **documenter les éventuelles limites des données** (fréquence, résolution spatiale, lacunes, artefacts).

---

## 🔁 Étape 3 — Transition R → Python

Chaque traitement réalisé en R au premier semestre doit être réimplémenté en Python :

| Traitement R | Équivalent Python attendu |
|--------------|----------------------------|
| `dplyr` / `tidyr` | `pandas` (`groupby`, `pivot`, `melt`, `fillna`) |
| `ggplot2` | `matplotlib` + `seaborn` |
| `tsibble` / `forecast` | `pandas` avec datetimes, `statsmodels` |
| Détection valeurs aberrantes (boxplot, IQR) | IQR, z-score, visualisation |
| Gestion NA (imputation, suppression) | `pandas.DataFrame.interpolate`, `fillna`, `dropna` |

### Fichiers attendus

- `preprocessing.py` ou un notebook `01_preprocessing.ipynb` (propre, commenté).
- Un fichier `validation_quality.py` contenant :
  - Le taux de données manquantes par variable,
  - La détection d'anomalies,
  - Un résumé statistique avant/après.

---

## 📊 Étape 4 — Analyse et visualisation avancée

Chaque étudiant doit produire des visualisations pertinentes :

1. **Série temporelle** d'une variable clé avec tendance (moyenne mobile, lissage).
2. **Comparaison saisonnière** (boxplots par mois ou saison).
3. **Relation entre deux variables** (scatter, heatmap de corrélation).
4. **Carte ou évolution spatiale** (facultatif mais valorisé) : *contour plot*, heatmap sur coordonnées.

> 💡 L'évaluation porte aussi sur la **variété des variables** : ne pas se limiter à la température seule.

---

## 🖥️ Étape 5 — Tableau de bord interactif

### Contenu minimum

- Un **filtre temporel** (glissière ou sélecteur de dates).
- Un **sélecteur de variable(s)** (température, précipitations, etc.).
- Un **graphique interactif** (zoom, survol).
- Une **carte** (facultative mais fortement encouragée).
- Un **indicateur texte** (ex. : *« Nombre de jours > 30 °C en 2023 : XX »*).

---

## 🎤 Étape 6 — Soutenance orale

**Format :** 10 minutes de présentation + 5 minutes de questions.

### Structure conseillée (10 min)

| Temps | Contenu |
|-------|---------|
| 1 min | Question scientifique et zone d'étude |
| 2 min | Source des données et qualité perçue |
| 2 min | Pipeline R → Python : difficultés et choix |
| 3 min | Démonstration du tableau de bord (en direct) |
| 2 min | Résultats principaux et regard critique |

### Critères d'évaluation (grille indicative)

| Critère | Pondération |
|---------|-------------|
| Pertinence de la question scientifique | **25 %** |
| Variété des variables climatiques utilisées | **20 %** |
| Qualité du passage R → Python (code, rigueur) | **20 %** |
| Tableau de bord (fonctionnalité, ergonomie) | **20 %** |
| Regard critique sur les données / acquisition | **10 %** |
| Clarté de la présentation (10 + 5 min) | **5 %** |

---

## 📁 Livrables finaux

À déposer sur **Google Classroom** ou **GitHub Classroom**.

1. **Dépôt GitHub** contenant :
   - Notebook(s) Jupyter (nettoyage, analyse),
   - Scripts Python ,
   - `README.md` expliquant la question, les données, et comment lancer le dashboard.
2. **Fichier `qualite_donnees.md`** (ou `.txt`) listant :
   - Sources exactes (source, résolution, période),
   - Taux de *missing* par variable,
   - Anomalies détectées et leur traitement.
3. **Lien ou vidéo** (optionnel) de démonstration du tableau de bord.
4. **Supports de présentation** .
