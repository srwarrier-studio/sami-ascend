# Tasks

- [x] 1. Domain and use cases: entities, `SalesOrderGateway`, errors, `MockSalesOrderGateway`, `CreateSalesOrder`, `ListSalesOrders`; add `structured-logging` dependency and call `setup_logging`. Done when the mock and use-case acceptance cases pass.
- [ ] 2. Butterfly gateway create: `Settings`, `httpx` dependency (note in `tech-stack.md`), request mapping, `201` mapping, `400` to `SalesOrderRejected`, failures to `SapUnavailable`. Done when the create gateway cases pass with `MockTransport`.
- [ ] 3. Butterfly gateway list: query building, `@odata.count`, item mapping, request id header on both calls. Done when the list gateway cases pass.
- [ ] 4. README and `specs/notes.md`. Done when the README shows how to run tests and use the gateway.
