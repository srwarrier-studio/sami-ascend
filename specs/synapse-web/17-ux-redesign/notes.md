# Notes

Items from the review that need an owner decision or another app:
- intent-api sentences use "INR 1,816,237.50" while tables use ₹ with Indian grouping.
- "Sales this month -58.3%" compares two days with a full month; the comparison should be like for like or say so.
- No "as of" time on the dashboard; synapse-api would have to return one.
- Gauge and day-sales chart (zero-valued closed days, heavy empty arc) live in `@sami/ui`.
- AI Mode has no app shell (phase decision kept); the only exit is a button.
- Microsoft sign-in button does nothing yet; no forgot-password link.
