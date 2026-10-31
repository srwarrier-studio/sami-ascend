# butterfly

Mock SAP. Serves the Sales OData V4 contract in `docs/sap/sales-contract.md` and the drivers contract in `docs/sap/drivers-contract.md` from seed data, so the apps can be built before the real RAP services exist. No auth, no database; data resets on restart. All data is invented.

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
- Summaries: `SalesSummaryByDay`, `SalesSummaryByCustomer`, `SalesSummaryByMaterial`, read-only, computed from the orders on every request, cancelled (`X`) orders left out; same query options as `SalesOrder` except `$expand`
- Writes: `POST SalesOrder` (deep insert, `201` + `Location`) and `PATCH SalesOrder('key')` (only `RequestedDeliveryDate`, needs `If-Match`)
- Small seed (`BUTTERFLY_SEED=small`): 30 orders over the last 10 days, built from today's date. New orders continue from `0000012031`; they live in memory until restart.
- Reference data: customers `0000100001` to `0000100005`; materials `RM-1001` to `RM-1004` in `KG`, `RM-1005` and `RM-1006` in `EA`; currency `INR`.

## Drivers service
Second read-only service on `/sap/opu/odata4/sap/zui_drivers_o4/srvd_a2x/sap/zdrivers/0001/`: `SalesContract`, `PurchaseDelivery`, `ProductionOrder`, `ProductionOrderComponent` (fields in `docs/sap/drivers-contract.md`). Same query options as the summaries; `$expand` and writes are refused.

```
curl "http://localhost:8003/sap/opu/odata4/sap/zui_drivers_o4/srvd_a2x/sap/zdrivers/0001/PurchaseDelivery?\$filter=Material%20eq%20'RAW-2002'&\$orderby=PromisedDeliveryDate%20desc&\$top=3"
```

## Seeds
`BUTTERFLY_SEED=story` (the default) serves 14 months of sales (about 1,360 orders from 2025-09-01 to today) plus contracts, purchase deliveries, production orders and components, built so that sales fall in August 2026 for known reasons: Acme Industries' contract ended on 12 July and was not renewed until 14 September, and Doosan Metals delivered Steel coil 12 days late, which delayed Steel plate production. Two events (a late copper rod delivery and a bearing machine breakdown, both in May) did not affect sales. The story is described in `docs/ai-analysis.md` section 7 and pinned by `tests/test_story_ground_truth.py`. `BUTTERFLY_SEED=small` serves the old 30 orders and an empty drivers service; anything else stops the start with a message. New orders continue after the last seeded number.

## Scenarios
`BUTTERFLY_SCENARIO` chooses the story served with `BUTTERFLY_SEED=story` (default `august-contract`); an unknown name stops the start with the list. Each scenario is a set of events applied to the same 14-month base history (`domain/entities/scenario.py`, list in `infrastructure/memory/scenarios.py`) and has a written ground truth in `scenarios/<name>.json`: month to ask about, expected change ranges, causes that must be found (with keys), things that must not be blamed, and whether anything stays unexplained.

| Name | What happens | Ground truth |
|------|--------------|--------------|
| `august-contract` | the story above | Acme's contract `0040000127`, the late steel coil `4500001207` and production order `0001000417`; the May decoys are not to blame |
| `price-cut` | Steel rod 12mm price down 15% from 2026-08-01 | value falls on that product, volume does not; no contract, supply or production event |
| `supplier-no-effect` | Steel coil 12 days late and Steel plate production 14 days late in July, orders unchanged | no drop; the delays exist and have no effect |
| `customer-lost` | Eastern Castings stops ordering from 2026-08-10, contract still valid | Eastern is the biggest mover; nothing explains it |
| `breakdown-shortfall` | Bearing 6204 production 10 days late in July (`MACHINE_BREAKDOWN`), half the bearing orders of Bharat, Cauvery and Deccan missing until 2026-08-15 | production order `0001000420`; no supplier delay |
| `quiet-month` | nothing | no month more than 5% from normal |
| `two-causes` (held back) | Deccan's contract ends 2026-07-20; Copper rod 10 days late with copper wire orders halved | contract `0040000152` and delivery `4500001208`, each tied to its own customer or product |
| `cancellations` (held back) | Cauvery cancels 40% of its August orders | the cancelled orders, not a contract or supply event |

Purchase scenarios (ground truth has `"metric": "purchases"`; a purchase counts in the month it was ordered, and orders are placed about the 24th of the month before delivery):

| Name | What happens | Ground truth |
|------|--------------|--------------|
| `purchase-price-rise` | Steel coil price +20% on orders from 2026-08-01 | August value up on that material by price; quantity unchanged |
| `stock-up` | Copper rod ordered 1.6 times in September | September value up by quantity on Copper rod; price unchanged; nothing in the data says why |
| `demand-surge` | Steel plate sales +35% from 2026-06-15, flowing to production plans from July and to Steel coil orders from August | August purchases up through Steel coil quantity; the chain is sales, production order, component, purchase |
| `quiet-purchases` | nothing | no month more than 5% from normal |
| `supplier-switch` (held back) | Bearing steel moves from Precision Bearings Co to Kalyani Wire Industries at +15% from October | October: one supplier lost, one gained, price up on Bearing steel |
| `double-cause` (held back) | Aluminium ingot price +25% and Wire rod quantity x1.5 in September | both found, each tied to its own material |

Purchase summaries (drivers service): `PurchaseSummaryByDay`, `PurchaseSummaryBySupplier` and `PurchaseSummaryByMaterial`, one row per order date and key, cancelled (`X`) items left out; `PurchaseDelivery` has `NetAmount` and `TransactionCurrency`.

Held-back scenarios are marked `"holdout": true`; tuning of the agent must not read them. Tests: `tests/test_scenario_events.py` and `test_purchase_events.py` (events), `test_purchase_summaries.py` (summaries), `test_scenario_ground_truth.py` (the data holds each truth), `test_scenario_service.py` (switch, contracts, agreement).

Not yet: delays and failures (butterfly/04), `$metadata`.

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
Today's totals then include it: `curl "http://localhost:8003/sap/opu/odata4/sap/zui_sales_o4/srvd_a2x/sap/zsales/0001/SalesSummaryByDay?\$orderby=OrderDate%20desc&\$top=1"`

Mistakes come back as `400 VALIDATION_FAILED` with one entry per problem in `details`.

## Test
```
uv run --package butterfly --with pytest --with httpx pytest apps/butterfly -v
```
`test_contract.py` reads the field tables and examples from the contract file, so a change to the contract that butterfly does not follow fails a test.
