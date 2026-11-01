from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "src" / "intent_api"
CALLERS = ["infrastructure/laya_choice_classifier.py", "infrastructure/synapse_data_source.py", "infrastructure/synapse_metric_source.py"]
CLIENTS = ("httpx", "requests", "urllib", "aiohttp", "socket")


def test_only_the_laya_and_synapse_gateways_make_outside_calls():
    found = sorted(
        str(path.relative_to(SOURCE))
        for path in SOURCE.rglob("*.py")
        if any(f"import {client}" in path.read_text() or f"from {client}" in path.read_text() for client in CLIENTS)
    )
    assert found == CALLERS
