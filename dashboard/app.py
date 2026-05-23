"""Dashboard Dash interactif — Climat & CO2 (1979-2025).

Lancement :
    cd Projet
    source venv/bin/activate
    python dashboard/app.py
    # → http://127.0.0.1:8050
"""
from __future__ import annotations
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from climat import config, io, preprocess                                   # noqa: E402

# ============================================================
# Chargement des données (CSV produits par les pipelines Python)
# ============================================================
CO2 = io.load_co2_global()
MLO = io.load_co2_mauna_loa()
SPO = io.load_co2_south_pole()
GCB = io.load_gcb()
ONI = io.load_oni()
VOSTOK = io.load_vostok()

CLIM25 = pd.read_csv(config.OUT_PHASE2 / "climate_co2_monthly.csv",
                     parse_dates=["date"])
CRE = pd.read_csv(config.OUT_PHASE2 / "cre_monthly_25.csv",
                  parse_dates=["date"])
CORR4 = pd.read_csv(config.OUT_PHASE2 / "correlations_4repr.csv")
TRENDS = pd.read_csv(config.OUT_PHASE2 / "trends_summary.csv")
JUMPS = pd.read_csv(config.OUT_PHASE2 / "cfsr_to_cfsv2_jumps.csv")
SYNTH = pd.read_csv(config.OUT_PHASE2 / "synthese_finale.csv")
PER_VAR = pd.read_csv(config.OUT_PHASE2 / "per_variable_stats.csv")
GRANGER = pd.read_csv(config.OUT_PHASE2 / "granger_results.csv")

BAND05 = pd.read_csv(config.OUT_PHASE3 / "monthly_band_means_05.csv",
                     parse_dates=["date"])
HOTSPOT_PATH = config.OUT_PHASE3 / "hotspots_summary.csv"
HOTSPOTS = pd.read_csv(HOTSPOT_PATH) if HOTSPOT_PATH.exists() else None
HOTSPOT_SERIES_PATH = config.OUT_PHASE3 / "hotspots_series.csv"
HOTSPOT_SERIES = (pd.read_csv(HOTSPOT_SERIES_PATH, parse_dates=["date"])
                  if HOTSPOT_SERIES_PATH.exists() else None)

# Nouveaux CSV phase 3 (scripts 08, 09, 10)
_p = config.OUT_PHASE3 / "regression_per_zone.csv"
REG_ZONE = pd.read_csv(_p) if _p.exists() else None
_p = config.OUT_PHASE3 / "granger_per_zone.csv"
GRANGER_ZONE = pd.read_csv(_p) if _p.exists() else None
_p = config.OUT_PHASE3 / "hemisphere_asymmetry_ratio.csv"
HEMI_RATIO = pd.read_csv(_p) if _p.exists() else None

# Cartes pixel-par-pixel (résolution 0.5°) — chargées depuis les pickles
TREND_PKL = config.OUT_PHASE3 / "trend_grids.pkl"
CORR_PKL = config.OUT_PHASE3 / "correlation_grids.pkl"
TREND_GRIDS = (pickle.load(open(TREND_PKL, "rb")) if TREND_PKL.exists() else None)
CORR_GRIDS = (pickle.load(open(CORR_PKL, "rb")) if CORR_PKL.exists() else None)

# Grille lon/lat 0.5° (lue 1 fois depuis le 1er NetCDF disponible)
try:
    from climat.io import get_grid
    LON_05, LAT_05 = get_grid(config.NC_05)
except Exception:
    LON_05, LAT_05 = None, None

ALL_VARS = config.CLIM_VARS + ["CRE_SW", "CRE_LW", "CRE_net"]
MAP_VARS = config.CLIM_VARS  # 18 vars disponibles en 0.5°


