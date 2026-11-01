from intent_api.domain.entities.answer import AnswerRule


class DescribeAnswers:
    def __init__(self, rules: dict[str, AnswerRule]):
        self.rules = rules

    def summary(self) -> str:
        return f"ok: {len(self.rules)} answers"
