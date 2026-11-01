from collections.abc import Callable
from dataclasses import dataclass, field

from intent_api.application.match_question import MatchQuestion
from intent_api.domain.entities.eval_case import EvalCase
from intent_api.domain.entities.match import Match

EXACT = "exact"
WRONG_OR_EXTRA = "wrong_or_extra"
MISSING = "missing"
WRONGLY_REFUSED = "wrongly_refused"
CORRECTLY_REFUSED = "correctly_refused"
WRONGLY_ANSWERED = "wrongly_answered"


@dataclass(frozen=True)
class Failure:
    case: EvalCase
    outcome: str
    match: Match


@dataclass
class Score:
    domain_min: float
    scenario_min: float
    counts: dict[str, int] = field(default_factory=dict)
    domain_right: int = 0
    domain_total: int = 0
    failures: list[Failure] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(self.counts.values())

    @property
    def harmful(self) -> int:
        return self.counts.get(WRONG_OR_EXTRA, 0) + self.counts.get(WRONGLY_ANSWERED, 0)


def outcome_of(case: EvalCase, match: Match) -> str:
    chosen = {item.scenario for item in match.selected}
    if not case.should_answer:
        return CORRECTLY_REFUSED if not match.answered else WRONGLY_ANSWERED
    if not match.answered:
        return WRONGLY_REFUSED
    if chosen == case.scenarios:
        return EXACT
    return MISSING if chosen < case.scenarios else WRONG_OR_EXTRA


class EvaluateMatches:
    def __init__(self, build_matcher: Callable[[float, float], MatchQuestion]):
        self.build_matcher = build_matcher

    def execute(self, cases: list[EvalCase], domain_min: float, scenario_min: float) -> Score:
        matcher = self.build_matcher(domain_min, scenario_min)
        score = Score(domain_min, scenario_min)
        for case in cases:
            match = matcher.match(case.question)
            outcome = outcome_of(case, match)
            score.counts[outcome] = score.counts.get(outcome, 0) + 1
            score.domain_total += 1
            score.domain_right += match.domain == case.domain
            if outcome not in (EXACT, CORRECTLY_REFUSED):
                score.failures.append(Failure(case, outcome, match))
        return score

    def sweep(self, cases: list[EvalCase], domain_mins: list[float], scenario_mins: list[float]) -> list[Score]:
        return [self.execute(cases, domain_min, scenario_min) for domain_min in domain_mins for scenario_min in scenario_mins]


def describe(score: Score) -> str:
    counts = score.counts
    answerable = sum(counts.get(name, 0) for name in (EXACT, WRONG_OR_EXTRA, MISSING, WRONGLY_REFUSED))
    refusable = counts.get(CORRECTLY_REFUSED, 0) + counts.get(WRONGLY_ANSWERED, 0)
    return "\n".join([
        f"thresholds: domain {score.domain_min:.2f}, scenario {score.scenario_min:.2f}; {score.total} questions",
        f"  answerable ({answerable}): exact {counts.get(EXACT, 0)}, wrong or extra scenario {counts.get(WRONG_OR_EXTRA, 0)}, missing {counts.get(MISSING, 0)}, wrongly refused {counts.get(WRONGLY_REFUSED, 0)}",
        f"  must refuse ({refusable}): correctly refused {counts.get(CORRECTLY_REFUSED, 0)}, wrongly answered {counts.get(WRONGLY_ANSWERED, 0)}",
        f"  domain right {score.domain_right}/{score.domain_total}; harmful (wrong or extra + wrongly answered) {score.harmful}",
    ])


def sweep_table(scores: list[Score]) -> str:
    lines = ["domain  scenario  exact  wrong/extra  missing  wrongly-refused  correctly-refused  wrongly-answered  harmful"]
    for score in scores:
        c = score.counts
        lines.append(
            f"{score.domain_min:6.2f}  {score.scenario_min:8.2f}  {c.get(EXACT, 0):5}  {c.get(WRONG_OR_EXTRA, 0):11}  {c.get(MISSING, 0):7}  "
            f"{c.get(WRONGLY_REFUSED, 0):15}  {c.get(CORRECTLY_REFUSED, 0):17}  {c.get(WRONGLY_ANSWERED, 0):16}  {score.harmful:7}"
        )
    return "\n".join(lines)


def describe_failures(score: Score) -> str:
    lines = []
    for failure in score.failures:
        chosen = ", ".join(f"{item.scenario}:{item.probability:.2f}" for item in failure.match.selected) or "-"
        lines.append(f"  [{failure.outcome}] want {failure.case.domain} {sorted(failure.case.scenarios) or 'refuse'}; got {failure.match.domain}:{failure.match.domain_probability:.2f} {failure.match.reason or ''} {chosen} | {failure.case.question[:60]}")
    return "\n".join(lines)
