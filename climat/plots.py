"""Helpers matplotlib/seaborn — équivalents aux thèmes ggplot du projet R."""
from __future__ import annotations
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns


def setup_theme(base_size: int = 12) -> None:
    """Style global équivalent à `theme_minimal(base_size = 12)` de ggplot."""
    sns.set_theme(style="whitegrid", context="notebook")
    mpl.rcParams.update({
        "font.size": base_size,
        "axes.titlesize": base_size + 1,
        "axes.labelsize": base_size,
        "xtick.labelsize": base_size - 1,
        "ytick.labelsize": base_size - 1,
        "legend.fontsize": base_size - 1,
        "figure.dpi": 110,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def save(fig: plt.Figure, path: Path, w: float = 10, h: float = 6,
         dpi: int = 150) -> None:
    """Sauvegarde une figure aux dimensions (en pouces) et résolution voulues."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.set_size_inches(w, h)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
