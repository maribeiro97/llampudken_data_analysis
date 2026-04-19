from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

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
except ImportError as exc:  # pragma: no cover - platform dependent
    raise RuntimeError("PySide6 is required to run the shot comparison GUI.") from exc


@dataclass
class ScopeTabState:
    """State and widgets for one oscilloscope tab."""

    figure: Figure
    canvas: FigureCanvasQTAgg
    channel_combo: QComboBox
    message_label: QLabel


class ShotComparisonGUI(QMainWindow):
    """PySide GUI to select shots and compare channels per oscilloscope tab."""

    def __init__(
        self,
        loader_factory: Callable[[Path], DataLoader] = DataLoader,
        config: PipelineConfig | None = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Oscilloscope shot comparison")
        self.resize(1200, 800)

        self.config = config or PipelineConfig(input_dir=Path("osc_data"), output_dir=Path("outputs"))
        self.loader = loader_factory(self.config.input_dir)
        self.index = build_shot_scope_index(self.loader)

        self._records_cache: dict[Path, object] = {}
        self.shots = sorted(self.index.keys(), key=int)
        self.scopes = sorted({scope for scopes in self.index.values() for scope in scopes})
        self.tabs: dict[str, ScopeTabState] = {}

        self.shot_a_combo = QComboBox()
        self.shot_b_combo = QComboBox()
        self.scope_hint_label = QLabel()
        self.notebook = QTabWidget()

        self._build_layout()
        self._populate_tabs()
        self._refresh_scope_hint()

    def _build_layout(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        controls_layout = QHBoxLayout()

        controls_layout.addWidget(QLabel("Shot A"))
        self.shot_a_combo.addItems(self.shots)
        controls_layout.addWidget(self.shot_a_combo)

        controls_layout.addWidget(QLabel("Shot B"))
        self.shot_b_combo.addItems(self.shots)
        if len(self.shots) > 1:
            self.shot_b_combo.setCurrentIndex(1)
        controls_layout.addWidget(self.shot_b_combo)

        controls_layout.addWidget(self.scope_hint_label)
        controls_layout.addStretch()

        self.shot_a_combo.currentTextChanged.connect(self._on_shot_change)
        self.shot_b_combo.currentTextChanged.connect(self._on_shot_change)

        layout.addLayout(controls_layout)
        layout.addWidget(self.notebook)

    def _populate_tabs(self) -> None:
        for scope in self.scopes:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)

            top_bar = QHBoxLayout()
            top_bar.addWidget(QLabel("Channel"))
            channel_combo = QComboBox()
            top_bar.addWidget(channel_combo)

            msg_label = QLabel("Select Shot A/B and click 'Plot comparison'.")
            top_bar.addWidget(msg_label)
            top_bar.addStretch()

            plot_button = QPushButton("Plot comparison")
            plot_button.clicked.connect(lambda _checked=False, s=scope: self.plot_for_scope(s))
            top_bar.addWidget(plot_button)

            tab_layout.addLayout(top_bar)

            fig = Figure(figsize=(8.5, 5.5), dpi=100)
            canvas = FigureCanvasQTAgg(fig)
            tab_layout.addWidget(canvas)

            self.tabs[scope] = ScopeTabState(
                figure=fig,
                canvas=canvas,
                channel_combo=channel_combo,
                message_label=msg_label,
            )
            self.notebook.addTab(tab, scope)

        self._refresh_channels_for_all_tabs()

    def _on_shot_change(self, _text: str) -> None:
        self._refresh_scope_hint()
        self._refresh_channels_for_all_tabs()

    def _refresh_scope_hint(self) -> None:
        shot_a = self.shot_a_combo.currentText()
        shot_b = self.shot_b_combo.currentText()
        scopes_a = available_oscilloscopes_for_shot(self.index, shot_a)
        scopes_b = available_oscilloscopes_for_shot(self.index, shot_b)
        common = common_oscilloscopes_for_shots(self.index, [shot_a, shot_b])
        self.scope_hint_label.setText(
            f"Shot {shot_a} scopes: {', '.join(scopes_a) or 'none'} | "
            f"Shot {shot_b} scopes: {', '.join(scopes_b) or 'none'} | "
            f"Common: {', '.join(common) or 'none'}"
        )

    def _refresh_channels_for_all_tabs(self) -> None:
        for scope in self.scopes:
            channels = self._channels_for_scope(scope)
            state = self.tabs[scope]
            state.channel_combo.blockSignals(True)
            state.channel_combo.clear()
            state.channel_combo.addItems(channels)
            state.channel_combo.blockSignals(False)
            if channels:
                state.message_label.setText("Ready to plot.")
            else:
                state.message_label.setText("This oscilloscope is not available in both selected shots.")

    def _channels_for_scope(self, scope: str) -> list[str]:
        shot_a, shot_b = self.shot_a_combo.currentText(), self.shot_b_combo.currentText()
        if scope not in self.index.get(shot_a, {}) or scope not in self.index.get(shot_b, {}):
            return []

        record_a = self._load_record(self.index[shot_a][scope])
        record_b = self._load_record(self.index[shot_b][scope])
        return sorted(set(record_a.channels.keys()) & set(record_b.channels.keys()))

    def _load_record(self, path: Path):
        if path not in self._records_cache:
            self._records_cache[path] = self.loader.load_file(path)
        return self._records_cache[path]

    def plot_for_scope(self, scope: str) -> None:
        state = self.tabs[scope]
        channel_name = state.channel_combo.currentText()
        if not channel_name:
            state.message_label.setText("No common channel available for this scope and shot pair.")
            return

        shot_a, shot_b = self.shot_a_combo.currentText(), self.shot_b_combo.currentText()
        record_a = self._load_record(self.index[shot_a][scope])
        record_b = self._load_record(self.index[shot_b][scope])

        state.figure.clear()
        ax = state.figure.add_subplot(111)
        ax.plot(record_a.time, record_a.channels[channel_name], label=f"Shot {shot_a}", alpha=0.75)
        ax.plot(record_b.time, record_b.channels[channel_name], label=f"Shot {shot_b}", alpha=0.75)
        axis_labels = record_a.metadata.get("axis_labels", ("Time [s]", "Signal [a.u.]"))
        ax.set_title(f"{scope} - channel {channel_name}")
        ax.set_xlabel(axis_labels[0])
        ax.set_ylabel(axis_labels[1])
        ax.legend(loc="best")
        state.figure.tight_layout()
        state.canvas.draw()

        state.message_label.setText(f"Plotted shots {shot_a} vs {shot_b} on {scope}.")


def launch_shot_comparison_gui(data_dir: Path = Path("osc_data")) -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    config = PipelineConfig(input_dir=data_dir, output_dir=Path("outputs"))
    window = ShotComparisonGUI(config=config)
    window.show()
    app.exec()


if __name__ == "__main__":
    launch_shot_comparison_gui()
