from collections import Counter
from dataclasses import dataclass

from intent_api.application.build_training_set import normalised
from intent_api.application.choose_scenarios import NOTHING
from intent_api.application.read_domain import OTHER
from intent_api.domain.entities.scenario import Library
from intent_api.domain.entities.training import Family, TrainingItem

MIN_FAMILIES = 4
MIN_REFUSING_SHARE = 0.2
MAX_UNBALANCE = 4
MAX_DUPLICATE_SHARE = 0.02


@dataclass(frozen=True)
class Report:
    lines: list[str]
    problems: list[str]


class CheckTrainingSet:
    def __init__(self, library: Library, families: list[Family], items: list[TrainingItem], evaluation: frozenset[str]):
        self.library = library
        self.families = families
        self.items = items
        self.evaluation = evaluation

    def execute(self) -> Report:
        lines: list[str] = []
        problems: list[str] = []
        train = [item for item in self.items if not item.heldout]
        held = [item for item in self.items if item.heldout]
        lines.append(f"{len(train)} training items, {len(held)} held-out items, {len(self.families)} families ({sum(family.heldout for family in self.families)} held out)")
        self.overlap(train, held, problems)
        self.coverage(train, held, lines, problems)
        self.balance(train, lines, problems)
        self.refusals(train, lines, problems)
        self.duplicates(lines, problems)
        return Report(lines, problems)

    def overlap(self, train: list[TrainingItem], held: list[TrainingItem], problems: list[str]) -> None:
        train_families = {family for item in train for family in item.families}
        held_families = {family for item in held for family in item.families}
        if train_families & held_families:
            problems.append(f"families in both training and held-out: {sorted(train_families & held_families)[:5]}")
        shared = {normalised(item.text) for item in train} & {normalised(item.text) for item in held}
        if shared:
            problems.append(f"{len(shared)} texts in both training and held-out, for example '{sorted(shared)[0]}'")
        leaked = {normalised(item.text) for item in self.items} & self.evaluation
        if leaked:
            problems.append(f"{len(leaked)} texts are also evaluation questions, for example '{sorted(leaked)[0]}'")

    def coverage(self, train: list[TrainingItem], held: list[TrainingItem], lines: list[str], problems: list[str]) -> None:
        wanted_domains = {*self.library.domains, OTHER}
        for name, items in (("training", train), ("held-out", held)):
            domains = {item.answer for item in items if item.kind == "domain"}
            scenarios = {item.answer for item in items if item.kind == "scenario"}
            if wanted_domains - domains:
                problems.append(f"{name}: no domain items for {sorted(wanted_domains - domains)}")
            if set(self.library.scenarios) - scenarios:
                problems.append(f"{name}: no scenario items for {sorted(set(self.library.scenarios) - scenarios)}")
            if NOTHING not in scenarios:
                problems.append(f"{name}: no items that teach 'nothing is asked'")
        groups = Counter((family.domain, family.scenario, family.nothing) for family in self.families)
        for (domain, scenario, nothing), count in sorted(groups.items(), key=str):
            if count < MIN_FAMILIES and (scenario or nothing):
                problems.append(f"group {scenario or ('forecast ' + domain)}: only {count} families, at least {MIN_FAMILIES} are needed for a held-out one")
        lines.append("domain items (training / held-out): " + ", ".join(f"{name} {sum(i.answer == name and i.kind == 'domain' for i in train)}/{sum(i.answer == name and i.kind == 'domain' for i in held)}" for name in wanted_domains))

    def balance(self, train: list[TrainingItem], lines: list[str], problems: list[str]) -> None:
        per_scenario = Counter(item.answer for item in train if item.kind == "scenario" and item.answer != NOTHING)
        lines.append("scenario items in training: " + ", ".join(f"{name} {per_scenario[name]}" for name in self.library.scenarios))
        counts = [per_scenario[name] for name in self.library.scenarios if per_scenario[name]]
        if counts and max(counts) > MAX_UNBALANCE * min(counts):
            problems.append(f"scenario items are unbalanced: {min(counts)} to {max(counts)} per scenario")
        per_domain = Counter(item.answer for item in train if item.kind == "domain" and item.answer in self.library.domains)
        counts = [per_domain[name] for name in self.library.domains if per_domain[name]]
        if counts and max(counts) > MAX_UNBALANCE * min(counts):
            problems.append(f"domain items are unbalanced: {min(counts)} to {max(counts)} per domain")

    def refusals(self, train: list[TrainingItem], lines: list[str], problems: list[str]) -> None:
        with_scenarios = {family.id for family in self.families if family.scenario}
        domain_items = [item for item in train if item.kind == "domain"]
        refusing = [item for item in domain_items if item.answer == OTHER or not set(item.families) <= with_scenarios]
        share = len(refusing) / max(1, len(domain_items))
        lines.append(f"refusing domain items (Other or a domain without scenarios, plus forecasts): {share:.0%}")
        if share < MIN_REFUSING_SHARE:
            problems.append(f"refusing domain items are only {share:.0%}, at least {MIN_REFUSING_SHARE:.0%} are needed")

    def duplicates(self, lines: list[str], problems: list[str]) -> None:
        counts = Counter((item.kind, normalised(item.text), item.offered, item.answer) for item in self.items)
        extra = sum(count - 1 for count in counts.values())
        lines.append(f"exact duplicates: {extra} of {len(self.items)}")
        if extra > MAX_DUPLICATE_SHARE * len(self.items):
            problems.append(f"{extra} exact duplicate items ({extra / len(self.items):.1%}); add templates or slot values")
        answers: dict[tuple, set[str]] = {}
        for item in self.items:
            answers.setdefault((item.kind, normalised(item.text)), set()).add(item.answer)
        clash = [key for key, labels in answers.items() if len(labels) > 1]
        if clash:
            problems.append(f"{len(clash)} questions have two different answers, for example '{clash[0][1]}'")
