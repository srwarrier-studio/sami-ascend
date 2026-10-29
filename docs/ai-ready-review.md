# AI-ready review (synapse-web 04, 2026-10-29)

Checked against what a small local model needs to build a board from widgets. Tests are in `apps/synapse-web/tests/aiReady.test.ts`.

| Need | Result | Notes |
|------|--------|-------|
| A list of widgets with name, description, size and JSON schema | Met | `registry.describe()`; JSON serializable, every widget has a description and size |
| A prompt that fits a small model | Met | Names plus descriptions are about 450 tokens (estimate); the full schemas are much larger, so give the model the short list first and a schema only for the widget it picked |
| No style choices for the model | Met | No colour, style, class or size props in any schema (tested) |
| Check a model answer before drawing it | Was a gap, fixed | Added `registry.validate(name, props)` and `parseAiBoard(json)` which rejects bad JSON, empty boards, unknown widgets and bad props with a message naming the widget |
| Safe fallback on bad props | Met | `registry.render` shows the fallback card |
| Data for widgets | Decision | A small model should not write data arrays (tables, series). For the POC let it pick a catalog entry by `id` (`catalog` has id, title, description) and fill only text such as title and measure; the catalog already loads real data. `parseAiBoard` still accepts raw props for the JSON-vs-OpenUI comparison |
| Catalog list for the model | Decision | `matchCatalog` is a keyword stand-in. The POC should hand the model `catalog` ids and descriptions and ask for a list of ids |
| Board shape | Met | `{ name, widgets: [{ widget, props }] }`; the store uses `{ id, catalogId }`, so map by catalog id |
| Layout control | Decision | Order only, spans come from `defaultW`; the model cannot place or size widgets, which suits a small model |
| Filters and dropdowns | Met | None exist; choosing the widget is the customisation |
| API support | Gap | `daySales` and `statusSplit` have no synapse-api route yet; design them in synapse-api 04 before the real data replaces the mock |
| Constrained output | Not tested | `registry.describe()` schemas are JSON Schema from zod; feeding them to the chosen runtime (Ollama `format`) is for the POC |
