"""Export downsampled trend (Sen slope) and correlation grids to JSON
for the dashboard-v2 globe overlay.

Input  : outputs/phase3_climat_05/{trend,correlation}_grids.pkl
         each is dict[var] -> (slope, pval) or float32 array (720, 361)
         shape = (lon=720@0.5deg, lat=361@0.5deg, idx0 = lat -90)

Output : dashboard-v2/data/trend_grids_36x18.json
         { "lat": [-85,-75,...,+85], "lon": [5,15,...,355], "vars": { VAR: {
             "sen":  { "grid": [[...18 rows of 36 cols...]],
                       "vmin": float, "vmax": float, "unit": str, "label": str },
             "corr": { "grid": [[...]], "vmin": -1, "vmax": 1, "label": "Corr. CO2 resid." } } } }

The grid orientation matches the existing T2M_TREND_GRID in data.jsx:
  row 0  = lat -85
  row 17 = lat +85
  col 0  = lon   5 (block 0..10)
  col 35 = lon 355 (block 350..360)
"""
import json
import pickle
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parents[2]
PHASE3 = HERE / "outputs" / "phase3_climat_05"
DASH = HERE / "dashboard-v2" / "data"

with open(PHASE3 / "trend_grids.pkl", "rb") as f:
    trend = pickle.load(f)
with open(PHASE3 / "correlation_grids.pkl", "rb") as f:
    corr = pickle.load(f)

# Same unit map as ALL_VARS_FULL in data.jsx (only source vars, no CRE)
UNITS = {
    "T2m": "K", "T500": "K", "SPFH2m": "kg/kg", "PWAT": "kg/m²",
    "APCP": "kg/m²", "TCDC": "%", "DLWRF": "W/m²", "ULWRF": "W/m²",
    "DSWRF": "W/m²", "USWRF": "W/m²", "PRMSL": "Pa",
    "CSDSF": "W/m²", "CSUSF": "W/m²", "CSDLF": "W/m²", "CSULF": "W/m²",
    "CDUVB": "W/m²", "DUVB": "W/m²", "ALBDO": "%",
}


def downsample(arr_lonlat: np.ndarray) -> np.ndarray:
    """720x361 -> 18x36 with block-mean. Drop the last lat (=+90) to make 360 divisible.
    Returns shape (18 lat, 36 lon) with row 0 = lat -85, row 17 = lat +85.
    """
    # arr shape: (lon=720, lat=361)
    # Truncate lat axis to 360 (drop the +90 pole row)
    a = arr_lonlat[:, :360]            # (720, 360)
    # block-mean: 20 lon per block, 20 lat per block
    a = a.reshape(36, 20, 18, 20)
    a = np.nanmean(a, axis=(1, 3))     # (36 lon, 18 lat)
    # Transpose to (18 lat, 36 lon) and flip lat so row 0 = -85
    a = a.T                            # (18 lat, 36 lon)  -- already lat -90..+89.5 ascending
    return a.astype(float)


def percentile_bounds(arr: np.ndarray, lo=1, hi=99):
    return float(np.nanpercentile(arr, lo)), float(np.nanpercentile(arr, hi))


lat_centers = [-85 + 10 * i for i in range(18)]   # -85..+85
lon_centers = [   5 + 10 * i for i in range(36)]  #   5..355

out = {
    "schema": 1,
    "lat": lat_centers,
    "lon": lon_centers,
    "shape": [18, 36],
    "note": "Downsampled (block-mean 20x20) from 0.5° pipeline. row=lat, col=lon. NaN-safe.",
    "vars": {},
}

for var in sorted(trend.keys()):
    slope = trend[var]["slope"]    # (720, 361)
    g_sen = downsample(slope).round(6).tolist()
    vmin_s, vmax_s = percentile_bounds(slope)
    # Symmetrize around 0 for divergent colormap legend
    vabs_s = max(abs(vmin_s), abs(vmax_s))
    sen_label = f"Pente Sen ({UNITS.get(var, '')}/an)" if UNITS.get(var) else "Pente Sen (/an)"

    g_corr = None
    if var in corr:
        c = corr[var]                # (720, 361)
        g_corr = downsample(c).round(4).tolist()

    out["vars"][var] = {
        "unit": UNITS.get(var, ""),
        "sen": {
            "grid": g_sen,
            "vmin": round(-vabs_s, 6),
            "vmax": round(+vabs_s, 6),
            "unit": UNITS.get(var, ""),
            "label": sen_label,
        },
    }
    if g_corr is not None:
        out["vars"][var]["corr"] = {
            "grid": g_corr,
            "vmin": -0.4,
            "vmax": +0.4,
            "label": "Corr. CO₂ résiduel",
        }

DASH.mkdir(parents=True, exist_ok=True)
out_path = DASH / "trend_grids_36x18.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

size_kb = out_path.stat().st_size / 1024
print(f"✓ Wrote {out_path} ({size_kb:.1f} KB)")
print(f"  Variables: {len(out['vars'])}")
print(f"  Shape per grid: {out['shape']}")
print(f"  Sample (T2m sen): vmin={out['vars']['T2m']['sen']['vmin']}, "
      f"vmax={out['vars']['T2m']['sen']['vmax']}")
