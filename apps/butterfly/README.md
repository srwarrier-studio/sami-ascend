# butterfly

Mock SAP. Serves the Sales OData V4 contract in `docs/sap/sales-contract.md` and the drivers contract in `docs/sap/drivers-contract.md` from seed data, so the apps can be built before the real RAP services exist. No auth. Data lives in a SQLite file (see Storage). All data is invented.

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
Second read-only service on `/sap/opu/odata4/sap/zui_drivers_o4/srvd_a2x/sap/zdrivers/0001/`: `SalesContract`, `PurchaseDelivery`, `CustomerInvoice`, `ProductionOrder`, `ProductionOrderComponent` (fields in `docs/sap/drivers-contract.md`). Receivables are read through `ReceivablesSummary`, `ReceivablesByCustomer` and `ReceivablesAgeing`, measured on the day in the custom parameter `AsOfDate` (default today, a bad date is `400`); invoices are one per non-cancelled sales order, with payment terms and delays fixed per customer so every ageing bucket has data and one customer never pays. Same query options as the summaries; `$expand` and writes are refused.

```
curl "http://localhost:8003/sap/opu/odata4/sap/zui_drivers_o4/srvd_a2x/sap/zdrivers/0001/PurchaseDelivery?\$filter=Material%20eq%20'RAW-2002'&\$orderby=PromisedDeliveryDate%20desc&\$top=3"
```

## Inventory service
Third read-only service on `/sap/opu/odata4/sap/zui_inventory_o4/srvd_a2x/sap/zinventory/0001/`, specified in `docs/sap/inventory-contract.md`: `MaterialStock` (stock on hand per material and storage location, with a derived `StockStatus` of `O`, `L` or `Z`) and `StockMovement` (goods movements with their entry time), plus the summaries `StockSummaryByWarehouse`, `StockSummaryByMaterialGroup`, `StockSummaryByStatus`, `StockValueByMonth`, `StockMovementSummaryByDay` and `StockMovementSummaryByHour`. Same query options as the other services; `$expand` and writes are refused.

The stock is generated from the data butterfly already holds, so every number can be explained: raw material receipts are the purchase deliveries, finished product receipts are the production orders, issues are the production order components and the sales order items, opening stock is posted as an initial entry (`561`), and about one material in nine is counted down to zero today (`702`). Stock is valued at a standard price per material in rupees. `BUTTERFLY_SEED=small` has no stock. The material groups and storage locations are master data and are always present.

## Production service
Fourth read-only service on `/sap/opu/odata4/sap/zui_production_o4/srvd_a2x/sap/zproduction/0001/`, specified in `docs/sap/production-contract.md`: `ProductionConfirmation` (what one work center produced in one shift: yield, scrap, target, scrap reason, valued at the standard price) and `WorkCenterDowntime` (stoppages by cause), plus the summaries `ProductionSummaryByDay`, `DowntimeSummaryByDay`, `ScrapSummaryByDay` and `OutputSummaryByLineShift`. Equipment effectiveness is worked out by the consumer from `ProductionSummaryByDay`. Same query options as the other services; `$expand` and writes are refused.

The shop floor is generated from the production orders, so it ties out: the yields of a completed order add up to its confirmed quantity and the targets to its planned quantity, every delayed order has a stoppage of its cause with 8 hours for each day it ran late, each order changes over on its first day and each line is maintained once a month. Orders that have not started have no confirmations. `BUTTERFLY_SEED=small` has no shop floor; the work centers are master data and are always present.

## Export service
Fifth read-only service on `/sap/opu/odata4/sap/zui_export_o4/srvd_a2x/sap/zexport/0001/`, specified in `docs/sap/export-contract.md`: `ExportShipment` (one outbound delivery of an order sold abroad, with destination country, transport mode, expected and actual arrival, and the value in rupees and in the order currency) and the summaries `ExportSummaryByDay`, `ExportSummaryByDestination` and `ExportSummaryByMode`. Same query options as the other services; `$expand` and writes are refused.

Shipments are generated with the seed from the orders that are not cancelled and not sold to `IN`: they ship on the requested delivery date, about 60% by sea, 25% by air, 15% by road, and a shipment whose arrival is after today is in transit. An order created through the API is part of the sales data at once (the sales summaries show it) but does not become a shipment, stock movement or invoice: those are generated from the seed's own orders only. `BUTTERFLY_SEED=small` has no shipments.

## Finance service
Sixth read-only service on `/sap/opu/odata4/sap/zui_finance_o4/srvd_a2x/sap/zfinance/0001/`, specified in `docs/sap/finance-contract.md`: `CashPayment` (money received from customers for cleared invoices, paid to vendors thirty to forty-five days after delivery, and the monthly running costs in six categories), with the summaries `CashSummaryByDay` and `ExpenseSummaryByDay`. Amounts are in rupees with the document amount beside them. Payments are derived from the invoices and purchase deliveries with the other documents, so they follow orders created through the API; the small seed has none.

## Purchase order service
`API_PURCHASEORDER_2` (V4) at `/sap/opu/odata4/sap/api_purchaseorder_2/srvd_a2x/sap/purchaseorder/0001/`: reads of `PurchaseOrder`, `PurchaseOrderItem` and `PurchaseOrderScheduleLine` with the usual query options. `POST PurchaseOrder` (deep insert of `_PurchaseOrderItem`, from `PurchaseRequisition` + `PurchaseRequisitionItem` or `Material` + `Plant` + `OrderQuantity`; optional `Idempotency-Key`) answers `201`; `PATCH PurchaseOrderItem(...)` with `{"PurchasingDocumentDeletionCode": "L"}` and `If-Match` (the `ETag` header of a single read) deletes an item. Orders are the rows of the purchase summaries, so they change the figures synapse reads.

