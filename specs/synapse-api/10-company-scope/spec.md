# synapse-api/10 company-scope

## Goal
Every synapse-api read can be limited to one of the user's companies or to all of them (the group view), and no widget or figure silently drops sales in another currency.

## Behavior
- **Scope.** Every route that reads butterfly (metrics, compare, month, records, rankings, totals, the catalog widgets) takes `company` (a company id such as `sabinsa`, or `all`, default `all`). The company must be one of the user's companies from the token, otherwise `403 COMPANY_NOT_ALLOWED`; `all` means all the user's companies (so a user with one company sees that company). The scope becomes a `CompanyCode` filter on every butterfly read (`or` of the user's codes for `all`); the browser never combines numbers across companies.
- **Registry.** `registry.toml` gets `company = "CompanyCode"` on every metric and record, and every summary `order` ends with `CompanyCode`, so paging by the whole key (butterfly contract) is stable. Rows keep summing per currency across the companies in scope; nothing is added across currencies.
- **Currency.** Totals, compare, month figures and trend reads already return one result per currency and stay that way. The catalog widgets, which show one number or series, take `currency` (default `USD`, the group's main currency), and the widget entry says which currency it shows; a widget never mixes currencies. The `INR` constant is removed from the widgets.
- **Records.** Contracts, deliveries, production orders and components carry `company_code` in the record graph, so a company's data does not mix with another's.
- **Mock source.** The mock sales source and metric source get a company and currency too, so the mock web flow works.

## Acceptance cases
- A user of `sabinsa` asking for `organica` gets `403`; `all` for that user equals `sabinsa`.
- A user of all three: `company=all` totals equal the three single-company totals added per currency.
- The butterfly request carries the right `CompanyCode` filter, and every summary `$orderby` ends with `CompanyCode`.
- A widget with `currency=INR` shows only INR rows, with `USD` only USD rows; the default is `USD` and the entry names it.
- The August story: for `company=sabinsa` and `USD`, August is 14.5% below July with Harborline Nutrition LLC about 80% of the change; for `all`, the same story is diluted and the rows add up. The butterfly scenario comparison tests are rewritten for one company and USD and keep their meaning.
- Existing route, cache and registry tests pass with the new parameters (the cache key includes company and currency).

## Out of scope
The company picker's use of the new parameter in synapse-web (a web phase), exchange rates and one reporting currency, intercompany eliminations, replacing the mock library with butterfly reads (its own phases), intent-api and sami-agents changes.

## Depends on
butterfly 12, workspace-api 04 (`Company.code`), auth-api 04.

## Open questions for the owner
- Is `USD` the right default currency for widgets, with a way to switch to `INR`, or should a widget show each currency as its own card?
- Should `all` for a user with several companies be the default on the dashboard, or the company picked in the header?
