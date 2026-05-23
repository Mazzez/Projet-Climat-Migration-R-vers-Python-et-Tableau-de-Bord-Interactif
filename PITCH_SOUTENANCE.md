# Pitch de soutenance — Climat & CO₂

> **Durée cible : 10 minutes.** Indications de support à l'écran en `[SUPPORT]`.
> Le pitch suit exactement l'ordre de `SOUTENANCE.md` : PowerPoint → Dashboard → Notebooks.

---

## 🎬 Ouverture (~30 s)

`[PPTX — SLIDE 01 · Titre]`

Bonjour, je vais vous présenter mon travail sur la migration en Python du pipeline d'analyse climat-CO₂, et le tableau de bord interactif qui en résulte.

La question scientifique est la suivante : à l'échelle globale, sur la période 1979 – 2025, **quelle est la nature du lien statistique entre les variables climatiques de surface et la concentration atmosphérique de CO₂** ?

Tout le monde admet qu'il existe une corrélation forte. Mais cette corrélation est-elle réelle, ou simplement portée par une tendance commune ? Et surtout : à l'échelle interannuelle, qui précède qui — le climat ou le CO₂ ?

Pour répondre, j'ai mobilisé huit sources de données et dix-huit variables climatiques, sur quarante-sept ans.

---

## 📊 Partie 1 — PowerPoint (~5 minutes)

### Slide 02 — Sources et formats (~1 min)

`[PPTX — SLIDE 02]`

Le projet repose sur huit sources de données, quatre formats de fichier, et environ soixante gigaoctets de données brutes.

Trois ensembles dominent. **Premièrement**, la série de CO₂ mensuel global de la NOAA GML, de janvier 1979 à décembre 2025 — c'est notre série de référence. **Deuxièmement**, les réanalyses météorologiques CFSR et CFSv2 du NCAR, en résolution 2.5° puis 0.5° — c'est le gros volume, cinquante-sept gigaoctets de GRIB2 pour la haute résolution. **Troisièmement**, des sources de contextualisation : Mauna Loa, le pôle Sud, la carotte de Vostok pour le paléoclimat, le Global Carbon Budget pour les émissions, et l'indice ENSO.

Le flux technique est le suivant : les GRIB2 sont lus avec `wgrib2`, convertis en NetCDF, puis traités avec `xarray`. Les CSV passent directement par `pandas`. **Zéro valeur manquante** après filtrage sur les dix-huit variables × cinq cent soixante-quatre mois.

### Slide 03 — Variables (~45 s)

`[PPTX — SLIDE 03]`

Les dix-huit variables retenues couvrent six familles : température (deux niveaux), humidité, eau précipitable, précipitations, couverture nuageuse, et surtout les flux radiatifs courtes et longues longueurs d'ondes, en ciel total et en ciel clair.

À partir des flux clear-sky et all-sky, je calcule trois indicateurs dérivés appelés **Cloud Radiative Effect**, qui isolent l'effet net des nuages sur le bilan radiatif. Le CRE_net global vaut moins dix-neuf virgule sept watts par mètre carré — parfaitement conforme à la valeur GIEC de moins vingt watts par mètre carré. C'est un sanity check important.

### Slide 04 — Migration R → Python (~45 s)

`[PPTX — SLIDE 04]`

La migration concerne vingt-deux scripts R réécrits en Python. Huit équivalences techniques résument l'effort : `dplyr` vers `pandas`, `ggplot` vers `matplotlib`, `forecast` vers `statsmodels`, `glmnet` vers `scikit-learn`, et ainsi de suite.

Le point le plus important est la **validation croisée** : un script automatique compare chaque CSV produit par Python avec celui produit par R. La précision relative maximale est de l'ordre de **dix puissance moins treize** sur toutes les moyennes pondérées, corrélations, et tendances Sen. C'est la précision flottante machine — autrement dit, **aucune dérive numérique** introduite par la migration. Et le pipeline Python tourne environ trois fois plus vite que le R.

### Slide 05 — Phase 1 : caractérisation du CO₂ (~1 min)

`[PPTX — SLIDE 05]`

Premier résultat : sur quarante-sept ans, le CO₂ atmosphérique est passé de **336 à 426 ppm**, soit une hausse de **plus quatre-vingt-neuf ppm**. La pente de Sen est de **plus un virgule huit huit un ppm par an**, avec un intervalle de confiance bootstrap à quatre-vingt-quinze pour cent de un virgule sept huit à un virgule neuf sept.

Cette tendance est extrêmement robuste : Mann-Kendall donne un tau de zéro virgule quatre-vingt-treize avec une p-value sous dix puissance moins cinquante. Le critère AIC privilégie un modèle exponentiel à zéro virgule cinq pour cent par an — autrement dit, le CO₂ doublerait actuellement en cent trente-sept ans si la tendance se maintenait.

