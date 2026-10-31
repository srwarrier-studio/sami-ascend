import re
from datetime import date

from sami_agents.application.question_reader import MONTHS, QuestionReader, correct_months
from sami_agents.domain.entities.case import Case, Decision
from sami_agents.domain.entities.question import Question, ReadResult
from sami_agents.domain.errors import CaseModelUnavailable
from sami_agents.domain.gateways.case_model import CaseModel

RESTRICTED = "I can only explain the whole company's figure for now, not one customer, product or supplier."
ONE_MONTH = "I answer one month at a time, for example: why did sales fall in August?"
OTHER = "Ask why a metric rose or fell in a month, for example: why did sales fall in August?"

INTENTS = {
    "why": "an explanation of why a business figure rose, fell or changed",
    "figure": "the value of a business figure for a period",
    "widgets": "to see charts, tables or a dashboard",
    "other": "something unrelated to the company's business figures",
}
DIRECTIONS = {"rise": "it went up or increased", "fall": "it went down, dropped or decreased", "change": "it changed or is unclear"}
PERIOD_WORDS = {"quarter", "quarterly", "week", "weeks", "weekly", "year", "years", "yearly", "ytd", "today", "yesterday", "half", "q1", "q2", "q3", "q4", "fortnight", "decade"}
SCOPE_PREPOSITION = re.compile(r"\b(?:to|from|of|for|by|at|in|with)\s+(?:(?:the|our|a|an)\s+)?([a-z][a-z0-9&'-]*)")
NOT_A_NAME = {
    "month", "months", "last", "previous", "this", "current", "next", "all", "each", "every", "total", "overall", "company", "group", "business",
    "us", "we", "you", "our", "it", "them", "customers", "customer", "suppliers", "supplier", "vendors", "clients", "products", "product",
    "end", "start", "beginning", "middle", "top", "bottom", "time", "point", "materials", "material", "orders", "order", "money", "figures", "numbers", "general", "both", "any", "now", "then", "so", "too",
}


class CaseReader:
    def __init__(self, rules: QuestionReader, model: CaseModel, min_confidence: float = 0.5):
        self.rules = rules
        self.model = model
        self.min_confidence = min_confidence

    def read(self, text: str, today: date) -> ReadResult:
        try:
            return self.passes(text, today)
        except CaseModelUnavailable:
            return self.rules.read(text, today)

    def passes(self, text: str, today: date) -> ReadResult:
        lowered = correct_months(" ".join(text.lower().split()))
        case = Case()
        intent = self.sure("intent", text, "What does the manager want?", INTENTS, case) or self.rules.intent(lowered)
        if intent is None or intent == "other":
            return ReadResult(None, "unreadable", case)
        if intent == "widgets":
            return ReadResult(None, "widgets", case)
        case.intent = intent
        subjects = {name: ", ".join(words) for name, words in self.rules.words.metrics.items()} | {"none": "neither of these"}
        metric = self.sure("subject", text, "Which business figure is the question about?", subjects, case)
        named = self.rules.metric(lowered)
        if metric is None:
            metric = named
        elif metric == "none" and named is not None:
            case.how_read.append(f"subject: the word for {named} overruled the model")
            metric = named
        if metric is None or metric == "none":
            return ReadResult(None, "unreadable", case)
        case.metric = metric
        case.direction = "change"
        if intent == "why":
            case.direction = self.sure("direction", text, "What happened to the figure?", DIRECTIONS, case) or self.rules.direction(lowered)
        if self.restricted(lowered):
            case.scope = "restricted"
            return ReadResult(None, "restricted", case)
        case.scope = "all"
        month = self.rules.month(lowered, today)
        if month is None:
            return ReadResult(None, "not_one_month" if self.names_a_period(lowered) else "unreadable", case)
        case.month = month
        if intent == "why" and month >= today.replace(day=1):
            return ReadResult(None, "not_finished", case)
        return ReadResult(Question(metric, case.direction, month, intent), None, case)

    def sure(self, name: str, text: str, instructions: str, choices: dict[str, str], case: Case) -> str | None:
        decision: Decision = self.model.decide(text, name, instructions, choices)
        case.confidences[name] = decision.confidence
        if decision.confidence < self.min_confidence:
            case.how_read.append(f"{name}: unsure, read by rules")
            return None
        case.how_read.append(f"{name}: {decision.choice}")
        return decision.choice

    def names_a_period(self, text: str) -> bool:
        return any(word in PERIOD_WORDS for word in re.findall(r"[a-z0-9]+", text))

    def restricted(self, text: str) -> bool:
        known = set(MONTHS) | NOT_A_NAME | PERIOD_WORDS
        for words in (*self.rules.words.metrics.values(), self.rules.words.why, self.rules.words.rise, self.rules.words.fall, self.rules.words.change):
            known |= {word for phrase in words for word in phrase.split()}
        return any(not match.group(1)[0].isdigit() and match.group(1) not in known for match in SCOPE_PREPOSITION.finditer(text))
