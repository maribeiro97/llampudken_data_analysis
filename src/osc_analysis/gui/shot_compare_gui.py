from __future__ import annotations

import logging
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import plotly.colors as plotly_colors
import plotly.graph_objects as go

from osc_analysis.config import PipelineConfig
from osc_analysis.gui.data_index import (
    available_oscilloscopes_for_shot,
    build_shot_scope_index,
    common_oscilloscopes_for_shots,
)
from osc_analysis.io.data_loader import DataLoader

try:
    from PySide6.QtWidgets import (
        QApplication,
        QComboBox,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QPushButton,
        QAbstractItemView,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtCore import QUrl
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError as exc:  # pragma: no cover - platform dependent
    raise RuntimeError(
        "PySide6 with QtWebEngine is required for the interactive Plotly GUI."
    ) from exc


SINGLE_SHOT_MODE = "Single shot (all oscilloscopes)"
COMPARE_MODE = "Compare two shots"
MULTI_SHOT_MODE = "Custom shot selection"
ALL_CHANNELS_OPTION = "All channels"
INDIVIDUAL_SHOTS_OPTION = "Plot individual shot traces"
AVERAGE_WITH_CI_OPTION = "Plot average with 95% CI"
logger = logging.getLogger(__name__)


@dataclass
class ScopeTabState:
    """State and widgets for one oscilloscope tab."""

    channel_combo: QComboBox
    message_label: QLabel
    web_view: QWebEngineView


class ShotComparisonGUI(QMainWindow):
    """PySide GUI with interactive Plotly charts for oscilloscope shots."""

    def __init__(
        self,
        loader_factory: Callable[[Path], DataLoader] = DataLoader,
        config: PipelineConfig | None = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Oscilloscope shot comparison")
        self.resize(1400, 900)

        self.config = config or PipelineConfig(input_dir=Path("osc_data"), output_dir=Path("outputs"))
        self.loader = loader_factory(self.config.input_dir)
        self.index = build_shot_scope_index(self.loader)
        logger.info("Loaded shot index from %s with %d shots.", self.config.input_dir, len(self.index))

        self._records_cache: dict[Path, object] = {}
        self._temp_dir = Path(tempfile.mkdtemp(prefix="osc_plotly_"))
        logger.info("Using temporary Plotly output directory: %s", self._temp_dir)
        self.shots = sorted(self.index.keys(), key=int)
        self.tabs: dict[str, ScopeTabState] = {}

        self.mode_combo = QComboBox()
        self.single_shot_combo = QComboBox()
        self.compare_shot_a_combo = QComboBox()
        self.compare_shot_b_combo = QComboBox()
        self.multi_shot_list = QListWidget()
        self.scope_hint_label = QLabel()
        self.plot_mode_combo = QComboBox()
        self.plot_all_button = QPushButton("Plot all oscilloscopes")
        self.notebook = QTabWidget()

        self._build_layout()
        self._wire_events()
        self._refresh_from_selection()

    def _build_layout(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)

        # Left options panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        left_layout.addWidget(QLabel("Plot mode"))
        self.mode_combo.addItems([SINGLE_SHOT_MODE, COMPARE_MODE, MULTI_SHOT_MODE])
        left_layout.addWidget(self.mode_combo)

        left_layout.addWidget(QLabel("Single-shot selection"))
        self.single_shot_combo.addItems(self.shots)
        left_layout.addWidget(self.single_shot_combo)

        left_layout.addWidget(QLabel("Compare selection: Shot A"))
        self.compare_shot_a_combo.addItems(self.shots)
        left_layout.addWidget(self.compare_shot_a_combo)

        left_layout.addWidget(QLabel("Compare selection: Shot B"))
        self.compare_shot_b_combo.addItems(self.shots)
        if len(self.shots) > 1:
            self.compare_shot_b_combo.setCurrentIndex(1)
        left_layout.addWidget(self.compare_shot_b_combo)

        left_layout.addWidget(QLabel("Custom shot selection"))
        self.multi_shot_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for index, shot in enumerate(self.shots):
            item = QListWidgetItem(shot)
            self.multi_shot_list.addItem(item)
            if index < 2:
                item.setSelected(True)
        left_layout.addWidget(self.multi_shot_list)

        self.scope_hint_label.setWordWrap(True)
        left_layout.addWidget(self.scope_hint_label)

        left_layout.addWidget(QLabel("Trace mode"))
        self.plot_mode_combo.addItems([INDIVIDUAL_SHOTS_OPTION, AVERAGE_WITH_CI_OPTION])
        left_layout.addWidget(self.plot_mode_combo)

        left_layout.addWidget(self.plot_all_button)
        left_layout.addStretch()

        layout.addWidget(left_panel, 0)
        layout.addWidget(self.notebook, 1)

    def _wire_events(self) -> None:
        self.mode_combo.currentTextChanged.connect(lambda _text: self._refresh_from_selection())
        self.single_shot_combo.currentTextChanged.connect(lambda _text: self._refresh_from_selection())
        self.compare_shot_a_combo.currentTextChanged.connect(lambda _text: self._refresh_from_selection())
        self.compare_shot_b_combo.currentTextChanged.connect(lambda _text: self._refresh_from_selection())
        self.multi_shot_list.itemSelectionChanged.connect(self._refresh_from_selection)
        self.plot_mode_combo.currentTextChanged.connect(lambda _text: self.plot_all_tabs())
        self.plot_all_button.clicked.connect(self.plot_all_tabs)

    def _refresh_from_selection(self) -> None:
        mode = self.mode_combo.currentText()
        is_single = mode == SINGLE_SHOT_MODE
        is_compare = mode == COMPARE_MODE
        is_multi = mode == MULTI_SHOT_MODE
        self.single_shot_combo.setEnabled(is_single)
        self.compare_shot_a_combo.setEnabled(is_compare)
        self.compare_shot_b_combo.setEnabled(is_compare)
        self.multi_shot_list.setEnabled(is_multi)

        self._refresh_scope_hint()
        self._rebuild_tabs()
        logger.info(
            "Selection changed | mode=%s | shots=%s | scopes=%s",
            self.mode_combo.currentText(),
            self._active_shots(),
            self._active_scopes(),
        )

    def _active_shots(self) -> list[str]:
        mode = self.mode_combo.currentText()
        if mode == SINGLE_SHOT_MODE:
            return [self.single_shot_combo.currentText()]
        if mode == COMPARE_MODE:
            return [self.compare_shot_a_combo.currentText(), self.compare_shot_b_combo.currentText()]
        selected = [item.text() for item in self.multi_shot_list.selectedItems()]
        if selected:
            return selected
        if self.shots:
            return [self.shots[0]]
        return [self.compare_shot_a_combo.currentText(), self.compare_shot_b_combo.currentText()]

    def _active_scopes(self) -> list[str]:
        active_shots = self._active_shots()
        if not active_shots:
            return []
        if len(active_shots) == 1:
            return available_oscilloscopes_for_shot(self.index, active_shots[0])
        return common_oscilloscopes_for_shots(self.index, active_shots)

    def _refresh_scope_hint(self) -> None:
        active_shots = self._active_shots()
        if len(active_shots) == 1:
            shot = active_shots[0]
            scopes = available_oscilloscopes_for_shot(self.index, shot)
            self.scope_hint_label.setText(
                f"Mode: {SINGLE_SHOT_MODE}\n"
                f"Shot {shot} available scopes: {', '.join(scopes) or 'none'}"
            )
            return

        shot_lines = []
        for shot in active_shots:
            scopes_for_shot = available_oscilloscopes_for_shot(self.index, shot)
            shot_lines.append(f"Shot {shot} scopes: {', '.join(scopes_for_shot) or 'none'}")
        common = common_oscilloscopes_for_shots(self.index, active_shots)
        self.scope_hint_label.setText(
            f"Mode: {self.mode_combo.currentText()}\n"
            + "\n".join(shot_lines)
            + f"\nCommon: {', '.join(common) or 'none'}"
        )

    def _rebuild_tabs(self) -> None:
        self.notebook.clear()
        self.tabs.clear()
        logger.info("Rebuilding oscilloscope tabs.")

        for scope in self._active_scopes():
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)

            top_bar = QHBoxLayout()
            top_bar.addWidget(QLabel("Channel"))

            channel_combo = QComboBox()
            channels = self._channels_for_scope(scope)
            channel_combo.addItems(channels)
            channel_combo.currentTextChanged.connect(lambda _text, s=scope: self.plot_for_scope(s))
            top_bar.addWidget(channel_combo)

            message = QLabel("Ready to plot." if channels else "No available channels for current selection.")
            top_bar.addWidget(message)
            top_bar.addStretch()

            plot_button = QPushButton("Plot")
            plot_button.setEnabled(bool(channels))
            plot_button.clicked.connect(lambda _checked=False, s=scope: self.plot_for_scope(s))
            top_bar.addWidget(plot_button)

            tab_layout.addLayout(top_bar)

            web_view = QWebEngineView()
            tab_layout.addWidget(web_view)

            self.tabs[scope] = ScopeTabState(
                channel_combo=channel_combo,
                message_label=message,
                web_view=web_view,
            )
            self.notebook.addTab(tab, scope)
            logger.info("Created tab for scope=%s with %d channel options.", scope, len(channels))

        self.plot_all_tabs()

    def _channels_for_scope(self, scope: str) -> list[str]:
        active_shots = self._active_shots()
        if len(active_shots) == 1:
            shot = active_shots[0]
            record = self._load_record(self.index[shot][scope])
            return [ALL_CHANNELS_OPTION, *sorted(record.channels.keys())]

        records = []
        for shot in active_shots:
            if scope not in self.index.get(shot, {}):
                return []
            records.append(self._load_record(self.index[shot][scope]))
        if not records:
            return []
        common_channels = set(records[0].channels.keys())
        for record in records[1:]:
            common_channels &= set(record.channels.keys())
        common_channels = sorted(common_channels)
        return [ALL_CHANNELS_OPTION, *common_channels]

    @staticmethod
    def _selected_channels(record, selected_channel: str) -> list[str]:
        if selected_channel == ALL_CHANNELS_OPTION:
            return sorted(record.channels.keys())
        return [selected_channel]

    @staticmethod
    def _compute_average_with_ci(records: list, channel_name: str, confidence_z: float = 1.96) -> dict[str, np.ndarray | int]:
        if not records:
            raise ValueError("At least one record is required to compute averages.")

        start = max(float(record.time[0]) for record in records)
        end = min(float(record.time[-1]) for record in records)
        if end <= start:
            raise ValueError("Selected shots do not share an overlapping time window.")

        common_time = records[0].time
        common_time = common_time[(common_time >= start) & (common_time <= end)]
        if common_time.size < 2:
            raise ValueError("Need at least two common samples to compute average traces.")

        aligned = [np.interp(common_time, record.time, record.channels[channel_name]) for record in records]
        stacked = np.vstack(aligned)
        mean_curve = np.mean(stacked, axis=0)

        if stacked.shape[0] == 1:
            lower_ci = mean_curve
            upper_ci = mean_curve
        else:
            std_curve = np.std(stacked, axis=0, ddof=1)
            se_curve = std_curve / np.sqrt(stacked.shape[0])
            ci_half_width = confidence_z * se_curve
            lower_ci = mean_curve - ci_half_width
            upper_ci = mean_curve + ci_half_width

        return {
            "time": common_time,
            "mean": mean_curve,
            "lower_ci": lower_ci,
            "upper_ci": upper_ci,
            "sample_count": stacked.shape[0],
        }

    def _load_record(self, path: Path):
        if path not in self._records_cache:
            self._records_cache[path] = self.loader.load_file(path)
        return self._records_cache[path]

    @staticmethod
    def _ci_fill_color(hex_color: str, alpha: float = 0.25) -> str:
        color = hex_color.lstrip("#")
        red = int(color[0:2], 16)
        green = int(color[2:4], 16)
        blue = int(color[4:6], 16)
        return f"rgba({red}, {green}, {blue}, {alpha})"

    def _build_plotly_figure(self, scope: str, channel_name: str) -> go.Figure:
        active_shots = self._active_shots()
        fig = go.Figure()

        if len(active_shots) == 1:
            shot = active_shots[0]
            record = self._load_record(self.index[shot][scope])
            for selected_channel in self._selected_channels(record, channel_name):
                fig.add_trace(
                    go.Scatter(
                        x=record.time,
                        y=record.channels[selected_channel],
                        mode="lines",
                        name=f"Shot {shot} - {selected_channel}",
                    )
                )
            axis_labels = record.metadata.get("axis_labels", ("Time [s]", "Signal [a.u.]"))
            fig.update_layout(
                template="plotly_dark",
                title=f"Shot {shot} - {scope} ({channel_name})",
                xaxis_title=axis_labels[0],
                yaxis_title=axis_labels[1],
            )
            return fig

        selected_records = [(shot, self._load_record(self.index[shot][scope])) for shot in active_shots]
        reference_record = selected_records[0][1]
        selected_channels = self._selected_channels(reference_record, channel_name)
        palette = plotly_colors.qualitative.Plotly
        for index, selected_channel in enumerate(selected_channels):
            channel_records = [record for _shot, record in selected_records if selected_channel in record.channels]
            if not channel_records:
                continue

            if self.plot_mode_combo.currentText() == AVERAGE_WITH_CI_OPTION:
                color = palette[index % len(palette)]
                stats = self._compute_average_with_ci(channel_records, selected_channel)
                fig.add_trace(
                    go.Scatter(
                        x=stats["time"],
                        y=stats["mean"],
                        mode="lines",
                        name=f"Average - {selected_channel} (n={stats['sample_count']})",
                        line=dict(color=color, width=2),
                    )
                )
                if stats["sample_count"] > 1:
                    fig.add_trace(
                        go.Scatter(
                            x=stats["time"],
                            y=stats["lower_ci"],
                            mode="lines",
                            line=dict(width=0),
                            showlegend=False,
                            hoverinfo="skip",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=stats["time"],
                            y=stats["upper_ci"],
                            mode="lines",
                            fill="tonexty",
                            fillcolor=self._ci_fill_color(color),
                            line=dict(width=0),
                            name=f"95% CI - {selected_channel}",
                            hoverinfo="skip",
                        )
                    )
                continue

            for shot, record in selected_records:
                if selected_channel not in record.channels:
                    continue
                fig.add_trace(
                    go.Scatter(
                        x=record.time,
                        y=record.channels[selected_channel],
                        mode="lines",
                        name=f"Shot {shot} - {selected_channel}",
                    )
                )

        shot_label = " vs ".join(active_shots)
        axis_labels = reference_record.metadata.get("axis_labels", ("Time [s]", "Signal [a.u.]"))
        fig.update_layout(
            template="plotly_dark",
            title=f"Shots {shot_label} - {scope} ({channel_name})",
            xaxis_title=axis_labels[0],
            yaxis_title=axis_labels[1],
        )
        return fig

    def plot_for_scope(self, scope: str) -> None:
        state = self.tabs[scope]
        channel_name = state.channel_combo.currentText()
        if not channel_name:
            state.message_label.setText("No channel available for this selection.")
            logger.warning("Skipping plot for scope=%s: no channel selected.", scope)
            return

        try:
            fig = self._build_plotly_figure(scope, channel_name)
            html_path = self._temp_dir / f"{scope}.html"
            fig.write_html(
                str(html_path),
                full_html=True,
                include_plotlyjs="directory",
                config={"responsive": True, "displaylogo": False},
            )
            state.web_view.load(QUrl.fromLocalFile(str(html_path.resolve())))
            state.message_label.setText("Interactive plot updated.")
            logger.info(
                "Plotted scope=%s channel=%s traces=%d html=%s.",
                scope,
                channel_name,
                len(fig.data),
                html_path,
            )
        except Exception as exc:  # pragma: no cover - runtime GUI safety
            state.message_label.setText(f"Plot failed: {exc}")
            logger.exception("Plot failed for scope=%s channel=%s", scope, channel_name)

    def plot_all_tabs(self) -> None:
        for scope in self.tabs:
            self.plot_for_scope(scope)


def launch_shot_comparison_gui(data_dir: Path = Path("osc_data")) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logger.info("Launching ShotComparisonGUI with data_dir=%s", data_dir)
    app = QApplication.instance() or QApplication(sys.argv)
    config = PipelineConfig(input_dir=data_dir, output_dir=Path("outputs"))
    window = ShotComparisonGUI(config=config)
    window.show()
    app.exec()


if __name__ == "__main__":
    launch_shot_comparison_gui()
