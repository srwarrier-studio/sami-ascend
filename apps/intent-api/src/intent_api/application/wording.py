from decimal import Decimal

from intent_api.domain.entities.figures import Comparison, MonthFigure, Row
from intent_api.domain.entities.period import Period

NOUNS = {"customer": "customers", "supplier": "suppliers", "material": "materials"}


def number(value: Decimal) -> str:
    return f"{value:,.0f}" if value == value.to_integral_value() else f"{value:,.2f}"


def money(currency: str, value: Decimal) -> str:
    return f"{currency} {number(value)}"


def percent_text(value: Decimal) -> str:
    return f"{abs(value):.1f}%"


def nothing_recorded(metric: str, period: Period) -> str:
    return f"No {metric} were recorded in {period.label}."


def value_line(metric: str, period: Period, comparison: Comparison) -> str:
    lead = f"{metric.capitalize()} so far in {period.label} were" if not period.complete else f"{metric.capitalize()} for {period.label} were"
    return f"{lead} {money(comparison.currency, comparison.current)}."


def compare_line(metric: str, period: Period, before: str, comparison: Comparison) -> str:
    lead = f"{metric.capitalize()} so far in {period.label} were" if not period.complete else f"{metric.capitalize()} for {period.label} were"
    amount = money(comparison.currency, comparison.current)
    previous = money(comparison.currency, comparison.previous)
    if comparison.change_percent is None:
        return f"{lead} {amount}, up from nothing in {before}."
    if comparison.change == 0:
        return f"{lead} {amount}, unchanged from {before} ({previous})."
    direction = "up" if comparison.change > 0 else "down"
    return f"{lead} {amount}, {direction} {percent_text(comparison.change_percent)} from {before} ({previous})."


def trend_line(metric: str, figure: MonthFigure) -> str:
    first, last = figure.trend[0], figure.trend[-1]
    start = f"{first.year}-{first.month:02d}"
    end = f"{last.year}-{last.month:02d}"
    began, ended = money(figure.currency, first.amount), money(figure.currency, last.amount)
    if first.amount == 0:
        return f"{metric.capitalize()} were {ended} in {end}, from nothing in {start}."
    change = (last.amount - first.amount) / first.amount * 100
    if change == 0:
        return f"{metric.capitalize()} were unchanged between {start} ({began}) and {end} ({ended})."
    direction = "up" if change > 0 else "down"
    return f"{metric.capitalize()} went {direction} {percent_text(change)} from {start} ({began}) to {end} ({ended})."


def ranking_line(metric: str, by: str, period: Period, comparison: Comparison, leader: Row) -> str:
    share = f" ({percent_text(leader.current / comparison.current * 100)} of {money(comparison.currency, comparison.current)})" if comparison.current else ""
    return f"{leader.name} led {metric} in {period.label} at {money(comparison.currency, leader.current)}{share}."


def ranking_title(by: str, period: Period, currency: str, multiple: bool) -> str:
    suffix = f" ({currency})" if multiple else ""
    return f"Top {NOUNS[by]}, {period.label}{suffix}"


def truncated_line(by: str, top: int) -> str:
    return f"Only the {top} {NOUNS[by]} with the biggest change were read, so a large one that barely changed may be missing."


READABLE = "Data is monthly, so I can read a month, a quarter, a year, a financial year (April to March) or a range such as April to June."


def period_refusal(detail: str, periods: list[str]) -> str:
    named = ", ".join(f"\u201c{item}\u201d" for item in periods)
    if detail == "time words that cannot be read":
        return f"I could not read {named} as a period. {READABLE}"
    if detail == "a period that has not started":
        return f"{named} has not started yet, so there is nothing to report. {READABLE}"
    if detail.startswith("more than") and detail.endswith("periods"):
        return f"You named {len(periods)} periods ({', '.join(periods)}), which is more than I can show at once. Ask for up to {detail.split()[2]}."
    return f"I could not settle on one period: {', '.join(periods)}. {READABLE}"


def qualifier_refusal(names: list[str], quantities: list[str], currencies: list[str]) -> str:
    quoted = lambda items: ", ".join(f"\u201c{item}\u201d" for item in items)
    sentences = []
    if names:
        sentences.append(f"I cannot filter by a named customer, supplier, material or country yet ({quoted(names)}), so I will not give you the company-wide figure as if it were theirs.")
    if quantities:
        sentences.append(f"I hold values in money, not quantities or counts ({quoted(quantities)}).")
    if currencies:
        sentences.append(f"I only hold rupees and dollars, not {quoted(currencies)}.")
    return " ".join(sentences)


def top_limit_line(asked: int, shown: int) -> str:
    return f"You asked for the top {asked}; I show at most {shown}."
