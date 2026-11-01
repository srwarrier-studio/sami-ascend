import json
from datetime import datetime, timezone
from pathlib import Path

from intent_api.domain.entities.match import Match
from intent_api.domain.gateways.unanswered_log import UnansweredLog


class JsonlUnansweredLog(UnansweredLog):
    def __init__(self, path: Path):
        self.path = path

    def record(self, question: str, match: Match) -> None:
        entry = {
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "question": question,
            "reason": match.reason,
            "domain": match.domain,
            "did_you_mean": list(match.did_you_mean),
        }
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def entries(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
