# synapse-web/18 board-overview

## Goal
The summary strip above a board is written from the widgets that are on that board, so a custom board with sales, purchase and receivables widgets gets an overview of those three topics, and a board with only sales widgets gets sales sentences only.

## Why
The strip (synapse-web 17, B3) always writes about sales. A manager builds boards by topic; the overview should follow the board. It reaches into synapse-api (the summary endpoint) on this branch, as phase 17 did; the owner approved that.

## Behavior
- **Request.** `GET /v1/synapse/summary?widgets=<id>,<id>,...&currency=INR&company=...` takes the catalog ids on the board. The web sends the ids of the active board and asks again when they change. An unknown id is ignored; no ids, or none that belong to a topic, return no sentences. At most 30 ids.
- **Topics and writers.** A topic is written when the board has at least one of its widgets. Each writer lists the widget that licenses each sentence, so a sentence only appears when the board shows the data behind it:
  | Topic | Widgets of the topic | Sentences (in this order) |
  |-------|----------------------|---------------------------|
  | Sales | `sales-today`, `sales-month`, `sales-year`, `orders-month`, `month-on-month`, `day-sales`, `high-value-sales`, `top-customers`, `top-materials`, `month-target`, `status-split` | headline (always); pace against target (with `month-target`); biggest customer mover (with `top-customers`) |
  | Purchases | the six `pur-*` that are real (`pur-spend`, `pur-open`, `pur-trend`, `pur-vendors`, `pur-recent`, `pur-ontime`) | headline (always); on-time share (with `pur-ontime`); open items (with `pur-open`); biggest supplier (with `pur-vendors`) |
  | Receivables | `fin-receivables`, `fin-ageing`, `fin-overdue` | headline (always); customer with most overdue (with `fin-overdue`); amount more than 30 days past due (with `fin-ageing`) |
  Other widgets (still mock) license nothing.
- **Length.** At most two sentences per topic, topics in the order Sales, Purchases, Receivables.
- **Sales sentences** are those of phase 17 B3. **Purchases headline:** `Purchases this month are <amount> (<days>[, N of M days so far]), up|down X% on <days>.`; while nothing has been ordered yet this month it reads `No purchase orders raised yet this month; last month's total was <amount>.` (butterfly and SAP place orders about the 24th). **On-time:** `<N>% of purchase items due in the last 90 days arrived by the promised date (a of b).` **Open items:** `<n> purchase items are still open.` **Supplier:** `<name> is the biggest supplier this month: <amount> (<share>% of purchases).` **Receivables headline:** `<amount> is outstanding from customers, <overdue> (<share>%) of it past its due date.` **Most overdue:** `<name> has the most overdue: <amount>.` **Ageing:** `<amount> is more than 30 days past due.`
- A sentence whose data is missing is left out. Amounts are in the requested currency (default INR), Indian grouping for INR.
- Cache key includes the sorted set of ids.
- **Web.** `SummaryStrip` sends the active board's catalog ids; the strip is drawn the same way (sentences, `Ask AI for more`). Switching boards or adding or removing a widget refreshes it.
- Nothing else changes in the strip.

## Acceptance cases
- A board with `sales-month` only gets the sales headline; adding `month-target` adds the pace sentence; adding `top-customers` adds the mover (still two at most, pace first).
- A board with `sales-month`, `pur-ontime` and `fin-receivables` gets sales, purchases and receivables headlines/sentences, in that order.
- A board with only mock widgets, or no ids, returns no sentences and the strip is not drawn.
- Purchases early in the month with no orders says no orders raised yet and gives last month's total.
- The web asks with the ids of the board shown and asks again after a widget is added.

## Out of scope
Inventory, Exports and Production topics (they follow their butterfly phases), writing the overview with a model, the PDF export, per-company sentences.

## Depends on
synapse-api 11 (purchase and receivables sources), synapse-web 17 (strip, KPI fields).
