# synapse-web/17 ux-redesign

## Goal
Fix the problems a UI/UX review of the running app found on the login page, the boards dashboard and AI Mode, without new services or new widgets.

## Why
A review of the rendered app (2026-11-02) found: an off-topic question ("what is the weather today") answered with unrelated sales widgets; the technical "Reading" card under every answer; no feedback while signing in or when the server is down; a crowded dashboard header where "Add widget" outranks reading; a silent switch into edit mode.

## Behavior
- **Login.** The form is disabled and shows a spinner while the request runs. A wrong password says "Incorrect email or password"; an unreachable service says "Cannot reach the sign-in service. Try again in a moment." (a different message, so a right password is not retried).
- **AI Mode, off-topic.** When intent-api reads a question as `not_about_business`, the widget planner is not asked. The reply says what AI Mode can do and offers the example questions as buttons. Every other refusal still falls through to the planner (phase 14).
- **AI Mode, reading card.** The card becomes a closed `How was this read?` disclosure under an answer; it stays open when intent-api refused and nothing answered. Content is unchanged.
- **AI Mode, suggestions.** `Did you mean Sales or Purchase?` becomes one button per domain that asks `Show <domain>` again.
- **AI Mode, waiting.** `Thinking…` becomes an animated three-dot indicator (still text for screen readers, still no animation under reduced motion). The message list is a `role="log"` live region.
- **AI Mode, scrolling.** After a reply the list scrolls to the start of the new answer, not its end, so the question and the first lines stay in view.
- **AI Mode, welcome.** The welcome splits examples into `Ask a question` and `Build a board`, with a one-line explanation of `@builder`.
- **Dashboard header.** `Edit` (`Done` while editing) is the one filled button; `Add widget` is outlined and still starts editing as it does today. `Export PDF` moves into a `More` menu next to `AI Mode`. While editing a banner reads `Editing. Changes save automatically. Press Done when finished.`
- Nothing else changes: AI Mode keeps its full screen layout, the Microsoft button, boards, presets, export, widgets.

## Acceptance cases
- Login shows busy, then the right message for a wrong password and for an unreachable service.
- "what is the weather today" with a `not_about_business` reading shows the explanation, example buttons, and no widgets; a `no_scenarios` refusal still shows widgets.
- The reading disclosure is closed on an answer and open on a refusal; a `Did you mean` button sends a new question.
- The log region exists; the thinking indicator shows while a reply is awaited.
- `Edit` is the filled button and `Add widget` still opens the library; `Export PDF` is in the `More` menu; editing shows the banner.

## Out of scope
Number format in intent-api sentences ("INR 1,816,237.50" next to "₹18,16,238"), month-to-date comparisons (-58.3% for two days against a month), an "as of" time for figures, the gauge and day-sales chart styling in `@sami/ui`, a forgot-password flow, the Microsoft sign-in, putting AI Mode inside the app shell, mobile layout. Each needs an owner decision or a backend change; see notes.md.

## Depends on
synapse-web 16 (merged).

# Part B: the dashboard tells the story

Added 2026-11-02 at the owner's request, after a review that found the Sales overview board "shows numbers but does not tell the story". It reaches into synapse-api and `@sami/ui` on this branch; the owner approved that in chat. Items are in priority order and are built in that order.

## Findings that shape the plan
- The comparisons are already like-for-like in synapse-api (`month_periods`, `year_periods` compare the same days). The problem is the wording: `vs last month` does not name the days, and two days against two days is too small a base to call a trend. The earlier review note that two days were compared with a full month was wrong.
- "Sales today" equals "Sales this month" whenever nothing was sold earlier in the month (Nov 1 was a Sunday). The data is right; the card does not say which days it covers.
- "Why did sales change last month?" returned generic sales cards because the running intent-api process started before the `why` scenarios were merged, so it had no rule for `sales_why` and refused with `not_answerable_yet`; the web then fell through to the keyword widget planner, which matched "sales" and drew unrelated cards. A fresh process loads the rule.

