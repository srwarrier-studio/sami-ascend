from dataclasses import dataclass, field


def predicate(cause: dict):
    kind, key = cause["type"], cause["key"]
    table = {
        "contract": lambda t: t["source"] == "record:contract",
        "purchase_delivery": lambda t: t["source"] == "record:purchase_delivery" and t["kind"] == "later_than",
        "production_order": lambda t: t["source"] == "record:production_order" and t["kind"] == "later_than",
        "price_change": lambda t: t["kind"] == "price_effect",
        "purchase_price_change": lambda t: t["kind"] == "price_effect",
        "purchase_quantity_change": lambda t: t["source"] == "record:purchase_delivery" and t["kind"] == "sum_changed",
        "supplier_switch": lambda t: t["source"] == "record:purchase_delivery" and t["kind"] == "set_changed",
        "demand_growth": lambda t: t["kind"] == "value_changed" and t["source"].startswith("metric:sales"),
    }
    match = table.get(kind, lambda t: False)
    return lambda tag: match(tag) and tag["key"] == key


@dataclass
class Score:
    scenario: str
    found: list[str] = field(default_factory=list)
    missed: list[str] = field(default_factory=list)
    invented: list[str] = field(default_factory=list)
    blamed: list[str] = field(default_factory=list)
    change_ok: bool = True
    unexplained_ok: bool = True
    quiet_ok: bool = True
    passed: bool = False


def path_tag_groups(finding: dict) -> list[list[dict]]:
    groups, offset = [], 0
    for path in finding["paths"]:
        groups.append(finding["causes"][offset:offset + len(path)])
        offset += len(path)
    return groups or ([finding["causes"]] if finding["causes"] else [])


def describe(tag: dict) -> str:
    return f"{tag['kind']} {tag['key']} ({tag['source']})"


def score(scenario: str, truth: dict, answer: dict) -> Score:
    result = Score(scenario)
    analysis = answer["analysis"]
    findings = analysis["findings"] if analysis else []
    groups = [group for finding in findings for group in path_tag_groups(finding)]
    wanted = [(f"{c['type']} {c['key']}", predicate(c)) for c in truth["causes"]]
    for label, match in wanted:
        (result.found if any(match(t) for group in groups for t in group) else result.missed).append(label)
    matches = [match for _, match in wanted]
    for group in groups:
        if not any(m(t) for m in matches for t in group):
            result.invented += [describe(t) for t in group]
    keys = {t["key"] for group in groups for t in group}
    result.blamed = [f"{n['type']} {n['key']}" for n in truth["not_blame"] if n["key"] in keys]
    low, high = truth["total_change_percent"]
    result.change_ok = bool(analysis) and low <= float(analysis["change_percent"]) <= high
    if truth["unexplained"]:
        largest = findings[0]["key"] if findings else None
        result.unexplained_ok = bool(analysis) and (float(analysis["unexplained_percent"]) >= 50 or largest == truth.get("biggest_mover"))
    if not truth["causes"] and not truth["unexplained"]:
        result.quiet_ok = not findings
    result.passed = not (result.missed or result.invented or result.blamed) and result.change_ok and result.unexplained_ok and result.quiet_ok
    return result
