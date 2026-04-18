from __future__ import annotations

import numpy as np

from osc_analysis.models import SignalRecord, SpectrumResults


class SpectralAnalyzer:
    """Compute one-sided FFT amplitude spectra for each channel."""

    def compute(self, record: SignalRecord) -> SpectrumResults:
        if len(record.time) < 2:
            return SpectrumResults(freqs_hz=np.array([]), amplitudes={k: np.array([]) for k in record.channels})

        n = len(record.time)
        freqs = np.fft.rfftfreq(n, d=1.0 / record.sampling_rate_hz)
        amps = {
            k: np.abs(np.fft.rfft(v)) / n
            for k, v in record.channels.items()
        }
        return SpectrumResults(freqs_hz=freqs, amplitudes=amps)
