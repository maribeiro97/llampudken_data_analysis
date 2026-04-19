from pathlib import Path

from osc_analysis.gui.data_index import (
    available_oscilloscopes_for_shot,
    build_shot_scope_index,
    common_oscilloscopes_for_shots,
)
from osc_analysis.io import DataLoader


def test_build_shot_scope_index_maps_shot_and_scope() -> None:
    loader = DataLoader(Path("osc_data"))
    index = build_shot_scope_index(loader)

    assert "1558" in index
    assert "dpo4104" in index["1558"]
    assert index["1558"]["dpo4104"].name == "shot1558_20240410_dpo4104.txt"


def test_available_and_common_oscilloscopes() -> None:
    loader = DataLoader(Path("osc_data"))
    index = build_shot_scope_index(loader)

    shot_scopes = available_oscilloscopes_for_shot(index, "1559")
    assert "dpo4104" in shot_scopes
    assert "tds7104" in shot_scopes

    common = common_oscilloscopes_for_shots(index, ["1558", "1559", "1560"])
    assert set(common) == {"dpo4104", "dpo5054", "tds3054", "tds5054", "tds5104", "tds684b", "tds7104"}
