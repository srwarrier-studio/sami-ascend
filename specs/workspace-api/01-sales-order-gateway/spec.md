# workspace-api/01 sales-order-gateway

## Goal
workspace-api can create and list sales orders through a `SalesOrderGateway` interface, with a mock implementation for tests and an implementation that calls butterfly over OData V4.

## Behavior
- **Domain:** `SalesOrder`, `SalesOrderItem`, `NewSalesOrder`, `NewSalesOrderItem` (plain dataclasses, decimals as `Decimal`, dates as `date`), the `SalesOrderGateway` interface, and errors `SalesOrderRejected` (carries the `details` list: code, target, message), `SapUnavailable`.
- **Interface:** `create(order: NewSalesOrder) -> SalesOrder` and `list_recent(top: int, skip: int) -> SalesOrderPage` (orders newest first by `SalesOrder` descending, plus total count).
- **Use cases:** `CreateSalesOrder` and `ListSalesOrders`, one `execute` each. `ListSalesOrders` limits `top` to 1..100 (default 20) and `skip` to 0 or more.
- **Mock:** `MockSalesOrderGateway` keeps orders in memory, numbers them from `0000000001`, and can be told to reject with given details.
- **Butterfly gateway:** `POST SalesOrder` for create; `GET SalesOrder?$orderby=SalesOrder desc&$top&$skip&$count=true&$expand=_Item` for list. Base URL comes from `Settings` (`SAP_BASE_URL`, default the butterfly root). Sends `X-Request-ID` from `get_request_id()`.
- **Errors:** `400 VALIDATION_FAILED` becomes `SalesOrderRejected` with all details; connection error, timeout or `5xx` becomes `SapUnavailable`. Apps branch on `code`, never on `message`.
- **Logging:** `setup_logging("workspace-api")` at import (structured-logging, see `specs/notes.md`). No order content in logs.
- **Layout:** `domain`, `application`, `infrastructure`, `entrypoint` as in the constitution. No HTTP routes here (phase 02).
- **Dependencies:** `httpx` (already used in tests; becomes a runtime dependency, add to `tech-stack.md`), `structured-logging` (workspace package).

## Acceptance cases
- Mock: create returns the order with a number and status `A`; list returns newest first and the right total; `skip` and `top` page correctly.
- `ListSalesOrders` clamps or rejects `top` outside 1..100 and negative `skip` (reject with `ValueError`; routes turn it into 422 in phase 02).
- Butterfly gateway (tests use `httpx.MockTransport`, never the network): the create request body matches the contract example; a `201` maps to `SalesOrder` with items; a `400` with several details maps to one `SalesOrderRejected` with every detail in order; `503`, timeout and connection error map to `SapUnavailable`; list builds the expected query and maps `@odata.count`.
- Decimals stay exact (`"50.000"` becomes `Decimal("50.000")`).
- `X-Request-ID` is sent on both calls.

## Out of scope
Routes, authentication and roles (phase 02), change order (`PATCH`), reading a single order, retries, caching, identity decision (shared/04), audit log, running against real butterfly (shared/05).

## Depends on
butterfly 01-02 (done), shared 03 structured-logging (done).
