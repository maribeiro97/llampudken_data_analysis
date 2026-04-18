from __future__ import annotations

import matplotlib.pyplot as plt


def apply_style(style: str) -> None:
    """Apply matplotlib style in one place for consistent output."""
    plt.style.use(style)
