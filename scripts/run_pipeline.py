#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from osc_analysis.config import PipelineConfig
from osc_analysis.pipeline import AnalysisPipeline


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    config = PipelineConfig(
        input_dir=repo_root / "osc_data",
        output_dir=repo_root / "outputs",
    )
    report = AnalysisPipeline(config).run()
    print(f"Processed {report.files_processed} files.")
    print(f"Generated {len(report.figure_paths)} figures.")
    for note in report.notes:
        print(f"- {note}")


if __name__ == "__main__":
    main()
