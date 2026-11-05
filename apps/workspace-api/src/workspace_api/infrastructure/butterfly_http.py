import httpx
from structured_logging import get_request_id

from workspace_api.domain.errors import SapNotReached, SapOutcomeUnknown


def send(client: httpx.Client, method: str, path: str, **kwargs) -> httpx.Response:
    headers = {"Accept": "application/json"}
    if request_id := get_request_id():
        headers["X-Request-ID"] = request_id
    try:
        response = client.request(method, path, headers=headers, **kwargs)
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout) as error:
        raise SapNotReached(type(error).__name__) from error
    except httpx.TransportError as error:
        raise SapOutcomeUnknown(type(error).__name__) from error
    if response.status_code in (429, 503):
        raise SapNotReached(f"status {response.status_code}")
    if response.status_code >= 500:
        raise SapOutcomeUnknown(f"status {response.status_code}")
    return response
