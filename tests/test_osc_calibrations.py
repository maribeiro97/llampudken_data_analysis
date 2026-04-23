from __future__ import annotations

from OSC_CALIBRATIONS import (
    CHANNEL_RULES,
    TIME_RULES,
    discover_channel_rules,
    discover_time_rules,
    discover_threshold_files,
    resolve_calibration_files,
    resolve_calibration_debug_metadata,
    select_file_for_shot,
)


def _thresholds(rules):
    return [threshold for threshold, _ in rules]


def _name_for_threshold(rules, target):
    for threshold, path in rules:
        if threshold == target:
            return path.name
    return None


def test_discovery_extracts_numeric_threshold_rules_from_repo_files() -> None:
    channel_rules = discover_channel_rules()
    time_rules = discover_time_rules()

    assert _thresholds(channel_rules) == sorted(_thresholds(channel_rules))
    assert _thresholds(time_rules) == sorted(_thresholds(time_rules))

    assert _name_for_threshold(channel_rules, float("-inf")) == "osc_channels.txt"
    assert _name_for_threshold(channel_rules, 516) == "osc_channels_516.txt"
    assert _name_for_threshold(channel_rules, 1493) == "osc_channels_1493.txt"

    assert _name_for_threshold(time_rules, float("-inf")) == "tiempo_cables.txt"
    assert _name_for_threshold(time_rules, 516) == "tiempo_cables_516.txt"
    assert _name_for_threshold(time_rules, 1493) == "tiempo_cables_1493.txt"

    assert all(path.name != "tiempo_cables_dos_lasers.txt" for _, path in time_rules)


def test_discover_threshold_files_reusable_for_both_calibration_families() -> None:
    channel_rules = discover_threshold_files(
        pattern="osc_data/configuraciones/osc_channels*.txt",
        base_name="osc_channels",
    )
    time_rules = discover_threshold_files(
        pattern="osc_data/tiempo_cables/tiempo_cables*.txt",
        base_name="tiempo_cables",
    )

    assert channel_rules == discover_channel_rules()
    assert time_rules == discover_time_rules()


def test_resolve_calibration_files_boundary_behavior() -> None:
    channel_thresholds = [threshold for threshold, _ in CHANNEL_RULES if threshold != float("-inf")]
    first_threshold = channel_thresholds[0]
    second_threshold = channel_thresholds[1]

    below_first_channels, _ = resolve_calibration_files(first_threshold - 1)
    at_first_channels, _ = resolve_calibration_files(first_threshold)
    between_channels, _ = resolve_calibration_files((first_threshold + second_threshold) // 2)

    assert below_first_channels.name == "osc_channels.txt"
    assert at_first_channels.name == f"osc_channels_{first_threshold}.txt"
    assert between_channels.name == f"osc_channels_{first_threshold}.txt"


def test_channel_and_time_selection_are_independent() -> None:
    channels_path, times_path = resolve_calibration_files(300)

    assert channels_path.name == "osc_channels_249.txt"
    assert times_path.name == "tiempo_cables.txt"


def test_select_file_for_shot_returns_threshold_and_path() -> None:
    threshold, path = select_file_for_shot(CHANNEL_RULES, 300)
    assert threshold == 249
    assert path.name == "osc_channels_249.txt"


def test_debug_selection_metadata_for_shot() -> None:
    metadata = resolve_calibration_debug_metadata(600)
    assert metadata["selected_channel_file"] == "osc_channels_559.txt"
    assert metadata["selected_cable_time_file"] == "tiempo_cables_559.txt"
    assert metadata["selected_thresholds"] == {"channels": 559, "times": 559}
