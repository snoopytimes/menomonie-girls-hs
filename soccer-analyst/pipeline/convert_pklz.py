"""
convert_pklz.py — Convert tracklab .pklz state file to JSON.

This script is designed to run inside the sn-gamestate venv (Python 3.9)
where tracklab's dependencies are available. It reads the pickled tracking
results and writes a clean JSON file consumable by our parser.py.

Usage (from sn-gamestate venv):
    python convert_pklz.py <pklz_path> <output_json_path> [--sample-rate <fps>]
"""

import argparse
import json
import pickle
import sys
import zipfile
from pathlib import Path

import numpy as np


def load_pklz(pklz_path: str) -> dict:
    """Load all video data from a .pklz tracker state file."""
    videos = {}
    with zipfile.ZipFile(pklz_path, "r") as zf:
        with zf.open("summary.json") as fp:
            summary = json.load(fp)

        names = zf.namelist()
        # Find detection files (numeric names without _image suffix)
        det_files = [
            n for n in names
            if n.endswith(".pkl") and not n.endswith("_image.pkl")
        ]

        for det_file in det_files:
            video_id = det_file.replace(".pkl", "")
            with zf.open(det_file) as fp:
                detections = pickle.load(fp)
            image_file = f"{video_id}_image.pkl"
            image_df = None
            if image_file in names:
                with zf.open(image_file) as fp:
                    image_df = pickle.load(fp)
            videos[video_id] = {
                "detections": detections,
                "images": image_df,
            }

    return videos


def convert_to_json(videos: dict, sample_rate: float) -> list[dict]:
    """
    Convert tracklab DataFrames to our minimap JSON format.

    Output format (per frame):
    {
        "frame_id": int,
        "timestamp": float,
        "players": [
            {
                "track_id": int,
                "team": "home" | "away" | "referee",
                "role": "player" | "goalkeeper" | "referee",
                "jersey_number": str | null,
                "bbox": [left, top, width, height],
                "pitch_xy": [x, y],
                "confidence": float,
            },
            ...
        ],
        "ball": null  // tracklab doesn't detect ball separately
    }
    """
    all_frames = []

    for video_id, data in videos.items():
        detections = data["detections"]
        images = data["images"]

        if detections is None or detections.empty:
            continue

        # Group detections by image_id (frame)
        for image_id, frame_dets in detections.groupby("image_id"):
            # Get frame index from image metadata
            frame_idx = int(image_id)
            if images is not None and image_id in images.index:
                img_row = images.loc[image_id]
                if "frame" in img_row.index:
                    frame_idx = int(img_row["frame"])

            timestamp = frame_idx / sample_rate if sample_rate > 0 else 0.0

            players = []
            for _, det in frame_dets.iterrows():
                # Extract pitch coordinates
                pitch_xy = [None, None]
                if "bbox_pitch" in det.index and det["bbox_pitch"] is not None:
                    bp = det["bbox_pitch"]
                    if isinstance(bp, dict):
                        pitch_xy = [
                            bp.get("x_bottom_middle"),
                            bp.get("y_bottom_middle"),
                        ]

                # Extract bbox
                bbox = [0, 0, 0, 0]
                for bbox_col in ("track_bbox_ltwh", "bbox_ltwh"):
                    if bbox_col in det.index and det[bbox_col] is not None:
                        b = det[bbox_col]
                        if hasattr(b, "tolist"):
                            bbox = b.tolist()
                        elif isinstance(b, (list, tuple)):
                            bbox = list(b)
                        break

                # Map team labels: tracklab uses "left"/"right", we use "home"/"away"
                team_raw = det.get("team", None)
                if team_raw == "left":
                    team = "home"
                elif team_raw == "right":
                    team = "away"
                elif team_raw is not None:
                    team = str(team_raw)
                else:
                    team = "unknown"

                # Role
                role = "player"
                if "role" in det.index and det["role"] is not None:
                    role = str(det["role"])
                    if role in ("referee",):
                        team = "referee"

                # Jersey number
                jersey = None
                for jn_col in ("jn_tracklet", "jersey_number_detection"):
                    if jn_col in det.index and det[jn_col] is not None:
                        jn = det[jn_col]
                        if isinstance(jn, (int, float)) and not np.isnan(jn):
                            jersey = str(int(jn))
                        elif isinstance(jn, str) and jn.strip():
                            jersey = jn.strip()
                        if jersey:
                            break

                # Confidence
                conf = 0.0
                for conf_col in ("track_bbox_conf", "bbox_conf"):
                    if conf_col in det.index and det[conf_col] is not None:
                        try:
                            conf = float(det[conf_col])
                            break
                        except (ValueError, TypeError):
                            pass

                # Track ID
                track_id = None
                if "track_id" in det.index and det["track_id"] is not None:
                    try:
                        track_id = int(det["track_id"])
                    except (ValueError, TypeError):
                        pass

                players.append({
                    "track_id": track_id,
                    "team": team,
                    "role": role,
                    "jersey_number": jersey,
                    "bbox": bbox,
                    "pitch_xy": pitch_xy,
                    "confidence": conf,
                })

            all_frames.append({
                "frame_id": frame_idx,
                "timestamp": round(timestamp, 3),
                "players": players,
                "ball": None,  # tracklab doesn't provide separate ball detection
            })

    # Sort by frame_id
    all_frames.sort(key=lambda f: f["frame_id"])
    return all_frames


def main():
    parser = argparse.ArgumentParser(
        description="Convert tracklab .pklz state to minimap JSON"
    )
    parser.add_argument("pklz_path", help="Path to .pklz tracker state file")
    parser.add_argument("output_path", help="Path to write output JSON")
    parser.add_argument(
        "--sample-rate", type=float, default=30.0,
        help="Video FPS for timestamp calculation (default: 30)",
    )
    args = parser.parse_args()

    if not Path(args.pklz_path).exists():
        print(f"Error: {args.pklz_path} not found", file=sys.stderr)
        sys.exit(1)

    videos = load_pklz(args.pklz_path)
    frames = convert_to_json(videos, args.sample_rate)

    with open(args.output_path, "w") as f:
        json.dump(frames, f, indent=2, default=str)

    print(f"Converted {len(frames)} frames to {args.output_path}")


if __name__ == "__main__":
    main()
