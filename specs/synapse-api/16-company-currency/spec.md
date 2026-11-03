# synapse-api/16 company-currency

## Goal
The sales, purchase and receivables widgets show the whole business in rupees by reading the company-currency amounts that butterfly 19 serves, so export orders (all in dollars) and dollar purchases and receivables are no longer left out of the INR view.

## Why
After the default currency became INR, the sources kept only rows whose document currency was INR. About four in five orders are in dollars, so the sales, top-customer, purchase and receivables widgets showed a fraction of the business, and a new dollar order did not show in the rupee receivables (found in butterfly 18). The conversion belongs in butterfly and later SAP, which hold the document rate, not in synapse-api.

## Behavior
- The butterfly sources read the `...Local` amounts and `LocalCurrency` (rupees) of `SalesSummaryByDay`, `...ByCustomer`, `...ByMaterial`, the high-value orders (`TotalNetAmountLocal`, also the `$filter` of the minimum), `PurchaseSummaryByDay`, `...BySupplier`, `...ByMaterialGroup`, the purchase items (`NetAmountLocal`) and the receivables summaries (`OpenAmountLocal`, `OverdueAmountLocal`). Rows carry `INR` as their currency, so a request for INR now includes every document currency.
- The intent-api registry (`registry.toml`, `RegistryMetricSource`) is not changed: the why analysis works per document currency.
- The `currency` parameter keeps its meaning: a request for another currency than the company currency finds no rows.
- Nothing else changes.

## Acceptance cases
- A summary row in dollars with a local amount is read as that rupee amount with currency `INR`; a rupee row is unchanged; the high-value orders query asks for `TotalNetAmountLocal`.
- Sales, purchase and receivables widgets built from mixed dollar and rupee rows count both in rupees.
- With butterfly 19 running, `sales-month`, `top-customers`, `month-on-month`, `fin-receivables`, `fin-ageing`, `fin-overdue`, `pur-spend` and `pur-vendors` equal the sums of the local amounts read directly from butterfly.

## Out of scope
Showing dollars, exchange rates in synapse-api, changing the intent-api path.

## Depends on
butterfly 19 (the local fields).
