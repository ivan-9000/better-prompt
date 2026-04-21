"""
Better Prompt — Plotly chart helpers.
Reusable interactive charts for the Evaluation Suite.
"""
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go


# ── Bar chart ─────────────────────────────────────────────────────────────────
def bar_chart_scores(
    variants: dict[str, float],
    title: str = "Metric Scores",
) -> go.Figure:
    """
    Horizontal bar chart comparing scores across prompt variants or metrics.

    Bars are colour-coded:
        Green  — score >= 0.7  (good)
        Orange — score >= 0.4  (moderate)
        Red    — score <  0.4  (poor)

    Args:
        variants: Dict mapping label → score (0.0 to 1.0).
        title:    Chart title.

    Returns:
        Plotly Figure object ready for st.plotly_chart().
    """
    if not variants:
        return go.Figure()

    names  = list(variants.keys())
    scores = list(variants.values())

    colors = [
        "rgba(50, 200, 100, 0.85)"  if s >= 0.7
        else "rgba(255, 165, 0, 0.85)" if s >= 0.4
        else "rgba(220, 50,  50, 0.85)"
        for s in scores
    ]

    fig = go.Figure(
        go.Bar(
            x=scores,
            y=names,
            orientation="h",
            marker_color=colors,
            text=[f"{s:.3f}" for s in scores],
            textposition="outside",
        )
    )

    fig.update_layout(
        title=title,
        xaxis=dict(range=[0, 1.15], title="Score"),
        yaxis=dict(title=""),
        template="plotly_white",
        height=max(250, len(names) * 55),
        margin=dict(l=20, r=40, t=50, b=20),
    )

    return fig


# ── Radar chart ───────────────────────────────────────────────────────────────
def radar_chart(
    metrics: dict[str, float],
    title: str = "Multi-Metric Overview",
) -> go.Figure:
    """
    Radar (spider) chart showing multiple metric scores simultaneously.

    Best for visualising balance across criteria
    (e.g. relevance, coherence, factuality, safety).

    Args:
        metrics: Dict mapping metric name → score (0.0 to 1.0).
        title:   Chart title.

    Returns:
        Plotly Figure object.
    """
    if not metrics:
        return go.Figure()

    categories = list(metrics.keys())
    values     = list(metrics.values())

    # Close the polygon by repeating the first value
    categories_closed = categories + [categories[0]]
    values_closed     = values     + [values[0]]

    fig = go.Figure(
        go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill="toself",
            fillcolor="rgba(99, 110, 250, 0.2)",
            line=dict(color="rgba(99, 110, 250, 1.0)", width=2),
            marker=dict(size=6),
        )
    )

    fig.update_layout(
        title=title,
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickformat=".1f",
            )
        ),
        template="plotly_white",
        height=400,
        margin=dict(l=40, r=40, t=60, b=40),
    )

    return fig


# ── Line chart ────────────────────────────────────────────────────────────────
def line_chart_optimization(
    scores: list[float],
    title: str = "Optimization Progress",
    labels: list[str] | None = None,
) -> go.Figure:
    """
    Line chart showing how scores improve across optimization iterations.

    Highlights the best-performing iteration with a gold star marker.

    Args:
        scores: List of scores in iteration order.
        title:  Chart title.
        labels: Optional list of iteration labels (e.g. version names).

    Returns:
        Plotly Figure object.
    """
    if not scores:
        return go.Figure()

    x_axis = labels if labels else list(range(1, len(scores) + 1))
    best_i = scores.index(max(scores))

    fig = go.Figure()

    # Main line
    fig.add_trace(
        go.Scatter(
            x=x_axis,
            y=scores,
            mode="lines+markers",
            name="Score",
            line=dict(color="rgba(99, 110, 250, 1.0)", width=2),
            marker=dict(size=8),
        )
    )

    # Best point highlight
    fig.add_trace(
        go.Scatter(
            x=[x_axis[best_i]],
            y=[scores[best_i]],
            mode="markers",
            name=f"Best ({scores[best_i]:.3f})",
            marker=dict(
                size=16,
                color="gold",
                symbol="star",
                line=dict(color="orange", width=1),
            ),
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="Iteration",
        yaxis_title="Score",
        yaxis=dict(range=[0, 1.1]),
        template="plotly_white",
        height=350,
        margin=dict(l=20, r=20, t=50, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    return fig


# ── Scatter chart ─────────────────────────────────────────────────────────────
def cost_quality_scatter(
    runs: list[dict],
    title: str = "Cost vs Quality",
) -> go.Figure:
    """
    Scatter plot comparing cost (USD) vs quality score across model runs.

    Each point represents one model run. Colour-coded by model name.
    Ideal for deciding whether a more expensive model is worth it.

    Args:
        runs:  List of dicts, each with keys:
               cost_usd (float), quality_score (float), model (str).
        title: Chart title.

    Returns:
        Plotly Figure object.
    """
    if not runs:
        return go.Figure()

    fig = px.scatter(
        runs,
        x="cost_usd",
        y="quality_score",
        color="model",
        hover_data=["model", "cost_usd", "quality_score"],
        title=title,
        template="plotly_white",
        labels={
            "cost_usd":      "Cost (USD)",
            "quality_score": "Quality Score",
        },
    )

    fig.update_traces(marker=dict(size=12, opacity=0.8))
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=50, b=40),
        yaxis=dict(range=[0, 1.1]),
    )

    return fig
