from datetime import date
from decimal import Decimal

from intent_api.domain.analysis.analysis import Analysis, Finding
from intent_api.domain.analysis.finding import Step

SCOPES = {"sabinsa": "Sami-Sabinsa", "neutraceuticals": "Sami Nutraceuticals", "organica": "Organica Aromatics"}
GROUP_LIMIT = "These are the figures of all your companies together; a cause inside one company can look smaller here."


def number(value: Decimal) -> str:
    return f"{value:,.0f}" if value == value.to_integral_value() else f"{value:,.2f}"


def percent_text(value: Decimal | None) -> str:
    return "" if value is None else f"{abs(value):.1f}%"


def month_label(day: date) -> str:
    return day.strftime("%B %Y")


def verb(change: Decimal) -> str:
    return "rose" if change > 0 else "fell" if change < 0 else "did not change"


def scope_label(company: str) -> str:
    return SCOPES.get(company, "all your companies")


def headline(analysis: Analysis, company: str) -> str:
    if not analysis.currency:
        return analysis.limits[0]
    label = f"{analysis.question.metric.capitalize()} of {scope_label(company)}"
    month, before = month_label(analysis.window.start), month_label(analysis.window.compare_start)
    amounts = f"{analysis.currency} {number(analysis.previous)} to {analysis.currency} {number(analysis.current)}"
    if analysis.change_percent is None:
        return f"{label} were {analysis.currency} {number(analysis.current)} in {month} and nothing in {before}."
    size = f" {percent_text(analysis.change_percent)}" if analysis.change != 0 else ""
    lead = f"{label} {verb(analysis.change)}{size} in {analysis.currency}" if analysis.significant else f"{label} were steady in {analysis.currency}: they {verb(analysis.change)}{size}"
    return f"{lead} from {before} to {month} ({amounts})."


def finding_sentence(analysis: Analysis, finding: Finding) -> str:
    text = f"{finding.name} {verb(finding.change)} {percent_text(finding.change_percent) or 'from nothing'} ({analysis.currency} {number(abs(finding.change))})"
    text += f", {finding.share_percent:.1f}% of the change." if analysis.significant and finding.share_percent is not None else "."
    if finding.kind == "price":
        text += f" Mostly price: the price effect is {analysis.currency} {number(abs(finding.price_effect))} and the volume effect {analysis.currency} {number(abs(finding.volume_effect))}."
    return text


def offset_sentence(analysis: Analysis, finding: Finding) -> str:
    return f"{finding.name} offset part of it: {verb(finding.change)} {percent_text(finding.change_percent) or 'from nothing'} ({analysis.currency} {number(abs(finding.change))})."


def step_sentence(step: Step, cause_key: str) -> str:
    n, label = step.numbers, step.label or step.node
    if step.kind == "coverage_gap":
        return f"no valid {label} for {n['days_uncovered']} days from {n['first_uncovered']} ({label} {cause_key})"
    if step.kind == "later_than":
        done = "still open" if n["open"] else f"done {n['done']}"
        reason = f", reason {n['reason']}" if n.get("reason") else ""
        return f"{label} {cause_key} being {n['days_late']} days late (due {n['due']}, {done}{reason})"
    if step.kind == "sum_changed":
        change = percent_text(n["change_percent"]) or "from nothing"
        return f"{label} totals going from {number(n['previous'])} to {number(n['current'])} ({change}) over the months leading up to it"
    if step.kind == "set_changed":
        parts = ([f"new {', '.join(n['new'])}"] if n["new"] else []) + ([f"gone {', '.join(n['gone'])}"] if n["gone"] else [])
        return f"the {n['field']} values of {label} changing: {'; '.join(parts)}"
    rising = n["current"] > n["previous"]
    return f"{label} {cause_key} {'rising' if rising else 'falling'} {percent_text(n['change_percent']) or 'from nothing'} over the months leading up to it"


def path_sentence(finding: Finding, path_index: int) -> str:
    offset = sum(len(p) for p in finding.paths[:path_index])
    path = finding.paths[path_index]
    parts = [step_sentence(step, finding.causes[offset + i].key) for i, step in enumerate(path)]
    text = f"This coincided with {parts[0]}"
    for deeper in parts[1:]:
        text += f", and behind that {deeper}"
    return text + "."


def unexplained_sentence(analysis: Analysis) -> str:
    if not analysis.significant:
        if analysis.findings:
            return "Overall the month was steady; the movements above are the ones with something behind them in the data we hold."
        return "Nothing unusual was found behind this month."
    if analysis.explained_percent == 0:
        return "No cause was found in the data we hold."
    return f"At least {analysis.explained_percent:.0f}% of the change is explained by what is listed above; {analysis.unexplained_percent:.0f}% is not explained by anything in the data we hold."


def other_currency_sentence(analysis: Analysis, currency: str, change_percent: Decimal | None) -> str:
    size = f" by {percent_text(change_percent)}" if change_percent is not None else ""
    return f"{analysis.question.metric.capitalize()} in {currency} also changed{size}; ask in {currency} to see why."


def lines(analysis: Analysis, company: str = "all") -> list[str]:
    out = [headline(analysis, company)]
    if not analysis.currency:
        return out
    for finding in analysis.findings:
        out.append(finding_sentence(analysis, finding))
        out += [path_sentence(finding, i) for i in range(len(finding.paths))]
    out += [offset_sentence(analysis, finding) for finding in analysis.offsets]
    out.append(unexplained_sentence(analysis))
    out += [other_currency_sentence(analysis, currency, change) for currency, change in analysis.other_currencies]
    out += analysis.limits
    if company == "all":
        out.append(GROUP_LIMIT)
    return out


def direction(change: Decimal) -> str:
    return "up" if change > 0 else "down" if change < 0 else "flat"


def change_text(finding: Finding) -> str:
    return percent_text(finding.change_percent) or "from nothing"


def amount_text(analysis: Analysis, finding: Finding) -> str:
    return f"{analysis.currency} {number(abs(finding.change))}"


def share_text(analysis: Analysis, finding: Finding) -> str | None:
    if analysis.significant and finding.share_percent is not None:
        return f"{finding.share_percent:.1f}% of the change"
    return None


def price_text(analysis: Analysis, finding: Finding) -> str | None:
    if finding.kind != "price":
        return None
    return f"Mostly price: the price effect is {analysis.currency} {number(abs(finding.price_effect))} and the volume effect {analysis.currency} {number(abs(finding.volume_effect))}."


def path_phrases(finding: Finding) -> list[list[str]]:
    phrases, offset = [], 0
    for path in finding.paths:
        phrases.append([step_sentence(step, finding.causes[offset + i].key) for i, step in enumerate(path)])
        offset += len(path)
    return phrases


def notes(analysis: Analysis, company: str) -> list[str]:
    out = [other_currency_sentence(analysis, currency, change) for currency, change in analysis.other_currencies]
    out += analysis.limits
    if company == "all":
        out.append(GROUP_LIMIT)
    return out
