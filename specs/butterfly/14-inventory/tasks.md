# Tasks

- [x] 1. Contract and questions. Done when `docs/sap/inventory-contract.md` and questions 18 to 26 are written and the owner has read them.
- [x] 2. Master data and the stock story: material groups, plants and storage locations, and the generator of movements and stock from the existing seeds, in memory and in SQLite. Done when the consistency cases (stock = opening + receipts − issues, never negative, ties to purchases, production and sales) pass.
- [x] 3. `MaterialStock` and `StockMovement` served with the service root, fields, filters and the contract examples tested. Done when they match the contract tables and the examples.
- [x] 4. The six summaries as views and the month-end valuation, with their hand-total tests. Done when each summary equals its hand total and the stock-value tie holds.
- [ ] 5. README, `docs/sap/` index, empty inventory for the small seed, missing data added on an existing database. Done when the whole butterfly suite passes on both stores.
