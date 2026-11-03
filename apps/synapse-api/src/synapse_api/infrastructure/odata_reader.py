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
            page, more = self.read_page(f"{path}&$top={PAGE}&$skip={len(rows)}")
            rows += page
            if not page or (len(page) < PAGE and not more):
                return rows

    def count(self, path: str) -> int:
        separator = "&" if "?" in path else "?"
        body = self.read_body(f"{path}{separator}$count=true&$top=0")
        try:
            return int(body["@odata.count"])
        except (KeyError, TypeError, ValueError) as error:
            raise SapUnavailable("unreadable count") from error

    def get_rows(self, path: str) -> list[dict]:
        return self.read_page(path)[0]

    def read_page(self, path: str) -> tuple[list[dict], bool]:
        body = self.read_body(path)
        try:
            return body["value"], "@odata.nextLink" in body
        except (KeyError, TypeError) as error:
            raise SapUnavailable("unreadable body") from error

    def read_body(self, path: str) -> dict:
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
            return response.json()
        except ValueError as error:
            raise SapUnavailable("unreadable body") from error


def company_clause(field: str, companies: tuple[str, ...] | None) -> str:
    if companies is None:
        return ""
    return "%20and%20(" + "%20or%20".join(f"{field}%20eq%20'{code}'" for code in companies) + ")"
