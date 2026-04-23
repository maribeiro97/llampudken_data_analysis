from __future__ import annotations

import copy
import re
import warnings
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent
_DEFAULT_CHANNELS_FILE = Path('osc_data/configuraciones/osc_channels.txt')
_DEFAULT_TIMES_FILE = Path('osc_data/tiempo_cables/tiempo_cables.txt')

# Threshold maps are maintained independently because channels and cable-time
# updates can land on different shots.
CHANNEL_FILE_THRESHOLDS: dict[int, Path] = {
    229: Path('osc_data/configuraciones/osc_channels_229.txt'),
    516: Path('osc_data/configuraciones/osc_channels_516.txt'),
}

TIME_FILE_THRESHOLDS: dict[int, Path] = {
    229: Path('osc_data/tiempo_cables/tiempo_cables.txt'),
    516: Path('osc_data/tiempo_cables/tiempo_cables_516.txt'),
}

DEFAULT_OSCS = {
    'dpo4104': {
        'channels': ['dR1', 'ICCD QE', 'Laser 1.0[J]', 'ICCD andor'],
        'axes_labels': ['Time [s]', 'Voltage [V]'],
        'times': [56.8, 84.5, 66.5, 95.5],
    },
    'dpo5054': {
        'channels': [
            'Line Switch Norte Óptico',
            'Line Switch Sur Óptico',
            'Pin 1 Norte',
            'Pin 1 Sur',
        ],
        'axes_labels': ['Time [s]', 'Voltage [V]'],
        'times': [0.0, 0.0, 387.0, 388.0],
    },
    'tds684b': {
        'channels': [
            'Clock',
            'Corriente Inyector',
            'BD Pin',
            'Laser 1 Trigger',
        ],
        'axes_labels': ['Time [s]', 'Voltage [V]'],
        'times': [0.0, 83.5, 184.0, 0.0],
    },
    'tds3054': {
        'channels': ['Pin 3 Norte', 'Pin 3 Sur', 'LGT Light', 'Trigger P400'],
        'axes_labels': ['Time [s]', 'Voltage [V]'],
    },
    'tds5054': {
        'channels': ['dR2', 'dVtln', 'dVtlc', 'dVtls'],
        'axes_labels': ['Time [s]', 'Voltage [V]'],
        'times': [57.0, 62.0, 60.0, 62.0],
    },
    'tds5104': {
        'channels': ['dR3', 'V Norte Eléctrico', 'V Sur Eléctrico', 'PCD 12.5μm Ti'],
        'axes_labels': ['Time [s]', 'Voltage [V]'],
        'times': [61.0, 101.6, 101.0, 63.0],
    },
    'tds7104': {
        'channels': [
            'Rogowski Principal, Factor 0.5',
            'Rogowski Principal Integrada, Factor 0.5, 1494 [kA/(mVns)]',
            'AXUV 2 25um Be',
            'MCP 1',
        ],
        'axes_labels': ['Time [s]', 'Voltage [V]'],
        'calibration_factors': [1.0, 1400.0 * 2, 1.0, 1.0],
        'times': [69.5, 71.0, 61.0, 67.5],
    },
}

_ID_ALIASES = {
    'tds4104': 'dpo4104',
    'tds684': 'tds684b',
}


def _normalize_osc_id(raw: str) -> str:
    normalized = raw.strip().lower().replace('_', '').replace('-', '')
    normalized = re.sub(r'\s+', '', normalized)
    return _ID_ALIASES.get(normalized, normalized)


def _clean_channel_label(raw: str) -> str:
    label = raw.strip()
    label = re.sub(r'^ch\s*\d+\s*[:\-]?\s*', '', label, flags=re.IGNORECASE)
    return label.strip()


def _extract_range_id(path: Path) -> str:
    match = re.search(r'_(\d+)$', path.stem)
    return match.group(1) if match else 'default'


