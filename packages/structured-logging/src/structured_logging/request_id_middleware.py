import logging
import re
import time
import uuid

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from structured_logging.request_id import request_id_var

HEADER = "x-request-id"
SAFE_REQUEST_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")

access_logger = logging.getLogger("access")


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = Headers(scope=scope).get(HEADER, "")
        request_id = incoming if SAFE_REQUEST_ID.fullmatch(incoming) else str(uuid.uuid4())
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        status = 500

        async def send_with_request_id(message: Message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                MutableHeaders(scope=message)[HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000
            access_logger.info(
                "%s %s %s %.1fms", scope["method"], scope["path"], status, elapsed_ms
            )
            request_id_var.reset(token)