# ============================================================
# Helpers
# ============================================================
def kpi_card(label: str, value: str, sub: str = "") -> dbc.Card:
    return dbc.Card([
        dbc.CardBody([
            html.Div(value, className="display-6 fw-bold"),
            html.Div(label, className="text-muted small"),
            html.Div(sub, className="text-info small mt-1") if sub else None,
        ])
    ], className="shadow-sm")


def fig_co2_main():
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=CO2["date"], y=CO2["average"], name="Brut",
        line=dict(color="lightgrey", width=1)))
    fig.add_trace(go.Scatter(
        x=CO2["date"], y=CO2["trend"], name="Trend NOAA",
        line=dict(color="darkred", width=2)))
    fig.update_layout(
        title="CO2 atmosphérique mondial — NOAA GML",
        xaxis_title=None, yaxis_title="ppm",
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )
    return fig


def fig_climat_series(var: str, drange: tuple[pd.Timestamp, pd.Timestamp]):
    sub = CLIM25[(CLIM25["date"] >= drange[0]) & (CLIM25["date"] <= drange[1])]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sub["date"], y=sub[var], name=var,
        line=dict(color="steelblue", width=1)))
    unit, long = config.META.get(var, ("", var))
    fig.update_layout(
        title=f"{var} — {long} ({unit})",
        xaxis_title=None, yaxis_title=f"{var} ({unit})",
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def fig_corr_repr():
    df = SYNTH.melt(id_vars="var",
                    value_vars=["r_level", "r_anom", "r_resid", "r_d12"],
                    var_name="repr", value_name="r")
    df["repr"] = df["repr"].map({"r_level": "Niveaux", "r_anom": "Anomalies",
                                  "r_resid": "Résidus", "r_d12": "d12 (annuel)"})
    order = SYNTH["var"].tolist()
    fig = px.bar(df, x="r", y="var", color="repr",
                 category_orders={"var": order[::-1]},
                 barmode="group", orientation="h",
                 color_discrete_sequence=px.colors.qualitative.Set1)
    fig.update_layout(title="Corrélation climat ↔ CO2 selon la représentation",
                      yaxis_title=None, xaxis_title="r (Pearson)",
                      height=600, margin=dict(l=80, r=20, t=50, b=40))
    fig.add_vline(x=0, line_color="black", line_width=0.5)
    return fig


def fig_trends_pct():
    df = TRENDS.copy()
    df["pct_per_year"] = df["sen_per_year"] / df["mean"] * 100
    df = df.sort_values("pct_per_year")
    fig = px.bar(df, x="pct_per_year", y="var", orientation="h",
                 color=df["pct_per_year"] > 0,
                 color_discrete_map={True: "tomato", False: "steelblue"})
    fig.update_layout(title="Vitesse d'évolution (% du moyen / an, 1979-2025)",
                      yaxis_title=None, xaxis_title="% / an",
                      showlegend=False, height=600,
                      margin=dict(l=80, r=20, t=50, b=40))
    fig.add_vline(x=0, line_color="black", line_width=0.5)
    return fig


def fig_band_anom_t2m():
    BAND_ORDER = ["austral", "temperate_S", "tropical", "temperate_N",
                  "boreal", "global"]
    df = BAND05.copy()
    df["band"] = pd.Categorical(df["band"], categories=BAND_ORDER, ordered=True)
    df = df.sort_values(["band", "date"])
    clim = (df.groupby(["band", df["date"].dt.month], observed=True)["T2m"]
            .transform("mean"))
    df["anom"] = df["T2m"] - clim
    fig = px.line(df[df["band"] != "global"],
                  x="date", y="anom", color="band",
                  color_discrete_sequence=px.colors.qualitative.Set1)
    fig.update_layout(title="Anomalie T2m par bande de latitude (0.5°)",
                      xaxis_title=None, yaxis_title="K",
                      height=450, margin=dict(l=40, r=20, t=50, b=40))
    fig.add_hline(y=0, line_dash="dash", line_color="grey")
    return fig


def fig_hotspots_series():
    if HOTSPOT_SERIES is None:
        return go.Figure()
    df = HOTSPOT_SERIES.copy()
    cols = [c for c in df.columns if c.endswith("_T2m")]
    long = df.melt(id_vars=["date", "year", "month"], value_vars=cols,
                   var_name="region_var", value_name="T2m")
    long["region"] = long["region_var"].str.replace("_T2m$", "", regex=True)
    fig = px.line(long, x="date", y="T2m", color="region",
                  color_discrete_sequence=px.colors.qualitative.Set1)
    fig.update_layout(title="T2m mensuelle par hotspot (0.5°)",
                      xaxis_title=None, yaxis_title="T2m (K)",
                      height=450, margin=dict(l=40, r=20, t=50, b=40))
    return fig


def fig_jumps():
    df = JUMPS.assign(jump_in_sd=lambda d: d["jump"] / d["sd_var"])
    df = df.sort_values("jump_in_sd")
    fig = px.bar(df, x="jump_in_sd", y="var", orientation="h",
                 color="significant",
                 color_discrete_map={True: "tomato", False: "grey"})
    fig.update_layout(title="Saut CFSR → CFSv2 (jan 2011) par variable",
                      yaxis_title=None, xaxis_title="Saut / écart-type",
                      height=600, margin=dict(l=80, r=20, t=50, b=40))
    fig.add_vline(x=0, line_color="black", line_width=0.5)
    return fig


def fig_reg_per_zone():
    if REG_ZONE is None:
        return go.Figure().update_layout(title="regression_per_zone non disponible")
    df = REG_ZONE.copy()
    df["zone_lbl"] = df["zone"].map(config.BAND_LABELS).fillna(df["zone"])
    df = df.sort_values("R2", ascending=True)
    color_seq = {"bande": "steelblue", "hotspot": "tomato"}
    fig = px.bar(df, x="R2", y="zone_lbl", color="type", orientation="h",
                 color_discrete_map=color_seq,
                 text=df["R2"].apply(lambda v: f"{v:.3f}"),
                 hover_data={"R2_adj": True, "top1": True, "top2": True, "top3": True})
    fig.update_layout(
        title="R² climat → CO2 résiduel par zone (régression multivariée)",
        xaxis_title="R²", yaxis_title=None, height=480,
        margin=dict(l=120, r=20, t=50, b=40),
    )
    fig.update_traces(textposition="outside")
    return fig


def fig_granger_per_zone():
    if GRANGER_ZONE is None:
        return go.Figure().update_layout(title="granger_per_zone non disponible")
    g = GRANGER_ZONE.copy()
    sig = (g.assign(sig_x=lambda d: (d["p_x_to_co2"] < 0.05).fillna(False),
                    sig_co2=lambda d: (d["p_co2_to_x"] < 0.05).fillna(False))
           .groupby(["zone", "type"], observed=True)
           .agg(n_vars=("var", "count"),
                n_x_to_co2_sig=("sig_x", "sum"),
                n_co2_to_x_sig=("sig_co2", "sum"))
           .reset_index())
    sig["zone_lbl"] = sig["zone"].map(config.BAND_LABELS).fillna(sig["zone"])
    sig["pct_x_to_co2"] = sig["n_x_to_co2_sig"] / sig["n_vars"] * 100
    sig = sig.sort_values("pct_x_to_co2")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sig["n_x_to_co2_sig"], y=sig["zone_lbl"],
                         orientation="h", name="X → CO2 (p<0.05)",
                         marker_color="tomato",
                         text=sig.apply(lambda r: f"{r['n_x_to_co2_sig']}/{r['n_vars']}", axis=1),
                         textposition="outside"))
    fig.add_trace(go.Bar(x=sig["n_co2_to_x_sig"], y=sig["zone_lbl"],
                         orientation="h", name="CO2 → X (p<0.05)",
                         marker_color="steelblue",
                         text=sig.apply(lambda r: f"{r['n_co2_to_x_sig']}/{r['n_vars']}", axis=1),
                         textposition="outside"))
    fig.update_layout(
        title="Causalité Granger (d12, lag 6 mois) — variables significatives par zone",
        barmode="group", xaxis_title="Nombre de variables", yaxis_title=None,
        height=480, margin=dict(l=120, r=20, t=50, b=40),
    )
    return fig


