#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare two shot ranges using average curves and confidence intervals."
    )
    parser.add_argument("--range-a-start", type=int, required=True, help="Start shot number for range A.")
    parser.add_argument("--range-a-end", type=int, required=True, help="End shot number for range A.")
    parser.add_argument("--range-b-start", type=int, required=True, help="Start shot number for range B.")
    parser.add_argument("--range-b-end", type=int, required=True, help="End shot number for range B.")
    parser.add_argument(
        "--oscilloscope-id",
        type=str,
        default=None,
        help="Optional oscilloscope id filter (for example: dpo4104).",
    )
    parser.add_argument(
        "--channel",
        type=str,
        default=None,
        help="Optional channel name. If omitted, the first common channel is used.",
    )
    return parser.parse_args()


def _in_shot_range(shot_number: str, start: int, end: int) -> bool:
    shot = int(shot_number)
    return start <= shot <= end


def main() -> None:
    args = _parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from osc_analysis.config import PipelineConfig
    from osc_analysis.io import DataLoader
    from osc_analysis.plotting import FigureBuilder
    from osc_analysis.preprocessing import SignalPreprocessor

    config = PipelineConfig(
        input_dir=repo_root / "osc_data",
        output_dir=repo_root / "outputs",
    )
    loader = DataLoader(config.input_dir)
    preprocessor = SignalPreprocessor(config.preprocess)
    figure_builder = FigureBuilder(config.plot_style)

    all_records = [preprocessor.process(loader.load_file(path)) for path in loader.list_data_files()]
    if args.oscilloscope_id:
        all_records = [record for record in all_records if record.oscilloscope_id == args.oscilloscope_id]

    range_a_records = [
        record
        for record in all_records
        if _in_shot_range(record.shot_number, args.range_a_start, args.range_a_end)
    ]
    range_b_records = [
        record
        for record in all_records
        if _in_shot_range(record.shot_number, args.range_b_start, args.range_b_end)
    ]
    if len(range_a_records) < 2 or len(range_b_records) < 2:
        raise RuntimeError("Each shot range needs at least two records to compute confidence intervals.")

    channel_name = args.channel
    compare_dir = config.output_dir / "figures" / "comparison"
    label_a = f"shots{args.range_a_start}-{args.range_a_end}"
    label_b = f"shots{args.range_b_start}-{args.range_b_end}"
    osc_suffix = f"_{args.oscilloscope_id}" if args.oscilloscope_id else ""
    stem = f"{label_a}_vs_{label_b}{osc_suffix}"

    range_compare_path = figure_builder.plot_two_ranges_with_ci(
        range_a_records,
        range_b_records,
        compare_dir / f"{stem}_mean_ci_compare.png",
        channel_name=channel_name,
        label_a=label_a,
        label_b=label_b,
    )
    range_a_path = figure_builder.plot_range_average_with_ci(
        range_a_records,
        compare_dir / f"{stem}_range_a_mean_ci.png",
        channel_name=channel_name,
        label=label_a,
    )
    range_b_path = figure_builder.plot_range_average_with_ci(
        range_b_records,
        compare_dir / f"{stem}_range_b_mean_ci.png",
        channel_name=channel_name,
        label=label_b,
    )

    stats_a = figure_builder.compute_range_average_with_ci(
        range_a_records,
        channel_name=channel_name,
    )
    stats_b = figure_builder.compute_range_average_with_ci(
        range_b_records,
        channel_name=channel_name,
    )

    print("Generated shot-range comparison figures:")
    print(f"- Two-range comparison: {range_compare_path}")
    print(f"- Range A mean+CI: {range_a_path}")
    print(f"- Range B mean+CI: {range_b_path}")
    print("Range summary:")
    print(
        f"- {label_a} ({stats_a['sample_count']} files), channel={stats_a['channel_name']},"
        f" mean_peak={float(np.max(stats_a['mean'])):.6g}"
    )
    print(
        f"- {label_b} ({stats_b['sample_count']} files), channel={stats_b['channel_name']},"
        f" mean_peak={float(np.max(stats_b['mean'])):.6g}"
    )


if __name__ == "__main__":
    main()
