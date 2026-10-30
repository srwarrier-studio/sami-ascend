from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from sami_agents.application.keyword_matcher import KeywordMatcher
from sami_agents.application.open_ui_writer import OpenUiWriter
from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.domain.errors import InvalidModelAnswer, ModelUnavailable
from sami_agents.domain.gateways.chat_model import ChatModel

BUILDER_TAG = "@builder"
INLINE_LIMIT = 4
BOARD_LIMIT = 15
BOARD_NAME_LIMIT = 30
DEFAULT_BOARD_NAME = "AI board"
NOT_FOUND = "I could not find a matching widget."


class ChatState(TypedDict, total=False):
    message: str
    catalog: list[CatalogEntry]
    builder: bool
    board_name: str
    picked: list[str]
    ids: list[str]
    program: str


def board_name_from(message: str) -> str:
    name = " ".join(message.split()).strip().title()
    return name[:BOARD_NAME_LIMIT].strip() or DEFAULT_BOARD_NAME


def join_titles(titles: list[str]) -> str:
    return titles[0] if len(titles) == 1 else ", ".join(titles[:-1]) + " and " + titles[-1]


class PlanChat:
    def __init__(self, model: ChatModel):
        self.model = model
        self.matcher = KeywordMatcher()
        self.writer = OpenUiWriter()
        self.graph = self._build()

    def execute(self, message: str, catalog: list[CatalogEntry]) -> str:
        return self.graph.invoke({"message": message, "catalog": catalog})["program"]

    def choose(self, message: str, catalog: list[CatalogEntry]) -> list[str]:
        return self.graph.invoke({"message": message, "catalog": catalog})["ids"]

    def _build(self):
        graph = StateGraph(ChatState)
        graph.add_node("route", self._route)
        graph.add_node("select", self._select)
        graph.add_node("validate", self._validate)
        graph.add_node("fallback", self._fallback)
        graph.add_node("reply", self._reply)
        graph.add_edge(START, "route")
        graph.add_edge("route", "select")
        graph.add_edge("select", "validate")
        graph.add_conditional_edges("validate", lambda state: "reply" if state["ids"] else "fallback", ["reply", "fallback"])
        graph.add_edge("fallback", "reply")
        graph.add_edge("reply", END)
        return graph.compile()

    def _route(self, state: ChatState) -> ChatState:
        message = state["message"].strip()
        if not message.lower().startswith(BUILDER_TAG):
            return {"builder": False, "message": message}
        request = message[len(BUILDER_TAG):].strip()
        return {"builder": True, "message": request, "board_name": board_name_from(request)}

    def _select(self, state: ChatState) -> ChatState:
        try:
            return {"picked": self.model.pick_widgets(state["message"], state["catalog"])}
        except (ModelUnavailable, InvalidModelAnswer):
            return {"picked": []}

    def _limit(self, state: ChatState) -> int:
        return BOARD_LIMIT if state["builder"] else INLINE_LIMIT

    def _validate(self, state: ChatState) -> ChatState:
        known = {entry.id for entry in state["catalog"]}
        unique = list(dict.fromkeys(entry_id for entry_id in state["picked"] if entry_id in known))
        return {"ids": unique[: self._limit(state)]}

    def _fallback(self, state: ChatState) -> ChatState:
        return {"ids": self.matcher.match(state["message"], state["catalog"], self._limit(state))}

    def _reply(self, state: ChatState) -> ChatState:
        ids = state["ids"]
        titles_by_id = {entry.id: entry.title for entry in state["catalog"]}
        if not ids:
            return {"program": self.writer.answer(NOT_FOUND, [])}
        if state["builder"]:
            name = state["board_name"]
            sentence = f"I built {name} with {len(ids)} widget{'s' if len(ids) != 1 else ''}."
            return {"program": self.writer.board(sentence, name, ids)}
        return {"program": self.writer.answer(f"Here is {join_titles([titles_by_id[entry_id] for entry_id in ids])}.", ids)}
