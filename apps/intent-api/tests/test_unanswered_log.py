import json

from fakes import FakeUnansweredLog

from intent_api.application.summarise_unanswered import SummariseUnanswered
from intent_api.domain.entities.match import NO_SCENARIOS, NOT_ABOUT_BUSINESS, Match
from intent_api.infrastructure.jsonl_unanswered_log import JsonlUnansweredLog


def refused(reason, domain, nearest) -> Match:
    return Match(domain, 0.5, {}, (), (), reason, tuple(nearest))


class TestJsonlUnansweredLog:
    def test_appends_one_line_per_refusal_with_the_reason_and_choices(self, tmp_path):
        log = JsonlUnansweredLog(tmp_path / "unanswered.jsonl")
        log.record("tell me a joke", refused(NOT_ABOUT_BUSINESS, "Other", ["Sales", "Purchase"]))
        log.record("wetter heute", refused(NOT_ABOUT_BUSINESS, "Other", []))
        lines = (tmp_path / "unanswered.jsonl").read_text().splitlines()
        assert len(lines) == 2
        first = json.loads(lines[0])
        assert (first["question"], first["reason"], first["did_you_mean"]) == ("tell me a joke", NOT_ABOUT_BUSINESS, ["Sales", "Purchase"])
        assert first["at"].endswith("+00:00")

    def test_reads_the_entries_back_and_an_absent_file_is_empty(self, tmp_path):
        log = JsonlUnansweredLog(tmp_path / "unanswered.jsonl")
        assert log.entries() == []
        log.record("ünïcode ✓", refused(NOT_ABOUT_BUSINESS, "Other", []))
        assert log.entries()[0]["question"] == "ünïcode ✓"


class TestSummariseUnanswered:
    def test_groups_refusals_by_the_nearest_domain_biggest_first(self):
        log = FakeUnansweredLog()
        log.record("who owes us", refused(NO_SCENARIOS, "Finance", ["Finance", "Sales"]))
        log.record("joke", refused(NOT_ABOUT_BUSINESS, "Other", ["Sales"]))
        log.record("overdue", refused(NO_SCENARIOS, "Finance", ["Finance"]))
        log.record("weather", refused(NOT_ABOUT_BUSINESS, "Other", []))
        assert SummariseUnanswered(log).execute().splitlines() == [
            "Finance: 2", "  [no_scenarios] who owes us", "  [no_scenarios] overdue",
            "Sales: 1", "  [not_about_business] joke",
            "no nearby domain: 1", "  [not_about_business] weather",
        ]

    def test_says_so_when_nothing_was_refused(self):
        assert SummariseUnanswered(FakeUnansweredLog()).execute() == "no refused questions"
