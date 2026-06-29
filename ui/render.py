"""Encoding-driven visualization renderers for Streamlit."""

from __future__ import annotations

import json
from typing import Any, Literal

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

NetworkNodeRole = Literal["sponsor", "drug", "condition", "unknown"]

_NETWORK_ROLE_COLORS: dict[NetworkNodeRole, str] = {
    "sponsor": "#2563eb",
    "drug": "#16a34a",
    "condition": "#dc2626",
    "unknown": "#94a3b8",
}

_NETWORK_LEGEND_ITEMS: tuple[tuple[str, NetworkNodeRole], ...] = (
    ("Sponsor", "sponsor"),
    ("Drug", "drug"),
    ("Condition", "condition"),
    ("Other", "unknown"),
)


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


def _network_node_degrees(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> dict[str, int]:
    degrees = {node["id"]: 0 for node in nodes}
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if source in degrees:
            degrees[source] += 1
        if target in degrees:
            degrees[target] += 1
    return degrees


def _infer_network_node_roles(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> dict[str, NetworkNodeRole]:
    roles: dict[str, NetworkNodeRole] = {node["id"]: "unknown" for node in nodes}

    def set_role(node_id: str, role: NetworkNodeRole) -> None:
        if node_id not in roles:
            return
        current = roles[node_id]
        if current == "unknown" or role != "unknown":
            roles[node_id] = role

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if not source or not target:
            continue
        match edge.get("label"):
            case "sponsored_by":
                set_role(source, "sponsor")
                set_role(target, "drug")
            case "studied_in":
                set_role(source, "drug")
                set_role(target, "condition")
            case "co_intervention":
                set_role(source, "drug")
                set_role(target, "drug")
            case _:
                continue

    return roles


def _network_node_size(degree: int) -> int:
    return min(40, 12 + degree * 3)


def _network_graph_options() -> str:
    return json.dumps(
        {
            "physics": {
                "enabled": True,
                "barnesHut": {
                    "gravitationalConstant": -8000,
                    "springLength": 180,
                    "springConstant": 0.04,
                    "avoidOverlap": 1,
                },
                "stabilization": {
                    "enabled": True,
                    "iterations": 250,
                    "fit": True,
                },
            },
            "edges": {
                "smooth": {"type": "continuous"},
                "color": {"color": "#94a3b8", "opacity": 0.6},
                "width": 1,
                "font": {"size": 0},
            },
            "nodes": {
                "font": {"size": 0},
                "borderWidth": 2,
                "borderWidthSelected": 3,
            },
            "interaction": {
                "hover": True,
                "tooltipDelay": 100,
            },
        }
    )


def _render_network_legend() -> None:
    legend_cols = st.columns(len(_NETWORK_LEGEND_ITEMS))
    for column, (label, role) in zip(legend_cols, _NETWORK_LEGEND_ITEMS, strict=True):
        color = _NETWORK_ROLE_COLORS[role]
        column.markdown(
            f'<span style="color:{color}; font-size:1.2em;">●</span> {label}',
            unsafe_allow_html=True,
        )
    st.caption("Hover nodes and edges for names and relationship types.")


def _render_network_graph(viz: dict[str, Any]) -> None:
    data = viz.get("data") or {}
    nodes = data.get("nodes") or []
    edges = data.get("edges") or []

    if not nodes:
        st.info("No network nodes to display.")
        return

    roles = _infer_network_node_roles(nodes, edges)
    degrees = _network_node_degrees(nodes, edges)

    _render_network_legend()

    net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="#333333")
    net.set_options(_network_graph_options())

    for node in nodes:
        node_id = node["id"]
        label = node.get("label") or node_id
        role = roles.get(node_id, "unknown")
        fill = _NETWORK_ROLE_COLORS[role]
        net.add_node(
            node_id,
            label=label,
            title=label,
            color={
                "background": fill,
                "border": "#ffffff",
                "highlight": {"background": fill, "border": "#ffffff"},
            },
            size=_network_node_size(degrees.get(node_id, 0)),
            borderWidth=2,
            borderWidthSelected=3,
            shape="dot",
        )

    for edge in edges:
        relationship = edge.get("label") or ""
        net.add_edge(
            edge["source"],
            edge["target"],
            title=relationship,
            label="",
            color={"color": "#94a3b8", "opacity": 0.6},
            width=1,
            smooth={"type": "continuous"},
        )

    html = net.generate_html(notebook=False)
    components.html(html, height=800, scrolling=True)
