from intent_api.application.choose_scenarios import ChooseScenarios
from intent_api.application.read_domain import OTHER, ReadDomain
from intent_api.domain.entities.match import NO_SCENARIOS, NOT_ABOUT_BUSINESS, NOT_SURE, NOTHING_MATCHED, Match
from intent_api.domain.entities.scenario import Library

NEAREST = 2


class MatchQuestion:
    def __init__(self, read_domain: ReadDomain, choose_scenarios: ChooseScenarios, library: Library, domain_min_probability: float = 0.0):
        self.read_domain = read_domain
        self.choose_scenarios = choose_scenarios
        self.library = library
        self.domain_min_probability = domain_min_probability

    def execute(self, text: str) -> Match:
        decision = self.read_domain.execute(text)
        nearest = tuple(sorted((name for name in decision.scores if name != OTHER), key=lambda name: -decision.scores[name])[:NEAREST])
        refused = lambda reason, offered=(): Match(decision.choice, decision.probability, decision.scores, offered, (), reason, nearest)
        if decision.choice == OTHER:
            return refused(NOT_ABOUT_BUSINESS)
        if decision.probability < self.domain_min_probability:
            return refused(NOT_SURE)
        offered = tuple(scenario.id for scenario in self.library.scenarios.values() if scenario.domain == decision.choice)
        if not offered:
            return refused(NO_SCENARIOS)
        selected = self.choose_scenarios.execute(text, decision.choice)
        if not selected:
            return refused(NOTHING_MATCHED, offered)
        return Match(decision.choice, decision.probability, decision.scores, offered, tuple(selected))
