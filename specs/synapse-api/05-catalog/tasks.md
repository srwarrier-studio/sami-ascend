# Tasks

- [x] 1. `CatalogEntry`, `WidgetCatalog` port, `ListCatalog`, `GetWidgetData` and the sales widget mappers over the existing `SalesSource` methods, with tests. Done when the sales entries return the same props the web `load` did.
- [x] 2. `SalesSource.order_statuses` on the mock and butterfly sources, the `MONTHLY_SALES_TARGET` setting, and the day sales, month target and status split entries. Done when the source and entry cases pass.
- [ ] 3. `MockLibraryCatalog` with the library entries from `mockLibrary.ts`. Done when every old library id is listed with valid props.
- [ ] 4. The `/v1/synapse/catalog` routes with roles, 404 and the cache; close the phase. Done when the route cases pass.
