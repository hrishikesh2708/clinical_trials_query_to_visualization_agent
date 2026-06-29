"""Streamlit demo UI for the ClinicalTrials visualize endpoint."""

from __future__ import annotations

from typing import Any

import streamlit as st
from client import BackendError, check_health, default_backend_url, fetch_visualization
from render import network_counts, render_visualization, tabular_row_count
from samples import (
    FILTER_FIELDS,
    sample_by_label,
    sample_select_options,
)

st.set_page_config(
    page_title="ClinicalTrials Visualize Demo",
    page_icon="📊",
    layout="wide",
)

NCT_STUDY_URL = "https://clinicaltrials.gov/study/{nct_id}"


def _init_session_state() -> None:
    if "backend_url" not in st.session_state:
        st.session_state.backend_url = default_backend_url()
    if "last_response" not in st.session_state:
        st.session_state.last_response = None
    if "last_error" not in st.session_state:
        st.session_state.last_error = None


def _build_request_body(
    query: str,
    filters: dict[str, str | int | None],
) -> dict[str, Any]:
    body: dict[str, Any] = {"query": query.strip()}
    for field in FILTER_FIELDS:
        value = filters.get(field)
        if field in ("start_year", "end_year"):
            if isinstance(value, str):
                value = _parse_optional_int(value, field)
            if value is None:
                continue
        if value is not None and value != "":
            body[field] = value
    start = body.get("start_year")
    end = body.get("end_year")
    if start is not None and end is not None and start > end:
        raise ValueError("start_year must be less than or equal to end_year")
    return body


def _apply_sample_to_filters(
    sample_request: dict[str, str | int | None],
) -> dict[str, str | int | None]:
    return {field: sample_request.get(field) for field in FILTER_FIELDS}


def _render_citations_tabular(viz: dict[str, Any]) -> None:
    encoding = viz.get("encoding") or {}
    x_col = encoding.get("x")
    rows = viz.get("data") or []

    for row in rows:
        if not row.get("citations"):
            continue
        label_parts = []
        if x_col and x_col in row:
            label_parts.append(str(row[x_col]))
        if "series" in encoding and encoding["series"] in row:
            label_parts.append(str(row[encoding["series"]]))
        label = " — ".join(label_parts) if label_parts else "Datum"

        with st.expander(label):
            for citation in row["citations"]:
                nct_id = citation["nct_id"]
                url = NCT_STUDY_URL.format(nct_id=nct_id)
                st.markdown(f"**[{nct_id}]({url})** — {citation['excerpt']}")


def _render_citations_network(viz: dict[str, Any]) -> None:
    data = viz.get("data") or {}
    nodes = data.get("nodes") or []
    edges = data.get("edges") or []

    tab_nodes, tab_edges = st.tabs(["Nodes", "Edges"])

    with tab_nodes:
        for node in nodes:
            if not node.get("citations"):
                continue
            label = node.get("label") or node["id"]
            with st.expander(label):
                for citation in node["citations"]:
                    nct_id = citation["nct_id"]
                    url = NCT_STUDY_URL.format(nct_id=nct_id)
                    st.markdown(f"**[{nct_id}]({url})** — {citation['excerpt']}")

    with tab_edges:
        for edge in edges:
            if not edge.get("citations"):
                continue
            edge_label = (
                f"{edge['source']} → {edge['target']}"
                + (f" ({edge['label']})" if edge.get("label") else "")
            )
            with st.expander(edge_label):
                for citation in edge["citations"]:
                    nct_id = citation["nct_id"]
                    url = NCT_STUDY_URL.format(nct_id=nct_id)
                    st.markdown(f"**[{nct_id}]({url})** — {citation['excerpt']}")


def _render_citations(viz: dict[str, Any]) -> None:
    viz_type = viz.get("type")
    if viz_type == "network_graph":
        _render_citations_network(viz)
    else:
        _render_citations_tabular(viz)


def _render_metadata(meta: dict[str, Any]) -> None:
    filters = meta.get("filters") or {}
    applied = {k: v for k, v in filters.items() if v is not None}
    if applied:
        st.markdown("**Applied filters**")
        for key, value in applied.items():
            st.markdown(f"- `{key}`: {value}")

    assumptions = meta.get("assumptions") or []
    if assumptions:
        st.markdown("**Assumptions**")
        for item in assumptions:
            st.markdown(f"- {item}")

    notes = meta.get("interpretation_notes")
    if notes:
        st.markdown("**Interpretation notes**")
        st.markdown(notes)


def _parse_optional_int(raw: str, field: str) -> int | None:
    text = raw.strip()
    if not text:
        return None
    try:
        value = int(text)
    except ValueError as exc:
        raise ValueError(f"{field} must be an integer") from exc
    if value < 1900 or value > 2100:
        raise ValueError(f"{field} must be between 1900 and 2100")
    return value


