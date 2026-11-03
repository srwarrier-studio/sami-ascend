# Notes

- Checked live against butterfly 14 (story seed): stock value, items below reorder level (7, of which 4 out of stock) and availability (88.9%) equal direct reads of `MaterialStock`.
- The headline can read "down 6.1% on the end of Oct": today's value includes the stock-count write-offs (`702`) butterfly posts today for about one material in nine. That is the seed's story, not a calculation error.
- `inv-warehouses` shows six bars for the group view (three plants, two stores each) and two for a single company.
- Run synapse-api next to a butterfly that has the inventory service (butterfly 14); `INVENTORY_BASE_URL` points at it. Without it the inventory widgets fail with the usual "SAP is not reachable" card.
- Still mock after this phase: Exports (7), Production (7), Finance cash and collections (5), Purchase by category (2).
