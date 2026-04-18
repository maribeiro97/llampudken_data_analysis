from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import plotly.graph_objects as go

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
        axis_labels = record.metadata.get("axis_labels", ("Time [s]", "Signal [a.u.]"))
        offsets = record.metadata.get("channel_delay_offsets_s", [0.0] * len(record.channels))
        for (ch_name, values), offset in zip(record.channels.items(), offsets):
            ax.plot(record.time - offset, values, label=ch_name)

        ax.set_title(f"Shot {record.shot_number} - {record.oscilloscope_id} (time domain)")
        ax.set_xlabel(axis_labels[0])
        ax.set_ylabel(axis_labels[1])
        ax.legend(loc="best")
        fig.tight_layout()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path)
        plt.close(fig)
        return out_path

    def plot_time_series_html(self, record: SignalRecord, out_path: Path) -> Path:
        axis_labels = record.metadata.get("axis_labels", ("Time [s]", "Signal [a.u.]"))
        offsets = record.metadata.get("channel_delay_offsets_s", [0.0] * len(record.channels))
        fig = go.Figure()
        for (ch_name, values), offset in zip(record.channels.items(), offsets):
            fig.add_trace(
                go.Scatter(
                    x=record.time - offset,
                    y=values,
                    mode="lines",
                    name=ch_name,
                )
            )
        fig.update_layout(
            template="plotly_dark",
            title=f"Shot {record.shot_number} - {record.oscilloscope_id} (time domain)",
            xaxis_title=axis_labels[0],
            yaxis_title=axis_labels[1],
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(out_path, include_plotlyjs="cdn")
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

    def plot_spectrum_html(self, spectrum: SpectrumResults, out_path: Path, shot_label: str) -> Path:
        fig = go.Figure()
        for ch_name, amp in spectrum.amplitudes.items():
            fig.add_trace(go.Scatter(x=spectrum.freqs_hz, y=amp, mode="lines", name=ch_name))
        fig.update_layout(
            template="plotly_dark",
            title=f"Shot {shot_label} (frequency domain)",
            xaxis_title="Frequency [Hz]",
            yaxis_title="Amplitude [a.u.]",
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(out_path, include_plotlyjs="cdn")
        return out_path
