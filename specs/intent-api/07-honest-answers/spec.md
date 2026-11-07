# intent-api/07 honest-answers

## Goal
An answer never replies to a different question than the one asked: it reads more of the ways a manager names a period, says when it assumed one, and refuses in plain words when it cannot apply a period, a named customer, a quantity or a top N.

## Why
Found on 2026-11-07 when the owner asked "whta is sales of current month" and got October 2026 (today was 7 November). `read_period.py` knows "this month", month names and years only; when it finds nothing it silently answers the last finished month. A probe of 55 phrasings (fixed date 7 November 2026) showed the same silent fallback for: current, present and previous month wording, MTD, month to date, YTD, year to date, "current year", this financial year, this quarter, Q3, third quarter, last quarter, H1, yesterday, today, this week, last week, last 30 days, last N months, past 12 months, "till date", "so far". Wrong or partial reads: "FY 2025-26" and "2025-26" read as 2025; "since april" read as April only; ranges ("from april to june", "between july and september", "jun, jul and aug") refused as "more than one period", and so is "September against August" because the comparison base is only recognised for "last month" and "last year". Reading the answer path also shows: a named customer, supplier, material or country is ignored (the scenario text promises it, the code has no filter, the figure is the company total), "top 3" always gives 5 (`top` setting), a quantity question ("how many kg of curcumin did we sell") gets a rupee figure, and an unsupported currency ("euros") is ignored.

## Behavior
- **Periods read.** Calendar: current, present and previous month, this and last quarter, Q1 to Q4, H1 and H2, this and last year, "so far this year", YTD, MTD, "since <month>", ranges ("from april to june", "between july and september", "jun, jul and aug"), "last N days, weeks or months" and "past N months". Financial year: April to March (owner to confirm), "this financial year", "FY 2025-26", "FY26", quarters of the financial year when written "FY Q3". A bare "Q3" means the calendar quarter unless FY is named.
- **Comparisons with two named periods** ("September against August", "Q2 vs Q1") answer as a comparison of those two periods; more than two periods is still refused.
- **Assumed period.** A question with no period words is answered for the last finished month and the answer says so ("No period was named, so this is October 2026"). The "How was this read?" panel shows the period as read.
- **Unreadable time words are refused, never defaulted.** If the question has a time word that is not read (yesterday, today, week, day, a date) the reply says which words it could not read and what it can read (month, quarter, year, financial year, ranges). Data is monthly, so day and week questions are refused honestly.
- **Qualifiers it cannot apply are refused.** A named customer, supplier, material or country (until a filter exists), a quantity or unit question (kg, tonnes, orders, number of), and a currency it does not hold are refused with a sentence; they never return the unfiltered figure. Owner decision below.
- **Top N.** "top 3", "top 10" are applied up to a maximum (owner to confirm 10); above that the answer says it shows the maximum.
- Wording is fixed templates; nothing is written by a model.

## Owner decisions needed before building
1. Financial year April to March? Fiscal quarters named only with "FY"?
2. Named customer, supplier, material or country: refuse now, or build the filter (needs the Synapse data to support it) in this phase?
3. Maximum top N.

## Acceptance cases
- The 55 phrasings of the probe each give a correct period or a refusal that names the unread words; none is answered with a different period without saying so.
- "whta is sales of current month" on 7 November 2026 answers November 2026, not complete, and says so.
- A question with no period says the month was assumed.
- "sales since april" covers April to the latest month; "from april to june" and "september against august" are answered.
- "sales to Nordhaven Pharma last month" never returns the company total unflagged.
- "top 3 customers" shows 3; "top 50" shows the maximum and says so.
- The 226 questions of `evals/questions.json` still match as before; new questions for each phrase family are added and held out.
- All tests pass.

## Out of scope
New scenarios, new domains, the classifier, the web layout (it only shows the new line), day-level data.

## Depends on
intent-api 06 (the eval questions).
