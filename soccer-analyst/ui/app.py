"""
Streamlit UI for Soccer Analyst.

Run with: streamlit run ui/app.py
"""

import os
import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import yaml

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.ingest import validate_video
from pipeline.tracker import run_tracking
from pipeline.parser import (
    load_minimap_json,
    parse_player_tracks,
    parse_ball_positions,
)
from pipeline.tactics import (
    generate_player_heatmap,
    plot_formation,
    compute_pressing_intensity,
    plot_pressing_chart,
    compute_formation_shape,
    compute_average_shape,
    save_report,
)


def load_config():
    config_path = Path(__file__).resolve().parent.parent / "config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main():
    st.set_page_config(
        page_title="Soccer Analyst",
        page_icon="",
        layout="wide",
    )

    st.title("Soccer Tactical Analyst")
    st.caption("Analyze game footage for formations, pressing, and positioning")

    config = load_config()
    config_path = str(Path(__file__).resolve().parent.parent / "config.yaml")

    # ---- Sidebar: Video Selection ----
    st.sidebar.header("Video Input")

    video_dir = Path(__file__).resolve().parent.parent / "data" / "videos"
    mp4_files = sorted(video_dir.glob("*.mp4"))

    input_method = st.sidebar.radio("Input method", ["Select existing", "Upload"])

    video_path = None

    if input_method == "Select existing":
        if mp4_files:
            selected = st.sidebar.selectbox(
                "Choose a video",
                mp4_files,
                format_func=lambda p: p.name,
            )
            video_path = str(selected)
        else:
            st.sidebar.info("No MP4 files found in data/videos/. Upload one or drop files there.")
    else:
        uploaded = st.sidebar.file_uploader("Upload MP4", type=["mp4"])
        if uploaded:
            save_path = video_dir / uploaded.name
            with open(save_path, "wb") as f:
                f.write(uploaded.getbuffer())
            video_path = str(save_path)
            st.sidebar.success(f"Saved to {save_path.name}")

    # ---- Sidebar: Config Display ----
    with st.sidebar.expander("Configuration"):
        st.json(config)

    # ---- Main Area ----
    if video_path is None:
        st.info("Select or upload a video to get started.")
        return

    # Video metadata
    try:
        metadata = validate_video(video_path)
    except Exception as e:
        st.error(f"Invalid video: {e}")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Duration", f"{metadata['duration']:.0f}s")
    col2.metric("Resolution", f"{metadata['width']}x{metadata['height']}")
    col3.metric("FPS", f"{metadata['fps']}")
    col4.metric("Codec", metadata["codec"])

    # ---- Pipeline Execution ----
    st.divider()

    total_frames = int(metadata["duration"] * metadata["fps"])
    st.caption(f"Video has ~{total_frames:,} total frames")

    if st.button("Run Analysis Pipeline", type="primary"):
        with st.status("Running SoccerNet GSR tracking pipeline...", expanded=True) as status:
            # Stream tracklab output into the status expander
            log_container = st.empty()
            log_lines = []

            def on_progress(line):
                log_lines.append(line)
                # Show last 15 lines of output
                log_container.code("\n".join(log_lines[-15:]), language=None)

            try:
                tracking_result = run_tracking(
                    video_path,
                    config_path=config_path,
                    progress_callback=on_progress,
                )
                stats = tracking_result["tracking_stats"]
                st.write(
                    f"Tracked {stats['total_detections']} detections "
                    f"across {stats['total_frames']} frames "
                    f"({stats['avg_players_per_frame']} avg players/frame)"
                )
            except FileNotFoundError as e:
                st.error(str(e))
                return
            except RuntimeError as e:
                st.error(f"Tracking failed: {e}")
                return

            # Step 2: Parse and analyze
            status.update(label="Generating tactical report...")
            try:
                minimap_data = load_minimap_json(tracking_result["minimap_json_path"])
                _display_report(minimap_data, metadata, config_path)
            except Exception as e:
                st.error(f"Report generation failed: {e}")
                return

            status.update(label="Analysis complete!", state="complete")

    # ---- Load Existing Report ----
    st.divider()
    st.subheader("Or: Load Existing Data")

    json_path = st.text_input(
        "Path to minimap JSON file",
        placeholder="output/reports/game1/minimap.json",
    )
    if json_path and st.button("Load JSON"):
        try:
            minimap_data = load_minimap_json(json_path)
            _display_report(minimap_data, metadata, config_path)
        except Exception as e:
            st.error(f"Failed to load JSON: {e}")


