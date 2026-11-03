# Notes

- Checked live against butterfly 17 (story seed): shipments (20) and export value (2,144,770.40) so far this month, and 122 shipments in transit, equal direct reads of the export service.
- Exports are valued in rupees (`NetAmount` in the company currency of the contract); the dollar value of an order is in `DocumentAmount` and is not shown by the widgets.
- The sales KPI class now takes its value format from the subclass (`value_format`), so count KPIs use the same month-to-date comparison, partial note and trend as the money KPIs.
- Run synapse-api next to a butterfly that has the export service (butterfly 17); `EXPORT_BASE_URL` points at it.
- Still mock after this phase: Finance cash and collections (5 widgets: `fin-collections`, `fin-collection-target`, `fin-cashflow`, `fin-payments`, `fin-expenses`).
