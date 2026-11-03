from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from synapse_api.domain.entities.board import Board, BoardWidget


class Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class WidgetBody(Camel):
    id: str = Field(min_length=1, max_length=64)
    catalog_id: str = Field(min_length=1, max_length=64)
    size: str | None = None

    def to_domain(self) -> BoardWidget:
        return BoardWidget(self.id, self.catalog_id, self.size)


class CreateBoardBody(Camel):
    name: str = Field(min_length=1, max_length=60)
    is_public: bool = False
    widgets: list[WidgetBody] = Field(default_factory=list, max_length=60)


class ChangeBoardBody(Camel):
    name: str | None = Field(default=None, min_length=1, max_length=60)
    is_public: bool | None = None


class SaveWidgetsBody(Camel):
    widgets: list[WidgetBody] = Field(max_length=60)


class BoardResponse(Camel):
    id: str
    name: str
    is_public: bool
    owner: str
    shared: bool
    widgets: list[WidgetBody]

    @classmethod
    def from_domain(cls, board: Board, shared: bool = False) -> "BoardResponse":
        widgets = [WidgetBody(id=w.id, catalog_id=w.catalog_id, size=w.size) for w in board.widgets]
        return cls(id=board.id, name=board.name, is_public=board.is_public, owner=board.owner_name, shared=shared, widgets=widgets)
