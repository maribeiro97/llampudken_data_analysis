from __future__ import annotations

import numpy as np

from osc_analysis.config import PreprocessingConfig
from osc_analysis.models import SignalRecord


class SignalPreprocessor:
    """Apply basic normalization and optional detrending to each channel."""

    def __init__(self, config: PreprocessingConfig) -> None:
        self.config = config

    def process(self, record: SignalRecord) -> SignalRecord:
        processed_channels: dict[str, np.ndarray] = {}
        for name, values in record.channels.items():
            channel = values.astype(float).copy()
            baseline = np.mean(channel[: self.config.noise_window])
            channel -= baseline
            if self.config.detrend:
                channel -= np.linspace(channel[0], channel[-1], len(channel))
            processed_channels[name] = channel

        return SignalRecord(
            shot_number=record.shot_number,
            oscilloscope_id=record.oscilloscope_id,
            date_code=record.date_code,
            file_path=record.file_path,
            time=record.time.copy(),
            channels=processed_channels,
            sampling_rate_hz=record.sampling_rate_hz,
            metadata={**record.metadata, "preprocessed": True},
        )
