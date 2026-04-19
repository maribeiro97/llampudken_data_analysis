from pathlib import Path

from osc_analysis.gui import launch_shot_comparison_gui


if __name__ == "__main__":
    launch_shot_comparison_gui(Path("osc_data"))
