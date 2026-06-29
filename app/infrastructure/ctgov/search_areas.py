from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SearchAreaPart(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pieces: list[str]
    type: str
    is_enum: bool = Field(alias="isEnum")
    is_synonyms: bool = Field(alias="isSynonyms")
    weight: float


class SearchArea(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    ui_label: str = Field(alias="uiLabel")
    param: str = ""
    parts: list[SearchAreaPart]


class SearchAreaDocument(BaseModel):
    name: str
    areas: list[SearchArea]


class StudySearchAreas(BaseModel):
    documents: list[SearchAreaDocument]

    @classmethod
    def from_api(cls, data: list[dict[str, Any]]) -> "StudySearchAreas":
        return cls(
            documents=[SearchAreaDocument.model_validate(item) for item in data]
        )

    def _all_areas(self) -> list[SearchArea]:
        areas: list[SearchArea] = []
        for document in self.documents:
            areas.extend(document.areas)
        return areas

    def areas_with_params(self) -> list[SearchArea]:
        return [area for area in self._all_areas() if area.param]

    def area_for_param(self, param: str) -> SearchArea | None:
        for area in self._all_areas():
            if area.param == param:
                return area
        return None

    def query_param_key(self, param: str) -> str:
        if self.area_for_param(param) is None:
            raise KeyError(f"Unknown search area param: {param!r}")
        return f"query.{param}"
