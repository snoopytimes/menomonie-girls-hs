# Soccer Analyst

Local tactical analysis tool for high school soccer. Processes game footage (MP4 exported from Hudl) to generate formation snapshots, player heatmaps, pressing intensity charts, and team shape analysis.

## Prerequisites

- Python 3.11+
- FFmpeg (`brew install ffmpeg`)
- ~4GB disk space for SoccerNet GSR model weights

## Setup

```bash
# 1. Install dependencies with uv
uv sync

# 2. Install SoccerNet GSR (player detection, tracking, and homography)
uv pip install soccernet
git clone https://github.com/SoccerNet/sn-gamestate.git
cd sn-gamestate
uv pip install -e .
cd ..

# 3. Download SoccerNet GSR model weights
# Follow the instructions in the sn-gamestate README to download
# pre-trained weights and place them in models/sn-gsr/
```

## Usage

### Run the Streamlit UI

```bash
uv run streamlit run ui/app.py
```

Then open http://localhost:8501 in your browser.

### Workflow

1. Drop your MP4 files into `data/videos/` (or upload via the UI)
2. Select a video and click "Run Analysis Pipeline"
3. View results across tabs: Heatmaps, Formation, Pressing, Raw Data
4. Export reports to `output/reports/`

### Configuration

Edit `config.yaml` to adjust:

- **Team color**: HSV range for home jersey detection (default: maroon)
- **Frame sample rate**: How many frames per second to extract (default: 2)
- **Pressing threshold**: Distance in meters to count as "pressing" (default: 10m)
- **Pitch dimensions**: Standard FIFA is 105x68m, adjust if your field differs

## Project Structure

```
soccer-analyst/
├── config.yaml          # All configurable parameters
├── data/videos/         # Drop MP4 files here
├── output/reports/      # Generated heatmaps, CSVs, PNGs
├── pipeline/
│   ├── ingest.py        # MP4 validation and frame extraction
│   ├── tracker.py       # SoccerNet GSR wrapper (stub — see below)
│   ├── parser.py        # Parse minimap JSON into DataFrames
│   └── tactics.py       # Formation, pressing, heatmap analysis
├── ui/
│   └── app.py           # Streamlit interface
└── pyproject.toml
```

## SoccerNet GSR Integration Status

`tracker.py` is currently a **stub**. It documents the expected inputs (extracted frames) and outputs (minimap JSON with per-frame player/ball positions in pitch coordinates).

To wire it up:
1. Install sn-gamestate (see Setup above)
2. Follow the integration steps documented in `pipeline/tracker.py`
3. The tracker should produce a JSON array of frame records — see the docstring in `tracker.py` for the exact schema

### Sideline Camera Considerations

SoccerNet GSR was trained on broadcast footage. Fixed sideline cameras differ in viewing angle, field of view, and perspective distortion. Areas likely to degrade:

- **Homography estimation**: The model expects broadcast-style pitch line patterns. Consider fine-tuning on 50-100 annotated sideline frames.
- **Far-side detection**: Players at the far end of the pitch will be small and occluded.
- **Ball detection**: Smaller apparent size from a lower camera angle.

See comments in `pipeline/tracker.py` for fine-tuning guidance.

## Loading Pre-generated Data

If you have minimap JSON from another source (manual annotation, a different tracker), you can load it directly through the UI without running the full pipeline. The JSON schema is documented in `pipeline/tracker.py`.
