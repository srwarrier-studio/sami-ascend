# butterfly

Mock SAP. Serves the Sales OData V4 contract in `docs/sap/sales-contract.md` from seed data, so the apps can be built before the real RAP services exist. No auth, no database; data resets on restart.

## Run
```
uv run --package butterfly butterfly
```
Listens on `http://localhost:8003`. Root path:
`/sap/opu/odata4/sap/zui_sales_o4/srvd_a2x/sap/zsales/0001/`

```
curl "http://localhost:8003/sap/opu/odata4/sap/zui_sales_o4/srvd_a2x/sap/zsales/0001/SalesOrder?\$filter=OverallStatus%20eq%20'A'&\$top=3&\$count=true"
```

## Served
- Reads: `SalesOrder`, `SalesOrder('key')` (with `@odata.etag`), `SalesOrder('key')/_Item`
- Query options: `$filter`, `$select`, `$orderby`, `$top`, `$skip`, `$count`, `$expand=_Item`
- Writes: `POST SalesOrder` (deep insert, `201` + `Location`) and `PATCH SalesOrder('key')` (only `RequestedDeliveryDate`, needs `If-Match`)
- Seed: 30 orders over the last 10 days, built from today's date. New orders continue from `0000012031`; they live in memory until restart.
- Reference data: customers `0000100001` to `0000100005`; materials `RM-1001` to `RM-1004` in `KG`, `RM-1005` and `RM-1006` in `EA`; currency `INR`.

Not yet: summaries (butterfly/03), delays and failures (butterfly/04), `$metadata`.

## Try the flow
```
R=http://localhost:8003/sap/opu/odata4/sap/zui_sales_o4/srvd_a2x/sap/zsales/0001/SalesOrder

curl -X POST $R -H 'Content-Type: application/json' -d '{
  "SalesOrderType": "OR", "SoldToParty": "0000100002", "TransactionCurrency": "INR",
  "_Item": [{"Material": "RM-1003", "Quantity": "12.5", "QuantityUnit": "KG"}]}'

curl "$R?\$filter=CreatedByUser%20eq%20'BUTTERFLY'&\$expand=_Item"

curl -X PATCH "$R('0000012031')" -H 'Content-Type: application/json' \
  -H 'If-Match: W/"<etag from the POST response>"' -d '{"RequestedDeliveryDate": "2030-01-15"}'
```
Mistakes come back as `400 VALIDATION_FAILED` with one entry per problem in `details`.

## Test
```
uv run --package butterfly --with pytest --with httpx pytest apps/butterfly -v
```
`test_contract.py` reads the field tables and examples from the contract file, so a change to the contract that butterfly does not follow fails a test.
