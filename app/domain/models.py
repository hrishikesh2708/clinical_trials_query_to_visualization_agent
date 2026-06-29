"""Safe accessors for trimmed ClinicalTrials.gov study JSON."""

from typing import Any


def _protocol_section(study: dict[str, Any]) -> dict[str, Any]:
    section = study.get("protocolSection")
    return section if isinstance(section, dict) else {}


def _module(study: dict[str, Any], name: str) -> dict[str, Any]:
    module = _protocol_section(study).get(name)
    return module if isinstance(module, dict) else {}


def nct_id(study: dict[str, Any]) -> str | None:
    identification = _module(study, "identificationModule")
    value = identification.get("nctId")
    return value if isinstance(value, str) and value else None


def start_date_struct(study: dict[str, Any]) -> dict[str, Any] | None:
    status = _module(study, "statusModule")
    struct = status.get("startDateStruct")
    return struct if isinstance(struct, dict) else None


def phases(study: dict[str, Any]) -> list[str]:
    design = _module(study, "designModule")
    raw = design.get("phases")
    if not isinstance(raw, list):
        return []
    return [phase for phase in raw if isinstance(phase, str) and phase]


def overall_status(study: dict[str, Any]) -> str | None:
    status = _module(study, "statusModule")
    value = status.get("overallStatus")
    return value if isinstance(value, str) and value else None


def enrollment_count(study: dict[str, Any]) -> int | None:
    design = _module(study, "designModule")
    enrollment = design.get("enrollmentInfo")
    if not isinstance(enrollment, dict):
        return None
    count = enrollment.get("count")
    return count if isinstance(count, int) else None


def intervention_names(study: dict[str, Any]) -> list[str]:
    arms = _module(study, "armsInterventionsModule")
    interventions = arms.get("interventions")
    if not isinstance(interventions, list):
        return []
    names: list[str] = []
    for item in interventions:
        if isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str) and name:
                names.append(name)
    return names


def intervention_types(study: dict[str, Any]) -> list[str]:
    arms = _module(study, "armsInterventionsModule")
    interventions = arms.get("interventions")
    if not isinstance(interventions, list):
        return []
    types: list[str] = []
    for item in interventions:
        if isinstance(item, dict):
            value = item.get("type")
            if isinstance(value, str) and value:
                types.append(value)
    return types


def conditions(study: dict[str, Any]) -> list[str]:
    conditions_module = _module(study, "conditionsModule")
    raw = conditions_module.get("conditions")
    if not isinstance(raw, list):
        return []
    return [condition for condition in raw if isinstance(condition, str) and condition]


def lead_sponsor_name(study: dict[str, Any]) -> str | None:
    sponsor = _module(study, "sponsorCollaboratorsModule")
    lead = sponsor.get("leadSponsor")
    if not isinstance(lead, dict):
        return None
    name = lead.get("name")
    return name if isinstance(name, str) and name else None


def countries(study: dict[str, Any]) -> list[str]:
    contacts = _module(study, "contactsLocationsModule")
    locations = contacts.get("locations")
    if not isinstance(locations, list):
        return []
    found: list[str] = []
    for location in locations:
        if isinstance(location, dict):
            country = location.get("country")
            if isinstance(country, str) and country:
                found.append(country)
    return found


def unique_countries(study: dict[str, Any]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for country in countries(study):
        if country not in seen:
            seen.add(country)
            unique.append(country)
    return unique
