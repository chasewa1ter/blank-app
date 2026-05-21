"""Defensive route efficiency: metrics + mock generator + plot.

The CV pipeline (player detection + tracking + ball landing) is not implemented yet.
This module exposes pure-function metrics that take a path in field coordinates,
plus a mock generator the Streamlit UI uses until real tracking is wired in.
"""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from . import geometry

FT_PER_S_TO_MPH = 0.681818


def route_efficiency_pct(path_ft: np.ndarray, optimal_distance_ft: float) -> float:
    """Optimal straight-line distance / actual path length, as a percentage."""
    if len(path_ft) < 2:
        return 0.0
    actual = np.linalg.norm(np.diff(path_ft, axis=0), axis=1).sum()
    if actual == 0:
        return 100.0
    return 100.0 * optimal_distance_ft / actual


def max_speed_mph(path_ft: np.ndarray, fps: float) -> float:
    """Peak frame-to-frame speed (3-frame smoothed) converted to mph."""
    if len(path_ft) < 2:
        return 0.0
    step_ft = np.linalg.norm(np.diff(path_ft, axis=0), axis=1)
    speed_fps = step_ft * fps
    if len(speed_fps) >= 3:
        speed_fps = np.convolve(speed_fps, np.ones(3) / 3, mode="valid")
    return float(speed_fps.max() * FT_PER_S_TO_MPH)


_STARTS_FT = {
    "CF": (0.0, 290.0),
    "LF": (-190.0, 230.0),
    "RF": (190.0, 230.0),
    "SS": (-35.0, 145.0),
    "2B": (35.0, 145.0),
    "3B": (-78.0, 100.0),
}


def mock_route_result(fielder_pos: str, fps: float = 30.0) -> dict:
    """Plausible-looking route for the demo: slight bow off the optimal line."""
    start = np.array(_STARTS_FT.get(fielder_pos, _STARTS_FT["CF"]), dtype=float)
    landing = start + np.array([55.0, -45.0])

    t = np.linspace(0.0, 1.0, 90)
    leg = landing - start
    perp = np.array([-leg[1], leg[0]])
    perp = perp / np.linalg.norm(perp)
    bow_ft = 14.0 * np.sin(np.pi * t)
    actual = start + leg * t[:, None] + perp * bow_ft[:, None]

    optimal = float(np.linalg.norm(leg))
    return {
        "fielder_pos": fielder_pos,
        "start_ft": start.tolist(),
        "landing_ft": landing.tolist(),
        "actual_path_ft": actual.tolist(),
        "optimal_distance_ft": optimal,
        "route_eff_pct": route_efficiency_pct(actual, optimal),
        "time_to_ball_s": len(actual) / fps,
        "max_speed_mph": max_speed_mph(actual, fps),
        "first_step_jump_s": 0.42,
        "fps": fps,
        "is_mock": True,
    }


def plot_route(result: dict) -> go.Figure:
    actual = np.array(result["actual_path_ft"])
    start = np.array(result["start_ft"])
    landing = np.array(result["landing_ft"])

    fig = go.Figure()

    diamond = np.vstack([geometry.BASES_FT, geometry.BASES_FT[0:1]])
    fig.add_trace(
        go.Scatter(
            x=diamond[:, 0], y=diamond[:, 1],
            mode="lines+markers",
            line=dict(color="#888", width=1),
            marker=dict(size=9, color="#bbb"),
            name="Bases",
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[start[0], landing[0]], y=[start[1], landing[1]],
            mode="lines",
            line=dict(color="#2ca02c", dash="dash", width=2),
            name=f"Optimal ({result['optimal_distance_ft']:.1f} ft)",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=actual[:, 0], y=actual[:, 1],
            mode="lines+markers",
            line=dict(color="#d62728", width=2),
            marker=dict(size=4),
            name="Actual route",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[start[0]], y=[start[1]],
            mode="markers+text",
            marker=dict(size=14, color="#1f77b4"),
            text=[f"Start ({result['fielder_pos']})"],
            textposition="top center",
            name="Fielder start",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[landing[0]], y=[landing[1]],
            mode="markers+text",
            marker=dict(size=14, color="#ff7f0e", symbol="x"),
            text=["Ball landing"],
            textposition="top center",
            name="Ball",
        )
    )

    fig.update_layout(
        title="Route to ball (field coordinates, feet)",
        xaxis_title="X (ft, +1B side)",
        yaxis_title="Y (ft, toward CF)",
        height=620,
        showlegend=True,
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font=dict(color="#eee"),
    )
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    return fig
