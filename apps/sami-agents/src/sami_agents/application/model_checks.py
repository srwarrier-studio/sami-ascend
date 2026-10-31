import re
from datetime import date

from sami_agents.application.analyse_question import month_end
from sami_agents.domain.entities.question import Question

DIRECTIONS = ("rise", "fall", "change")
MAX_HEADLINE = 300


def risky_tokens(text: str) -> set[str]:
    tokens = [t.strip(".,;:!?()\"'") for t in text.split()]
    return {t for i, t in enumerate(tokens) if t and (any(c.isdigit() for c in t) or (i > 0 and t[0].isupper()))}


def accept_question(data: object, metrics: list[str], today: date) -> Question | None:
    if not isinstance(data, dict) or data.get("metric") not in metrics or data.get("direction") not in DIRECTIONS:
        return None
    match = re.fullmatch(r"(\d{4})-(\d{2})", str(data.get("month", "")))
    if match is None or not 1 <= int(match.group(2)) <= 12:
        return None
    first = date(int(match.group(1)), int(match.group(2)), 1)
    if month_end(first) >= today:
        return None
    return Question(data["metric"], data["direction"], first)


def accept_rewrite(candidate: str | None, original: str) -> str | None:
    if not candidate or "\n" in candidate or len(candidate) > MAX_HEADLINE:
        return None
    return candidate.strip() if risky_tokens(candidate) <= risky_tokens(original) else None
