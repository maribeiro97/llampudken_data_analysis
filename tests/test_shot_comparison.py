from pathlib import Path

import numpy as np

from osc_analysis.config import PlotStyleConfig
from osc_analysis.models import SignalRecord
from osc_analysis.plotting import FigureBuilder


def _make_record(shot: str, phase: float, delay_offset_s: float = 0.0) -> SignalRecord:
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
        metadata={"channel_delay_offsets_s": [delay_offset_s]},
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


def test_overlay_alignment_uses_per_record_delay_offsets() -> None:
    builder = FigureBuilder(PlotStyleConfig())
    t_a = np.linspace(0.0, 1.0, 1000)
    t_b = np.linspace(0.02, 1.02, 1000)
    signal = np.sin(2 * np.pi * 5 * t_a)

    shot_a = SignalRecord(
        shot_number="1001",
        oscilloscope_id="dpo5054",
        date_code="20240410",
        file_path=Path("/tmp/1001.txt"),
        time=t_a,
        channels={"CH1": signal},
        sampling_rate_hz=1000.0,
        metadata={"channel_delay_offsets_s": [0.0]},
    )
    shot_b = SignalRecord(
        shot_number="1002",
        oscilloscope_id="dpo5054",
        date_code="20240410",
        file_path=Path("/tmp/1002.txt"),
        time=t_b,
        channels={"CH1": signal},
        sampling_rate_hz=1000.0,
        metadata={"channel_delay_offsets_s": [0.02]},
    )

    metrics = builder.compute_shot_comparison_metrics(shot_a, shot_b, channel_name="CH1")
    assert metrics["correlation"] > 0.999
    assert metrics["rms_delta"] < 1e-3


def test_range_average_returns_ci_bands() -> None:
    builder = FigureBuilder(PlotStyleConfig())
    range_records = [
        _make_record("1001", 0.0),
        _make_record("1002", 0.2),
        _make_record("1003", -0.1),
    ]
    stats = builder.compute_range_average_with_ci(range_records, channel_name="CH1")

    assert stats["sample_count"] == 3
    assert stats["time"].shape == stats["mean"].shape
    assert stats["lower_ci"].shape == stats["upper_ci"].shape
    assert np.all(stats["upper_ci"] >= stats["lower_ci"])


def test_range_plot_outputs_are_written(tmp_path: Path) -> None:
    builder = FigureBuilder(PlotStyleConfig())
    range_a = [_make_record("1001", 0.0), _make_record("1002", 0.1), _make_record("1003", 0.2)]
    range_b = [_make_record("1004", 0.3), _make_record("1005", 0.4), _make_record("1006", 0.5)]

    range_a_path = builder.plot_range_average_with_ci(
        range_a, tmp_path / "range_a_mean_ci.png", channel_name="CH1", label="A"
    )
    range_compare_path = builder.plot_two_ranges_with_ci(
        range_a,
        range_b,
        tmp_path / "range_compare.png",
        channel_name="CH1",
        label_a="A",
        label_b="B",
    )
    mean_only_path = builder.plot_channel_mean_across_shots(
        range_a,
        tmp_path / "range_a_mean_only.png",
        channel_name="CH1",
        label="A mean only",
    )

    assert range_a_path.exists()
    assert range_compare_path.exists()
    assert mean_only_path.exists()
    assert range_a_path.with_suffix(".html").exists()
    assert range_a_path.with_suffix(".pdf").exists()
    assert range_a_path.with_suffix(".svg").exists()
    assert range_compare_path.with_suffix(".html").exists()
    assert range_compare_path.with_suffix(".pdf").exists()
    assert range_compare_path.with_suffix(".svg").exists()
    assert mean_only_path.with_suffix(".html").exists()
    assert mean_only_path.with_suffix(".pdf").exists()
    assert mean_only_path.with_suffix(".svg").exists()
