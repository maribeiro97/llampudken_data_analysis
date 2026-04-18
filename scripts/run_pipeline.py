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
    from osc_analysis.pipeline import AnalysisPipeline

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
