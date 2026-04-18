from __future__ import annotations

from pathlib import Path

import numpy as np

from osc_analysis.models import SignalRecord


class DataLoader:
    """Load oscilloscope text files and produce SignalRecord objects."""

    def __init__(self, data_root: Path) -> None:
        self.data_root = Path(data_root)

    def list_data_files(self) -> list[Path]:
        return sorted(self.data_root.glob("*.txt"))

    def parse_filename(self, file_path: Path) -> tuple[str, str, str]:
        stem = file_path.stem
        shot, date_code, oscilloscope_id = stem.split("_")
        shot_number = shot.replace("shot", "")
        return shot_number, date_code, oscilloscope_id

    def load_file(self, file_path: Path) -> SignalRecord:
        data = np.loadtxt(file_path)
        time = data[:, 0]
        channels = {f"ch{i}": data[:, i] for i in range(1, data.shape[1])}
        dt = float(np.mean(np.diff(time))) if len(time) > 1 else 1.0
        sampling_rate_hz = 1.0 / dt if dt else 0.0
        shot_number, date_code, oscilloscope_id = self.parse_filename(file_path)
        return SignalRecord(
            shot_number=shot_number,
            oscilloscope_id=oscilloscope_id,
            date_code=date_code,
            file_path=file_path,
            time=time,
            channels=channels,
            sampling_rate_hz=sampling_rate_hz,
        )
