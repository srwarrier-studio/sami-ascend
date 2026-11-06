import math

from onnx_classifier.domain.errors import InvalidQuestion
from onnx_classifier.domain.gateways.pair_scorer import PairScorer


class ScoreChoice:
    def __init__(self, scorer: PairScorer, temperature: float):
        self.scorer = scorer
        self.temperature = temperature

    def execute(self, text: str, instructions: str, choices: dict[str, str]) -> dict[str, float]:
        if not choices:
            raise InvalidQuestion("a choice question needs at least one option")
        options = [f"{instructions} {name}: {description}" for name, description in choices.items()]
        scaled = [value / self.temperature for value in self.scorer.logits(text, options)]
        top = max(scaled)
        exps = [math.exp(value - top) for value in scaled]
        total = sum(exps)
        return {name: value / total for name, value in zip(choices, exps)}
