from pathlib import Path

import numpy as np

from osc_analysis.config import PlotStyleConfig
from osc_analysis.models import SignalRecord
from osc_analysis.plotting import FigureBuilder


def _make_record(shot: str, phase: float) -> SignalRecord:
    time = np.linspace(0.0, 1.0, 1000)
    signal = np.sin(2 * np.pi * 5 * time + phase)
    return SignalRecord(
        shot_number=shot,
        oscilloscope_id="dpo5054",
        date_code="20240410",
        file_path=Path(f"/tmp/{shot}.txt"),
        time=time,
        channels={"CH1": signal},
        sampling_rate_hz=1000.0,
        metadata={},
    )


def test_compare_metrics_returns_expected_keys() -> None:
    builder = FigureBuilder(PlotStyleConfig())
    shot_a = _make_record("1001", 0.0)
    shot_b = _make_record("1002", 0.3)

    metrics = builder.compute_shot_comparison_metrics(shot_a, shot_b, channel_name="CH1")

    assert set(metrics.keys()) == {
        "centroid_shift",
        "rms_delta",
        "peak_delta",
        "correlation",
        "area_delta",
    }
    assert metrics["peak_delta"] > 0.0


def test_compare_plot_outputs_are_written(tmp_path: Path) -> None:
    builder = FigureBuilder(PlotStyleConfig())
    shot_a = _make_record("1001", 0.0)
    shot_b = _make_record("1002", 0.25)

    overlay = builder.plot_shot_overlay(shot_a, shot_b, tmp_path / "overlay.png", channel_name="CH1")
    heatmap = builder.plot_shot_difference_heatmap(
        shot_a, shot_b, tmp_path / "diff_heatmap.png", channel_name="CH1"
    )
    kde = builder.plot_shot_kde_panel(shot_a, shot_b, tmp_path / "kde_panel.png", channel_name="CH1")

    assert overlay.exists()
    assert heatmap.exists()
    assert kde.exists()
