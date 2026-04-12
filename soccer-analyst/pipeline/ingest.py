"""
ingest.py — MP4 validation and frame extraction.

Accepts a path to an MP4 file (exported from Hudl), validates it,
and extracts frames at a configurable sample rate using FFmpeg.
Extracted frames are saved to a temporary directory for downstream processing.
"""

import os
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import cv2
import yaml


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def validate_video(video_path: str) -> dict:
    """
    Validate that the file is a playable MP4 video using ffprobe.

    Returns a dict with video metadata:
        - duration (float): video length in seconds
        - width (int): frame width in pixels
        - height (int): frame height in pixels
        - fps (float): frames per second
        - codec (str): video codec name

    Raises:
        FileNotFoundError: if the file doesn't exist
        ValueError: if the file is not a valid video or has no video stream
    """
    video_path = Path(video_path)

    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if not video_path.suffix.lower() == ".mp4":
        raise ValueError(f"Expected .mp4 file, got: {video_path.suffix}")

    # Use ffprobe to extract video metadata
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        str(video_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        raise RuntimeError(
            "ffprobe not found. Install FFmpeg: brew install ffmpeg"
        )
    except subprocess.CalledProcessError as e:
        raise ValueError(f"ffprobe failed — file may be corrupt: {e.stderr}")

    probe = json.loads(result.stdout)

    # Find the video stream
    video_stream = None
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == "video":
            video_stream = stream
            break

    if video_stream is None:
        raise ValueError(f"No video stream found in {video_path}")

    # Parse FPS from r_frame_rate (e.g., "30/1" or "30000/1001")
    fps_parts = video_stream.get("r_frame_rate", "30/1").split("/")
    fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0

    duration = float(probe.get("format", {}).get("duration", 0))

    metadata = {
        "duration": duration,
        "width": int(video_stream.get("width", 0)),
        "height": int(video_stream.get("height", 0)),
        "fps": round(fps, 2),
        "codec": video_stream.get("codec_name", "unknown"),
        "path": str(video_path.resolve()),
    }

    return metadata


def extract_frames(
    video_path: str,
    output_dir: str | None = None,
    config_path: str = "config.yaml",
) -> dict:
    """
    Extract frames from an MP4 at the configured sample rate.

    Args:
        video_path: Path to the MP4 file.
        output_dir: Directory to save frames. If None, uses a temp directory.
        config_path: Path to config.yaml.

    Returns:
        dict with:
            - frames_dir (str): path to directory containing extracted frames
            - frame_count (int): number of frames extracted
            - sample_rate (float): FPS used for extraction
            - video_metadata (dict): output of validate_video()
    """
    config = load_config(config_path)
    video_cfg = config.get("video", {})

    sample_rate = video_cfg.get("frame_sample_rate", 2)
    max_resolution = video_cfg.get("max_resolution", 1920)
    output_format = video_cfg.get("output_format", "jpg")
    jpeg_quality = video_cfg.get("jpeg_quality", 85)

    # Validate the video first
    metadata = validate_video(video_path)

    # Create output directory
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="soccer_analyst_frames_")
    else:
        os.makedirs(output_dir, exist_ok=True)

    # Build FFmpeg command
    # Scale down if needed, maintaining aspect ratio
    scale_filter = f"scale='min({max_resolution},iw):-2'"

    # Quality settings per format
    if output_format == "jpg":
        quality_args = ["-q:v", str(max(1, min(31, 31 - int(jpeg_quality * 31 / 100))))]
    else:
        quality_args = []

    output_pattern = os.path.join(output_dir, f"frame_%06d.{output_format}")

    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vf", f"{scale_filter},fps={sample_rate}",
        *quality_args,
        "-y",  # overwrite
        output_pattern,
    ]

    try:
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        raise RuntimeError("ffmpeg not found. Install FFmpeg: brew install ffmpeg")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg frame extraction failed: {e.stderr}")

    # Count extracted frames
    frame_files = sorted(
        f for f in os.listdir(output_dir)
        if f.startswith("frame_") and f.endswith(f".{output_format}")
    )

    return {
        "frames_dir": output_dir,
        "frame_count": len(frame_files),
        "sample_rate": sample_rate,
        "video_metadata": metadata,
    }


def cleanup_frames(frames_dir: str) -> None:
    """Remove the temporary frames directory after processing."""
    if os.path.isdir(frames_dir):
        shutil.rmtree(frames_dir)
