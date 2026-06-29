"""Encoding-driven visualization renderers for Streamlit."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network


def render_visualization(viz: dict[str, Any]) -> None:
    """Render a visualization dict from the backend response."""
    viz_type = viz.get("type")
    match viz_type:
        case "bar_chart":
            _render_bar_chart(viz)
        case "grouped_bar_chart":
            _render_grouped_bar_chart(viz)
        case "time_series":
            _render_time_series(viz)
        case "histogram":
            _render_histogram(viz)
        case "network_graph":
            _render_network_graph(viz)
        case "scatter_plot":
            st.info(
                "Unsupported visualization type: scatter_plot is not assigned "
                "to any horizon."
            )
        case _:
            st.warning(f"Unknown visualization type: {viz_type!r}")


def tabular_row_count(viz: dict[str, Any]) -> int:
    data = viz.get("data")
    if isinstance(data, list):
        return len(data)
    return 0


def network_counts(viz: dict[str, Any]) -> tuple[int, int]:
    data = viz.get("data") or {}
    nodes = data.get("nodes") or []
    edges = data.get("edges") or []
    return len(nodes), len(edges)


def _chart_rows(viz: dict[str, Any]) -> pd.DataFrame:
    rows = viz.get("data") or []
    if not isinstance(rows, list):
        return pd.DataFrame()
    cleaned = [{k: v for k, v in row.items() if k != "citations"} for row in rows]
    return pd.DataFrame(cleaned)


def _render_bar_chart(viz: dict[str, Any]) -> None:
    encoding = viz["encoding"]
    df = _chart_rows(viz)
    if df.empty:
        st.info("No chart data to display.")
        return

    x_col = encoding["x"]
    y_col = encoding["y"]
    df = df.sort_values(y_col, ascending=False)

    if len(df) > 15:
        fig = px.bar(
            df,
            x=y_col,
            y=x_col,
            orientation="h",
            labels={x_col: x_col, y_col: y_col},
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
    else:
        fig = px.bar(
            df,
            x=x_col,
            y=y_col,
            labels={x_col: x_col, y_col: y_col},
        )

    fig.update_layout(margin={"l": 20, "r": 20, "t": 30, "b": 20})
    st.plotly_chart(fig, width="stretch")


def _render_grouped_bar_chart(viz: dict[str, Any]) -> None:
    encoding = viz["encoding"]
    df = _chart_rows(viz)
    if df.empty:
        st.info("No chart data to display.")
        return

    fig = px.bar(
        df,
        x=encoding["x"],
        y=encoding["y"],
        color=encoding["series"],
        barmode="group",
        labels={
            encoding["x"]: encoding["x"],
            encoding["y"]: encoding["y"],
            encoding["series"]: encoding["series"],
        },
    )
    fig.update_layout(margin={"l": 20, "r": 20, "t": 30, "b": 20})
    st.plotly_chart(fig, width="stretch")


def _render_time_series(viz: dict[str, Any]) -> None:
    encoding = viz["encoding"]
    df = _chart_rows(viz)
    if df.empty:
        st.info("No chart data to display.")
        return

    series_col = encoding.get("series")
    if series_col and series_col in df.columns:
        fig = px.line(
            df,
            x=encoding["x"],
            y=encoding["y"],
            color=series_col,
            markers=True,
            labels={
                encoding["x"]: encoding["x"],
                encoding["y"]: encoding["y"],
                series_col: series_col,
            },
        )
    else:
        fig = px.line(
            df,
            x=encoding["x"],
            y=encoding["y"],
            markers=True,
            labels={encoding["x"]: encoding["x"], encoding["y"]: encoding["y"]},
        )

    fig.update_layout(margin={"l": 20, "r": 20, "t": 30, "b": 20})
    st.plotly_chart(fig, width="stretch")


def _render_histogram(viz: dict[str, Any]) -> None:
    encoding = viz["encoding"]
    df = _chart_rows(viz)
    if df.empty:
        st.info("No chart data to display.")
        return

    fig = px.bar(
        df,
        x=encoding["x"],
        y=encoding["y"],
        labels={encoding["x"]: encoding["x"], encoding["y"]: encoding["y"]},
    )
    fig.update_layout(margin={"l": 20, "r": 20, "t": 30, "b": 20})
    st.plotly_chart(fig, width="stretch")


def _render_network_graph(viz: dict[str, Any]) -> None:
    data = viz.get("data") or {}
    nodes = data.get("nodes") or []
    edges = data.get("edges") or []

    if not nodes:
        st.info("No network nodes to display.")
        return

    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="#333333")
    net.toggle_physics(True)

    for node in nodes:
        label = node.get("label") or node["id"]
        net.add_node(node["id"], label=label, title=label)

    for edge in edges:
        title = edge.get("label") or ""
        net.add_edge(edge["source"], edge["target"], title=title, label=title)

    html = net.generate_html(notebook=False)
    components.html(html, height=650, scrolling=True)
