"""
tactics.py — Formation shape, pressing intensity, and heatmap analysis.

All analysis operates on pitch coordinates (meters) parsed from the
SoccerNet GSR minimap JSON via parser.py.
"""

import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for server/CLI use
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
import seaborn as sns
import yaml


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Pitch drawing utility
# ---------------------------------------------------------------------------

def draw_pitch(ax, pitch_length: float = 105.0, pitch_width: float = 68.0):
    """Draw a top-down soccer pitch on a matplotlib Axes."""
    ax.set_xlim(-2, pitch_length + 2)
    ax.set_ylim(-2, pitch_width + 2)
    ax.set_aspect("equal")
    ax.set_facecolor("#2e8b57")

    line_color = "white"
    lw = 1.5

    # Pitch outline
    ax.plot([0, pitch_length], [0, 0], color=line_color, lw=lw)
    ax.plot([0, pitch_length], [pitch_width, pitch_width], color=line_color, lw=lw)
    ax.plot([0, 0], [0, pitch_width], color=line_color, lw=lw)
    ax.plot([pitch_length, pitch_length], [0, pitch_width], color=line_color, lw=lw)

    # Halfway line
    ax.plot([pitch_length / 2, pitch_length / 2], [0, pitch_width], color=line_color, lw=lw)

    # Center circle
    center_circle = plt.Circle((pitch_length / 2, pitch_width / 2), 9.15,
                                fill=False, color=line_color, lw=lw)
    ax.add_patch(center_circle)

    # Penalty areas (16.5m from goal line, 40.3m wide)
    pen_y_start = (pitch_width - 40.3) / 2
    for x_start in [0, pitch_length - 16.5]:
        ax.add_patch(patches.Rectangle(
            (x_start, pen_y_start), 16.5, 40.3,
            fill=False, edgecolor=line_color, lw=lw,
        ))

    # Goal areas (5.5m from goal line, 18.3m wide)
    goal_y_start = (pitch_width - 18.3) / 2
    for x_start in [0, pitch_length - 5.5]:
        ax.add_patch(patches.Rectangle(
            (x_start, goal_y_start), 5.5, 18.3,
            fill=False, edgecolor=line_color, lw=lw,
        ))

    ax.set_xticks([])
    ax.set_yticks([])

    return ax


# ---------------------------------------------------------------------------
# Heatmaps
# ---------------------------------------------------------------------------

def generate_player_heatmap(
    player_df: pd.DataFrame,
    track_id: int | None = None,
    team: str | None = None,
    config_path: str = "config.yaml",
) -> plt.Figure:
    """
    Generate a top-down pitch heatmap for a player or team.

    Args:
        player_df: DataFrame from parser.parse_player_tracks()
        track_id: If set, generate heatmap for this specific player.
        team: If set (and track_id is None), generate heatmap for the whole team.
        config_path: Path to config.yaml.

    Returns:
        matplotlib Figure with the heatmap drawn on a pitch.
    """
    config = load_config(config_path)
    tactics_cfg = config.get("tactics", {})
    output_cfg = config.get("output", {})

    pitch_length = tactics_cfg.get("pitch_length", 105.0)
    pitch_width = tactics_cfg.get("pitch_width", 68.0)
    resolution = tactics_cfg.get("heatmap_resolution", 105)
    colormap = output_cfg.get("heatmap_colormap", "YlOrRd")

    # Filter data
    df = player_df.dropna(subset=["pitch_x", "pitch_y"])
    if track_id is not None:
        df = df[df["track_id"] == track_id]
    elif team is not None:
        df = df[df["team"] == team]

    if df.empty:
        fig, ax = plt.subplots(figsize=(12, 8))
        draw_pitch(ax, pitch_length, pitch_width)
        ax.set_title("No data available")
        return fig

    # Build 2D histogram
    x_bins = np.linspace(0, pitch_length, resolution + 1)
    y_bins = np.linspace(0, pitch_width, int(resolution * pitch_width / pitch_length) + 1)

    heatmap, xedges, yedges = np.histogram2d(
        df["pitch_x"].values,
        df["pitch_y"].values,
        bins=[x_bins, y_bins],
    )

    # Normalize
    if heatmap.max() > 0:
        heatmap = heatmap / heatmap.max()

    fig, ax = plt.subplots(figsize=(12, 8))
    draw_pitch(ax, pitch_length, pitch_width)

    # Overlay heatmap with transparency
    ax.imshow(
        heatmap.T,
        extent=[0, pitch_length, 0, pitch_width],
        origin="lower",
        cmap=colormap,
        alpha=0.6,
        interpolation="gaussian",
        aspect="auto",
    )

    label = f"Player {track_id}" if track_id else (team or "All Players")
    ax.set_title(f"Heatmap — {label}", fontsize=14, color="white", pad=10)

    fig.patch.set_facecolor("#1a1a2e")
    fig.tight_layout()

    return fig


# ---------------------------------------------------------------------------
# Formation shape
# ---------------------------------------------------------------------------

