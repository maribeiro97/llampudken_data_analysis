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
        self._save_matplotlib_outputs(fig, out_path)
        plt.close(fig)
        self.plot_time_series_html(record, out_path.with_suffix(".html"))
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
        self._save_matplotlib_outputs(fig, out_path)
        plt.close(fig)
        self.plot_spectrum_html(spectrum, out_path.with_suffix(".html"), shot_label)
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
            self._channel_time(record_a, chosen_channel),
            record_a.channels[chosen_channel],
            label=f"Shot {record_a.shot_number}",
            alpha=0.65,
        )
        ax.plot(
            self._channel_time(record_b, chosen_channel),
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
        self._save_matplotlib_outputs(fig, out_path)
        plt.close(fig)
        self.plot_shot_overlay_html(record_a, record_b, out_path.with_suffix(".html"), channel_name=chosen_channel)
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

    def compute_range_average_with_ci(
        self,
        records: list[SignalRecord],
        channel_name: str | None = None,
        confidence_z: float = 1.96,
    ) -> dict[str, np.ndarray | float | str | int]:
        """Compute mean curve and confidence interval for a shot range."""
        if not records:
            raise ValueError("At least one record is required.")
        if len(records) < 2:
            raise ValueError("At least two records are required for confidence intervals.")

        chosen_channel = channel_name or self._resolve_channel_name_for_many(records)
        common_t, stacked = self._stack_records_on_common_time(records, chosen_channel)
        mean_curve = np.mean(stacked, axis=0)
        std_curve = np.std(stacked, axis=0, ddof=1)
        se_curve = std_curve / np.sqrt(stacked.shape[0])
        ci_half_width = confidence_z * se_curve

        return {
            "channel_name": chosen_channel,
            "time": common_t,
            "mean": mean_curve,
            "lower_ci": mean_curve - ci_half_width,
            "upper_ci": mean_curve + ci_half_width,
            "sample_count": stacked.shape[0],
            "confidence_z": confidence_z,
        }

    def plot_range_average_with_ci(
        self,
        records: list[SignalRecord],
        out_path: Path,
        channel_name: str | None = None,
        label: str | None = None,
        color: str = "#4C72B0",
    ) -> Path:
        """Plot one shot range as mean curve with confidence band."""
        apply_style(self.style.style)
        stats = self.compute_range_average_with_ci(records, channel_name=channel_name)

        fig, ax = plt.subplots(figsize=(10, 5), dpi=self.style.dpi)
        axis_labels = records[0].metadata.get("axis_labels", ("Time [s]", "Signal [a.u.]"))
        series_label = label or f"Shots {records[0].shot_number}-{records[-1].shot_number}"
        time = stats["time"]
        mean = stats["mean"]
        lower = stats["lower_ci"]
        upper = stats["upper_ci"]

        ax.plot(time, mean, color=color, label=f"{series_label} mean")
        ax.fill_between(time, lower, upper, color=color, alpha=0.25, label="95% CI")
        ax.set_title(f"Range average with confidence interval ({stats['channel_name']})")
        ax.set_xlabel(axis_labels[0])
        ax.set_ylabel(axis_labels[1])
        ax.legend(loc="best")
        fig.tight_layout()
        self._save_matplotlib_outputs(fig, out_path)
        plt.close(fig)
        self.plot_range_average_with_ci_html(
            records,
            out_path.with_suffix(".html"),
            channel_name=stats["channel_name"],
            label=series_label,
            color=color,
        )
        return out_path

    def plot_two_ranges_with_ci(
        self,
        range_a_records: list[SignalRecord],
        range_b_records: list[SignalRecord],
        out_path: Path,
        channel_name: str | None = None,
        label_a: str = "Range A",
        label_b: str = "Range B",
    ) -> Path:
        """Overlay two shot-range mean curves and their confidence intervals."""
        if not range_a_records or not range_b_records:
            raise ValueError("Both ranges must include at least one record.")
        apply_style(self.style.style)

        chosen_channel = channel_name or self._resolve_channel_name_for_many(range_a_records + range_b_records)
        range_a = self.compute_range_average_with_ci(range_a_records, channel_name=chosen_channel)
        range_b = self.compute_range_average_with_ci(range_b_records, channel_name=chosen_channel)
        axis_labels = range_a_records[0].metadata.get("axis_labels", ("Time [s]", "Signal [a.u.]"))

        fig, ax = plt.subplots(figsize=(10, 5), dpi=self.style.dpi)
        ax.plot(range_a["time"], range_a["mean"], color="#4C72B0", label=f"{label_a} mean")
        ax.fill_between(range_a["time"], range_a["lower_ci"], range_a["upper_ci"], color="#4C72B0", alpha=0.25)
        ax.plot(range_b["time"], range_b["mean"], color="#DD8452", label=f"{label_b} mean")
        ax.fill_between(range_b["time"], range_b["lower_ci"], range_b["upper_ci"], color="#DD8452", alpha=0.25)
        ax.set_title(f"Shot-range comparison with confidence intervals ({chosen_channel})")
        ax.set_xlabel(axis_labels[0])
        ax.set_ylabel(axis_labels[1])
        ax.legend(loc="best")
        fig.tight_layout()
        self._save_matplotlib_outputs(fig, out_path)
        plt.close(fig)
        self.plot_two_ranges_with_ci_html(
            range_a_records,
            range_b_records,
            out_path.with_suffix(".html"),
            channel_name=chosen_channel,
            label_a=label_a,
            label_b=label_b,
        )
        return out_path

    def compute_channel_mean_curve(
        self,
        records: list[SignalRecord],
        channel_name: str,
    ) -> dict[str, np.ndarray | str | int]:
        """Compute aligned mean curve for a single channel across many shots."""
        if len(records) < 1:
            raise ValueError("At least one record is required.")
        common_t, stacked = self._stack_records_on_common_time(records, channel_name)
        return {
            "channel_name": channel_name,
            "time": common_t,
            "mean": np.mean(stacked, axis=0),
            "sample_count": stacked.shape[0],
        }

    def plot_channel_mean_across_shots(
        self,
        records: list[SignalRecord],
        out_path: Path,
        channel_name: str,
        label: str = "Mean curve",
        color: str = "#55A868",
    ) -> Path:
        """Plot only the mean curve for one channel across multiple shots."""
        apply_style(self.style.style)
        mean_stats = self.compute_channel_mean_curve(records, channel_name)
        axis_labels = records[0].metadata.get("axis_labels", ("Time [s]", "Signal [a.u.]"))

        fig, ax = plt.subplots(figsize=(10, 5), dpi=self.style.dpi)
        ax.plot(mean_stats["time"], mean_stats["mean"], color=color, label=f"{label} (n={mean_stats['sample_count']})")
        ax.set_title(f"Mean curve across shots ({channel_name})")
        ax.set_xlabel(axis_labels[0])
        ax.set_ylabel(axis_labels[1])
        ax.legend(loc="best")
        fig.tight_layout()
        self._save_matplotlib_outputs(fig, out_path)
        plt.close(fig)
        self.plot_channel_mean_across_shots_html(
            records,
            out_path.with_suffix(".html"),
            channel_name=channel_name,
            label=label,
            color=color,
        )
        return out_path

    def plot_shot_overlay_html(
        self,
        record_a: SignalRecord,
        record_b: SignalRecord,
        out_path: Path,
        channel_name: str | None = None,
    ) -> Path:
        """HTML counterpart for shot overlay plot."""
        chosen_channel = channel_name or self._resolve_channel_name(record_a, record_b)
        axis_labels = record_a.metadata.get("axis_labels", ("Time [s]", "Signal [a.u.]"))
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=self._channel_time(record_a, chosen_channel),
                y=record_a.channels[chosen_channel],
                mode="lines",
                name=f"Shot {record_a.shot_number}",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=self._channel_time(record_b, chosen_channel),
                y=record_b.channels[chosen_channel],
                mode="lines",
                name=f"Shot {record_b.shot_number}",
            )
        )
        fig.update_layout(
            template="plotly_dark",
            title=f"Shot overlay ({chosen_channel})",
            xaxis_title=axis_labels[0],
            yaxis_title=axis_labels[1],
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(out_path, include_plotlyjs="cdn")
        return out_path

    def plot_range_average_with_ci_html(
        self,
        records: list[SignalRecord],
        out_path: Path,
        channel_name: str | None = None,
        label: str | None = None,
        color: str = "#4C72B0",
    ) -> Path:
        """HTML counterpart for one shot-range mean+CI plot."""
        stats = self.compute_range_average_with_ci(records, channel_name=channel_name)
        axis_labels = records[0].metadata.get("axis_labels", ("Time [s]", "Signal [a.u.]"))
        series_label = label or f"Shots {records[0].shot_number}-{records[-1].shot_number}"

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=stats["time"], y=stats["upper_ci"], mode="lines", line={"width": 0}, showlegend=False)
        )
        fig.add_trace(
            go.Scatter(
                x=stats["time"],
                y=stats["lower_ci"],
                mode="lines",
                line={"width": 0},
                fill="tonexty",
                fillcolor="rgba(76, 114, 176, 0.25)",
                name="95% CI",
            )
        )
        fig.add_trace(
            go.Scatter(x=stats["time"], y=stats["mean"], mode="lines", line={"color": color}, name=f"{series_label} mean")
        )
        fig.update_layout(
            template="plotly_dark",
            title=f"Range average with confidence interval ({stats['channel_name']})",
            xaxis_title=axis_labels[0],
            yaxis_title=axis_labels[1],
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(out_path, include_plotlyjs="cdn")
        return out_path

    def plot_two_ranges_with_ci_html(
        self,
        range_a_records: list[SignalRecord],
        range_b_records: list[SignalRecord],
        out_path: Path,
        channel_name: str | None = None,
        label_a: str = "Range A",
        label_b: str = "Range B",
    ) -> Path:
        """HTML counterpart for two shot-range comparison."""
        chosen_channel = channel_name or self._resolve_channel_name_for_many(range_a_records + range_b_records)
        range_a = self.compute_range_average_with_ci(range_a_records, channel_name=chosen_channel)
        range_b = self.compute_range_average_with_ci(range_b_records, channel_name=chosen_channel)
        axis_labels = range_a_records[0].metadata.get("axis_labels", ("Time [s]", "Signal [a.u.]"))

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=range_a["time"], y=range_a["upper_ci"], mode="lines", line={"width": 0}, showlegend=False))
        fig.add_trace(
            go.Scatter(
                x=range_a["time"],
                y=range_a["lower_ci"],
                mode="lines",
                line={"width": 0},
                fill="tonexty",
                fillcolor="rgba(76, 114, 176, 0.25)",
                name=f"{label_a} 95% CI",
            )
        )
        fig.add_trace(go.Scatter(x=range_a["time"], y=range_a["mean"], mode="lines", line={"color": "#4C72B0"}, name=f"{label_a} mean"))
        fig.add_trace(go.Scatter(x=range_b["time"], y=range_b["upper_ci"], mode="lines", line={"width": 0}, showlegend=False))
        fig.add_trace(
            go.Scatter(
                x=range_b["time"],
                y=range_b["lower_ci"],
                mode="lines",
                line={"width": 0},
                fill="tonexty",
                fillcolor="rgba(221, 132, 82, 0.25)",
                name=f"{label_b} 95% CI",
            )
        )
        fig.add_trace(go.Scatter(x=range_b["time"], y=range_b["mean"], mode="lines", line={"color": "#DD8452"}, name=f"{label_b} mean"))
        fig.update_layout(
            template="plotly_dark",
            title=f"Shot-range comparison with confidence intervals ({chosen_channel})",
            xaxis_title=axis_labels[0],
            yaxis_title=axis_labels[1],
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(out_path, include_plotlyjs="cdn")
        return out_path

    def plot_channel_mean_across_shots_html(
        self,
        records: list[SignalRecord],
        out_path: Path,
        channel_name: str,
        label: str = "Mean curve",
        color: str = "#55A868",
    ) -> Path:
        """HTML counterpart for channel mean across shots."""
        mean_stats = self.compute_channel_mean_curve(records, channel_name)
        axis_labels = records[0].metadata.get("axis_labels", ("Time [s]", "Signal [a.u.]"))
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=mean_stats["time"],
                y=mean_stats["mean"],
                mode="lines",
                line={"color": color},
                name=f"{label} (n={mean_stats['sample_count']})",
            )
        )
        fig.update_layout(
            template="plotly_dark",
            title=f"Mean curve across shots ({channel_name})",
            xaxis_title=axis_labels[0],
            yaxis_title=axis_labels[1],
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(out_path, include_plotlyjs="cdn")
        return out_path

    @staticmethod
    def _resolve_channel_name(record_a: SignalRecord, record_b: SignalRecord) -> str:
        common = [name for name in record_a.channels if name in record_b.channels]
        if not common:
            raise ValueError("No common channel names found between the two records.")
        return common[0]

    @staticmethod
    def _align_channel_to_common_time(
        record_a: SignalRecord,
        record_b: SignalRecord,
        channel_name: str,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        time_a = FigureBuilder._channel_time(record_a, channel_name)
        time_b = FigureBuilder._channel_time(record_b, channel_name)
        start = max(float(time_a[0]), float(time_b[0]))
        end = min(float(time_a[-1]), float(time_b[-1]))
        if start >= end:
            return np.array([]), np.array([]), np.array([])

        sample_count = int(min(time_a.size, time_b.size))
        common_t = np.linspace(start, end, sample_count)
        a_interp = np.interp(common_t, time_a, record_a.channels[channel_name])
        b_interp = np.interp(common_t, time_b, record_b.channels[channel_name])
        return common_t, a_interp, b_interp

    @staticmethod
    def _resolve_channel_name_for_many(records: list[SignalRecord]) -> str:
        common_channels = set(records[0].channels.keys())
        for record in records[1:]:
            common_channels.intersection_update(record.channels.keys())
        if not common_channels:
            raise ValueError("No common channel names found across the selected records.")
        return sorted(common_channels)[0]

    @staticmethod
    def _stack_records_on_common_time(
        records: list[SignalRecord],
        channel_name: str,
    ) -> tuple[np.ndarray, np.ndarray]:
        aligned_times = [FigureBuilder._channel_time(record, channel_name) for record in records]
        start = max(float(time[0]) for time in aligned_times)
        end = min(float(time[-1]) for time in aligned_times)
        if start >= end:
            raise ValueError("Selected records do not have overlapping time support.")

        sample_count = min(time.size for time in aligned_times)
        common_t = np.linspace(start, end, sample_count)
        stacked = np.vstack(
            [
                np.interp(common_t, record_time, record.channels[channel_name])
                for record_time, record in zip(aligned_times, records)
            ]
        )
        return common_t, stacked

    @staticmethod
    def _channel_time(record: SignalRecord, channel_name: str) -> np.ndarray:
        channels = list(record.channels.keys())
        try:
            channel_index = channels.index(channel_name)
        except ValueError:
            channel_index = 0
        offsets = record.metadata.get("channel_delay_offsets_s", [0.0] * len(channels))
        offset = offsets[channel_index] if channel_index < len(offsets) else 0.0
        return record.time - float(offset)

    @staticmethod
    def _save_matplotlib_outputs(fig: plt.Figure, out_path: Path) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, bbox_inches="tight")
        fig.savefig(out_path.with_suffix(".pdf"), bbox_inches="tight")
        fig.savefig(out_path.with_suffix(".svg"), bbox_inches="tight")