def fig_hemi_ratio():
    if HEMI_RATIO is None:
        return go.Figure().update_layout(title="hemisphere_asymmetry_ratio non disponible")
    h = HEMI_RATIO.copy()
    ref = 5.6  # CO2 MLO/SPO phase 1
    h["color"] = ["tomato"] * len(h)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=h["var"], y=h["ratio_N_over_S"],
                         marker_color=h["color"],
                         text=h["ratio_N_over_S"].apply(lambda v: f"{v:.2f}×"),
                         textposition="outside",
                         name="Climat N/S"))
    fig.add_hline(y=ref, line_dash="dash", line_color="darkred",
                  annotation_text=f"Référence CO2 MLO/SPO = {ref}×",
                  annotation_position="top right")
    fig.update_layout(
        title="Asymétrie hémisphérique : amplitude saisonnière N / S",
        xaxis_title=None, yaxis_title="Ratio Boréale / Australe",
        margin=dict(l=40, r=20, t=50, b=40), height=400,
    )
    return fig


def fig_pixel_map(var: str, kind: str = "trend"):
    """Carte interactive Plotly de la pente locale (kind='trend') ou de la
    corrélation pixel-CO2_resid (kind='corr')."""
    if LON_05 is None or LAT_05 is None:
        return go.Figure().update_layout(
            title="Cartes 0.5° non disponibles (NetCDF source absent)")
    grids = TREND_GRIDS if kind == "trend" else CORR_GRIDS
    if grids is None or var not in grids:
        return go.Figure().update_layout(
            title=f"Carte {kind} indisponible pour {var}")
    if kind == "trend":
        Z = grids[var]["slope"]
        unit, long = config.META.get(var, ("", var))
        zlim = float(np.nanquantile(np.abs(Z), 0.99))
        zmin, zmax = -zlim, zlim
        title = f"{var} — pente locale (régression sur anomalies, par an)"
        cbar_label = f"{unit} / an"
    else:
        Z = grids[var]
        zmin, zmax = -1.0, 1.0
        title = f"{var} — corrélation pixel ↔ CO2 résiduel"
        cbar_label = "r"

    fig = go.Figure(data=go.Heatmap(
        z=Z.T, x=LON_05, y=LAT_05,
        colorscale="RdBu_r", zmin=zmin, zmax=zmax,
        colorbar=dict(title=cbar_label, len=0.85),
        zsmooth=False,
    ))
    fig.update_layout(
        title=title,
        xaxis_title="Longitude (°)", yaxis_title="Latitude (°)",
        margin=dict(l=40, r=20, t=50, b=40),
        height=480,
        yaxis=dict(scaleanchor="x", scaleratio=1),
    )
    # Régions hotspots overlay (rectangles)
    region_colors = {"Amazonie": "limegreen", "Indonesie": "magenta",
                     "Siberie": "cyan", "Sahel": "yellow"}
    for rname, reg in config.REGIONS.items():
        lon0, lon1 = reg["lon"]
        lat0, lat1 = reg["lat"]
        # Wrap longitudes > 360
        if lon1 > 360:
            for x0, x1 in [(lon0, 360), (0, lon1 - 360)]:
                fig.add_shape(type="rect", x0=x0, x1=x1, y0=lat0, y1=lat1,
                              line=dict(color=region_colors[rname], width=2),
                              fillcolor="rgba(0,0,0,0)")
        else:
            fig.add_shape(type="rect", x0=lon0, x1=lon1, y0=lat0, y1=lat1,
                          line=dict(color=region_colors[rname], width=2),
                          fillcolor="rgba(0,0,0,0)")
        fig.add_annotation(x=(lon0 + lon1) / 2, y=lat1 + 3,
                           text=rname, showarrow=False,
                           font=dict(color=region_colors[rname], size=10))
    return fig


