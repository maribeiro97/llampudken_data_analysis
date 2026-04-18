from __future__ import annotations

import numpy as np

from osc_analysis.models import FeatureResults, SignalRecord


class FeatureExtractor:
    """Extract simple time-domain features channel-by-channel."""

    def extract(self, record: SignalRecord) -> FeatureResults:
        rms = {k: float(np.sqrt(np.mean(v**2))) for k, v in record.channels.items()}
        peak = {k: float(np.max(np.abs(v))) for k, v in record.channels.items()}
        return FeatureResults(channel_rms=rms, channel_peak=peak)
