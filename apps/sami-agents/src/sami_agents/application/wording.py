from datetime import date
from decimal import Decimal

from sami_agents.domain.entities.analysis import Analysis, Finding
from sami_agents.domain.entities.figure import Figure
from sami_agents.domain.entities.finding import Step


def number(value: Decimal) -> str:
    return f"{value:,.0f}" if value == value.to_integral_value() else f"{value:,.2f}"


def percent_text(value: Decimal | None) -> str:
    return "" if value is None else f"{abs(value):.1f}%"


def month_label(day: date) -> str:
    return day.strftime("%B %Y")


def verb(change: Decimal) -> str:
    return "rose" if change > 0 else "fell" if change < 0 else "did not change"


def headline(analysis: Analysis) -> str:
    if not analysis.currency:
        return analysis.limits[0]
    label = analysis.question.metric.capitalize()
    month, before = month_label(analysis.window.start), month_label(analysis.window.compare_start)
    amounts = f"{analysis.currency} {number(analysis.previous)} to {analysis.currency} {number(analysis.current)}"
    if analysis.change_percent is None:
        return f"{label} were {analysis.currency} {number(analysis.current)} in {month} and nothing in {before}."
    size = f" {percent_text(analysis.change_percent)}" if analysis.change != 0 else ""
    lead = f"{label} {verb(analysis.change)}{size}" if analysis.significant else f"{label} were steady: they {verb(analysis.change)}{size}"
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


def lines(analysis: Analysis) -> list[str]:
    out = [headline(analysis)]
    if not analysis.currency:
        return out
    for finding in analysis.findings:
        out.append(finding_sentence(analysis, finding))
        out += [path_sentence(finding, i) for i in range(len(finding.paths))]
    out += [offset_sentence(analysis, finding) for finding in analysis.offsets]
    out.append(unexplained_sentence(analysis))
    out += analysis.limits
    return out


def figure_lines(figure: Figure) -> list[str]:
    label, month = figure.question.metric.capitalize(), month_label(figure.window.start)
    if not figure.currency:
        return [f"No {figure.question.metric} were recorded in {month}."]
    amount = f"{figure.currency} {number(figure.current)}"
    if figure.so_far:
        return [f"{label} so far this month ({month}) were {amount}."]
    before = month_label(figure.window.compare_start)
    if figure.change_percent is None:
        return [f"{label} for {month} were {amount}, up from nothing in {before}."]
    previous = f"{figure.currency} {number(figure.previous)}"
    if figure.change == 0:
        sentence = f"{label} for {month} were {amount}, unchanged from {before} ({previous})."
    else:
        direction = "up" if figure.change > 0 else "down"
        sentence = f"{label} for {month} were {amount}, {direction} {percent_text(figure.change_percent)} from {before} ({previous})."
    if not figure.significant:
        return [sentence]
    word = "rose" if figure.change > 0 else "fell"
    return [sentence, f"Ask why {figure.question.metric} {word} in {figure.window.start.strftime('%B')} for the reasons."]
