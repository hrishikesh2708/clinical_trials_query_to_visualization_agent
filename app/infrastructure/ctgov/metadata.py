from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MetadataParams(BaseModel):
    include_indexed_only: bool = False
    include_historic_only: bool = False

    def to_query_params(self) -> dict[str, str]:
        params: dict[str, str] = {}
        if self.include_indexed_only:
            params["includeIndexedOnly"] = "true"
        if self.include_historic_only:
            params["includeHistoricOnly"] = "true"
        return params


class MetadataDedLink(BaseModel):
    label: str
    url: str


class MetadataFieldNode(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    piece: str
    title: str
    source_type: str = Field(alias="sourceType")
    type: str
    ded_link: MetadataDedLink | None = Field(default=None, alias="dedLink")
    children: list["MetadataFieldNode"] | None = None


class StudyMetadata(BaseModel):
    roots: list[MetadataFieldNode]

    @classmethod
    def from_api(cls, data: list[dict[str, Any]]) -> "StudyMetadata":
        return cls(roots=[MetadataFieldNode.model_validate(item) for item in data])

    def field_pieces(self) -> list[str]:
        pieces: list[str] = []
        for root in self.roots:
            self._collect_field_pieces(root, pieces)
        return pieces

    def _collect_field_pieces(
        self, node: MetadataFieldNode, pieces: list[str]
    ) -> None:
        if node.children:
            for child in node.children:
                self._collect_field_pieces(child, pieces)
        else:
            pieces.append(node.piece)
