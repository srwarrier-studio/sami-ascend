from datetime import date
from decimal import Decimal

from sami_agents.domain.entities.analysis import Analysis, Finding
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
    lead = f"{label} {verb(analysis.change)} {percent_text(analysis.change_percent)}" if analysis.significant else f"{label} were steady: they {verb(analysis.change)} {percent_text(analysis.change_percent)}"
    return f"{lead} from {before} to {month} ({amounts})."


def finding_sentence(analysis: Analysis, finding: Finding) -> str:
    text = f"{finding.name} {verb(finding.change)} {percent_text(finding.change_percent) or 'from nothing'} ({analysis.currency} {number(abs(finding.change))})"
    text += f", {finding.share_percent:.1f}% of the change." if finding.share_percent is not None else "."
    if finding.kind == "price":
        text += f" Mostly price: the price effect is {analysis.currency} {number(abs(finding.price_effect))} and the volume effect {analysis.currency} {number(abs(finding.volume_effect))}."
    return text


def offset_sentence(analysis: Analysis, finding: Finding) -> str:
    return f"{finding.name} offset part of it: {verb(finding.change)} {percent_text(finding.change_percent) or 'from nothing'} ({analysis.currency} {number(abs(finding.change))})."


def step_sentence(step: Step, cause_key: str) -> str:
    n = step.numbers
    if step.kind == "coverage_gap":
        return f"no valid {step.node} for {n['days_uncovered']} days from {n['first_uncovered']} ({step.node} {cause_key})"
    if step.kind == "later_than":
        done = "still open" if n["open"] else f"done {n['done']}"
        reason = f", reason {n['reason']}" if n.get("reason") else ""
        return f"{step.node} {cause_key} was {n['days_late']} days late (due {n['due']}, {done}{reason})"
    if step.kind == "sum_changed":
        change = percent_text(n["change_percent"]) or "from nothing"
        return f"{step.node} totals went from {number(n['previous'])} to {number(n['current'])} ({change})"
    if step.kind == "set_changed":
        parts = ([f"new {', '.join(n['new'])}"] if n["new"] else []) + ([f"gone {', '.join(n['gone'])}"] if n["gone"] else [])
        return f"the {n['field']} values of {step.node} changed: {'; '.join(parts)}"
    return f"{step.node} {cause_key} {verb(n['current'] - n['previous'])} {percent_text(n['change_percent']) or 'from nothing'}"


def path_sentence(finding: Finding, path_index: int) -> str:
    offset = sum(len(p) for p in finding.paths[:path_index])
    path = finding.paths[path_index]
    parts = [step_sentence(step, finding.causes[offset + i].key) for i, step in enumerate(path)]
    text = f"This coincided with {parts[0]}"
    for deeper in parts[1:]:
        text += f", and behind that {deeper}"
    return text + "."


def unexplained_sentence(analysis: Analysis) -> str:
    if not analysis.findings and not analysis.significant:
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
