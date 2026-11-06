from pathlib import Path

import pytest

from onnx_classifier.entrypoint.app import build_score_choice
from onnx_classifier.infrastructure.settings import Settings

MODEL_DIR = Path(__file__).resolve().parents[3] / "Training" / "onnx-deberta" / "serve"
DOMAINS = {
    "Sales": "sales, exports, customers, countries, revenue",
    "Purchase": "purchases, imports, suppliers, raw materials, spend",
    "Shipments": "shipments, dispatch, containers, in transit",
    "Finance": "receivables, payments, overdue, cash",
    "Inventory": "stock, warehouses, reorder",
    "Production": "production, batches, yield, plant, scrap",
    "Other": "everything else",
}


@pytest.mark.skipif(not (MODEL_DIR / "model.onnx").exists(), reason="the trained model is not in Training/onnx-deberta/serve")
class TestRealModel:
    @pytest.mark.parametrize("question,expected", [
        ("which receivables are overdue", "Finance"),
        ("how much did we sell last month", "Sales"),
        ("what is the capital of france", "Other"),
        ("imports from Canada last month", "Purchase"),
    ])
    def test_reads_domain_questions(self, question, expected):
        score = build_score_choice(Settings(model_dir=MODEL_DIR))
        result = score.execute(question, "Which department should handle this?", DOMAINS)
        assert max(result, key=result.get) == expected
