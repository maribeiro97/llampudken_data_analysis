from pathlib import Path

import numpy as np

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

    assert "Rogowski Principal, Factor 0.5" in record.channels
    assert "Rogowski Principal Integrada, Factor 0.5, 1494 [kA/(mVns)]" in record.channels
    calibrated = record.channels["Rogowski Principal Integrada, Factor 0.5, 1494 [kA/(mVns)]"]
    assert np.allclose(calibrated[:10], raw[:10, 2] * 2800.0)
    assert "channel_delay_offsets_s" in record.metadata