## B1. Honest comparisons (synapse-api, `@sami/ui`)
- Each sales KPI returns `period` and `comparedWith` as readable day ranges (`1–2 Nov`, `1–2 Oct`; today is `Mon 2 Nov` against `Sun 1 Nov`; year is `1 Jan–2 Nov` against the same days a year earlier), and the card caption becomes `<period> vs <comparedWith>`.
- A KPI is `partial` when fewer than 7 days of its month have passed, or fewer than 7 days are in the window for the month and year cards. A partial card returns `note: "2 of 31 days so far"`, draws its change in neutral grey, and shows the note under the caption.
- When the month so far equals today (nothing earlier in the month), the month card says so through its labels (`1–2 Nov`, `Sun 1 Nov: no sales`) and not through a different number.
- Acceptance: Nov 2 with a sale only on the 2nd gives the month card `period "1–2 Nov"`, `comparedWith "1–2 Oct"`, `partial true`, `note "2 of 30 days so far"`; the same data on Nov 20 is not partial.

## B2. As of and period on every headline widget (synapse-api, `@sami/ui`)
- The catalog data endpoint adds `asOf` (UTC ISO time the figures were read, taken inside the cached load, so a cached answer keeps its original time). Headline widgets are the four KPI cards, month target and the two charts.
- `KpiCard` and `GaugeChart` take `asOf` and show `as of 22:41` (local time) at the right of the title row; the period is in the caption (B1), the gauge already says `this month`.
- Acceptance: a cached read returns the same `asOf` twice; the KPI shows the time; a card without `asOf` shows nothing.

## B3. A summary strip (synapse-api, synapse-web)
- `GET /v1/summary` (same roles and company scope as the catalog, same cache) returns `{asOf, currency, sentences: [...]}` with at most three sentences made by fixed templates from the same data, no model:
  1. Headline: sales so far this month against the same days last month, with `(2 of 30 days)` while partial.
  2. Biggest mover: the customer with the largest absolute change this month so far against the same days last month, with the amount.
  3. Behind or ahead of target: share of the target reached against share of the month gone, only when a target is set.
- A sentence whose data is missing is left out; no data at all returns an empty list and the strip is not drawn.
- The web draws the strip above the board with `as of <time>`; a failed request draws nothing.
- Acceptance: with data the endpoint returns the three sentences in that order; no target gives two; a customer-less month gives two; the company scope applies.

## B4. Key widgets open into the answer (synapse-web)
- The sales KPI cards, Day sales and Month-on-month sales get a `Why?` button that opens AI Mode with `Why did sales change last month?` already sent (route search `ask`, sent once).
- Top customers, Top materials and Recent high-value sales get `See all`, which opens a modal with the first 20 rows (the data endpoint takes `top`, 1 to 20 for these three, default as today).
- Neither shows while editing a board, and neither is drawn when the card fails to load.
- Acceptance: `Why?` lands in AI Mode and the question is asked once, also after a reload of the same URL; `See all` asks for 20 rows and shows them.

## B5. Colour only for what needs attention (`@sami/ui`, synapse-api)
- `KpiCard` draws a change in neutral grey; only a fall worse than 10% is drawn red with its arrow; a rise is never green. Partial cards (B1) are always neutral.
- The invoice status split no longer paints Completed green; only a slice named `Overdue` keeps the red tone.
- Acceptance: +5% and +37% are grey, -5% is grey, -12% is red, a partial -58% is grey with its note.

## B6. A real answer to a why question (synapse-web)
- When intent-api read a `*_why` scenario and could not answer (`not_answerable_yet` or any refusal), AI Mode says `I could not explain that change right now.` and offers the answerable examples; it does not fall through to the keyword widget planner. Other refusals keep falling through as in phase 14.
- A running intent-api must be restarted after a merge. The owner restarts it; this phase does not touch the owner's servers.
- Acceptance: a `sales_why` reading with `not_answerable_yet` shows the sentence and no widgets; a Finance refusal still shows widgets.

## Out of scope for Part B
Real SAP `asOf` posting times, per-company targets, explaining each KPI inside its own card, exporting the strip to the PDF, a model-written summary, changing intent-api.
