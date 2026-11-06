import json
import math
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from bench import evaluate

TRAIN = Path(__file__).resolve().parent.parent / "train.jsonl"


def load(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def softmax_over(logits):
    top = max(logits.values())
    exps = {name: math.exp(value - top) for name, value in logits.items()}
    total = sum(exps.values())
    return {name: value / total for name, value in exps.items()}


def masked_scorer(model, featurize, labels):
    index = {label: position for position, label in enumerate(labels)}

    def score(text, instructions, choices):
        log_probs = np.log(model.predict_proba(featurize([text]))[0] + 1e-9)
        return softmax_over({name: log_probs[index[name]] for name in choices if name in index} or {name: 0.0 for name in choices})

    return score


def cosine_scorer(encoder, temperature):
    cache = {}

    def embed(texts):
        missing = [t for t in texts if t not in cache]
        if missing:
            for t, v in zip(missing, encoder.encode(missing, normalize_embeddings=True)):
                cache[t] = v
        return np.array([cache[t] for t in texts])

    def score(text, instructions, choices):
        question = embed([text])[0]
        options = embed([f"{name}: {description}" for name, description in choices.items()])
        return softmax_over(dict(zip(choices, (options @ question) / temperature)))

    return score


def main():
    train = load(TRAIN)
    texts = [item["state"]["question"] for item in train]
    labels = [item["expected"]["choice"] for item in train]

    tfidf = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit(texts)
    linear = LogisticRegression(C=20, max_iter=2000).fit(tfidf.transform(texts), labels)
    print("tfidf+logreg", evaluate(masked_scorer(linear, tfidf.transform, list(linear.classes_))))

    encoder = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu")
    print("bge-small zero-shot cosine", evaluate(cosine_scorer(encoder, 0.05)))

    vectors = encoder.encode(texts, normalize_embeddings=True)
    head = LogisticRegression(C=20, max_iter=2000).fit(vectors, labels)
    featurize = lambda batch: encoder.encode(batch, normalize_embeddings=True)
    print("bge-small+logreg", evaluate(masked_scorer(head, featurize, list(head.classes_))))


if __name__ == "__main__":
    main()
