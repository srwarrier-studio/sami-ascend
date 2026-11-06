from onnx_classifier.domain.gateways.pair_scorer import PairScorer


class FakePairScorer(PairScorer):
    def __init__(self, logits: list[float]):
        self.values = logits
        self.calls = []

    def logits(self, question: str, options: list[str]) -> list[float]:
        self.calls.append((question, options))
        return self.values[: len(options)]
