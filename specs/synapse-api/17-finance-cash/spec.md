# synapse-api/17 finance-cash

## Goal
The five Finance cash widgets of the catalog read butterfly's finance service (`docs/sap/finance-contract.md`) instead of `mock_library.json`, and a board with them gets a cash topic in its overview. After this no widget is served from fixed numbers.

## Behavior
- **Gateway.** `FinanceSource` with a butterfly implementation reading `CashSummaryByDay`, `ExpenseSummaryByDay` and `CashPayment` (direction `I`), scoped by company, and a mock for tests. New settings `FINANCE_BASE_URL` and `MONTHLY_COLLECTION_TARGET` (default 30,000,000).
- **Widgets, same ids so saved boards keep working** (amounts are in rupees, the company currency of the contract):
  - `fin-collections` KPI: money received so far this month against the same days last month, with day ranges, partial note and six-month trend like the sales KPIs.
  - `fin-collection-target` gauge: money received this month against the target.
  - `fin-cashflow` line: cash in against cash out for each of the last six months.
  - `fin-payments` table: the latest payments received (payment, customer, date, amount), top 5.
  - `fin-expenses` donut: running costs by category over the last 90 days.
- **Overview.** A cash topic when the board has one of these widgets, at most two sentences, after Exports:
  1. Headline (always): `Collections this month are <amount> (<days>[, N of M days so far]), up|down X% on <days>.`
  2. With `fin-collection-target`: `Collections are <n>% of the <target> monthly target.`
  3. With `fin-cashflow`: `This month <in> came in and <out> went out, <diff> more in than out|more out than in.`
  4. With `fin-expenses`: `<Category> is the largest running cost over the last 90 days: <amount> (<share>% of costs).`
- Nothing already served changes shape; the mock library no longer lists or serves a cash widget.

## Acceptance cases
- `fin-collections` gives value, delta, period, comparedWith, partial note and trend like `sales-month`, counting only incoming payments.
- `fin-cashflow` has six months with cash in and, as the compare series, cash out.
- `fin-payments` lists only incoming payments, latest first. `fin-expenses` names categories and leaves out zero ones.
- The overview respects the two-sentence cap and is left out when the board has no cash widget or no finance source.
- With butterfly 20 running the widgets match direct reads and the catalog has no duplicate id.

## Out of scope
Cash forecasting, bank balances, any butterfly change.

## Depends on
butterfly 20 (finance service), synapse-api 16.