def compute_formation_shape(
    player_df: pd.DataFrame,
    frame_id: int,
    team: str = "home",
) -> dict:
    """
    Compute the team's formation shape at a given frame.

    Returns:
        dict with:
            - positions: list of (pitch_x, pitch_y) for each player
            - centroid: (x, y) average position
            - spread: average distance from centroid (compactness metric)
            - width: max lateral spread
            - depth: max longitudinal spread
    """
    frame_data = player_df[
        (player_df["frame_id"] == frame_id) &
        (player_df["team"] == team)
    ].dropna(subset=["pitch_x", "pitch_y"])

    if frame_data.empty:
        return {"positions": [], "centroid": None, "spread": None, "width": None, "depth": None}

    positions = list(zip(frame_data["pitch_x"], frame_data["pitch_y"]))
    xs = frame_data["pitch_x"].values
    ys = frame_data["pitch_y"].values

    centroid = (float(xs.mean()), float(ys.mean()))
    distances = np.sqrt((xs - centroid[0]) ** 2 + (ys - centroid[1]) ** 2)

    return {
        "positions": positions,
        "centroid": centroid,
        "spread": float(distances.mean()),
        "width": float(ys.max() - ys.min()),
        "depth": float(xs.max() - xs.min()),
    }


def plot_formation(
    player_df: pd.DataFrame,
    frame_id: int,
    config_path: str = "config.yaml",
) -> plt.Figure:
    """Plot both teams' positions at a given frame on a pitch diagram."""
    config = load_config(config_path)
    tactics_cfg = config.get("tactics", {})
    team_cfg = config.get("team", {})

    pitch_length = tactics_cfg.get("pitch_length", 105.0)
    pitch_width = tactics_cfg.get("pitch_width", 68.0)

    fig, ax = plt.subplots(figsize=(12, 8))
    draw_pitch(ax, pitch_length, pitch_width)

    frame_data = player_df[player_df["frame_id"] == frame_id].dropna(
        subset=["pitch_x", "pitch_y"]
    )

    colors = {"home": "maroon", "away": "dodgerblue", "referee": "yellow"}

    for team_label, color in colors.items():
        team_data = frame_data[frame_data["team"] == team_label]
        if not team_data.empty:
            display_name = team_cfg.get(f"{team_label}_label", team_label.capitalize())
            ax.scatter(
                team_data["pitch_x"], team_data["pitch_y"],
                c=color, s=120, edgecolors="white", linewidths=1.5,
                label=display_name, zorder=5,
            )
            # Player ID labels
            for _, row in team_data.iterrows():
                ax.annotate(
                    str(int(row["track_id"])),
                    (row["pitch_x"], row["pitch_y"]),
                    fontsize=7, ha="center", va="center", color="white",
                    fontweight="bold", zorder=6,
                )

    timestamp = 0.0
    if not frame_data.empty:
        timestamp = frame_data.iloc[0]["timestamp"]

    ax.legend(loc="upper right", fontsize=10)
    ax.set_title(f"Formation — Frame {frame_id} ({timestamp:.1f}s)",
                 fontsize=14, color="white", pad=10)

    fig.patch.set_facecolor("#1a1a2e")
    fig.tight_layout()

    return fig


# ---------------------------------------------------------------------------
# Pressing intensity
# ---------------------------------------------------------------------------