def fig_taux_annuel(year_from: int, year_to: int):
    annual = (CO2.groupby("year")
              .agg(annual_mean=("average", "mean"), n=("average", "count"))
              .reset_index().query("n >= 6"))
    annual["rate"] = annual["annual_mean"].diff()
    annual = annual.query("year >= @year_from and year <= @year_to")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=annual["year"], y=annual["rate"],
                         marker_color="darkorange", name="Taux annuel"))
    fig.update_layout(title="Taux annuel de croissance du CO2 (ppm/an)",
                      xaxis_title=None, yaxis_title="ppm/an",
                      margin=dict(l=40, r=20, t=50, b=40))
    return fig


def fig_vostok_overlay():
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=VOSTOK["gas_ageBP"] / 1000, y=VOSTOK["CO2"],
                             name="Vostok (paléo)", line=dict(color="steelblue")))
    co2_now = float(CO2["average"].iloc[-1])
    fig.add_hline(y=co2_now, line_dash="dash", line_color="darkred",
                  annotation_text=f"Niveau actuel : {co2_now:.0f} ppm")
    fig.update_layout(title="CO2 sur 414 000 ans (Vostok) vs niveau actuel",
                      xaxis_title="Milliers d'années avant 1950 (BP)",
                      yaxis_title="ppm",
                      xaxis=dict(autorange="reversed"),
                      margin=dict(l=40, r=20, t=50, b=40))
    return fig


