import calendar
import difflib
import re
from dataclasses import dataclass, field

from intent_api.application.read_period import MONTHS, NUMBER_WORDS, alternatives

WEEKDAYS = {name.lower() for name in calendar.day_name} | {name.lower() for name in calendar.day_abbr}
CAPITALISED = re.compile(r"[A-Z][A-Za-z&'.-]*")
TOP = re.compile(rf"\b(?:top|best|largest|biggest|highest)\s+(?P<n>\d+|{'|'.join(NUMBER_WORDS)})\b", re.IGNORECASE)
MAX_TOP = 10


@dataclass
class Qualifiers:
    names: list[str] = field(default_factory=list)
    quantities: list[str] = field(default_factory=list)
    currencies: list[str] = field(default_factory=list)
    top: int | None = None
    top_asked: int | None = None

    @property
    def refused(self) -> bool:
        return bool(self.names or self.quantities or self.currencies)


class ReadQualifiers:
    def __init__(self, words: dict[str, list[str]]):
        self.words = words
        self.markers = re.compile(rf"(?<!\w)(?:{alternatives(words['company_markers'])})(?!\w)")
        self.quantity = re.compile(rf"(?<!\w)(?:{alternatives(words['quantity'])})(?!\w)")
        self.currency = re.compile(rf"(?<!\w)(?:{alternatives(words['other_currencies'])})(?!\w)")
        self.countries = re.compile(rf"(?<!\w)(?:{alternatives(words['countries'])})(?!\w)")
        self.long_months = [name for name in MONTHS if len(name) >= 5]
        self.skipped = set(MONTHS) | WEEKDAYS | set(words["own_names"]) | set(words["ignored_capitals"])

    def read(self, text: str) -> Qualifiers:
        lowered = text.lower()
        found = Qualifiers()
        found.names = self.names(text, lowered)
        found.quantities = [match.group(0) for match in self.quantity.finditer(lowered)]
        found.currencies = [match.group(0) for match in self.currency.finditer(lowered)]
        top = TOP.search(text)
        if top:
            asked = top.group("n")
            found.top_asked = int(asked) if asked.isdigit() else NUMBER_WORDS[asked.lower()]
            found.top = min(found.top_asked, MAX_TOP)
        return found

    def is_skipped(self, word: str) -> bool:
        return word in self.skipped or bool(difflib.get_close_matches(word, self.long_months, n=1, cutoff=0.8))

    def names(self, text: str, lowered: str) -> list[str]:
        names = [match.group(0) for match in self.countries.finditer(lowered)]
        names += [match.group(0) for match in self.markers.finditer(lowered)]
        words = text.split()
        run: list[str] = []
        for index, word in enumerate(words):
            token = word.strip(",.?!;:()\"")
            proper = bool(CAPITALISED.fullmatch(token)) and token != token.upper() and index > 0 and not self.is_skipped(token.lower())
            if proper:
                run.append(token)
            elif run:
                names.append(" ".join(run))
                run = []
        if run:
            names.append(" ".join(run))
        return list({name.lower(): name for name in names}.values())
