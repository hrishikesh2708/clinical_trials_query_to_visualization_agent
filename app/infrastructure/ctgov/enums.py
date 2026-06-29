from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.infrastructure.ctgov.client import CtgovClient


class EnumValue(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    value: str
    legacy_value: str | None = Field(default=None, alias="legacyValue")
    exceptions: dict[str, str] | None = None


class EnumType(BaseModel):
    type: str
    pieces: list[str]
    values: list[EnumValue]


class CtgovEnums(BaseModel):
    enums: list[EnumType]

    @classmethod
    def from_api(cls, data: list[dict[str, Any]]) -> "CtgovEnums":
        return cls(enums=[EnumType.model_validate(item) for item in data])

    def values_for_type(self, enum_type: str) -> set[str]:
        for item in self.enums:
            if item.type == enum_type:
                return {v.value for v in item.values}
        raise KeyError(f"Unknown enum type: {enum_type}")

    def resolve_value(self, enum_type: str, raw: str) -> str:
        for item in self.enums:
            if item.type != enum_type:
                continue
            for entry in item.values:
                if raw == entry.value:
                    return entry.value
                if entry.legacy_value and raw == entry.legacy_value:
                    return entry.value
                if entry.exceptions:
                    for legacy in entry.exceptions.values():
                        if raw == legacy:
                            return entry.value
            allowed = ", ".join(v.value for v in item.values)
            raise ValueError(
                f"Invalid {enum_type} value {raw!r}. Allowed: {allowed}"
            )
        raise KeyError(f"Unknown enum type: {enum_type}")

    def label_for(self, enum_type: str, raw: str) -> str:
        code = self.resolve_value(enum_type, raw)
        for item in self.enums:
            if item.type != enum_type:
                continue
            for entry in item.values:
                if entry.value == code:
                    return entry.legacy_value or entry.value
        return code

    def validate_phase(self, phase: str) -> str:
        return self.resolve_value("Phase", phase)

    def validate_overall_status(self, status: str) -> str:
        return self.resolve_value("Status", status)


class CtgovEnumsLoader:
    def __init__(self, client: CtgovClient) -> None:
        self._client = client
        self._cache: CtgovEnums | None = None

    def load(self, *, force_refresh: bool = False) -> CtgovEnums:
        if self._cache is None or force_refresh:
            self._cache = CtgovEnums.from_api(self._client.fetch_enums())
        return self._cache

    def validate_phase(self, phase: str) -> str:
        return self.load().validate_phase(phase)

    def validate_overall_status(self, status: str) -> str:
        return self.load().validate_overall_status(status)

    def label_for(self, enum_type: str, raw: str) -> str:
        return self.load().label_for(enum_type, raw)
