# Tasks: butterfly/12 group-data

- [ ] 1. The contract: `CompanyCode` and `Country` in the field tables, examples, summary keys and the write rules, and the consultant questions. Done when the contract tests describe the new fields (butterfly still passes with one placeholder company).
- [ ] 2. Companies, products, customers and currencies for sales: the master data per company, orders, items, contracts and the sales summaries carry `CompanyCode`, `Country` and `USD`/`INR`. Done when the company, no-steel, currency and write-validation cases pass for sales and the hashes are re-pinned.
- [ ] 3. Purchases and production: suppliers, raw materials, deliveries, production orders, components and the purchase summaries follow the new products and companies. Done when the same cases pass for the drivers service.
- [ ] 4. Invoices and receivables follow the new customers, currencies and companies. Done when the invoice and receivable cases pass per company.
- [ ] 5. Scenarios: events, ground truth files, agreement tests and the README use the new names. Done when every scenario's ground truth holds and the owner has looked at the data.
