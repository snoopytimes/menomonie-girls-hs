"""
tracker.py — SoccerNet Game State Reconstruction wrapper.

Invokes the tracklab CLI (from the sn-gamestate repo) via subprocess to run
player detection, tracking, team identification, and camera calibration on
video frames. Converts the .pklz tracker state output into our minimap JSON
format for downstream tactical analysis.

IMPORTANT — Camera Considerations:
    SoccerNet GSR models were trained on broadcast footage (elevated, panning
    cameras). Our footage is from a FIXED SIDELINE CAMERA, which differs in:
    - Narrower field of view (may not see the full pitch)
    - Lower camera angle (more perspective distortion, more occlusion)
    - No camera panning (homography is more stable, but coverage is limited)

    This may degrade accuracy for:
    - Homography estimation (the model expects broadcast-style keypoint patterns)
    - Player detection at far end of pitch (small, heavily occluded)
    - Ball detection (smaller apparent size from sideline angle)

    TO FINE-TUNE for sideline footage:
    1. Annotate 50-100 frames from your sideline footage with pitch keypoints
    2. Fine-tune the homography module using the sn-gamestate training scripts
    3. For detection, add sideline frames to the training set with bounding box
       annotations and retrain the detector head
"""

import json
import logging
import os
import subprocess
from glob import glob
from pathlib import Path

import yaml

log = logging.getLogger(__name__)

# Path to sn-gamestate repo relative to project root
_DEFAULT_SN_GAMESTATE_DIR = "sn-gamestate"


def _find_sn_gamestate_dir(config_path: str = "config.yaml") -> Path:
    """Locate the sn-gamestate directory."""
    config = _load_config(config_path)
    tracker_cfg = config.get("tracker", {})

    # Check config for custom path
    sn_dir = tracker_cfg.get("sn_gamestate_dir", _DEFAULT_SN_GAMESTATE_DIR)
    sn_path = Path(sn_dir)

    if not sn_path.is_absolute():
        # Resolve relative to project root (parent of pipeline/)
        project_root = Path(__file__).resolve().parent.parent
        sn_path = project_root / sn_path

    if not sn_path.exists():
        raise FileNotFoundError(
            f"sn-gamestate directory not found at {sn_path}. "
            f"Clone it: git clone https://github.com/SoccerNet/sn-gamestate.git {sn_path}"
        )

    return sn_path


def _load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def _find_latest_pklz(outputs_dir: Path) -> Path | None:
    """Find the most recently created .pklz state file in tracklab outputs."""
    pklz_files = sorted(outputs_dir.rglob("*.pklz"), key=os.path.getmtime)
    return pklz_files[-1] if pklz_files else None