def _parse_osc_channels_file(path: Path) -> dict[str, list[str]]:
    parsed: dict[str, list[str]] = {}
    current_osc: str | None = None

    for lineno, raw_line in enumerate(path.read_text(encoding='utf-8', errors='replace').splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            current_osc = None
            continue

        if current_osc is None:
            current_osc = _normalize_osc_id(line)
            if not current_osc:
                warnings.warn(f'{path.name}:{lineno} invalid oscilloscope id line skipped')
                current_osc = None
                continue
            parsed.setdefault(current_osc, [])
            continue

        label = _clean_channel_label(line)
        if not label:
            warnings.warn(f'{path.name}:{lineno} empty channel line skipped')
            continue

        # Skip clearly corrupted repeated-character lines without crashing.
        unique_ratio = len(set(label)) / max(len(label), 1)
        if len(label) > 120 and unique_ratio < 0.1:
            warnings.warn(f'{path.name}:{lineno} malformed channel label skipped')
            continue

        parsed[current_osc].append(label)

    return parsed


def _parse_tiempo_cables_file(path: Path) -> dict[str, list[float]]:
    lines = [line.strip() for line in path.read_text(encoding='utf-8', errors='replace').splitlines() if line.strip()]
    if not lines:
        return {}

    headers = [_normalize_osc_id(token) for token in lines[0].split()]
    parsed: dict[str, list[float]] = {header: [] for header in headers}

    for row_idx, line in enumerate(lines[1:], start=2):
        numeric_tokens = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', line)
        if not numeric_tokens:
            warnings.warn(f'{path.name}:{row_idx} no numeric delay values found; row skipped')
            continue

        values = [float(token) for token in numeric_tokens]
        if len(values) == len(headers):
            for osc_id, value in zip(headers, values):
                parsed[osc_id].append(value)
        elif len(values) == 1 and headers:
            # Some files append extra rows only for first scope (e.g. tls216 in _2103).
            parsed[headers[0]].append(values[0])
        elif len(values) < len(headers):
            warnings.warn(f'{path.name}:{row_idx} has fewer columns than header; padding skipped columns')
            for idx, value in enumerate(values):
                parsed[headers[idx]].append(value)
        else:
            warnings.warn(f'{path.name}:{row_idx} has extra columns; extra values ignored')
            for idx, osc_id in enumerate(headers):
                parsed[osc_id].append(values[idx])

    return parsed


def _sized_list(values: list, target_len: int, fill_value):
    data = list(values)
    if len(data) < target_len:
        data.extend([fill_value] * (target_len - len(data)))
    elif len(data) > target_len:
        data = data[:target_len]
    return data


def _resolve_threshold_path(shot_number: int, threshold_map: dict[int, Path], default_path: Path) -> Path:
    selected = default_path
    for threshold in sorted(threshold_map):
        if shot_number >= threshold:
            selected = threshold_map[threshold]
    return selected


def resolve_calibration_files(shot_number: int) -> tuple[Path, Path]:
    shot = int(shot_number)
    channels_rel_path = _resolve_threshold_path(shot, CHANNEL_FILE_THRESHOLDS, _DEFAULT_CHANNELS_FILE)
    times_rel_path = _resolve_threshold_path(shot, TIME_FILE_THRESHOLDS, _DEFAULT_TIMES_FILE)
    return (_BASE_DIR / channels_rel_path, _BASE_DIR / times_rel_path)


def _build_osc_config_map(channels_path: Path, times_path: Path) -> dict[str, dict]:
    merged: dict[str, dict] = copy.deepcopy(DEFAULT_OSCS)
    channel_map = _parse_osc_channels_file(channels_path) if channels_path.exists() else {}
    time_map = _parse_tiempo_cables_file(times_path) if times_path.exists() else {}

    osc_ids = set(merged) | set(channel_map) | set(time_map)
    for osc_id in osc_ids:
        config = copy.deepcopy(merged.get(osc_id, {}))
        config.setdefault('axes_labels', ['Time [s]', 'Voltage [V]'])

        channels = channel_map.get(osc_id, config.get('channels', []))
        times = time_map.get(osc_id, config.get('times', []))
        calibration_factors = config.get('calibration_factors', [1.0] * len(channels))

        channel_count = len(channels) if channels else len(times)
        if channel_count == 0:
            channel_count = len(calibration_factors)
        if channel_count == 0:
            channel_count = 4

        channels = _sized_list(list(channels), channel_count, '')
        channels = [label if label else f'ch{idx + 1}' for idx, label in enumerate(channels)]

        times = _sized_list(list(times), channel_count, 0.0)
        calibration_factors = _sized_list(list(calibration_factors), channel_count, 1.0)

        config['channels'] = channels
        config['times'] = times
        config['calibration_factors'] = calibration_factors
        merged[osc_id] = config

    return merged


def get_osc_config(osc_id: str, shot_number: int | None = None) -> dict:
    normalized_id = _normalize_osc_id(osc_id)
    scoped = None
    config_tag = 'default'
    if shot_number is not None:
        try:
            channels_path, times_path = resolve_calibration_files(int(shot_number))
            config_tag = f'{channels_path.name}|{times_path.name}'
            cache_key = (channels_path, times_path)
            if cache_key not in _CONFIG_CACHE:
                _CONFIG_CACHE[cache_key] = _build_osc_config_map(channels_path, times_path)
            scoped = _CONFIG_CACHE[cache_key].get(normalized_id)
        except (TypeError, ValueError):
            scoped = None

    if scoped is not None:
        config = copy.deepcopy(scoped)
        config['range_id'] = config_tag
        return config

    fallback = DEFAULT_OSCS.get(normalized_id, {'channels': [], 'times': [], 'axes_labels': ['Time [s]', 'Voltage [V]']})
    config = copy.deepcopy(fallback)
    config['range_id'] = config_tag
    return config


_CONFIG_CACHE: dict[tuple[Path, Path], dict[str, dict]] = {}

# Backward compatibility with older consumers.
OSCS = copy.deepcopy(DEFAULT_OSCS)
