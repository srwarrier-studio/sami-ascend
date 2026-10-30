from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from sami_agents.application.keyword_matcher import KeywordMatcher
from sami_agents.application.open_ui_writer import OpenUiWriter
from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.domain.errors import RelevanceUnavailable
from sami_agents.domain.gateways.relevance_checker import RelevanceChecker

BUILDER_TAG = "@builder"
INLINE_LIMIT = 4
BOARD_LIMIT = 15
INLINE_CHECKS = 8
BOARD_CHECKS = 15
BOARD_NAME_LIMIT = 30
DEFAULT_BOARD_NAME = "AI board"
DEFAULT_THRESHOLD = 0.35
NOT_FOUND = "I could not find a matching widget."
GRAPH_STEPS = 100


class ChatState(TypedDict, total=False):
    message: str
    catalog: list[CatalogEntry]
    builder: bool
    board_name: str
    candidate: str | None
    ids: list[str]
    rejected: list[str]
    checks: int
    unchecked: bool
    program: str


def board_name_from(message: str) -> str:
    name = " ".join(message.split()).strip().title()
    return name[:BOARD_NAME_LIMIT].strip() or DEFAULT_BOARD_NAME


def join_titles(titles: list[str]) -> str:
    return titles[0] if len(titles) == 1 else ", ".join(titles[:-1]) + " and " + titles[-1]


class PlanChat:
    def __init__(self, checker: RelevanceChecker | None = None, matcher: KeywordMatcher | None = None, threshold: float = DEFAULT_THRESHOLD):
        self.checker = checker
        self.matcher = matcher or KeywordMatcher()
        self.threshold = threshold
        self.writer = OpenUiWriter()
        self.graph = self._build()

    def execute(self, message: str, catalog: list[CatalogEntry]) -> str:
        return self.run(message, catalog)["program"]

    def choose(self, message: str, catalog: list[CatalogEntry]) -> list[str]:
        return self.run(message, catalog)["ids"]

    def run(self, message: str, catalog: list[CatalogEntry]) -> ChatState:
        return self.graph.invoke({"message": message, "catalog": catalog}, {"recursion_limit": GRAPH_STEPS})

    def _build(self):
        graph = StateGraph(ChatState)
        graph.add_node("route", self._route)
        graph.add_node("propose", self._propose)
        graph.add_node("verify", self._verify)
        graph.add_node("reply", self._reply)
        graph.add_edge(START, "route")
        graph.add_edge("route", "propose")
        graph.add_conditional_edges("propose", lambda state: "verify" if state["candidate"] else "reply", ["verify", "reply"])
        graph.add_conditional_edges("verify", lambda state: "reply" if self._finished(state) else "propose", ["propose", "reply"])
        graph.add_edge("reply", END)
        return graph.compile()

    def _route(self, state: ChatState) -> ChatState:
        message = state["message"].strip()
        start = {"ids": [], "rejected": [], "checks": 0, "unchecked": self.checker is None}
        if not message.lower().startswith(BUILDER_TAG):
            return {**start, "builder": False, "message": message}
        request = message[len(BUILDER_TAG):].strip()
        return {**start, "builder": True, "message": request, "board_name": board_name_from(request)}

    def _limit(self, state: ChatState) -> int:
        return BOARD_LIMIT if state["builder"] else INLINE_LIMIT

    def _budget(self, state: ChatState) -> int:
        return BOARD_CHECKS if state["builder"] else INLINE_CHECKS

    def _finished(self, state: ChatState) -> bool:
        if len(state["ids"]) >= self._limit(state):
            return True
        return not state["unchecked"] and state["checks"] >= self._budget(state)

    def _propose(self, state: ChatState) -> ChatState:
        skip = set(state["ids"]) | set(state["rejected"])
        ranked = self.matcher.rank(state["message"], state["catalog"], skip)
        return {"candidate": ranked[0] if ranked else None}

    def _verify(self, state: ChatState) -> ChatState:
        candidate = state["candidate"]
        approved = {"ids": [*state["ids"], candidate]}
        if state["unchecked"] or self.checker is None:
            return approved
        entry = next(entry for entry in state["catalog"] if entry.id == candidate)
        try:
            score = self.checker.check(state["message"], entry)
        except RelevanceUnavailable:
            return {**approved, "unchecked": True}
        if score >= self.threshold:
            return {**approved, "checks": state["checks"] + 1}
        return {"rejected": [*state["rejected"], candidate], "checks": state["checks"] + 1}

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