# ============================================================
# Layout
# ============================================================
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY],
           title="Climat & CO2")


def make_kpis() -> dbc.Row:
    sen_co2 = (TRENDS.query("var == 'T2m'")["sen_per_year"].iloc[0] * 47
               if "T2m" in TRENDS["var"].values else None)
    n_obs_climat = len(CLIM25)
    yrs_co2 = float(CO2["decimal"].iloc[-1] - CO2["decimal"].iloc[0])
    delta_co2 = float(CO2["average"].iloc[-1] - CO2["average"].iloc[0])
    return dbc.Row([
        dbc.Col(kpi_card("Période d'analyse",
                         f"{int(yrs_co2)} ans",
                         f"{CO2['date'].min().date()} → {CO2['date'].max().date()}"), md=3),
        dbc.Col(kpi_card("Hausse CO2",
                         f"+{delta_co2:.1f} ppm",
                         f"~{delta_co2/yrs_co2:.2f} ppm/an"), md=3),
        dbc.Col(kpi_card("Réchauffement T2m global",
                         f"+{sen_co2:.2f} K"
                         if sen_co2 is not None else "n/a",
                         "Pente de Sen sur 47 ans"), md=3),
        dbc.Col(kpi_card("Variables climatiques",
                         f"{n_obs_climat} mois × 21 vars",
                         "Réanalyses CFSR/CFSv2 + 3 CRE"), md=3),
    ], className="g-3 mb-3")


def make_filters() -> dbc.Card:
    return dbc.Card(dbc.CardBody([
        dbc.Row([
            dbc.Col([
                html.Label("Période :", className="form-label"),
                dcc.RangeSlider(
                    id="year-range",
                    min=int(CLIM25["year"].min()),
                    max=int(CLIM25["year"].max()),
                    value=[int(CLIM25["year"].min()), int(CLIM25["year"].max())],
                    marks={y: str(y) for y in range(1980, 2030, 5)},
                    step=1,
                    tooltip={"placement": "bottom", "always_visible": False},
                ),
            ], md=8),
            dbc.Col([
                html.Label("Variable climatique :", className="form-label"),
                dcc.Dropdown(
                    id="var-dropdown",
                    options=[{"label": f"{v} — {config.META[v][1]}", "value": v}
                             for v in ALL_VARS],
                    value="T2m", clearable=False,
                ),
            ], md=4),
        ]),
    ]), className="shadow-sm mb-3")


