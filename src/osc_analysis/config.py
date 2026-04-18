from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PreprocessingConfig:
    """Parameters for signal preprocessing."""

    noise_window: int = 1_000
    detrend: bool = True
    smoothing_window: int = 31


@dataclass(frozen=True)
class PlotStyleConfig:
    """Plot style controls used for all generated figures."""

    style: str = "dark_background"
    dpi: int = 120


@dataclass(frozen=True)
class PipelineConfig:
    """High-level pipeline configuration."""

    input_dir: Path
    output_dir: Path
    preprocess: PreprocessingConfig = PreprocessingConfig()
    plot_style: PlotStyleConfig = PlotStyleConfig()
