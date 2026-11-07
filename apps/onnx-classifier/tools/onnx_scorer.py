import json
import sys
from pathlib import Path

import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

from bench import HELDOUT, evaluate

MAX_LENGTH = 96


def onnx_scorer(model_path: Path, tokenizer_dir: Path, temperature: float, threads: int = 2):
    options = ort.SessionOptions()
    options.intra_op_num_threads = threads
    session = ort.InferenceSession(str(model_path), options, providers=["CPUExecutionProvider"])
    wanted = {node.name for node in session.get_inputs()}
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir)

    def score(text, instructions, choices):
        names = list(choices)
        second = [f"{instructions} {name}: {choices[name]}" for name in names]
        encoded = tokenizer([text] * len(names), second, truncation=True, max_length=MAX_LENGTH, padding=True, return_tensors="np")
        feed = {key: value.astype(np.int64) for key, value in encoded.items() if key in wanted}
        logits = session.run(None, {**feed})[0].reshape(-1) / temperature
        exps = np.exp(logits - logits.max())
        return dict(zip(names, (exps / exps.sum()).tolist()))

    return score


if __name__ == "__main__":
    model, tokenizer_dir, temperature = Path(sys.argv[1]), Path(sys.argv[2]), float(sys.argv[3])
    path = Path(sys.argv[4]) if len(sys.argv) > 4 else HELDOUT
    print(model.name, json.dumps(evaluate(onnx_scorer(model, tokenizer_dir, temperature), path)))
