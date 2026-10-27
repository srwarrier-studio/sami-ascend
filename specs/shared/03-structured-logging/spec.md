# shared/03 structured-logging

## Goal
One small Python package that gives every API JSON logs on stdout with a request id that follows a request across services.

## Behavior
- Package `structured-logging` in `packages/structured-logging` (import `structured_logging`), flat like token-verification, standard library only plus Starlette (already via FastAPI).
- `setup_logging(service)` makes the root logger write one JSON object per line to stdout: `timestamp` (UTC, `Z`), `level`, `service`, `request_id`, `message`, and `exception` when present. Uvicorn loggers go through the same handler.
- `RequestIdMiddleware` (ASGI): uses the incoming `X-Request-ID` header if it is a short safe string (letters, digits, `-`, `_`, up to 64), else generates a UUID. Stores it in a `ContextVar`, returns it in the `X-Request-ID` response header.
- `get_request_id()` returns the current id, so a gateway can send it as `X-Request-ID` when it calls another service or butterfly.
- One access log line per request: method, path (no query string), status, duration in ms. Never headers, cookies, bodies or query strings.
- auth-api calls `setup_logging("auth-api")` and adds the middleware, as the first user.

## Acceptance cases
- A log line is valid JSON with the fields above; extra text with newlines stays on one line.
- An exception log carries `exception`.
- Request without the header gets a generated id; response echoes it; log lines in that request carry it.
- Request with a valid header keeps it; an invalid one (too long, spaces, newline) is replaced.
- The access log line has no query string, cookie or authorization value.
- Outside a request `request_id` is `null`.
- Existing auth-api tests still pass.

## Out of scope
Log shipping, retention, alerting, log viewer, tracing/OpenTelemetry, audit log, wiring into synapse-api and workspace-api (their phases), propagation helpers beyond `get_request_id()`.

## Depends on
Nothing.
