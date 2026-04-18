#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


def main() -> None:
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

    all_files = loader.list_data_files()
    if len(all_files) < 2:
        raise RuntimeError("Need at least two oscilloscope files to run comparison template.")

    candidate_records = [preprocessor.process(loader.load_file(file_path)) for file_path in all_files]
    first = None
    second = None
    channel_name = None
    for idx, record_a in enumerate(candidate_records):
        for record_b in candidate_records[idx + 1 :]:
            shared_channels = [name for name in record_a.channels if name in record_b.channels]
            if shared_channels:
                first = record_a
                second = record_b
                channel_name = shared_channels[0]
                break
        if first is not None:
            break

    if first is None or second is None or channel_name is None:
        raise RuntimeError("Could not find two files that share at least one channel.")
    compare_dir = config.output_dir / "figures" / "comparison"
    shot_pair = f"shot{first.shot_number}_vs_shot{second.shot_number}_{first.oscilloscope_id}"

    overlay_path = figure_builder.plot_shot_overlay(
        first,
        second,
        compare_dir / f"{shot_pair}_overlay.png",
        channel_name=channel_name,
    )
    heatmap_path = figure_builder.plot_shot_difference_heatmap(
        first,
        second,
        compare_dir / f"{shot_pair}_diff_heatmap.png",
        channel_name=channel_name,
    )
    kde_path = figure_builder.plot_shot_kde_panel(
        first,
        second,
        compare_dir / f"{shot_pair}_kde_panel.png",
        channel_name=channel_name,
    )
    metrics = figure_builder.compute_shot_comparison_metrics(
        first,
        second,
        channel_name=channel_name,
    )

    print("Generated comparison figures:")
    print(f"- Overlay: {overlay_path}")
    print(f"- Difference heatmap: {heatmap_path}")
    print(f"- KDE panel: {kde_path}")
    print("Metrics:")
    for key, value in metrics.items():
        print(f"- {key}: {value:.6g}")


if __name__ == "__main__":
    main()
