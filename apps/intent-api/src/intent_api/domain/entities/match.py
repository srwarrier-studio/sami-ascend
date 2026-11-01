from dataclasses import dataclass

from intent_api.domain.entities.selection import Selected

NOT_ABOUT_BUSINESS = "not_about_business"
NOT_SURE = "not_sure"
NO_SCENARIOS = "no_scenarios"
NOTHING_MATCHED = "nothing_matched"
NOT_ANSWERABLE_YET = "not_answerable_yet"
PERIOD_NOT_SUPPORTED = "period_not_supported"


@dataclass(frozen=True)
class Match:
    domain: str | None
    domain_probability: float
    domain_scores: dict[str, float]
    offered: tuple[str, ...] = ()
    selected: tuple[Selected, ...] = ()
    reason: str | None = None
    did_you_mean: tuple[str, ...] = ()

    @property
    def answered(self) -> bool:
        return self.reason is None
