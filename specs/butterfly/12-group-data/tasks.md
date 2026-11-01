# Tasks: butterfly/12 group-data

- [x] 1a. Sales service contract: `CompanyCode` and `Country` on `SalesOrder`, `CompanyCode` in the three sales summaries and the create rule, in the contract, examples and code, with one placeholder company (`INA1`) and country (`IN`). Done when the sales contract tests describe the new fields and the create-validation cases pass.
- [x] 1b. Drivers service contract: `CompanyCode` on contracts, deliveries, production orders, components, invoices and every purchase and receivables summary, and the consultant questions. Done when the drivers contract and summary tests pass with the placeholder company.
- [x] 2. Companies, products, customers and currencies for sales: the master data per company, orders, items, contracts and the sales summaries carry `CompanyCode`, `Country` and `USD`/`INR`. Done when the company, no-steel, currency and write-validation cases pass for sales and the hashes are re-pinned.
- [x] 3. Purchases and production: suppliers, raw materials, deliveries, production orders, components and the purchase summaries follow the new products and companies. Done when the same cases pass for the drivers service.
- [ ] 4. Invoices and receivables follow the new customers, currencies and companies. Done when the invoice and receivable cases pass per company.
- [ ] 5. Scenarios: events, ground truth files, agreement tests and the README use the new names. Done when every scenario's ground truth holds and the owner has looked at the data.
