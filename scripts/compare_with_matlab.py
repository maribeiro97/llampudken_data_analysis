#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from osc_analysis.validation import ParityChecker


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    matlab_dir = repo_root / "matlab_reference"
    python_dir = repo_root / "outputs" / "figures" / "png"
    result = ParityChecker().compare_figure_counts(matlab_dir=matlab_dir, python_dir=python_dir)
    status = "PASS" if result.passed else "FAIL"
    print(f"[{status}] {result.message}")


if __name__ == "__main__":
    main()
