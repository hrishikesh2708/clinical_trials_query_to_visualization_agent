"""Query horizons and visualization compatibility rules.

Normative spec: docs/horizon_matrix.md
"""

from dataclasses import dataclass
from enum import StrEnum

from app.domain.visualization import VisualizationType, assert_never


class Horizon(StrEnum):
    TIME_TREND = "time_trend"
    DISTRIBUTION = "distribution"
    COMPARISON = "comparison"
    GEOGRAPHIC = "geographic"
    NETWORK = "network"


@dataclass(frozen=True, slots=True)
class HorizonSpec:
    """Static metadata for a query horizon (paths, API projection, allowed viz)."""

    horizon: Horizon
    canonical_json_paths: tuple[str, ...]
    fields_pieces: tuple[str, ...]
    allowed_viz: frozenset[VisualizationType]


_HORIZON_ALLOWED: dict[Horizon, frozenset[VisualizationType]] = {
    Horizon.TIME_TREND: frozenset({VisualizationType.TIME_SERIES}),
    Horizon.DISTRIBUTION: frozenset(
        {VisualizationType.BAR_CHART, VisualizationType.HISTOGRAM}
    ),
    Horizon.COMPARISON: frozenset(
        {VisualizationType.GROUPED_BAR_CHART, VisualizationType.BAR_CHART}
    ),
    Horizon.GEOGRAPHIC: frozenset({VisualizationType.BAR_CHART}),
    Horizon.NETWORK: frozenset({VisualizationType.NETWORK_GRAPH}),
}

_HORIZON_SPECS: dict[Horizon, HorizonSpec] = {
    Horizon.TIME_TREND: HorizonSpec(
        horizon=Horizon.TIME_TREND,
        canonical_json_paths=(
            "studies[].protocolSection.statusModule.startDateStruct.date",
            "studies[].protocolSection.statusModule.startDateStruct.type",
            "studies[].protocolSection.identificationModule.nctId",
        ),
        fields_pieces=("NCTId", "StartDateStruct"),
        allowed_viz=_HORIZON_ALLOWED[Horizon.TIME_TREND],
    ),
    Horizon.DISTRIBUTION: HorizonSpec(
        horizon=Horizon.DISTRIBUTION,
        canonical_json_paths=(
            "studies[].protocolSection.designModule.phases[]",
            "studies[].protocolSection.statusModule.overallStatus",
            "studies[].protocolSection.armsInterventionsModule.interventions[].type",
            "studies[].protocolSection.designModule.enrollmentInfo.count",
            "studies[].protocolSection.identificationModule.nctId",
        ),
        fields_pieces=("NCTId", "Phase"),
        allowed_viz=_HORIZON_ALLOWED[Horizon.DISTRIBUTION],
    ),
    Horizon.COMPARISON: HorizonSpec(
        horizon=Horizon.COMPARISON,
        canonical_json_paths=(
            "studies[].protocolSection.designModule.phases[]",
            "studies[].protocolSection.armsInterventionsModule.interventions[].name",
            "studies[].protocolSection.sponsorCollaboratorsModule.leadSponsor.name",
            "studies[].protocolSection.conditionsModule.conditions[]",
            "studies[].protocolSection.identificationModule.nctId",
        ),
        fields_pieces=("NCTId", "Phase", "InterventionName"),
        allowed_viz=_HORIZON_ALLOWED[Horizon.COMPARISON],
    ),
    Horizon.GEOGRAPHIC: HorizonSpec(
        horizon=Horizon.GEOGRAPHIC,
        canonical_json_paths=(
            "studies[].protocolSection.contactsLocationsModule.locations[].country",
            "studies[].protocolSection.identificationModule.nctId",
        ),
        fields_pieces=("NCTId", "LocationCountry"),
        allowed_viz=_HORIZON_ALLOWED[Horizon.GEOGRAPHIC],
    ),
    Horizon.NETWORK: HorizonSpec(
        horizon=Horizon.NETWORK,
        canonical_json_paths=(
            "studies[].protocolSection.armsInterventionsModule.interventions[].name",
            "studies[].protocolSection.sponsorCollaboratorsModule.leadSponsor.name",
            "studies[].protocolSection.conditionsModule.conditions[]",
            "studies[].derivedSection.interventionBrowseModule.meshes[]",
            "studies[].derivedSection.conditionBrowseModule.meshes[]",
            "studies[].protocolSection.identificationModule.nctId",
        ),
        fields_pieces=(
            "NCTId",
            "InterventionName",
            "LeadSponsorName",
            "Condition",
            "DerivedSection",
        ),
        allowed_viz=_HORIZON_ALLOWED[Horizon.NETWORK],
    ),
}


def horizon_spec(horizon: Horizon) -> HorizonSpec:
    """Return static metadata for a horizon."""
    match horizon:
        case Horizon.TIME_TREND:
            return _HORIZON_SPECS[Horizon.TIME_TREND]
        case Horizon.DISTRIBUTION:
            return _HORIZON_SPECS[Horizon.DISTRIBUTION]
        case Horizon.COMPARISON:
            return _HORIZON_SPECS[Horizon.COMPARISON]
        case Horizon.GEOGRAPHIC:
            return _HORIZON_SPECS[Horizon.GEOGRAPHIC]
        case Horizon.NETWORK:
            return _HORIZON_SPECS[Horizon.NETWORK]
        case _ as unreachable:
            assert_never(unreachable)


def allowed_visualization_types(horizon: Horizon) -> frozenset[VisualizationType]:
    """Return visualization types permitted for a query horizon."""
    match horizon:
        case Horizon.TIME_TREND:
            return _HORIZON_ALLOWED[Horizon.TIME_TREND]
        case Horizon.DISTRIBUTION:
            return _HORIZON_ALLOWED[Horizon.DISTRIBUTION]
        case Horizon.COMPARISON:
            return _HORIZON_ALLOWED[Horizon.COMPARISON]
        case Horizon.GEOGRAPHIC:
            return _HORIZON_ALLOWED[Horizon.GEOGRAPHIC]
        case Horizon.NETWORK:
            return _HORIZON_ALLOWED[Horizon.NETWORK]
        case _ as unreachable:
            assert_never(unreachable)


def is_visualization_compatible(
    horizon: Horizon, viz_type: VisualizationType
) -> bool:
    """Return True if viz_type is allowed for the given horizon."""
    return viz_type in allowed_visualization_types(horizon)
