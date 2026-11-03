# Notes

- Measured on the story seed (4,175 orders) with a real server: first start builds the database in about 1.1 s, a restart that keeps it takes 0.6 s, `SalesOrder?$top=1000` answers in 45 ms, `ReceivablesSummary` in 12 ms, `SalesSummaryByDay` in 14 ms. The whole butterfly suite (1,033 tests) runs in about 95 s either way.
- `BUTTERFLY_STORE=sqlite` runs every test against SQLite; the default run already uses SQLite through `build_default_app` (tests set `BUTTERFLY_DB=:memory:`).
- The default file is `apps/butterfly/butterfly.db` (ignored by git, with its `-wal` and `-shm` files).
- Summary rows: when two orders of one customer on one day carry different customer names, the view shows the alphabetically first (`MIN`); the old code showed the first order's. The seed has none.
- Next: butterfly 14 to 18 (material group, inventory, exports, production output, payments), each with its `docs/sap/` contract first.
