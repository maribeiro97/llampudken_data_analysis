from pathlib import Path

from osc_analysis.io import DataLoader


def test_parse_filename() -> None:
    loader = DataLoader(Path("osc_data"))
    shot, date_code, osc = loader.parse_filename(Path("shot1558_20240410_dpo4104.txt"))
    assert shot == "1558"
    assert date_code == "20240410"
    assert osc == "dpo4104"
