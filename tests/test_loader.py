from pathlib import Path

import numpy as np

from osc_analysis.calibration import get_calibration
from osc_analysis.io import DataLoader


def test_parse_filename() -> None:
    loader = DataLoader(Path("osc_data"))
    shot, date_code, osc = loader.parse_filename(Path("shot1558_20240410_dpo4104.txt"))
    assert shot == "1558"
    assert date_code == "20240410"
    assert osc == "dpo4104"


def test_loader_applies_calibration_metadata() -> None:
    loader = DataLoader(Path("osc_data"))
    file_path = Path("osc_data/shot1558_20240410_tds7104.txt")
    raw = np.loadtxt(file_path)
    record = loader.load_file(file_path)

    assert "rogowski principal, factor 0.5" in record.channels
    assert "rogowski principal integrada, factor 0.5, 1494 kA/(mVns)" in record.channels
    calibrated = record.channels["rogowski principal integrada, factor 0.5, 1494 kA/(mVns)"]
    assert np.allclose(calibrated[:10], raw[:10, 2] * 2800.0)
    assert "channel_delay_offsets_s" in record.metadata
    assert record.metadata["calibration_range_id"] == "1493"


def test_calibration_changes_across_ranges_for_same_scope() -> None:
    cal_1493 = get_calibration("dpo4104", channel_count=4, shot_number=1493)
    cal_1723 = get_calibration("dpo4104", channel_count=4, shot_number=1723)

    assert cal_1493.calibration_range_id == "1493"
    assert cal_1723.calibration_range_id == "1723"
    assert cal_1493.channel_names != cal_1723.channel_names
    assert cal_1493.channel_delay_ns != cal_1723.channel_delay_ns


def test_calibration_source_files_for_shot_300_and_600() -> None:
    cal_300 = get_calibration("dpo4104", channel_count=4, shot_number=300)
    cal_600 = get_calibration("dpo4104", channel_count=4, shot_number=600)

    assert cal_300.calibration_source_files == {
        "channels": "osc_channels_249.txt",
        "times": "tiempo_cables.txt",
    }
    assert cal_600.calibration_source_files == {
        "channels": "osc_channels_559.txt",
        "times": "tiempo_cables_559.txt",
    }


def test_loader_includes_calibration_source_files_metadata(tmp_path: Path) -> None:
    file_path = tmp_path / "shot0600_20240101_dpo4104.txt"
    data = np.column_stack(
        [
            np.arange(5, dtype=float),
            np.linspace(0.0, 1.0, 5),
            np.linspace(1.0, 2.0, 5),
            np.linspace(2.0, 3.0, 5),
            np.linspace(3.0, 4.0, 5),
        ]
    )
    np.savetxt(file_path, data)

    loader = DataLoader(tmp_path)
    record = loader.load_file(file_path)

    assert record.metadata["calibration_source_files"] == {
        "channels": "osc_channels_559.txt",
        "times": "tiempo_cables_559.txt",
    }
    assert record.metadata["calibration_selection_metadata"] == {
        "selected_channel_file": "osc_channels_559.txt",
        "selected_cable_time_file": "tiempo_cables_559.txt",
        "selected_thresholds": {"channels": 559, "times": 559},
    }
