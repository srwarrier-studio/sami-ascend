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
