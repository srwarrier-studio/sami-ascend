import re
from datetime import date

from sami_agents.application.analyse_question import month_end
from sami_agents.domain.entities.question import Question

DIRECTIONS = ("rise", "fall", "change")
MAX_HEADLINE = 300
MARKUP = re.compile(r"[*_`#<>\[\]|]")
NEGATIONS = {"no", "not", "nothing", "none", "never", "without", "cannot"}
PROTECTED = ("of the change", "part of it", "steady", "mostly price", "unchanged")
RETAINED = 0.8


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


def keeps_everything(candidate: str, original: str) -> bool:
    words = {t.strip(".,;:!?()\"'").lower() for t in candidate.split()}
    return {t.lower() for t in risky_tokens(original)} <= words


def words_of(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower().replace("n't", " not"))


def keeps_the_meaning(candidate: str, original: str) -> bool:
    before, after = words_of(original), words_of(candidate)
    if sum(w in NEGATIONS for w in before) != sum(w in NEGATIONS for w in after):
        return False
    if any(phrase in original.lower() and phrase not in candidate.lower() for phrase in PROTECTED):
        return False
    if original.lower().count("and behind that") != candidate.lower().count("and behind that"):
        return False
    return sum(w in set(after) for w in before) >= RETAINED * len(before)


def accept_rewrite(candidate: str | None, original: str) -> str | None:
    if not candidate or "\n" in candidate or len(candidate) > MAX_HEADLINE or len(candidate) > 2 * len(original) or MARKUP.search(candidate):
        return None
    if risky_tokens(candidate) <= risky_tokens(original) and keeps_everything(candidate, original) and keeps_the_meaning(candidate, original):
        return candidate.strip()
    return None
