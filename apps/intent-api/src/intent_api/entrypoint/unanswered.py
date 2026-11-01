from intent_api.application.summarise_unanswered import SummariseUnanswered
from intent_api.infrastructure.jsonl_unanswered_log import JsonlUnansweredLog
from intent_api.infrastructure.settings import Settings


def main() -> None:
    print(SummariseUnanswered(JsonlUnansweredLog(Settings().unanswered_log)).execute())
