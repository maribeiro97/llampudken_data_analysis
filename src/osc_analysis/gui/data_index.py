from __future__ import annotations

from pathlib import Path

from osc_analysis.io.data_loader import DataLoader


def build_shot_scope_index(loader: DataLoader) -> dict[str, dict[str, Path]]:
    """Create a nested map: shot_number -> oscilloscope_id -> file path."""
    index: dict[str, dict[str, Path]] = {}
    for path in loader.list_data_files():
        shot_number, _, oscilloscope_id = loader.parse_filename(path)
        index.setdefault(shot_number, {})[oscilloscope_id] = path
    return index


def available_oscilloscopes_for_shot(index: dict[str, dict[str, Path]], shot_number: str) -> list[str]:
    """Return sorted oscilloscopes that exist for one shot."""
    return sorted(index.get(shot_number, {}).keys())


def common_oscilloscopes_for_shots(index: dict[str, dict[str, Path]], shots: list[str]) -> list[str]:
    """Return oscilloscopes available in all selected shots."""
    if not shots:
        return []

    common = set(index.get(shots[0], {}).keys())
    for shot in shots[1:]:
        common.intersection_update(index.get(shot, {}).keys())
    return sorted(common)
