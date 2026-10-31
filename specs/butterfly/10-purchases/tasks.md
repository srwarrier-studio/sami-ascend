# Tasks

- [x] 1. The contract change and the purchase value: `NetAmount` and `TransactionCurrency` on `PurchaseDelivery`, prices per raw material, the cancelled status. Done when the field table and example cases pass and the old data hashes still match except deliveries.
- [x] 2. The three purchase summaries in the drivers service. Done when the sum, cancelled, paging and example cases pass.
- [x] 3. The new events (price change, quantity change, demand growth, supplier switch) in the generator. Done when each event case passes, including the sales-to-purchase chain.
- [x] 4. The scenarios `purchase-price-rise`, `stock-up`, `demand-surge`, `quiet-purchases` and the held-back `supplier-switch` and `double-cause` with ground truth files. Done when their ground-truth cases pass.
- [ ] 5. The metric field in the ground truth files, the agreement and contract tests for every scenario, and the README. Done when the agreement and contract cases pass and the owner has looked at the scenarios.