Le chiffre frappant : cette hausse moderne est **trente fois plus rapide** que tout pic naturel enregistré sur les quatre cent quatorze mille ans de la carotte de Vostok.

L'anomalie COVID-19 ? Visible, mais marginale : moins zéro virgule quatre ppm cumulés. La fraction airborne reste stable à environ cinquante-trois pour cent.

### Slide 06 — Phase 2 : climat global 2.5° (~1 min)

`[PPTX — SLIDE 06]`

C'est le cœur de l'analyse. Pour chaque variable, je calcule cinq représentations temporelles : la série brute, les anomalies désaisonnées, les résidus dé-trendés, la différence mois-à-mois, et la différence saisonnière à douze mois.

**Constat majeur** : onze variables sur vingt-et-une affichent une corrélation supérieure à zéro virgule quatre sur les niveaux, mais perdent ce lien sur les résidus. Autrement dit, leur corrélation avec le CO₂ est **spurieuse** — elles partagent simplement la tendance séculaire.

Les **cinq variables qui résistent** sur les résidus sont : CRE_LW à moins zéro virgule cinq, CRE_SW à plus zéro virgule cinq, DSWRF, CRE_net, et PRMSL. Ce sont les variables physiquement actives à l'échelle interannuelle.

**Test de causalité de Granger** sur d12 avec lag six mois : **quinze variables sur vingt-et-une causent significativement le CO₂**, dont cinq sont bidirectionnelles. Le sens dominant est donc bien **climat → CO₂**.

Et un chiffre symbolique : le LW descendant ciel clair, le CSDLF, monte de **plus sept virgule huit quatre watts par mètre carré sur quarante-sept ans**. C'est la signature directe et mesurée du forçage gaz à effet de serre.

### Slide 07 — Phase 3 : climat régional 0.5° (~45 s)

`[PPTX — SLIDE 07]`

À cette résolution, on traite **deux cent soixante mille pixels** × cinq cent soixante-quatre mois × dix-huit variables.

Ce qui ressort spatialement : **l'amplification arctique est de l'ordre de quatre fois** la tendance globale. La pente Sen de T2m est de plus zéro virgule zéro cinq deux Kelvin par an au-dessus du soixantième parallèle nord, contre zéro virgule zéro un sept en moyenne globale.

J'ai défini quatre hotspots régionaux : Sahel, Sibérie centrale, Amazonie, Indonésie. Chacun raconte une histoire physique différente — semi-aride sensible aux SST tropicales pour le Sahel, modulation ENSO pour l'Indonésie, etc.

Et la régression multivariée par zone montre que **le R² global est de zéro virgule sept cinq**, le tropical zéro virgule six neuf, mais le boréal seulement zéro virgule vingt-huit. Cela révèle que **le couplage statistique est très inégal géographiquement**.

Enfin, **validation croisée 0.5° versus 2.5°** : corrélations entre zéro virgule neuf neuf neuf neuf et un. La cohérence entre les deux pipelines est totale.

### Slide 08 — Regard critique (~1 min)

`[PPTX — SLIDE 08]`

Maintenant le regard critique — c'est essentiel pour l'honnêteté scientifique.

Le passage du modèle CFSR à CFSv2 en janvier 2011 introduit un **saut artificiel sur dix-sept des vingt-et-une variables**. Sur certaines, comme CRE_LW, ce saut atteint moins un virgule neuf deux écart-types. C'est un événement instrumental, pas un signal climatique.

Conséquence : sur la série brute, mon modèle multivarié explique soixante-quinze pour cent de la variance résiduelle du CO₂. **Après homogénéisation**, ce R² chute à **quarante-six pour cent**. **Un tiers de la variance explicative était portée par cet artefact technique.**

Mais voici le point intéressant : après homogénéisation, T2m et CSDLF — c'est-à-dire la température et le forçage GES directement mesurable — voient au contraire leur corrélation avec le CO₂ **augmenter**. L'artefact masquait le signal physique. **L'homogénéisation démasque la signature gaz à effet de serre.**

---

## 🌐 Partie 2 — Démonstration du Dashboard (~3 minutes)

`[BASCULER VERS LE NAVIGATEUR — http://127.0.0.1:8088]`

`[PPTX — SLIDE 09 visible 5 secondes puis bascule]`

Je vais maintenant vous montrer le résultat sous forme interactive. Le dashboard est entièrement servi en local, sans bundler, sans installation, juste un serveur Python statique. La technologie : React, Three.js, et la texture NASA Blue Marble pour le globe.

`[DASHBOARD — SECTION 01 Hero]`

Section un, l'accroche. Les quatre KPI sont vivants : la pente Sen, le réchauffement T2m, l'amplification arctique, et la comparaison Vostok. Le globe en arrière-plan utilise la vraie texture satellite.

