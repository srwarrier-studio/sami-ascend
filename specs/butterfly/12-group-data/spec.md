# butterfly/12 group-data

## Goal
Butterfly's sample data looks like the Sami group (three companies in one SAP client, mostly export sales in USD and INR, herbal extract, nutraceutical and aroma chemical products) instead of steel and bearings, and every row says which company it belongs to.

## Behavior
### Companies (`docs/sap/`, changed first)
- Every entity in the sales service and the drivers service (orders, contracts, deliveries, production orders, components, invoices; items reach their company through their order) and every summary gains `CompanyCode` (`Edm.String` 4, not nullable), as a field to read, `$filter` and `$select`, and as part of every summary key. A summary without a company filter still returns one row per company, so a consumer adds them up for the group view; butterfly never sums across companies.
- `CompanyCode` values are the owner's real codes `INA1`, `INA2`, `INA3`; which company is which is assumed for now: `INA1` Sami-Sabinsa Group Limited, `INA2` Sami Nutraceuticals Private Limited, `INA3` Organica Aromatics Private Limited. They map to the auth-api companies `sabinsa`, `neutraceuticals`, `organica`. The real codes go into `docs/sap/consultant-questions.md`.
- A create takes `CompanyCode` (a change cannot move an order to another company); a missing or unknown code is a validation error.

### Data (invented names only; no real customers, suppliers or amounts)
- **Products** per company, replacing the steel list: Sabinsa sells standardised herbal and spice extracts and fine chemicals; Nutraceuticals sells finished nutraceutical ingredients and probiotics; Organica sells aroma chemicals. About 6 materials per company, each with a unit (`KG`, `MT`) and a price.
- **Customers**: about 6 per company, invented, mostly export buyers across several countries (the USA the largest), a small domestic share. A customer has a country; the country is a new field `Country` (`Edm.String` 2, ISO code) on the order and the invoice, taken from the customer (not written by the client).
- **Currency**: export sales and invoices in `USD`, domestic in `INR`; purchases of imported raw material in `USD`, local purchases in `INR`. Rows keep one `TransactionCurrency`; no exchange rate is added.
- **Suppliers and raw materials**: contract-farmed turmeric and black pepper in India (INR), imported turmeric (USD), solvents and chemical intermediates; each company buys what it makes products from, and production orders and components follow the new products.
- **Invoices**: payment terms and delays per customer follow the new customers (export buyers on longer terms; one customer who never pays; one slow payer), still fixed arithmetic.
- The generator stays fixed arithmetic with no random numbers, and the event machinery and scenario list from butterfly 08 to 11 keep working: the same scenarios exist, with their events pointing at the new customers, materials and suppliers, and their ground truth files rewritten with the new names.

## Acceptance cases
- Every row of every entity and summary has a `CompanyCode` among the three; `$filter=CompanyCode eq 'INA2'` returns only that company, and the per-company totals of a summary add up to the all-company data.
- Each company has its own products, customers and suppliers; no product, customer or supplier appears under two companies.
- No steel, bearing or old customer/supplier name remains in the data, scenarios, README or tests.
- A USD row and an INR row both exist for sales, purchases and invoices, and every summary keeps them in separate rows.
- The contract field tables, the examples and the data agree (the contract tests); the ground truth of every scenario holds for the new names, including the held-back ones.
- Data hashes are re-pinned on purpose, once, in the task that changes the data; a scenario never changes data before its first event.
- Creating a sales order with no or an unknown `CompanyCode` fails with a validation error naming the field.

## Out of scope
Exchange rates and a reporting currency, intercompany sales between the three companies, the group view and company filtering in synapse-api, auth-api, the web apps and intent-api (follow-up phases), replacing the synapse-api and UI mock library with butterfly reads (separate phases), real SAP codes and master data.

## Depends on
butterfly 11 (receivables), `docs/sap/consultant-questions.md`.

## Open questions for the owner
- Which of `INA1`, `INA2`, `INA3` is which company? The spec assumes the order Sabinsa, Nutraceuticals, Organica.
- Which product families should each company have (the spec guesses extracts for Sabinsa, finished ingredients and probiotics for Nutraceuticals, aroma chemicals for Organica)?
- Should intercompany sales (one group company selling to another) exist in the sample data, or stay out until finance answers?
