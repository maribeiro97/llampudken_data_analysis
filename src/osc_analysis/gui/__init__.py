"""GUI tools for interactive oscilloscope shot comparison."""

from .data_index import (
    available_oscilloscopes_for_shot,
    build_shot_scope_index,
    common_oscilloscopes_for_shots,
)

__all__ = [
    "ShotComparisonGUI",
    "available_oscilloscopes_for_shot",
    "build_shot_scope_index",
    "common_oscilloscopes_for_shots",
    "launch_shot_comparison_gui",
]


def __getattr__(name: str):
    if name in {"ShotComparisonGUI", "launch_shot_comparison_gui"}:
        from .shot_compare_gui import ShotComparisonGUI, launch_shot_comparison_gui

        return {
            "ShotComparisonGUI": ShotComparisonGUI,
            "launch_shot_comparison_gui": launch_shot_comparison_gui,
        }[name]
    raise AttributeError(name)