## Storage
Butterfly keeps its data in SQLite tables (orders, drivers, master data, stock) behind the repository interfaces, and answers `$filter`, `$orderby`, `$top`, `$skip`, `$count` and `$select` with SQL (values are bound parameters, column names come from the field whitelists). The summaries are SQL views and the receivables entities are queries with a bound `AsOfDate`; each is one file in `src/butterfly/infrastructure/sqlite/views/`, named after its OData entity.

- `BUTTERFLY_DB` is the file, default `apps/butterfly/butterfly.db` (ignored by git). `:memory:` keeps nothing between restarts.
- Money is stored as integer cents and quantities as integer thousandths, so sums are exact; the repositories convert to and from `Decimal`.
- At start the seed (`BUTTERFLY_SEED`, `BUTTERFLY_SCENARIO`) is written into the file when the file is empty, or the seed, the scenario or the day changed. The seeds are built relative to today, so a new day moves the seeded data; orders created through the API are kept and the numbers continue after them. Delete the file to start clean.
- The in-memory repositories remain as test doubles. `BUTTERFLY_STORE=sqlite pytest apps/butterfly/tests` runs every test against SQLite instead.

## Seeds
`BUTTERFLY_SEED=story` (the default) serves 14 months of data (about 4,100 orders from 2025-09-01 to today) for the three group companies `INA1` (Sami-Sabinsa Group, herbal extracts, exports in USD), `INA2` (Sami Nutraceuticals, probiotics and finished products, USD and INR) and `INA3` (Organica Aromatics, aroma chemicals, USD and INR), each with its own customers, products, suppliers and numbers, plus contracts, invoices, purchase deliveries, production orders and components. The story and every scenario event belong to `INA1`; the other two companies stay quiet. In the story, sales of `INA1` fall in August 2026 for known reasons: Harborline Nutrition LLC's contract ended on 12 July and was not renewed until 14 September, and Deccan Agro Growers Cooperative delivered Black pepper, whole 12 days late, which delayed Piperine extract 95% production. Two events (a late Frankincense resin delivery and a Probiotic capsule machine breakdown, both in May) did not affect sales. Amounts are in each customer's currency (`USD` or `INR`) and every row has a `CompanyCode`; read one company with `$filter=CompanyCode eq 'INA1'`. The story is described in `docs/ai-analysis.md` section 7 and pinned by `tests/test_story_ground_truth.py`. `BUTTERFLY_SEED=small` serves the old 30 orders and an empty drivers service; anything else stops the start with a message. New orders continue after the last seeded number.

## Scenarios
`BUTTERFLY_SCENARIO` chooses the story served with `BUTTERFLY_SEED=story` (default `august-contract`); an unknown name stops the start with the list. Each scenario is a set of events applied to the same 14-month base history (`domain/entities/scenario.py`, list in `infrastructure/memory/scenarios.py`) and has a written ground truth in `scenarios/<name>.json`: month to ask about, expected change ranges, causes that must be found (with keys), things that must not be blamed, and whether anything stays unexplained.

| Name | What happens | Ground truth |
|------|--------------|--------------|
| `august-contract` | the story above | Harborline's contract `0040000127`, the late Black pepper, whole delivery `4500001207` and production order `0001000417`; the May decoys are not to blame |
| `price-cut` | Curcumin extract 95% price down 15% from 2026-08-01 | value falls on that product, volume does not; no contract, supply or production event |
| `supplier-no-effect` | Black pepper, whole 12 days late and Piperine extract 95% production 14 days late in July, orders unchanged | no drop; the delays exist and have no effect |
| `customer-lost` | Lakeshore Supplements Inc stops ordering from 2026-08-10, contract still valid | Lakeshore is the biggest mover; nothing explains it |
| `breakdown-shortfall` | Probiotic capsule 10B CFU production 10 days late in July (`MACHINE_BREAKDOWN`), half the Probiotic capsule 10B CFU orders of Eurovita, Nordic and Pacific missing until 2026-08-15 | production order `0001000420`; no supplier delay |
| `quiet-month` | nothing | no month more than 5% from normal |
| `two-causes` (held back) | Pacific's contract ends 2026-07-20; Frankincense resin 10 days late with Boswellia extract 65% orders halved | contract `0040000152` and delivery `4500001208`, each tied to its own customer or product |
| `cancellations` (held back) | Nordic cancels 40% of its August orders | the cancelled orders, not a contract or supply event |

Purchase scenarios (ground truth has `"metric": "purchases"`; a purchase counts in the month it was ordered, and orders are placed about the 24th of the month before delivery):

| Name | What happens | Ground truth |
|------|--------------|--------------|
| `purchase-price-rise` | Black pepper, whole price +20% on orders from 2026-08-01 | August value up on that material by price; quantity unchanged |
| `stock-up` | Frankincense resin ordered 1.6 times in September | September value up by quantity on Frankincense resin; price unchanged; nothing in the data says why |
| `demand-surge` | Piperine extract 95% sales +35% from 2026-06-15, flowing to production plans from July and to Black pepper, whole orders from August | August purchases up through Black pepper, whole quantity; the chain is sales, production order, component, purchase |
| `quiet-purchases` | nothing | no month more than 5% from normal |
| `supplier-switch` (held back) | Gelatin capsule shells moves from Pack-Rite Industries Pvt Ltd to Malnad Botanicals Pvt Ltd at +15% from October | October: one supplier lost, one gained, price up on Gelatin capsule shells |
| `double-cause` (held back) | Withania root, dried price +25% and Laminate film for sachets quantity x1.5 in September | both found, each tied to its own material |

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
