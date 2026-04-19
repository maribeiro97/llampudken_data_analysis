from __future__ import annotations

from pathlib import Path

from osc_analysis.analysis import FeatureExtractor, SpectralAnalyzer
from osc_analysis.config import PipelineConfig
from osc_analysis.io import DataLoader
from osc_analysis.models import PipelineReport
from osc_analysis.plotting import FigureBuilder
from osc_analysis.preprocessing import SignalPreprocessor


class AnalysisPipeline:
    """Orchestrate load -> preprocess -> analyze -> plot."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.loader = DataLoader(config.input_dir)
        self.preprocessor = SignalPreprocessor(config.preprocess)
        self.features = FeatureExtractor()
        self.spectral = SpectralAnalyzer()
        self.plotter = FigureBuilder(config.plot_style)

    def run(self, max_files: int | None = None) -> PipelineReport:
        files = self.loader.list_data_files()
        if max_files is not None:
            files = files[:max_files]

        figure_paths: list[Path] = []
        notes: list[str] = []
        png_time_dir = self.config.output_dir / "figures" / "png" / "time"
        png_fft_dir = self.config.output_dir / "figures" / "png" / "fft"
        png_time_dir.mkdir(parents=True, exist_ok=True)
        png_fft_dir.mkdir(parents=True, exist_ok=True)
        for file_path in files:
            raw = self.loader.load_file(file_path)
            processed = self.preprocessor.process(raw)
            feat = self.features.extract(processed)
            spec = self.spectral.compute(processed)

            shot_tag = f"shot{processed.shot_number}_{processed.oscilloscope_id}"
            shot_dir = f"shot{processed.shot_number}"
            time_fig = png_time_dir / shot_dir / f"{shot_tag}_time.png"
            freq_fig = png_fft_dir / shot_dir / f"{shot_tag}_fft.png"

            figure_paths.append(self.plotter.plot_time_series(processed, time_fig))
            figure_paths.append(self.plotter.plot_spectrum(spec, freq_fig, shot_tag))
            figure_paths.append(time_fig.with_suffix(".html"))
            figure_paths.append(time_fig.with_suffix(".pdf"))
            figure_paths.append(time_fig.with_suffix(".svg"))
            figure_paths.append(freq_fig.with_suffix(".html"))
            figure_paths.append(freq_fig.with_suffix(".pdf"))
            figure_paths.append(freq_fig.with_suffix(".svg"))

            notes.append(
                f"{shot_tag}: peaks={feat.channel_peak} rms={feat.channel_rms}"
            )

        return PipelineReport(files_processed=len(files), figure_paths=figure_paths, notes=notes)
