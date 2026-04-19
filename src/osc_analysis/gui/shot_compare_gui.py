from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

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
        QMainWindow,
        QPushButton,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError as exc:  # pragma: no cover - platform dependent
    raise RuntimeError(
        "PySide6 with QtWebEngine is required for the interactive Plotly GUI."
    ) from exc


SINGLE_SHOT_MODE = "Single shot (all oscilloscopes)"
COMPARE_MODE = "Compare two shots"
ALL_CHANNELS_OPTION = "All channels"


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

        self._records_cache: dict[Path, object] = {}
        self.shots = sorted(self.index.keys(), key=int)
        self.tabs: dict[str, ScopeTabState] = {}

        self.mode_combo = QComboBox()
        self.single_shot_combo = QComboBox()
        self.compare_shot_a_combo = QComboBox()
        self.compare_shot_b_combo = QComboBox()
        self.scope_hint_label = QLabel()
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
        self.mode_combo.addItems([SINGLE_SHOT_MODE, COMPARE_MODE])
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

        self.scope_hint_label.setWordWrap(True)
        left_layout.addWidget(self.scope_hint_label)

        left_layout.addWidget(self.plot_all_button)
        left_layout.addStretch()

        layout.addWidget(left_panel, 0)
        layout.addWidget(self.notebook, 1)

    def _wire_events(self) -> None:
        self.mode_combo.currentTextChanged.connect(lambda _text: self._refresh_from_selection())
        self.single_shot_combo.currentTextChanged.connect(lambda _text: self._refresh_from_selection())
        self.compare_shot_a_combo.currentTextChanged.connect(lambda _text: self._refresh_from_selection())
        self.compare_shot_b_combo.currentTextChanged.connect(lambda _text: self._refresh_from_selection())
        self.plot_all_button.clicked.connect(self.plot_all_tabs)

    def _refresh_from_selection(self) -> None:
        is_single = self.mode_combo.currentText() == SINGLE_SHOT_MODE
        self.single_shot_combo.setEnabled(is_single)
        self.compare_shot_a_combo.setEnabled(not is_single)
        self.compare_shot_b_combo.setEnabled(not is_single)

        self._refresh_scope_hint()
        self._rebuild_tabs()

    def _active_shots(self) -> list[str]:
        if self.mode_combo.currentText() == SINGLE_SHOT_MODE:
            return [self.single_shot_combo.currentText()]
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

        shot_a, shot_b = active_shots
        scopes_a = available_oscilloscopes_for_shot(self.index, shot_a)
        scopes_b = available_oscilloscopes_for_shot(self.index, shot_b)
        common = common_oscilloscopes_for_shots(self.index, active_shots)
        self.scope_hint_label.setText(
            f"Mode: {COMPARE_MODE}\n"
            f"Shot {shot_a} scopes: {', '.join(scopes_a) or 'none'}\n"
            f"Shot {shot_b} scopes: {', '.join(scopes_b) or 'none'}\n"
            f"Common: {', '.join(common) or 'none'}"
        )

    def _rebuild_tabs(self) -> None:
        self.notebook.clear()
        self.tabs.clear()

        for scope in self._active_scopes():
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)

            top_bar = QHBoxLayout()
            top_bar.addWidget(QLabel("Channel"))

            channel_combo = QComboBox()
            channels = self._channels_for_scope(scope)
            channel_combo.addItems(channels)
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

        self.plot_all_tabs()

    def _channels_for_scope(self, scope: str) -> list[str]:
        active_shots = self._active_shots()
        if len(active_shots) == 1:
            shot = active_shots[0]
            record = self._load_record(self.index[shot][scope])
            return [ALL_CHANNELS_OPTION, *sorted(record.channels.keys())]

        shot_a, shot_b = active_shots
        if scope not in self.index.get(shot_a, {}) or scope not in self.index.get(shot_b, {}):
            return []

        record_a = self._load_record(self.index[shot_a][scope])
        record_b = self._load_record(self.index[shot_b][scope])
        common_channels = sorted(set(record_a.channels.keys()) & set(record_b.channels.keys()))
        return [ALL_CHANNELS_OPTION, *common_channels]

    @staticmethod
    def _selected_channels(record, selected_channel: str) -> list[str]:
        if selected_channel == ALL_CHANNELS_OPTION:
            return sorted(record.channels.keys())
        return [selected_channel]

    def _load_record(self, path: Path):
        if path not in self._records_cache:
            self._records_cache[path] = self.loader.load_file(path)
        return self._records_cache[path]

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

        shot_a, shot_b = active_shots
        record_a = self._load_record(self.index[shot_a][scope])
        record_b = self._load_record(self.index[shot_b][scope])
        for selected_channel in self._selected_channels(record_a, channel_name):
            if selected_channel not in record_b.channels:
                continue
            fig.add_trace(
                go.Scatter(
                    x=record_a.time,
                    y=record_a.channels[selected_channel],
                    mode="lines",
                    name=f"Shot {shot_a} - {selected_channel}",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=record_b.time,
                    y=record_b.channels[selected_channel],
                    mode="lines",
                    name=f"Shot {shot_b} - {selected_channel}",
                )
            )
        axis_labels = record_a.metadata.get("axis_labels", ("Time [s]", "Signal [a.u.]"))
        fig.update_layout(
            template="plotly_dark",
            title=f"Shot {shot_a} vs {shot_b} - {scope} ({channel_name})",
            xaxis_title=axis_labels[0],
            yaxis_title=axis_labels[1],
        )
        return fig

    def plot_for_scope(self, scope: str) -> None:
        state = self.tabs[scope]
        channel_name = state.channel_combo.currentText()
        if not channel_name:
            state.message_label.setText("No channel available for this selection.")
            return

        try:
            fig = self._build_plotly_figure(scope, channel_name)
            html = fig.to_html(full_html=False, include_plotlyjs=True)
            state.web_view.setHtml(html)
            state.message_label.setText("Interactive plot updated.")
        except Exception as exc:  # pragma: no cover - runtime GUI safety
            state.message_label.setText(f"Plot failed: {exc}")

    def plot_all_tabs(self) -> None:
        for scope in self.tabs:
            self.plot_for_scope(scope)


def launch_shot_comparison_gui(data_dir: Path = Path("osc_data")) -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    config = PipelineConfig(input_dir=data_dir, output_dir=Path("outputs"))
    window = ShotComparisonGUI(config=config)
    window.show()
    app.exec()


if __name__ == "__main__":
    launch_shot_comparison_gui()