def compute_pressing_intensity(
    player_df: pd.DataFrame,
    ball_df: pd.DataFrame,
    team: str = "home",
    config_path: str = "config.yaml",
) -> pd.DataFrame:
    """
    Compute pressing intensity over time.

    Pressing is defined as the number of players within a configurable
    distance threshold of the ball at each frame.

    Returns a DataFrame with columns:
        - frame_id (int)
        - timestamp (float)
        - pressing_count (int): number of team players within threshold of ball
        - min_distance (float): closest player distance to ball
        - avg_distance (float): average distance of pressing players to ball
    """
    config = load_config(config_path)
    tactics_cfg = config.get("tactics", {})
    threshold = tactics_cfg.get("pressing_distance_threshold", 10.0)

    # Only frames where ball is detected
    ball_detected = ball_df[ball_df["detected"]].dropna(subset=["pitch_x", "pitch_y"])
    team_players = player_df[player_df["team"] == team].dropna(
        subset=["pitch_x", "pitch_y"]
    )

    rows = []
    for _, ball_row in ball_detected.iterrows():
        fid = ball_row["frame_id"]
        bx, by = ball_row["pitch_x"], ball_row["pitch_y"]

        frame_players = team_players[team_players["frame_id"] == fid]
        if frame_players.empty:
            rows.append({
                "frame_id": fid,
                "timestamp": ball_row["timestamp"],
                "pressing_count": 0,
                "min_distance": None,
                "avg_distance": None,
            })
            continue

        distances = np.sqrt(
            (frame_players["pitch_x"].values - bx) ** 2 +
            (frame_players["pitch_y"].values - by) ** 2
        )

        pressing_mask = distances <= threshold
        pressing_distances = distances[pressing_mask]

        rows.append({
            "frame_id": fid,
            "timestamp": ball_row["timestamp"],
            "pressing_count": int(pressing_mask.sum()),
            "min_distance": float(distances.min()),
            "avg_distance": float(pressing_distances.mean()) if len(pressing_distances) > 0 else None,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=[
            "frame_id", "timestamp", "pressing_count", "min_distance", "avg_distance",
        ])

    return df.sort_values("frame_id").reset_index(drop=True)


def plot_pressing_chart(
    pressing_df: pd.DataFrame,
    config_path: str = "config.yaml",
) -> plt.Figure:
    """Plot pressing intensity over time as a line chart."""
    config = load_config(config_path)
    team_cfg = config.get("team", {})
    output_cfg = config.get("output", {})

    fig, ax = plt.subplots(figsize=(14, 5))

    if pressing_df.empty:
        ax.set_title("No pressing data available")
        return fig

    ax.fill_between(
        pressing_df["timestamp"],
        pressing_df["pressing_count"],
        alpha=0.3,
        color="maroon",
    )
    ax.plot(
        pressing_df["timestamp"],
        pressing_df["pressing_count"],
        color="maroon",
        linewidth=1.5,
    )

    ax.set_xlabel("Time (seconds)", fontsize=12)
    ax.set_ylabel("Players pressing", fontsize=12)
    ax.set_title(
        f"Pressing Intensity — {team_cfg.get('home_label', 'Home')}",
        fontsize=14,
    )
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Average team shape by game phase
# ---------------------------------------------------------------------------

def compute_average_shape(
    player_df: pd.DataFrame,
    team: str = "home",
    phase: str | None = None,
) -> dict:
    """
    Compute average positions for each tracked player.

    Args:
        player_df: Full player tracking DataFrame.
        team: Which team to analyze.
        phase: Optional game phase filter (not yet implemented —
               requires event detection or manual annotation).

    Returns:
        dict mapping track_id -> {"avg_x": float, "avg_y": float, "samples": int}
    """
    df = player_df[player_df["team"] == team].dropna(subset=["pitch_x", "pitch_y"])

    # TODO: Filter by game phase once event detection is implemented.
    # Phase detection could use:
    # - Ball position (attacking third, middle third, defensive third)
    # - Team centroid movement direction
    # - Manual timestamp annotations

    result = {}
    for track_id, group in df.groupby("track_id"):
        result[int(track_id)] = {
            "avg_x": float(group["pitch_x"].mean()),
            "avg_y": float(group["pitch_y"].mean()),
            "samples": len(group),
        }

    return result


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def save_report(
    player_df: pd.DataFrame,
    ball_df: pd.DataFrame,
    video_metadata: dict,
    config_path: str = "config.yaml",
) -> str:
    """
    Generate and save a full tactical report.

    Creates:
        - Team heatmaps (home and away)
        - Formation snapshots at evenly spaced intervals
        - Pressing intensity chart
        - CSV exports of raw data

    Returns:
        Path to the report output directory.
    """
    config = load_config(config_path)
    output_cfg = config.get("output", {})
    tactics_cfg = config.get("tactics", {})
    dpi = output_cfg.get("figure_dpi", 150)
    save_csv = output_cfg.get("save_csv", True)

    # Create report directory named after the video
    video_name = Path(video_metadata.get("path", "unknown")).stem
    report_dir = os.path.join(output_cfg.get("report_dir", "output/reports"), video_name)
    os.makedirs(report_dir, exist_ok=True)

    # Heatmaps
    for team in ["home", "away"]:
        fig = generate_player_heatmap(player_df, team=team, config_path=config_path)
        fig.savefig(
            os.path.join(report_dir, f"heatmap_{team}.png"),
            dpi=dpi, bbox_inches="tight",
        )
        plt.close(fig)

    # Formation snapshots — evenly spaced through the video
    total_frames = player_df["frame_id"].nunique()
    if total_frames > 0:
        snapshot_count = min(6, total_frames)
        snapshot_frames = np.linspace(
            player_df["frame_id"].min(),
            player_df["frame_id"].max(),
            snapshot_count,
            dtype=int,
        )
        for i, fid in enumerate(snapshot_frames):
            fig = plot_formation(player_df, int(fid), config_path=config_path)
            fig.savefig(
                os.path.join(report_dir, f"formation_{i:02d}_frame{fid}.png"),
                dpi=dpi, bbox_inches="tight",
            )
            plt.close(fig)

    # Pressing chart
    pressing_df = compute_pressing_intensity(
        player_df, ball_df, team="home", config_path=config_path
    )
    fig = plot_pressing_chart(pressing_df, config_path=config_path)
    fig.savefig(
        os.path.join(report_dir, "pressing_intensity.png"),
        dpi=dpi, bbox_inches="tight",
    )
    plt.close(fig)

    # CSV exports
    if save_csv:
        player_df.to_csv(os.path.join(report_dir, "player_tracks.csv"), index=False)
        ball_df.to_csv(os.path.join(report_dir, "ball_positions.csv"), index=False)
        pressing_df.to_csv(os.path.join(report_dir, "pressing_intensity.csv"), index=False)

    return report_dir