`[DASHBOARD — SECTION 02 Trajectoire]`

Section deux, la trajectoire CO₂. Vous voyez ici les **cinq cent soixante-quatre vraies valeurs mensuelles NOAA**, avec trois modèles ajustables — linéaire, quadratique, cubique. Et la timeline des événements : Pinatubo en 91, Kyoto, l'accord de Paris en 2015, le creux COVID, et Hunga Tonga en 2022.

`[DASHBOARD — SECTION 03 Earth 3D — temps fort]`

Section trois, le globe interactif. C'est ici que les **trente-six grilles scientifiques réelles** sont exposées. Je sélectionne T2m en mode Sen — vous voyez l'amplification arctique très marquée. Le badge **RÉEL** confirme que ces données viennent directement du pipeline 0.5°, et non d'une approximation.

`[DASHBOARD — Cliquer un hotspot]`

Si je clique sur un hotspot — disons l'Amazonie — un panneau s'ouvre avec les tendances Sen par variable, les p-values Mann-Kendall, la corrélation au CO₂ résiduel, le nombre de variables Granger-causales, et le R² local.

`[DASHBOARD — SECTION 04 Lien]`

Section quatre, le lien climat-CO₂. La heatmap **vingt-et-une variables par cinq représentations** rend visible le glissement entre corrélations brutes — toutes en orange — et corrélations résiduelles — beaucoup plus pâles, voire négatives. Le diagramme Sankey en bas synthétise les Granger : dix variables strict climat-vers-CO₂, cinq bidirectionnelles, trois inverses, trois aucune.

`[DASHBOARD — SECTION 05 Hotspots]`

Section cinq, les hotspots. **Quatre mini-globes**, chacun cadré sur sa région. À droite, le radar des R² par zone montre l'inégalité géographique : le tropical et le boréal portent l'essentiel du signal.

`[DASHBOARD — SECTION 06 Critique]`

Section six enfin, la critique. La timeline interactive permet de cliquer chaque variable affectée par le saut CFSR-CFSv2. À droite, les trois limites assumées du travail. Et le panneau « À propos » liste les sources.

---

## 📓 Partie 3 — Notebooks (~30 s)

`[BASCULER VERS LE DOSSIER notebooks/ — OPTIONNEL]`

Pour la preuve technique, quatre notebooks Jupyter sont disponibles, avec leur PDF correspondant : **préprocessing**, **Phase 1 CO₂**, **Phase 2 climat 2.5°**, **Phase 3 climat 0.5°**. Si vous avez une question sur une méthode précise — un test de Granger, un calcul Sen, une cartographie pixel — j'ouvre directement le notebook concerné pendant les questions.

---

## 🎯 Conclusion (~30 s)

`[PPTX — SLIDE 10]`

Pour résumer en trois résultats :

**Premièrement**, les corrélations brutes climat-CO₂ sont en grande partie trompeuses : onze variables sur vingt-et-une perdent leur lien sur les résidus.

**Deuxièmement**, cinq variables seulement sont réellement actives à l'échelle interannuelle ; et quinze sur vingt-et-une causent statistiquement le CO₂ au sens de Granger. Le sens dominant est bien **climat précède CO₂**.

**Troisièmement**, une partie du signal apparent est un artefact instrumental — le saut CFSR-CFSv2 — qui explique à lui seul un tiers du R². Après correction, le forçage gaz à effet de serre direct, lui, ressort plus clairement.

L'ensemble est validé à **dix puissance moins treize** vis-à-vis du R d'origine, et le dashboard est reproductible en zéro setup.

Merci de votre attention, je suis prêt à répondre à vos questions.

---

## 💡 Astuces de pitch

- **Rythme :** environ 150 mots/minute. Si vous trouvez ce pitch trop dense, supprimer les phrases marquées comme exemples (`Mauna Loa`, `pôle Sud`, etc.) — gardez les chiffres clés.
- **Transitions :** « Premier résultat », « Constat majeur », « Le point intéressant » — ce sont des cailloux pour le jury qui décroche.
- **Chiffres à savoir par cœur :** **+1.881 ppm/an** · **+89 ppm** · **+0.78 K T2m** · **+7.84 W/m² CSDLF** · **15/21 Granger** · **R² 0.748 → 0.46** · **17/21 sauts** · **30× vs paléo** · **4× amplif arctique** · **10⁻¹³ validation**.
- **Si vous dépassez le temps**, sacrifier dans cet ordre : Slide 5 phase 1 (déjà connue) → détails phase 3 hotspots → astuces techniques du dashboard.
- **Si vous avez du rab**, ralentir sur la section critique (slide 8) : c'est 25 % de la note et c'est le moment où vous montrez votre maturité scientifique.
