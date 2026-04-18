from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class SignalRecord:
    """Container for one oscilloscope text file."""

    shot_number: str
    oscilloscope_id: str
    date_code: str
    file_path: Path
    time: np.ndarray
    channels: dict[str, np.ndarray]
    sampling_rate_hz: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureResults:
    """Time-domain features extracted from a signal record."""

    channel_rms: dict[str, float]
    channel_peak: dict[str, float]


@dataclass
class SpectrumResults:
    """Frequency-domain representation per channel."""

    freqs_hz: np.ndarray
    amplitudes: dict[str, np.ndarray]


@dataclass
class PipelineReport:
    """Pipeline outputs and metadata for one run."""

    files_processed: int
    figure_paths: list[Path]
    notes: list[str] = field(default_factory=list)
