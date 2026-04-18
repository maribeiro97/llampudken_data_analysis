# llampudken_data_analysis

Starter OOP scaffolding to migrate MATLAB oscilloscope analysis to Python while preserving figure equivalence.

## Quick start

```bash
python -m pip install -e .
python scripts/run_pipeline.py
```

Generated outputs are written under `outputs/figures` and `outputs/reports`.
The pipeline emits static PNG plots under `outputs/figures/png` and interactive Plotly HTML files under `outputs/figures/html`.

## Project layout

- `src/osc_analysis/io`: file loading/parsing and channel calibration from `OSC_CALIBRATIONS.py`.
- `src/osc_analysis/preprocessing`: baseline correction and detrending.
- `src/osc_analysis/analysis`: feature extraction and spectral analysis.
- `src/osc_analysis/plotting`: matplotlib figure generation.
- `src/osc_analysis/pipeline`: end-to-end orchestration.
- `src/osc_analysis/validation`: parity checks against MATLAB references.

## Next steps

1. Port each MATLAB processing function into dedicated classes/methods.
2. Add true numerical and visual parity checks in `validation/parity_checker.py`.
3. Expand tests to validate algorithm equivalence shot-by-shot.
