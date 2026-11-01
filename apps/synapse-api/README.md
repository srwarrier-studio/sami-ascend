# synapse-api

Backend for the management dashboard. This phase only reads sales data from SAP; use cases and routes come later.

## Sales source
`SalesSource` (in `domain/gateways`) has `daily_sales(start, end)`, `customer_sales(start, end)`, `material_sales(start, end)` and `high_value_orders(minimum, top)`. Dates are inclusive and rows come back ordered by date, one per day per currency. High-value orders exclude cancelled ones, newest first.

- `ButterflySalesSource` calls the Sales OData V4 contract in `docs/sap/sales-contract.md`. Set `SAP_BASE_URL` (default: butterfly on `http://localhost:8003` with the contract root path).
- `MockSalesSource` holds the rows it is given; `fail()` makes every call raise `SapUnavailable`.
- `SapUnavailable` covers timeouts, connection errors, any status other than `200` and an unreadable body.

```python
from datetime import date
from synapse_api.infrastructure.butterfly_sales_source import ButterflySalesSource
from synapse_api.infrastructure.settings import Settings

source = ButterflySalesSource(Settings())
rows = source.daily_sales(date(2026, 10, 1), date(2026, 10, 27))
```

## Company scope and currency
Every read route takes `company` (`sabinsa`, `neutraceuticals`, `organica` or `all`, default `all`). `all` means every company in the user's token; a company the user does not have is `403 COMPANY_NOT_ALLOWED`, an unknown one is `422`, and a user with no companies gets `403`. The scope becomes a `CompanyCode` filter on every butterfly read through `for_companies(...)` on the sources and the catalog. Catalog data takes `currency` (default `DEFAULT_CURRENCY`, `USD`) and says which currency it shows; amounts of different currencies are never added.

## Test
```
uv run --package synapse-api --with pytest pytest apps/synapse-api -v
```
Tests never call the network; the butterfly source is tested with `httpx.MockTransport`.
