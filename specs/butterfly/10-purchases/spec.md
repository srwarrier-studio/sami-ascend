# butterfly/10 purchases

## Goal
Butterfly serves purchase values and several purchase stories with a written ground truth, so "why did purchases rise in a month" can be built and tested the same way as "why did sales fall".

## Behavior
### Contract (`docs/sap/drivers-contract.md`, changed first)
- `PurchaseDelivery` gains `NetAmount` (`Edm.Decimal` 15,2, ordered quantity times the net price) and `TransactionCurrency` (`Edm.String` 5, `INR`), after `OrderedQuantity`'s neighbours in the field table; the contract examples are updated.
- Three read-only summary entities in the drivers service, like the sales summaries, excluding cancelled purchase items, with the same query options and the whole key in the order: `PurchaseSummaryByDay` (`OrderDate`, `TotalNetAmount`, `OrderCount`, `Currency`), `PurchaseSummaryBySupplier` (adds `Supplier`, `SupplierName`), `PurchaseSummaryByMaterial` (adds `Material`, `MaterialDescription`, `TotalQuantity`, `QuantityUnit`). The date is the purchase `OrderDate`: a purchase counts in the month it was ordered.
- A `DeliveryStatus` `X` (cancelled) is added to the codes, used by one scenario.

### Data
- Each raw material has a net price per unit (fixed arithmetic) and one monthly purchase order per raw material as today; the amount is ordered quantity times price. Quantities, dates and statuses of every scenario that existed before this phase do not change.
- New events (domain, next to the butterfly 09 ones):
  - **purchase price change**: raw material, factor, from month (the price on orders from then on);
  - **purchase quantity change**: raw material, factor, from month and until month (orders larger or smaller, nothing else changes);
  - **demand growth**: product, factor, from date; sales orders of that product grow by the factor, its production orders plan the same factor more from the following month, its components' required quantity grow with them, and the purchase orders of the raw materials it uses grow from the month after that, so growth in sales can be followed down to purchases;
  - **supplier switch**: raw material, new supplier, price factor, from month (the purchase rows come from the other supplier).
- A scenario never changes data before its first event; the generator is still fixed arithmetic with no random numbers.

### Scenarios
| Name | Events | Written ground truth (the month to ask about is given) |
|------|--------|---------------------------------------------------------|
| `purchase-price-rise` | Steel coil price +20% from August 2026 | August purchase value rises because of price on Steel coil (supplier Doosan); quantity unchanged; no sales or production event |
| `stock-up` | Copper rod ordered quantity x1.6 in September 2026 only | September purchase value rises because of quantity on Copper rod; price unchanged; no production, sales or supplier event, nothing in the data explains why more was ordered |
| `demand-surge` | Steel plate sales +35% from 2026-06-15 (flows to production and to Steel coil purchases) | August purchase value rises through Steel coil quantity; chain: sales of Steel plate, then production order planned quantity, then component requirement, then the purchase; price unchanged |
| `quiet-purchases` | none | no month more than 5% from normal |
| `supplier-switch` (held back) | Bearing steel moves from Precision Bearings Co to Kalyani Wire Industries at +15% price from October 2026 | October purchases: one supplier lost, one new, price up on Bearing steel; no sales or production event |
| `double-cause` (held back) | Aluminium ingot price +25% from September 2026 and Wire rod ordered quantity x1.5 in September 2026 | both found, each tied to its own material; no event behind the quantity change |

- `BUTTERFLY_SCENARIO` accepts these names too; each has `scenarios/<name>.json` in the butterfly 09 format, extended with the metric (`sales` or `purchases`) and the cause types `purchase_price_change`, `purchase_quantity_change`, `demand_growth` and `supplier_switch`. Held-back files carry `"holdout": true`.
- The README lists the new scenarios and the purchase summaries.

## Acceptance cases
- The sales, contract, production and component data of every butterfly 09 scenario is unchanged (pinned by hashes per list); the delivery data changes only by the two new fields and its hash is re-pinned on purpose.
- Contract tests: the field table and every example in the drivers contract (including the new fields and summaries) match butterfly; the three purchase summaries equal the sums of the deliveries by day, supplier and material, without cancelled rows, and page like the sales summaries.
- For each new scenario, the facts in its ground truth hold in the data (change within its range, product or supplier split, effect type, events exist with the stated keys and dates, the not-to-blame events exist and have no effect, a quiet scenario has no month beyond 5%).
- `demand-surge`: the sales, production and purchase quantities all rise by the factor in the expected months and not earlier.
- The base history before the first event is identical across scenarios; the scenario list, held-back flags and ground truth files agree.
- Existing scenarios answer purchase questions sensibly: `august-contract` purchases do not move more than 5% in August.

## Out of scope
The agent, synapse-api reads of the purchase summaries (they come with the synapse-api registry), receipts per item, invoice values, exchange rates, writes, failure modes.

## Depends on
butterfly 08 and 09, `docs/ai-analysis.md`.
