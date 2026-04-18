from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParityResult:
    passed: bool
    message: str


class ParityChecker:
    """Placeholder validator for MATLAB/Python output parity."""

    def compare_figure_counts(self, matlab_dir: Path, python_dir: Path) -> ParityResult:
        matlab_count = len(list(matlab_dir.glob("*.png")))
        python_count = len(list(python_dir.glob("*.png")))
        passed = matlab_count == python_count and python_count > 0
        return ParityResult(
            passed=passed,
            message=f"matlab_figures={matlab_count}, python_figures={python_count}",
        )