tabs = dcc.Tabs(id="tabs", value="t-overview", children=[
    dcc.Tab(label="Vue d'ensemble", value="t-overview"),
    dcc.Tab(label="CO2 (Phase 1)", value="t-co2"),
    dcc.Tab(label="Climat global 2.5° (Phase 2)", value="t-climat25"),
    dcc.Tab(label="Régional 0.5° (Phase 3)", value="t-climat05"),
    dcc.Tab(label="Climat ↔ CO2", value="t-link"),
    dcc.Tab(label="Critique / qualité", value="t-quality"),
])


app.layout = dbc.Container([
    html.H2("🌍 Climat & CO2 — 1979 → 2025  (migration R → Python)",
            className="my-3"),
    html.Div(id="kpi-row", children=make_kpis()),
    make_filters(),
    tabs,
    html.Div(id="tab-content", className="mt-3"),
    html.Hr(),
    html.Footer([
        html.Small("Données : NOAA GML, NCAR CFSR/CFSv2, GCB 2025v15, Vostok. "
                   "Pipeline Python — projet ESSAI 1A 2025-2026.",
                   className="text-muted"),
    ], className="my-3"),
], fluid=True)


# ============================================================
# Callbacks
# ============================================================
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "value"),
    Input("year-range", "value"),
    Input("var-dropdown", "value"),
)
def render_tab(tab, year_range, var):
    drange = (pd.Timestamp(f"{year_range[0]}-01-01"),
              pd.Timestamp(f"{year_range[1]}-12-31"))

    if tab == "t-overview":
        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_co2_main()), md=6),
            dbc.Col(dcc.Graph(figure=fig_climat_series(var, drange)), md=6),
            dbc.Col(dcc.Graph(figure=fig_corr_repr()), md=6),
            dbc.Col(dcc.Graph(figure=fig_trends_pct()), md=6),
        ])

    if tab == "t-co2":
        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_co2_main()), md=12),
            dbc.Col(dcc.Graph(figure=fig_taux_annuel(year_range[0], year_range[1])), md=6),
            dbc.Col(dcc.Graph(figure=fig_vostok_overlay()), md=6),
        ])

    if tab == "t-climat25":
        sub = CLIM25[(CLIM25["date"] >= drange[0]) & (CLIM25["date"] <= drange[1])]
        # série + tendance simple
        unit, long = config.META[var]
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=sub["date"], y=sub[var],
                                  name=var, line=dict(color="steelblue", width=1)))
        # Lissage moyenne mobile 12 mois
        ma = sub[var].rolling(12, center=True).mean()
        fig1.add_trace(go.Scatter(x=sub["date"], y=ma, name="MA 12 mois",
                                  line=dict(color="darkred", width=2)))
        fig1.update_layout(title=f"{var} — {long} ({unit})",
                           yaxis_title=f"{var} ({unit})",
                           margin=dict(l=40, r=20, t=50, b=40))

        fig_cre = go.Figure()
        cre_sub = CRE[(CRE["date"] >= drange[0]) & (CRE["date"] <= drange[1])]
        for c, color in [("CRE_SW", "steelblue"), ("CRE_LW", "tomato"), ("CRE_net", "purple")]:
            fig_cre.add_trace(go.Scatter(x=cre_sub["date"], y=cre_sub[c],
                                         name=c, line=dict(color=color, width=1)))
        fig_cre.update_layout(title="Cloud Radiative Effects (W/m²)",
                              yaxis_title="W/m²",
                              margin=dict(l=40, r=20, t=50, b=40))
        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig1), md=12),
            dbc.Col(dcc.Graph(figure=fig_cre), md=12),
            dbc.Col(dcc.Graph(figure=fig_jumps()), md=12),
        ])

    if tab == "t-climat05":
        # Carte de la variable sélectionnée — type "trend" par défaut.
        # On utilise var pour la variable, mais T500/CRE non dispos en 0.5° :
        # fallback sur T2m si non disponible.
        var_map = var if var in MAP_VARS else "T2m"
        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_band_anom_t2m()), md=6),
            dbc.Col(dcc.Graph(figure=fig_hotspots_series()), md=6),
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5(f"Cartes pixel-par-pixel 0.5° — {var_map}",
                            className="card-title"),
                    html.P(
                        "Utilise les pickles produits par "
                        "phase3_climat_05/04_05_trend_and_corr_maps.py. "
                        "Les rectangles colorés délimitent les 4 hotspots.",
                        className="text-muted small",
                    ),
                    dbc.Tabs([
                        dbc.Tab(dcc.Graph(figure=fig_pixel_map(var_map, "trend")),
                                label="Tendance Sen / an"),
                        dbc.Tab(dcc.Graph(figure=fig_pixel_map(var_map, "corr")),
                                label="Corrélation avec CO2 résiduel"),
                    ]),
                ]), className="shadow-sm"),
            ], md=12),
            dbc.Col(html.Div(id="hotspot-table",
                             children=[
                                 html.H5("Synthèse hotspots", className="mt-3"),
                                 html.Pre(HOTSPOTS.round(3).to_string(index=False)
                                          if HOTSPOTS is not None
                                          else "Hotspots non encore calculés",
                                          style={"font-size": "0.8em"})]),
                    md=12),
            # --- Nouveaux panneaux (scripts 08 / 09 / 10) ---
            dbc.Col(dcc.Graph(figure=fig_reg_per_zone()), md=6),
            dbc.Col(dcc.Graph(figure=fig_granger_per_zone()), md=6),
            dbc.Col(dcc.Graph(figure=fig_hemi_ratio()), md=12),
        ])

    if tab == "t-link":
        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_corr_repr()), md=12),
            dbc.Col(html.Div([
                html.H5("Synthèse Granger (lag 6 mois, d12)"),
                html.Pre(GRANGER.query("repr == 'd12'")
                         [["var", "p_x_to_co2", "p_co2_to_x", "sens"]]
                         .round(4).to_string(index=False),
                         style={"font-size": "0.8em"}),
            ]), md=12),
        ])

    if tab == "t-quality":
        n_sig_trend = int((TRENDS["mk_pvalue"] < 0.05).sum())
        n_sig_jump = int((JUMPS["p_value"] < 0.05).sum())
        return dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5("Sanity check des moyennes globales", className="card-title"),
                html.P("18/18 variables dans leur plage climatologique attendue."),
                html.P("CRE_net = -19.7 W/m², conforme IPCC (~-20 W/m²)."),
                html.P(f"Tendances Mann-Kendall significatives : {n_sig_trend} / 21"),
                html.P(f"Sauts CFSR→CFSv2 significatifs : {n_sig_jump} / 21"),
            ])), md=6),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5("Limites identifiées", className="card-title"),
                html.Ul([
                    html.Li("Détendrage linéaire alors que la trend CO2 est cubique"
                            " — courbure résiduelle en U dans le fit stepwise."),
                    html.Li("Corrélations sur résidus modérées (|r| ≤ 0.5) — "
                            "signal interannuel global limité."),
                    html.Li("Discontinuité CFSR→CFSv2 (jan 2011) introduit un saut "
                            "de niveau, ~1.9 sd sur CRE_LW."),
                    html.Li("La phase 0.5° utilise un MK sous-échantillonné (1/16) "
                            "pour les p-values — choix de coût."),
                ]),
            ])), md=6),
            dbc.Col(dcc.Graph(figure=fig_jumps()), md=12),
        ])

    return html.Div("Onglet inconnu")


if __name__ == "__main__":
    app.run(debug=False, port=8050)
