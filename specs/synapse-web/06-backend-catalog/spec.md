# synapse-web/06 backend-catalog

## Goal
synapse-web logs in through auth-api and gets the catalog and every widget's data from synapse-api, so the app holds only views and thin HTTP clients.

## Behavior
- `HttpSessionClient` implements `SessionClient` against auth-api: `login` posts to `${VITE_AUTH_URL}/login/password`, `me` gets `/me`, `logout` posts `/logout`, all with `credentials: 'include'` (auth-api sets the `access_token` cookie and allows `FRONTEND_URL`). A 401 from `/me` is signed out. `main.tsx` uses it; `MockSessionClient` stays for tests.
- `CatalogClient` (interface): `list()` and `data(id)`. `HttpCatalogClient` calls `${VITE_SYNAPSE_URL}/v1/synapse/catalog` and `/catalog/{id}/data` with credentials; `MockCatalogClient` serves fixtures for tests. A non-OK status is an error with the server's message; 401 sends the user to `/login`.
- The catalog is loaded once after sign-in and reaches pages through router context (`catalog`: the entries). Nothing imports a constant catalog any more: the board grid, widget library, `/widgets` page and the AI mock planner read it from context. `matchCatalog` takes the entries as an argument.
- `CatalogWidget` fetches `data(id)` from the client (no more `load(data)` and no `SalesData`), refreshes every 5 minutes without a skeleton flash, and shows the error alert as today.
- Removed from synapse-web: `catalog.ts` entries and `load` functions, `libraryEntries.ts`, `SalesData` and `MockSalesData`, and the import of `mockLibrary`. `@sami/ui` keeps `mockLibrary` for the playground.
- The board store is still the mock (`BoardStore`); synapse-api 04 replaces it later.

## Acceptance cases
- Session: login success sets the user; wrong password returns false; 401 on `/me` is signed out; logout calls the endpoint; requests send credentials (fake fetch).
- Catalog client: list and data parse; non-OK is an error with the message; 401 redirects to login.
- App: after login the board shows the widgets fetched by id; the widget library, `/widgets` and AI Mode list the loaded catalog; a failing data call shows that widget's error and the others still draw; the 5-minute refresh calls `data(id)` again without a skeleton.
- No synapse-web file imports a constant catalog, `SalesData` or `mockLibrary`.

## Out of scope
Board storage (synapse-api 04), AI (phases 06 and 07), Entra login button wiring, resizing the catalog UI.

## Depends on
synapse-api 05, auth-api 03, synapse-web 05.
