"""Paths, mappings de variables et constantes du projet."""
from __future__ import annotations
from pathlib import Path

# ============================================================
# Racines (les données restent dans le projet R d'origine)
# ============================================================
PROJECT_ROOT = Path(
    "/home/mazzez/Bureau/ESSAI/1er année/Programmation Mathematique/Projet"
)

# Le projet R a été consolidé : les données CSV CO2 et les NetCDF processed/
# sont maintenant dans Final Version/. Les GRIB bruts (lourds) restent dans
# Data/. On résout chaque dossier vers le premier emplacement existant.
_R_FINAL = Path("/home/mazzez/Bureau/R project/Final Version")
_R_DATA = Path("/home/mazzez/Bureau/R project/Data")


def _resolve(*candidates: Path) -> Path:
    for c in candidates:
        if c.exists():
            return c
    # Aucun n'existe : on retourne le premier comme valeur cible
    return candidates[0]


# Données sources (CSV CO2, NetCDF processed) — d'abord Final Version, puis Data
DATA_CO2 = _resolve(_R_FINAL / "CO2", _R_DATA / "CO2")
NC_25 = _resolve(_R_FINAL / "processed" / "nc_subset_25",
                 _R_DATA / "processed" / "nc_subset_25")
NC_05 = _resolve(_R_FINAL / "processed" / "nc_subset_05",
                 _R_DATA / "processed" / "nc_subset_05")

# GRIB bruts (source CFSR/CFSv2) — d'abord Data/, fallback Final Version
GRIB_25 = _resolve(_R_DATA / "2.5° x 2.5°", _R_FINAL / "2.5° x 2.5°")
GRIB_05 = _resolve(_R_DATA / "0.5° x 0.5°", _R_FINAL / "0.5° x 0.5°")
GRIB_25_SUBSET = _resolve(_R_FINAL / "2.5° x 2.5° subset",
                          _R_DATA / "2.5° x 2.5° subset")
GRIB_05_SUBSET = _resolve(_R_FINAL / "0.5° x 0.5° subset",
                          _R_DATA / "0.5° x 0.5° subset")

# Conservé pour rétro-compatibilité (anciens scripts)
R_DATA_ROOT = _R_DATA

# Outputs Python (mirror des outputs R, par phase)
OUTPUTS = PROJECT_ROOT / "outputs"
OUT_PHASE1 = OUTPUTS / "phase1_co2"
OUT_PHASE2 = OUTPUTS / "phase2_climat_25"
OUT_PHASE3 = OUTPUTS / "phase3_climat_05"

# ============================================================
# 18 variables climatiques + métadonnées
# ============================================================
# wgrib2 -netcdf nomme les variables `<CODE>_<level>` ; mapping vers nom court
VAR_MAP_25 = {
    "TMP_2maboveground": "T2m",
    "TMP_500mb": "T500",
    "SPFH_2maboveground": "SPFH2m",
    "PWAT_entireatmosphere_consideredasasinglelayer_": "PWAT",
    "APCP_surface": "APCP",
    "TCDC_entireatmosphere_consideredasasinglelayer_": "TCDC",
    "DLWRF_surface": "DLWRF",
    "ULWRF_surface": "ULWRF",
    "DSWRF_surface": "DSWRF",
    "USWRF_surface": "USWRF",
    "PRMSL_meansealevel": "PRMSL",
    "CSDSF_surface": "CSDSF",
    "CSUSF_surface": "CSUSF",
    "CSDLF_surface": "CSDLF",
    "CSULF_surface": "CSULF",
    "CDUVB_surface": "CDUVB",
    "DUVB_surface": "DUVB",
    "ALBDO_surface": "ALBDO",
}

# Pour le 0.5°, T500 est exposé sous "TMP" (la dim plevel=500 est unique)
VAR_MAP_05 = dict(VAR_MAP_25)
del VAR_MAP_05["TMP_500mb"]
VAR_MAP_05["TMP"] = "T500"

CLIM_VARS = list(VAR_MAP_25.values())  # 18 variables (ordre d'origine)
ALL_VARS = CLIM_VARS + ["CRE_SW", "CRE_LW", "CRE_net"]  # 21 incluant CRE

# Plages "raisonnables" attendues pour la moyenne globale annuelle (sanity)
EXPECTED_RANGES = {
    "T2m": (284, 290),
    "T500": (254, 262),
    "SPFH2m": (0.008, 0.011),
    "PWAT": (22, 28),
    "APCP": (0.3, 0.7),
    "TCDC": (55, 70),
    "DLWRF": (325, 350),
    "ULWRF": (380, 405),
    "DSWRF": (185, 215),
    "USWRF": (25, 45),
    "PRMSL": (101000, 101300),
    "CSDSF": (240, 275),
    "CSUSF": (30, 45),
    "CSDLF": (300, 325),
    "CSULF": (380, 405),
    "CDUVB": (3.5, 4.5),
    "DUVB": (2.8, 3.8),
    "ALBDO": (9, 15),
}

