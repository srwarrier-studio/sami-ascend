import httpx
from structured_logging import get_request_id

from synapse_api.domain.errors import SapUnavailable

PAGE = 1000


class ODataReader:
    def __init__(self, base_url: str, timeout: float, transport: httpx.BaseTransport | None = None):
        self.client = httpx.Client(base_url=base_url, timeout=timeout, transport=transport)

    def all_rows(self, path: str) -> list[dict]:
        rows: list[dict] = []
        while True:
            page = self.get_rows(f"{path}&$top={PAGE}&$skip={len(rows)}")
            rows += page
            if len(page) < PAGE:
                return rows

    def get_rows(self, path: str) -> list[dict]:
        headers = {"Accept": "application/json"}
        if request_id := get_request_id():
            headers["X-Request-ID"] = request_id
        try:
            response = self.client.get(path, headers=headers)
        except httpx.TransportError as error:
            raise SapUnavailable(type(error).__name__) from error
        if response.status_code != 200:
            raise SapUnavailable(f"unexpected status {response.status_code}")
        try:
            return response.json()["value"]
        except (ValueError, KeyError, TypeError) as error:
            raise SapUnavailable("unreadable body") from error