def _display_report(minimap_data: list[dict], metadata: dict, config_path: str):
    """Parse tracking data and display all report tabs."""
    player_df = parse_player_tracks(minimap_data)
    ball_df = parse_ball_positions(minimap_data)

    if player_df.empty:
        st.warning("No player tracking data found in the JSON.")
        return

    tab_heatmap, tab_formation, tab_pressing, tab_data = st.tabs([
        "Heatmaps", "Formation", "Pressing", "Raw Data",
    ])

    config = load_config()
    team_cfg = config.get("team", {})

    # ---- Heatmaps Tab ----
    with tab_heatmap:
        st.subheader("Player Heatmaps")

        heatmap_team = st.selectbox(
            "Team",
            ["home", "away"],
            format_func=lambda t: team_cfg.get(f"{t}_label", t.capitalize()),
        )

        team_data = player_df[player_df["team"] == heatmap_team]
        track_ids = sorted(team_data["track_id"].unique())

        # Build display labels with jersey numbers where available
        jersey_map = {}
        if "jersey_number" in team_data.columns:
            for tid in track_ids:
                jn = team_data[team_data["track_id"] == tid]["jersey_number"].dropna().mode()
                if not jn.empty:
                    jersey_map[tid] = str(jn.iloc[0])

        def _format_player(x):
            if x is None:
                return "All Players"
            jn = jersey_map.get(x)
            return f"#{jn} (Track {int(x)})" if jn else f"Track {int(x)}"

        selected_player = st.selectbox(
            "Player (or All)",
            [None] + list(track_ids),
            format_func=_format_player,
        )

        fig = generate_player_heatmap(
            player_df,
            track_id=selected_player,
            team=heatmap_team if selected_player is None else None,
            config_path=config_path,
        )
        st.pyplot(fig)

    # ---- Formation Tab ----
    with tab_formation:
        st.subheader("Formation Snapshots")

        frame_ids = sorted(player_df["frame_id"].unique())
        selected_frame = st.slider(
            "Frame",
            min_value=int(frame_ids[0]),
            max_value=int(frame_ids[-1]),
            value=int(frame_ids[0]),
        )

        fig = plot_formation(player_df, selected_frame, config_path=config_path)
        st.pyplot(fig)

        # Shape metrics
        col1, col2 = st.columns(2)
        for team, col in [("home", col1), ("away", col2)]:
            shape = compute_formation_shape(player_df, selected_frame, team)
            label = team_cfg.get(f"{team}_label", team.capitalize())
            with col:
                st.markdown(f"**{label} Shape**")
                if shape["centroid"]:
                    st.write(f"Compactness (avg spread): {shape['spread']:.1f}m")
                    st.write(f"Width: {shape['width']:.1f}m")
                    st.write(f"Depth: {shape['depth']:.1f}m")
                else:
                    st.write("No data for this frame")

    # ---- Pressing Tab ----
    with tab_pressing:
        st.subheader("Pressing Intensity")
        pressing_df = compute_pressing_intensity(
            player_df, ball_df, team="home", config_path=config_path
        )

        if pressing_df.empty:
            st.warning("No pressing data — ball positions may be missing.")
        else:
            fig = plot_pressing_chart(pressing_df, config_path=config_path)
            st.pyplot(fig)

            col1, col2, col3 = st.columns(3)
            col1.metric("Avg Players Pressing", f"{pressing_df['pressing_count'].mean():.1f}")
            col2.metric("Max Players Pressing", f"{pressing_df['pressing_count'].max()}")
            col3.metric(
                "Avg Closest Distance",
                f"{pressing_df['min_distance'].mean():.1f}m"
                if pressing_df['min_distance'].notna().any() else "N/A",
            )

    # ---- Raw Data Tab ----
    with tab_data:
        st.subheader("Player Tracking Data")
        st.dataframe(player_df, use_container_width=True)

        st.subheader("Ball Positions")
        st.dataframe(ball_df, use_container_width=True)

        # Save report button
        if st.button("Save Full Report to Disk"):
            report_dir = save_report(
                player_df, ball_df, metadata, config_path=config_path
            )
            st.success(f"Report saved to: {report_dir}")


if __name__ == "__main__":
    main()