def run_tracking(
    video_path: str,
    config_path: str = "config.yaml",
    progress_callback=None,
) -> dict:
    """
    Run the SoccerNet GSR pipeline on a video file.

    Invokes tracklab via subprocess using the sn-gamestate venv, then converts
    the .pklz output into our minimap JSON format.

    Args:
        video_path: Path to the MP4 file to analyze.
        config_path: Path to config.yaml for settings.
        progress_callback: Optional callable(line: str) for streaming output.

    Returns:
        dict with:
            - minimap_json_path (str): Path to the output minimap JSON file.
            - tracking_stats (dict): Summary statistics.
    """
    video_path = Path(video_path).resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    config = _load_config(config_path)
    tracker_cfg = config.get("tracker", {})

    sn_dir = _find_sn_gamestate_dir(config_path)
    sn_venv_python = sn_dir / ".venv" / "bin" / "python"
    sn_uv = "uv"  # Assume uv is on PATH

    if not sn_venv_python.exists():
        raise RuntimeError(
            f"sn-gamestate venv not found at {sn_venv_python}. "
            f"Set it up: cd {sn_dir} && uv venv --python 3.9 && uv pip install -e ."
        )

    # Step 1: Run tracklab CLI via subprocess
    log.info("Running tracklab on %s...", video_path.name)

    # caffeinate -i prevents macOS idle sleep for the duration of tracklab.
    # Without this, a sleeping Mac suspends the process and drops the UI.
    tracklab_cmd = [
        "caffeinate", "-i",
        sn_uv, "run", "--no-sync",
        "--project", str(sn_dir),
        "--python", str(sn_venv_python),
        "tracklab", "-cn", "soccernet",
        "dataset=video",
        f"dataset.video_path={video_path}",
        "dataset.eval_set=val",
        "eval_tracking=False",
        "test_tracking=True",
        # MPS (Apple Silicon) tensors cannot be shared between DataLoader worker
        # processes via shared memory. Force single-process loading.
        "engine.num_workers=0",
    ]

    # Apply config overrides
    batch_size = tracker_cfg.get("batch_size", 8)
    tracklab_cmd.append(f"modules.bbox_detector.batch_size={batch_size}")

    confidence = tracker_cfg.get("confidence_threshold", 0.5)
    tracklab_cmd.append(f"modules.bbox_detector.cfg.min_confidence={confidence}")

    # Limit frames if configured (useful for long videos)
    max_frames = tracker_cfg.get("max_frames", -1)
    if max_frames > 0:
        tracklab_cmd.append(f"++dataset.nframes={max_frames}")

    # TODO: Enable jersey_number_detect and tracklet_agg once full mmcv is
    # installed. Jersey number recognition maps track IDs to actual player
    # numbers, enabling per-player movement analysis across games.
    # To enable:
    #   1. Build mmcv from source (requires full C++ extensions, not mmcv-lite):
    #      pip install mmcv==2.0.1 (on Linux, or build from source on macOS)
    #   2. Set tracker.enable_jersey_ocr: true in config.yaml
    #   3. Pipeline will include: jersey_number_detect, tracklet_agg
    enable_jersey = tracker_cfg.get("enable_jersey_ocr", False)
    if enable_jersey:
        tracklab_cmd.append(
            "pipeline=[bbox_detector,reid,track,pitch,calibration,"
            "jersey_number_detect,tracklet_agg,team,team_side]"
        )
    else:
        # tracklet_agg is required to convert role_detection -> role,
        # which TrackletTeamClustering (team module) depends on.
        # Override attributes to only aggregate role (no jersey_number).
        tracklab_cmd.append(
            "pipeline=[bbox_detector,reid,track,pitch,calibration,tracklet_agg,team,team_side]"
        )
        tracklab_cmd.append("modules.tracklet_agg.cfg.attributes=[role]")

    log.info("Command: %s", " ".join(tracklab_cmd))

    # Stream output line-by-line for progress visibility
    # PYTORCH_ENABLE_MPS_FALLBACK=1: some torchvision ops (e.g. nms) are not
    # implemented for Apple MPS; this allows them to fall back to CPU silently.
    tracklab_env = {**os.environ, "PYTORCH_ENABLE_MPS_FALLBACK": "1"}
    process = subprocess.Popen(
        tracklab_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=str(sn_dir),
        env=tracklab_env,
        bufsize=1,
    )

    output_lines = []
    for line in process.stdout:
        line = line.rstrip()
        output_lines.append(line)
        log.info("tracklab: %s", line)
        if progress_callback:
            progress_callback(line)

    process.wait()

    if process.returncode != 0:
        last_output = "\n".join(output_lines[-20:])
        raise RuntimeError(
            f"tracklab exited with code {process.returncode}.\n"
            f"Last output:\n{last_output}"
        )

    # Step 2: Find the .pklz output
    outputs_dir = sn_dir / "outputs"
    states_dir = sn_dir / "states"

    pklz_path = _find_latest_pklz(states_dir)
    if pklz_path is None:
        pklz_path = _find_latest_pklz(outputs_dir)
    if pklz_path is None:
        raise FileNotFoundError(
            "No .pklz state file found after tracklab run. "
            "Check tracklab output for errors."
        )

    log.info("Found tracker state: %s", pklz_path)

    # Step 3: Convert .pklz to minimap JSON using sn-gamestate's Python
    # (because the pickle may contain tracklab-specific objects)
    converter_script = Path(__file__).resolve().parent / "convert_pklz.py"
    output_dir = Path(config.get("output", {}).get("report_dir", "output/reports"))
    output_dir.mkdir(parents=True, exist_ok=True)
    json_output_path = output_dir / f"{video_path.stem}_minimap.json"

    # Get video FPS for timestamp calculation
    video_fps = _get_video_fps(str(video_path))

    convert_cmd = [
        str(sn_venv_python),
        str(converter_script),
        str(pklz_path),
        str(json_output_path),
        "--sample-rate", str(video_fps),
    ]

    log.info("Converting .pklz to JSON...")
    conv_result = subprocess.run(
        convert_cmd,
        capture_output=True,
        text=True,
    )

    if conv_result.returncode != 0:
        raise RuntimeError(
            f"pklz conversion failed: {conv_result.stderr}"
        )

    log.info("Conversion output: %s", conv_result.stdout.strip())

    # Step 4: Compute tracking stats
    with open(json_output_path, "r") as f:
        minimap_data = json.load(f)

    total_frames = len(minimap_data)
    total_detections = sum(len(f["players"]) for f in minimap_data)
    avg_players = total_detections / total_frames if total_frames > 0 else 0
    ball_frames = sum(1 for f in minimap_data if f.get("ball") is not None)

    return {
        "minimap_json_path": str(json_output_path),
        "tracking_stats": {
            "total_frames": total_frames,
            "total_detections": total_detections,
            "avg_players_per_frame": round(avg_players, 1),
            "ball_detection_rate": round(ball_frames / total_frames, 2) if total_frames > 0 else 0,
        },
    }


def _get_video_fps(video_path: str) -> float:
    """Get video FPS using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            str(video_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        probe = json.loads(result.stdout)
        for stream in probe.get("streams", []):
            if stream.get("codec_type") == "video":
                fps_parts = stream.get("r_frame_rate", "30/1").split("/")
                return float(fps_parts[0]) / float(fps_parts[1])
    except Exception:
        pass
    return 30.0
