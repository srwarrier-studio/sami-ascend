# synapse-api/08 compare

## Goal
synapse-api answers "where did the change come from" for any two periods and any dimension, and returns a month's figure with its trend, so the AI analysis finds facts from one generic read instead of one endpoint per question.

## Behavior
Two new read routes on the sales router under `/v1/synapse`. Same roles as the other sales routes (`MANAGEMENT`, `ADMIN`), same 5-minute cache, same error format (`INVALID_QUERY` is 422 and `SAP_UNAVAILABLE` is 503, as in the other routes). Built from the existing `SalesSource` reads, so butterfly and the real SAP views both work. All amounts are net sales without cancelled orders, per currency (a currency is a separate result, as in the top lists).

### `GET /sales/compare`
Query: `start`, `end` (the period), `compare_start`, `compare_end` (the period to compare with), all dates; optional `by` (`customer` or `material`, none means totals only); `top` (1 to 50, default 10).
- A period is valid when `start <= end` and it is at most 400 days. The two periods may have different lengths; no date or length is assumed (a month, a week or a year all work). Anything invalid, or an unknown `by`, is `INVALID_QUERY` 422.
- Response, per currency: `totals` with `current`, `previous`, `change` (current minus previous) and `change_percent` (null when previous is 0).
- With `by`, `rows` ordered by absolute change, largest first, at most `top`, then one `other` row that sums the rest (left out when nothing remains), so rows always add up to `totals.change`. A row has `key`, `name`, `current`, `previous`, `change`, `share_of_change_percent` (its change over the total change, null when the total change is 0).
- A key present in only one period is a row with 0 for the other (a lost customer has `current` 0; a new one `previous` 0).
- With `by=material` a row also has `quantity_current`, `quantity_previous`, `unit`, `price_current`, `price_previous` (net amount over quantity, 4 decimals, null when the quantity is 0), and `volume_effect` and `price_effect`. `volume_effect = (q_cur - q_prev) * price_prev`, `price_effect = change - volume_effect`, so they add up to `change`. When `price_prev` is unknown (nothing sold before) the whole change is volume effect.
- `by=customer` has no quantity, so no volume or price split.

### `GET /sales/month`
Query: `month` (`YYYY-MM`), `trend` (1 to 24, default 6).
- Response, per currency: `figure` (`net_amount`, `order_count`), `previous_change_percent` against the month before (null when that is 0 or has no data), `complete` (false when the month is the current one and not over), and `trend`: the `trend` months ending with `month`, oldest first, each `month` and `net_amount`.
- A month after the current month is `INVALID_QUERY`. With no data in the window the list is empty.

## Acceptance cases
- Against butterfly's `august-contract` data: August against July totals -14.5%; by customer, Acme's change is about 80% of it and the rows sum to `totals.change` with `other` included.
- Against `price-cut`: by material, Steel rod's `price_effect` is about -14% of its previous value (the total change is -19% with volume -4.7%) and `volume_effect` is small; the other materials have almost no price effect.
- Against `customer-lost`: by customer, Eastern Castings is the first row and its `current` is 0 for a period after its last order.
- A key in only one period is a row; with `by=material` and no earlier sale, `price_effect` is 0 and `volume_effect` equals `change`.
- No `by`: only `totals`. `top=1` gives one row plus `other`. Equal changes order by key.
- Two currencies give two separate results.
- Invalid: `start` after `end`, a period over 400 days, `top=0` or 51, unknown `by`, missing date, bad date format.
- `/sales/month`: figure, change against the previous month, six trend months oldest first; `complete` false for the current month; a future month and `trend=25` are invalid; a month with no data gives an empty list, as month-on-month does.
- A second identical call inside 5 minutes reads from the cache (no new source reads); a different query does not.
- Roles: `MANAGEMENT` and `ADMIN` pass, other roles get 403, no cookie 401.
- A `SapUnavailable` is the usual 503 and nothing partial is returned.

## Out of scope
Metrics other than net sales (quantity, order count), dimensions other than customer and material, drilling into a dimension inside another (customer by material), caching beyond the existing 5 minutes, company filtering, the contract and events read (synapse-api 09), anything in sami-agents or synapse-web.

## Depends on
synapse-api 07 (complete reads), butterfly 09 (scenarios for the acceptance cases; unit tests use the mock sales source).
