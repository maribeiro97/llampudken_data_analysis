from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import seaborn as sns

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

    def plot_shot_overlay(
        self,
        record_a: SignalRecord,
        record_b: SignalRecord,
        out_path: Path,
        channel_name: str | None = None,
    ) -> Path:
        """Overlay one channel from two shots on shared axes for visual comparison."""
        apply_style(self.style.style)
        fig, ax = plt.subplots(figsize=(10, 5), dpi=self.style.dpi)
        chosen_channel = channel_name or self._resolve_channel_name(record_a, record_b)

        ax.plot(
            record_a.time,
            record_a.channels[chosen_channel],
            label=f"Shot {record_a.shot_number}",
            alpha=0.65,
        )
        ax.plot(
            record_b.time,
            record_b.channels[chosen_channel],
            label=f"Shot {record_b.shot_number}",
            alpha=0.65,
        )
        axis_labels = record_a.metadata.get("axis_labels", ("Time [s]", "Signal [a.u.]"))
        ax.set_title(f"Shot overlay ({chosen_channel})")
        ax.set_xlabel(axis_labels[0])
        ax.set_ylabel(axis_labels[1])
        ax.legend(loc="best")
        fig.tight_layout()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path)
        plt.close(fig)
        return out_path

    def plot_shot_difference_heatmap(
        self,
        record_a: SignalRecord,
        record_b: SignalRecord,
        out_path: Path,
        channel_name: str | None = None,
        bins: int = 75,
    ) -> Path:
        """Plot a 2D density difference map (shot B - shot A) for one channel."""
        apply_style(self.style.style)
        chosen_channel = channel_name or self._resolve_channel_name(record_a, record_b)
        t_a, y_a = self._normalize_to_unit_square(record_a.time, record_a.channels[chosen_channel])
        t_b, y_b = self._normalize_to_unit_square(record_b.time, record_b.channels[chosen_channel])

        hist_a, xedges, yedges = np.histogram2d(t_a, y_a, bins=bins, range=[[0.0, 1.0], [0.0, 1.0]])
        hist_b, _, _ = np.histogram2d(t_b, y_b, bins=[xedges, yedges])
        diff = hist_b - hist_a

        fig, ax = plt.subplots(figsize=(8, 6), dpi=self.style.dpi)
        vlim = float(np.max(np.abs(diff))) if np.any(diff) else 1.0
        mesh = ax.pcolormesh(xedges, yedges, diff.T, cmap="coolwarm", vmin=-vlim, vmax=vlim, shading="auto")
        fig.colorbar(mesh, ax=ax, label="Density difference (Shot B - Shot A)")
        ax.set_title(f"Difference heatmap ({chosen_channel})")
        ax.set_xlabel("Normalized time")
        ax.set_ylabel("Normalized amplitude")
        fig.tight_layout()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path)
        plt.close(fig)
        return out_path

    def plot_shot_kde_panel(
        self,
        record_a: SignalRecord,
        record_b: SignalRecord,
        out_path: Path,
        channel_name: str | None = None,
    ) -> Path:
        """Create side-by-side KDE panel for two shots plus direct overlay."""
        apply_style(self.style.style)
        chosen_channel = channel_name or self._resolve_channel_name(record_a, record_b)

        t_a, y_a = self._normalize_to_unit_square(record_a.time, record_a.channels[chosen_channel])
        t_b, y_b = self._normalize_to_unit_square(record_b.time, record_b.channels[chosen_channel])

        fig, axes = plt.subplots(1, 3, figsize=(16, 5), dpi=self.style.dpi, sharex=True, sharey=True)
        sns.kdeplot(x=t_a, y=y_a, fill=True, thresh=0.05, levels=15, cmap="Blues", ax=axes[0])
        axes[0].set_title(f"Shot {record_a.shot_number} density")
        sns.kdeplot(x=t_b, y=y_b, fill=True, thresh=0.05, levels=15, cmap="Oranges", ax=axes[1])
        axes[1].set_title(f"Shot {record_b.shot_number} density")
        sns.kdeplot(x=t_a, y=y_a, fill=False, levels=10, color="#4C72B0", ax=axes[2])
        sns.kdeplot(x=t_b, y=y_b, fill=False, levels=10, color="#DD8452", ax=axes[2])
        axes[2].set_title("Contour overlay")
        axes[2].plot([], [], color="#4C72B0", label=f"Shot {record_a.shot_number}")
        axes[2].plot([], [], color="#DD8452", label=f"Shot {record_b.shot_number}")
        axes[2].legend(loc="best")

        for ax in axes:
            ax.set_xlabel("Normalized time")
            ax.set_ylabel("Normalized amplitude")

        fig.suptitle(f"Shot comparison panel ({chosen_channel})")
        fig.tight_layout()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path)
        plt.close(fig)
        return out_path

    def compute_shot_comparison_metrics(
        self,
        record_a: SignalRecord,
        record_b: SignalRecord,
        channel_name: str | None = None,
    ) -> dict[str, float]:
        """Return lightweight numeric metrics to complement the visual comparison."""
        chosen_channel = channel_name or self._resolve_channel_name(record_a, record_b)
        common_t, a_interp, b_interp = self._align_channel_to_common_time(record_a, record_b, chosen_channel)
        if common_t.size < 2:
            raise ValueError("Need at least two shared samples to compare two shots.")

        delta = b_interp - a_interp
        centroid_shift = float(np.mean(delta))
        rms_delta = float(np.sqrt(np.mean(np.square(delta))))
        peak_delta = float(np.max(np.abs(delta)))
        corrcoef = float(np.corrcoef(a_interp, b_interp)[0, 1])
        area_delta = float(np.trapezoid(np.abs(delta), common_t))

        return {
            "centroid_shift": centroid_shift,
            "rms_delta": rms_delta,
            "peak_delta": peak_delta,
            "correlation": corrcoef,
            "area_delta": area_delta,
        }

    @staticmethod
    def _resolve_channel_name(record_a: SignalRecord, record_b: SignalRecord) -> str:
        common = [name for name in record_a.channels if name in record_b.channels]
        if not common:
            raise ValueError("No common channel names found between the two records.")
        return common[0]

    @staticmethod
    def _normalize_to_unit_square(time_values: np.ndarray, signal_values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        time_min = float(np.min(time_values))
        time_span = float(np.max(time_values) - time_min)
        signal_min = float(np.min(signal_values))
        signal_span = float(np.max(signal_values) - signal_min)
        norm_t = np.zeros_like(time_values) if time_span == 0.0 else (time_values - time_min) / time_span
        norm_y = np.zeros_like(signal_values) if signal_span == 0.0 else (signal_values - signal_min) / signal_span
        return norm_t, norm_y

    @staticmethod
    def _align_channel_to_common_time(
        record_a: SignalRecord,
        record_b: SignalRecord,
        channel_name: str,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        start = max(float(record_a.time[0]), float(record_b.time[0]))
        end = min(float(record_a.time[-1]), float(record_b.time[-1]))
        if start >= end:
            return np.array([]), np.array([]), np.array([])

        sample_count = int(min(record_a.time.size, record_b.time.size))
        common_t = np.linspace(start, end, sample_count)
        a_interp = np.interp(common_t, record_a.time, record_a.channels[channel_name])
        b_interp = np.interp(common_t, record_b.time, record_b.channels[channel_name])
        return common_t, a_interp, b_interp