# Métadonnées (unités + nom long)
META = {
    "T2m":     ("K",      "Température air 2 m"),
    "T500":    ("K",      "Température 500 hPa"),
    "SPFH2m":  ("kg/kg",  "Humidité spécifique 2 m"),
    "PWAT":    ("kg/m²",  "Eau précipitable colonne"),
    "APCP":    ("kg/m²",  "Précipitations cumulées"),
    "TCDC":    ("%",      "Couverture nuageuse totale"),
    "DLWRF":   ("W/m²",   "LW descendant surface"),
    "ULWRF":   ("W/m²",   "LW ascendant surface"),
    "DSWRF":   ("W/m²",   "SW descendant surface"),
    "USWRF":   ("W/m²",   "SW réfléchi surface"),
    "PRMSL":   ("Pa",     "Pression réduite mer"),
    "CSDSF":   ("W/m²",   "SW descendant ciel clair"),
    "CSUSF":   ("W/m²",   "SW ascendant ciel clair"),
    "CSDLF":   ("W/m²",   "LW descendant ciel clair"),
    "CSULF":   ("W/m²",   "LW ascendant ciel clair"),
    "CDUVB":   ("W/m²",   "UV-B ciel clair"),
    "DUVB":    ("W/m²",   "UV-B all-sky"),
    "ALBDO":   ("%",      "Albédo de surface"),
    "CRE_SW":  ("W/m²",   "Cloud Radiative Effect SW"),
    "CRE_LW":  ("W/m²",   "Cloud Radiative Effect LW"),
    "CRE_net": ("W/m²",   "Cloud Radiative Effect net"),
}

# ============================================================
# 5 bandes de latitude (phase 3 — 0.5°)
#
# Intervalles NON-chevauchants : tropical inclut ses 2 bornes [-30, 30],
# les autres bandes excluent leur frontière côté tropical pour éviter le
# double-comptage des pixels limites. Total : 60+60+121+60+60 = 361 lignes
# de latitude au pas 0.5°.
# ============================================================
import numpy as _np


def _band_boreal(lat):     return lat > 60
def _band_temp_N(lat):     return (lat > 30) & (lat <= 60)
def _band_tropical(lat):   return (lat >= -30) & (lat <= 30)
def _band_temp_S(lat):     return (lat >= -60) & (lat < -30)
def _band_austral(lat):    return lat < -60
def _band_global(lat):     return _np.ones_like(lat, dtype=bool)


# Prédicats sur le vecteur lat (1D) — donnent un masque booléen 1D
BAND_PREDICATES = {
    "boreal":      _band_boreal,
    "temperate_N": _band_temp_N,
    "tropical":    _band_tropical,
    "temperate_S": _band_temp_S,
    "austral":     _band_austral,
    "global":      _band_global,
}

# Intervalles "informatifs" (utilisés pour les labels et le dashboard).
# Lecture : austral (-90, -60), temperate_S [-60, -30), tropical [-30, 30],
# temperate_N (30, 60], boreal (60, 90].
BANDS = {
    "boreal":      (60,  90),
    "temperate_N": (30,  60),
    "tropical":    (-30, 30),
    "temperate_S": (-60, -30),
    "austral":     (-90, -60),
    "global":      (-90, 90),
}

BAND_LABELS = {
    "boreal":      "Boréale (60-90°N)",
    "temperate_N": "Tempérée N (30-60°N)",
    "tropical":    "Tropicale (30°S-30°N)",
    "temperate_S": "Tempérée S (60-30°S)",
    "austral":     "Australe (90-60°S)",
    "global":      "Global",
}

# ============================================================
# 4 hotspots régionaux (phase 3 — 0.5°)
# Longitudes en convention 0–360 (cohérent avec les NetCDF)
# ============================================================
REGIONS = {
    "Amazonie":  {"lat": (-5,  5),  "lon": (290, 310),
                  "label": "Amazonie (5°S-5°N, 70-50°W)"},
    "Indonesie": {"lat": (-10, 5),  "lon": (95,  141),
                  "label": "Indonésie (10°S-5°N, 95-141°E)"},
    "Siberie":   {"lat": (55,  70), "lon": (70,  130),
                  "label": "Sibérie centrale (55-70°N, 70-130°E)"},
    "Sahel":     {"lat": (10,  20), "lon": (340, 400),
                  "label": "Sahel (10-20°N, 20°W-40°E)"},
}

# ============================================================
# Constantes physiques
# ============================================================
PPM_TO_GTC = 2.124          # 1 ppm CO2 atm <-> 2.124 GtC
GTC_TO_GTCO2 = 44.0 / 12.0  # masse molaire CO2 / C
MTCO2_TO_GTC = 1.0 / (1000.0 * GTC_TO_GTCO2)


def ensure_dirs() -> None:
    """Crée tous les dossiers de sortie nécessaires."""
    for p in (OUT_PHASE1, OUT_PHASE2, OUT_PHASE3,
              OUT_PHASE2 / "plots", OUT_PHASE2 / "per_variable",
              OUT_PHASE3 / "plots", OUT_PHASE3 / "maps"):
        p.mkdir(parents=True, exist_ok=True)
