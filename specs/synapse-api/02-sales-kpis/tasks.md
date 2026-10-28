# Tasks

- [ ] 1. Domain results and `InvalidQuery`. Done when the four result dataclasses and the error exist and a test builds each.
- [ ] 2. Period totals: `GetTodaySales`, `GetMonthToDateSales`, `GetYearToDateSales`. Done when their acceptance cases pass against `MockSalesSource`.
- [ ] 3. `GetMonthOnMonthSales` and `GetRecentHighValueOrders`. Done when MoM (zero months, year boundary, order) and pass-through cases pass.
- [ ] 4. `GetTopCustomers` and `GetTopMaterials`. Done when ranking, `top` cut, ties and per-currency cases pass.
- [ ] 5. `SalesCache` and `Settings.CACHE_SECONDS`. Done when all cache cases pass with a fake clock; notes updated in `specs/notes.md`.
