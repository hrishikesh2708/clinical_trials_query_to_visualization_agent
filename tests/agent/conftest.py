"""Shared fixtures for agent query planner tests."""

from app.infrastructure.ctgov.enums import CtgovEnums

ENUMS_FIXTURE = [
    {
        "type": "Phase",
        "pieces": ["Phase"],
        "values": [
            {"value": "NA", "legacyValue": "Not Applicable"},
            {"value": "PHASE3", "legacyValue": "Phase 3"},
        ],
    },
    {
        "type": "Status",
        "pieces": ["OverallStatus"],
        "values": [
            {"value": "RECRUITING", "legacyValue": "Recruiting"},
            {"value": "COMPLETED", "legacyValue": "Completed"},
        ],
    },
]


def enums_from_fixture() -> CtgovEnums:
    return CtgovEnums.from_api(ENUMS_FIXTURE)
