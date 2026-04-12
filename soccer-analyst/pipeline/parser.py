"""
parser.py — Parse SoccerNet GSR minimap JSON into structured DataFrames.

Converts the raw per-frame JSON output from the tracker into clean
Pandas DataFrames suitable for tactical analysis.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd


def load_minimap_json(json_path: str) -> list[dict]:
    """Load the minimap JSON file produced by the tracker."""
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Minimap JSON not found: {json_path}")

    with open(path, "r") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Expected a JSON array of frame records")

    return data


def parse_player_tracks(minimap_data: list[dict]) -> pd.DataFrame:
    """
    Parse player tracking data into a DataFrame.

    Returns a DataFrame with columns:
        - frame_id (int): frame number
        - timestamp (float): seconds into the video
        - track_id (int): persistent player ID across frames
        - team (str): "home", "away", or "referee"
        - role (str): "player", "goalkeeper", or "referee"
        - jersey_number (str or None): detected jersey number
        - pixel_x, pixel_y (float): center of bbox in pixel coordinates
        - pitch_x, pitch_y (float): position on pitch in meters
        - confidence (float): detection confidence
    """
    rows = []
    for frame in minimap_data:
        frame_id = frame["frame_id"]
        timestamp = frame.get("timestamp", 0.0)

        for player in frame.get("players", []):
            # bbox is [left, top, width, height] from tracklab
            bbox = player.get("bbox", [0, 0, 0, 0])
            pixel_center_x = bbox[0] + bbox[2] / 2
            pixel_center_y = bbox[1] + bbox[3] / 2
            pitch_xy = player.get("pitch_xy", [None, None])

            rows.append({
                "frame_id": frame_id,
                "timestamp": timestamp,
                "track_id": player.get("track_id"),
                "team": player.get("team", "unknown"),
                "role": player.get("role", "player"),
                "jersey_number": player.get("jersey_number"),
                "pixel_x": pixel_center_x,
                "pixel_y": pixel_center_y,
                "pitch_x": pitch_xy[0],
                "pitch_y": pitch_xy[1],
                "confidence": player.get("confidence", 0.0),
            })

    df = pd.DataFrame(rows)

    if df.empty:
        return pd.DataFrame(columns=[
            "frame_id", "timestamp", "track_id", "team", "role",
            "jersey_number", "pixel_x", "pixel_y", "pitch_x", "pitch_y",
            "confidence",
        ])

    return df.sort_values(["frame_id", "track_id"]).reset_index(drop=True)


def parse_ball_positions(minimap_data: list[dict]) -> pd.DataFrame:
    """
    Parse ball position data into a DataFrame.

    Returns a DataFrame with columns:
        - frame_id (int)
        - timestamp (float)
        - pitch_x, pitch_y (float): ball position on pitch in meters
        - confidence (float)
        - detected (bool): whether the ball was detected in this frame
    """
    rows = []
    for frame in minimap_data:
        frame_id = frame["frame_id"]
        timestamp = frame.get("timestamp", 0.0)
        ball = frame.get("ball")

        if ball is not None:
            pitch_xy = ball.get("pitch_xy", [None, None])
            rows.append({
                "frame_id": frame_id,
                "timestamp": timestamp,
                "pitch_x": pitch_xy[0],
                "pitch_y": pitch_xy[1],
                "confidence": ball.get("confidence", 0.0),
                "detected": True,
            })
        else:
            rows.append({
                "frame_id": frame_id,
                "timestamp": timestamp,
                "pitch_x": None,
                "pitch_y": None,
                "confidence": 0.0,
                "detected": False,
            })

    df = pd.DataFrame(rows)

    if df.empty:
        return pd.DataFrame(columns=[
            "frame_id", "timestamp", "pitch_x", "pitch_y",
            "confidence", "detected",
        ])

    return df.sort_values("frame_id").reset_index(drop=True)


def get_team_data(player_df: pd.DataFrame, team: str) -> pd.DataFrame:
    """Filter player DataFrame for a specific team."""
    return player_df[player_df["team"] == team].copy()


def get_frame_snapshot(
    player_df: pd.DataFrame,
    ball_df: pd.DataFrame,
    frame_id: int,
) -> dict:
    """
    Get all player and ball positions for a single frame.

    Returns:
        dict with:
            - players: DataFrame of player positions at this frame
            - ball: dict with pitch_x, pitch_y (or None if not detected)
            - timestamp: float
    """
    frame_players = player_df[player_df["frame_id"] == frame_id]
    frame_ball_row = ball_df[ball_df["frame_id"] == frame_id]

    ball_pos = None
    if not frame_ball_row.empty and frame_ball_row.iloc[0]["detected"]:
        ball_pos = {
            "pitch_x": frame_ball_row.iloc[0]["pitch_x"],
            "pitch_y": frame_ball_row.iloc[0]["pitch_y"],
        }

    timestamp = 0.0
    if not frame_players.empty:
        timestamp = frame_players.iloc[0]["timestamp"]
    elif not frame_ball_row.empty:
        timestamp = frame_ball_row.iloc[0]["timestamp"]

    return {
        "players": frame_players,
        "ball": ball_pos,
        "timestamp": timestamp,
    }
