# workspace-api

Workflow backend for department users. This phase has the SAP gateway only; HTTP routes come in workspace-api/02.

## Gateway
`SalesOrderGateway` (in `domain/gateways`) has `create(NewSalesOrder)` and `list_recent(top, skip)`. Use cases `CreateSalesOrder` and `ListSalesOrders` wrap it.

- `ButterflySalesOrderGateway` calls the Sales OData V4 contract in `docs/sap/sales-contract.md`. Set `SAP_BASE_URL` (default: butterfly on `http://localhost:8003` with the contract root path).
- `MockSalesOrderGateway` keeps orders in memory for tests; `reject_with(details)` makes the next creates fail.
- `SalesOrderRejected` carries every validation detail (branch on `code`); `SapUnavailable` covers timeouts, connection errors and `5xx`.

## Test
```
uv run --package workspace-api --with pytest pytest apps/workspace-api -v
```
Tests never call the network; the butterfly gateway is tested with `httpx.MockTransport`.
