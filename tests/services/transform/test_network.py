from app.domain.horizons import Horizon
from app.domain.visualization import VisualizationType
from app.services.fetch import load_fixture_studies
from app.services.transform import transform_studies
from app.services.transform.base import TransformContext
from tests.services.conftest import assert_excerpts_in_source, load_expected_viz


def test_network_graph_matches_golden_summary() -> None:
    studies = load_fixture_studies("network_diabetes_sponsor_drug")
    viz = transform_studies(
        TransformContext(
            horizon=Horizon.NETWORK,
            viz_type=VisualizationType.NETWORK_GRAPH,
            studies=studies,
        )
    )
    expected = load_expected_viz("network_diabetes_sponsor_drug")

    assert viz.encoding.model_dump() == expected["encoding"]
    assert len(viz.data.nodes) == expected["node_count"]
    assert len(viz.data.edges) == expected["edge_count"]
    assert [node.id for node in viz.data.nodes[:3]] == expected["sample_node_ids"]
    assert all(node.citations for node in viz.data.nodes)
    assert all(edge.citations for edge in viz.data.edges)
    assert_excerpts_in_source(
        studies,
        [citation.model_dump() for citation in viz.data.nodes[0].citations],
    )
