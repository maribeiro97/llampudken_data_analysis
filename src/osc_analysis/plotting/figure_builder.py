from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from osc_analysis.config import PlotStyleConfig
from osc_analysis.models import SignalRecord, SpectrumResults
from osc_analysis.plotting.plot_style import apply_style


class FigureBuilder:
    """Create and save figures equivalent to MATLAB outputs."""

    def __init__(self, style: PlotStyleConfig) -> None:
        self.style = style

    def plot_time_series(self, record: SignalRecord, out_path: Path) -> Path:
        apply_style(self.style.style)
        fig, ax = plt.subplots(figsize=(10, 5), dpi=self.style.dpi)
        for ch_name, values in record.channels.items():
            ax.plot(record.time, values, label=ch_name)

        ax.set_title(f"Shot {record.shot_number} - {record.oscilloscope_id} (time domain)")
        ax.set_xlabel("Time [s]")
        ax.set_ylabel("Signal [a.u.]")
        ax.legend(loc="best")
        fig.tight_layout()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path)
        plt.close(fig)
        return out_path

    def plot_spectrum(self, spectrum: SpectrumResults, out_path: Path, shot_label: str) -> Path:
        apply_style(self.style.style)
        fig, ax = plt.subplots(figsize=(10, 5), dpi=self.style.dpi)
        for ch_name, amp in spectrum.amplitudes.items():
            ax.plot(spectrum.freqs_hz, amp, label=ch_name)

        ax.set_title(f"Shot {shot_label} (frequency domain)")
        ax.set_xlabel("Frequency [Hz]")
        ax.set_ylabel("Amplitude [a.u.]")
        ax.legend(loc="best")
        fig.tight_layout()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path)
        plt.close(fig)
        return out_path
