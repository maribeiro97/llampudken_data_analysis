from __future__ import annotations

import matplotlib.pyplot as plt


def apply_style(style: str) -> None:
    """Apply matplotlib style in one place for consistent output."""
    plt.style.use(style)
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "axes.edgecolor": "black",
            "axes.labelcolor": "black",
            "xtick.color": "black",
            "ytick.color": "black",
            "grid.color": "#D8D8D8",
            "font.size": 11,
            "axes.titlesize": 12,
            "axes.labelsize": 11,
            "legend.fontsize": 10,
            "figure.dpi": 300,
            "savefig.dpi": 300,
        }
    )
