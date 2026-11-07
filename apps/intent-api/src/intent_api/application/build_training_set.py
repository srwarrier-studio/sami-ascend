import random
import re
from dataclasses import dataclass

from intent_api.application.choose_scenarios import NOTHING
from intent_api.application.read_domain import OTHER
from intent_api.domain.entities.scenario import Library
from intent_api.domain.entities.training import Family, TrainingItem

MIN_TYPO_LENGTH = 4
SLOT = re.compile(r"\{(\w+)\}")
JOINERS = [" and ", ", ", " and also ", " then "]
SPELLINGS = {"revenue": "revnue", "purchases": "purchses", "customers": "custmers", "customer": "custmer", "compare": "compre", "september": "septmber", "august": "augsut", "month": "mnth", "last": "lst", "quarter": "qarter", "supplier": "suppler", "suppliers": "supplers", "spend": "spnd"}


@dataclass(frozen=True)
class Settings:
    seed: int = 20261101
    per_template: int = 8
    typo_rate: float = 0.35
    second_typo_rate: float = 0.3
    combos_per_domain: int = 60
    subset_rate: float = 0.3
    cap_train: int = 150
    cap_heldout: int = 60


def normalised(text: str) -> str:
    return text.lower().rstrip("?").strip()


def with_typo(text: str, rng: random.Random) -> str:
    words = text.split(" ")
    known = [index for index, word in enumerate(words) if word.lower() in SPELLINGS]
    if known and rng.random() < 0.5:
        index = rng.choice(known)
        words[index] = SPELLINGS[words[index].lower()]
        return " ".join(words)
    long_words = [index for index, word in enumerate(words) if len(word) >= MIN_TYPO_LENGTH and word.isalpha()]
    if not long_words:
        return text
    index = rng.choice(long_words)
    word = words[index]
    position = rng.randrange(1, len(word) - 1)
    kind = rng.choice(["swap", "drop", "double"])
    if kind == "swap":
        word = word[:position] + word[position + 1] + word[position] + word[position + 2:]
    elif kind == "drop":
        word = word[:position] + word[position + 1:]
    else:
        word = word[:position] + word[position] + word[position:]
    words[index] = word
    return " ".join(words)


class BuildTrainingSet:
    def __init__(self, library: Library, families: list[Family], slots: dict[str, list[str]], settings: Settings = Settings(), exclude: frozenset[str] = frozenset()):
        self.library = library
        self.families = families
        self.slots = slots
        self.settings = settings
        self.exclude = exclude

    def execute(self) -> list[TrainingItem]:
        items: list[TrainingItem] = []
        texts: dict[str, list[tuple[Family, str]]] = {}
        for family in sorted(self.families, key=lambda item: item.id):
            rng = random.Random(f"{self.settings.seed}:{family.id}")
            for text in self.expand(family, rng):
                texts.setdefault(family.id, []).append((family, text))
                items += self.items_for(family, text, rng)
        items += self.combined(texts)
        return self.capped(self.deduplicated(items))

    def deduplicated(self, items: list[TrainingItem]) -> list[TrainingItem]:
        seen: set[tuple] = set()
        kept = []
        for item in items:
            key = (item.kind, normalised(item.text), item.offered, item.answer, item.heldout)
            if key not in seen:
                seen.add(key)
                kept.append(item)
        return kept

    def capped(self, items: list[TrainingItem]) -> list[TrainingItem]:
        groups: dict[tuple, list[int]] = {}
        for position, item in enumerate(items):
            groups.setdefault((item.kind, item.answer, item.heldout), []).append(position)
        dropped: set[int] = set()
        for key, positions in sorted(groups.items(), key=str):
            cap = self.settings.cap_heldout if key[2] else self.settings.cap_train
            if len(positions) > cap:
                rng = random.Random(f"{self.settings.seed}:cap:{key}")
                combined = [position for position in positions if len(items[position].families) == 2][:cap]
                singles = [position for position in positions if position not in set(combined)]
                room = cap - len(combined)
                firsts = list({items[position].families: position for position in reversed(singles)}.values())[:room]
                rest = [position for position in singles if position not in set(firsts)]
                kept = set(combined) | set(firsts) | set(rng.sample(rest, room - len(firsts)))
                dropped.update(set(positions) - kept)
        return [item for position, item in enumerate(items) if position not in dropped]

    def expand(self, family: Family, rng: random.Random) -> list[str]:
        out: list[str] = []
        for template in family.templates:
            seen: set[str] = set()
            for _ in range(self.settings.per_template * 3):
                if len(seen) >= self.settings.per_template:
                    break
                text = SLOT.sub(lambda match: rng.choice(self.slots[match.group(1)]), template)
                if text not in seen and normalised(text) not in self.exclude:
                    seen.add(text)
                    out.append(self.styled(text, rng))
        return out

    def styled(self, text: str, rng: random.Random) -> str:
        if rng.random() < self.settings.typo_rate:
            text = with_typo(text, rng)
            if rng.random() < self.settings.second_typo_rate:
                text = with_typo(text, rng)
        if rng.random() < 0.3:
            text = text[0].upper() + text[1:]
        if rng.random() < 0.3:
            text += "?"
        return text

    def domain_item(self, family: Family, text: str) -> TrainingItem:
        offered = (*self.library.domains, OTHER)
        return TrainingItem("domain", text, family.domain, offered, (family.id,), family.heldout)

    def scenario_item(self, family: Family, text: str, answer: str, rng: random.Random) -> TrainingItem:
        names = [scenario.id for scenario in self.library.scenarios.values() if scenario.domain == family.domain]
        if rng.random() < self.settings.subset_rate:
            others = [name for name in names if name != answer]
            keep = rng.randint(1, max(1, len(others) // 2))
            chosen = set(rng.sample(others, min(keep, len(others))))
            names = [name for name in names if name == answer or name in chosen]
        return TrainingItem("scenario", text, answer, (*names, NOTHING), (family.id,), family.heldout)

    def items_for(self, family: Family, text: str, rng: random.Random) -> list[TrainingItem]:
        items = [self.domain_item(family, text)] if family.domain_item else []
        if family.scenario:
            items.append(self.scenario_item(family, text, family.scenario, rng))
        elif family.nothing:
            items.append(self.scenario_item(family, text, NOTHING, rng))
        return items

    def combined(self, texts: dict[str, list[tuple[Family, str]]]) -> list[TrainingItem]:
        items: list[TrainingItem] = []
        for heldout in (False, True):
            for domain in self.library.domains:
                pool = [family for family in sorted(self.families, key=lambda item: item.id) if family.domain == domain and family.scenario and family.heldout == heldout]
                openers = [family for family in pool if family.domain_item]
                if not openers or len({family.scenario for family in pool}) < 2:
                    continue
                rng = random.Random(f"{self.settings.seed}:combo:{domain}:{heldout}")
                for position in range(self.settings.combos_per_domain // (1 if not heldout else 3)):
                    first, second = rng.choice(openers), pool[position % len(pool)]
                    if first.scenario == second.scenario:
                        continue
                    one, two = rng.choice(texts[first.id])[1], rng.choice(texts[second.id])[1]
                    one, two = one.rstrip("?"), two.rstrip("?").lower()
                    whole = f"{one}{rng.choice(JOINERS)}{two}"
                    items.append(TrainingItem("domain", whole, domain, (*self.library.domains, OTHER), (first.id, second.id), heldout))
                    items.append(self.scenario_item(first, one, first.scenario, rng))
                    items.append(self.scenario_item(second, two, second.scenario, rng))
        return items
