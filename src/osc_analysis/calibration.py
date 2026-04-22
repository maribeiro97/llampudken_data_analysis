from __future__ import annotations

from dataclasses import dataclass

from osc_analysis.osc_calibrations import get_osc_config

REFERENCE_DELAY_NS = get_osc_config("tds7104").get("times", [0.0, 0.0])[1]


@dataclass(frozen=True)
class OscCalibration:
    channel_names: list[str]
    axis_labels: tuple[str, str]
    calibration_factors: list[float]
    channel_delay_ns: list[float]
    calibration_range_id: str


def get_calibration(oscilloscope_id: str, channel_count: int, shot_number: int | None = None) -> OscCalibration:
    raw = get_osc_config(oscilloscope_id, shot_number=shot_number)

    channel_names = list(raw.get("channels", []))
    if len(channel_names) < channel_count:
        channel_names.extend(f"ch{i}" for i in range(len(channel_names) + 1, channel_count + 1))
    else:
        channel_names = channel_names[:channel_count]

    axes = raw.get("axes_labels", ["Time [s]", "Voltage [V]"])
    axis_labels = (axes[0], axes[1])

    calibration_factors = list(raw.get("calibration_factors", []))
    if len(calibration_factors) < channel_count:
        calibration_factors.extend([1.0] * (channel_count - len(calibration_factors)))
    else:
        calibration_factors = calibration_factors[:channel_count]

    delay_ns = list(raw.get("times", []))
    if len(delay_ns) < channel_count:
        delay_ns.extend([0.0] * (channel_count - len(delay_ns)))
    else:
        delay_ns = delay_ns[:channel_count]

    return OscCalibration(
        channel_names=channel_names,
        axis_labels=axis_labels,
        calibration_factors=calibration_factors,
        channel_delay_ns=delay_ns,
        calibration_range_id=str(raw.get("range_id", "default")),
    )


def delay_offsets_s(delays_ns: list[float], reference_delay_ns: float = REFERENCE_DELAY_NS) -> list[float]:
    return [(delay - reference_delay_ns) * 1e-9 for delay in delays_ns]
