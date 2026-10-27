import json
import logging
from datetime import datetime, timezone

from structured_logging.request_id import get_request_id


class JsonFormatter(logging.Formatter):
    def __init__(self, service: str):
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, timezone.utc)
        line = {
            "timestamp": timestamp.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "level": record.levelname,
            "service": self.service,
            "request_id": get_request_id(),
            "message": record.getMessage(),
        }
        if record.exc_info:
            line["exception"] = self.formatException(record.exc_info)
        return json.dumps(line)
