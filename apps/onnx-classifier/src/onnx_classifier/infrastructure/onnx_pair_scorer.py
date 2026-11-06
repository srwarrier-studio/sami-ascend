from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

from onnx_classifier.domain.gateways.pair_scorer import PairScorer

PAD = "[PAD]"


class OnnxPairScorer(PairScorer):
    def __init__(self, model_dir: Path, max_length: int, threads: int):
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads
        self.session = ort.InferenceSession(str(model_dir / "model.onnx"), options, providers=["CPUExecutionProvider"])
        self.tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length)
        self.tokenizer.enable_padding(pad_id=self.tokenizer.token_to_id(PAD), pad_token=PAD)

    def logits(self, question: str, options: list[str]) -> list[float]:
        encoded = self.tokenizer.encode_batch([(question, option) for option in options])
        feed = {
            "input_ids": np.array([item.ids for item in encoded], dtype=np.int64),
            "attention_mask": np.array([item.attention_mask for item in encoded], dtype=np.int64),
        }
        return self.session.run(None, feed)[0].reshape(-1).tolist()