def _summary_metrics(viz: dict[str, Any], meta: dict[str, Any]) -> None:
    viz_type = viz.get("type", "unknown")
    total = meta.get("total_studies_fetched", "—")

    if viz_type == "network_graph":
        node_count, edge_count = network_counts(viz)
        c1, c2, c3 = st.columns(3)
        c1.metric("Nodes", node_count)
        c2.metric("Edges", edge_count)
        c3.metric("Studies fetched", total)
    else:
        c1, c2 = st.columns(2)
        c1.metric("Data rows", tabular_row_count(viz))
        c2.metric("Studies fetched", total)

    granularity = meta.get("time_granularity")
    if granularity:
        st.caption(f"Time granularity: {granularity}")


def _submit_query(
    query: str,
    filter_values: dict[str, str | int | None],
    healthy: bool,
    backend_url: str,
) -> None:
    if not query.strip():
        st.warning("Query is required.")
    elif not healthy:
        st.error("Backend is not reachable. Start the FastAPI server first.")
    else:
        try:
            body = _build_request_body(query, filter_values)
        except ValueError as exc:
            st.warning(str(exc))
        else:
            with st.spinner("Running visualize pipeline (may take up to 2 minutes)..."):
                try:
                    st.session_state.last_response = fetch_visualization(
                        body, backend_url
                    )
                    st.session_state.last_error = None
                except BackendError as exc:
                    st.session_state.last_response = None
                    st.session_state.last_error = exc


def main() -> None:
    _init_session_state()

    st.title("ClinicalTrials Query-to-Visualization")
    st.caption("Demo UI — displays backend response only; no direct API or LLM calls.")

    with st.sidebar:
        st.header("Backend")
        backend_url = st.text_input(
            "Backend URL",
            value=st.session_state.backend_url,
            help="FastAPI server base URL (session-only override).",
        )
        st.session_state.backend_url = backend_url.rstrip("/")

        healthy = check_health(st.session_state.backend_url)
        if healthy:
            st.success("Backend reachable")
        else:
            st.error(
                "Backend unreachable — start with: "
                "uv run uvicorn app.main:app --reload"
            )

        st.divider()
        st.header("Sample queries")

        sample_labels = sample_select_options()
        selected_label = st.selectbox(
            "Pick a sample",
            sample_labels,
            index=0,
            key="sample_select",
        )
        selected_sample = sample_by_label(selected_label)

        sample_filters: dict[str, str | int | None] = {}
        default_query = ""
        filter_values: dict[str, str | int | None] = {}
        if selected_sample:
            default_query = str(selected_sample.request.get("query", ""))
            sample_filters = _apply_sample_to_filters(selected_sample.request)

        with st.expander("Optional filters", expanded=False):
            for field in FILTER_FIELDS:
                default_val = sample_filters.get(field)
                raw = st.text_input(
                    field,
                    value=str(default_val) if default_val is not None else "",
                    key=f"filter_{field}",
                )
                filter_values[field] = raw.strip() or None

        run_clicked = st.button(
            "Visualize",
            type="primary",
            use_container_width=True,
            key="sidebar_visualize",
        )

    query = st.text_area(
        "Natural-language query",
        value=default_query,
        height=100,
        placeholder="e.g. How many breast cancer trials started each year?",
    )

    col_btn, _ = st.columns([1, 5])
    with col_btn:
        send_clicked = st.button(
            "Visualize",
            type="primary",
            use_container_width=True,
            key="main_visualize",
        )

    if run_clicked or send_clicked:
        _submit_query(
            query,
            filter_values,
            healthy,
            st.session_state.backend_url,
        )

    if st.session_state.last_error:
        err = st.session_state.last_error
        st.error(f"**{err.code}** — {err.message}")
        if err.status_code in (502, 503):
            st.info("Upstream ClinicalTrials.gov error — try again in a moment.")

    response = st.session_state.last_response
    if not response:
        return

    viz = response.get("visualization") or {}
    meta = response.get("meta") or {}

    st.subheader(meta.get("title", "Visualization"))
    col_type, col_metrics = st.columns([1, 4])
    with col_type:
        st.markdown(f"**Type:** `{viz.get('type', 'unknown')}`")
    with col_metrics:
        _summary_metrics(viz, meta)

    render_visualization(viz)

    with st.expander("Citations", expanded=False):
        _render_citations(viz)

    with st.expander("Metadata", expanded=False):
        _render_metadata(meta)

    with st.expander("Raw JSON response", expanded=False):
        st.json(response)


if __name__ == "__main__":
    main()
